import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
# from duckduckgo_search import DDGS
import DDGS

# --- CONFIGURATION ---
st.set_page_config(page_title="Sentinel Terminal", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {background-color: #0E1117; padding: 10px; border-radius: 5px; border: 1px solid #262730;}
</style>
""", unsafe_allow_html=True)

# --- SETUP ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("❌ Secrets missing!")
    st.stop()

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- LIVE MARKET DATA FRAGMENT ---
@st.fragment(run_every=30)
def show_market_data(ticker):
    if not ticker: return
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        current = info.last_price
        prev = info.previous_close
        change = current - prev
        pct = (change / prev) * 100
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric(label=f"{ticker} PRICE", value=f"${current:.2f}", delta=f"{change:.2f} ({pct:.2f}%)")
        with col2:
            hist = stock.history(period="1mo")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color='#00C0F2', width=2), fill='tozeroy', fillcolor='rgba(0, 192, 242, 0.1)'))
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=100, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
    except:
        st.warning("Market data unavailable.")

# --- AGENT: LIVE RESEARCHER (DuckDuckGo) ---
def perform_live_research(ticker):
    with st.status(f"🕵️ Agent researching {ticker}...", expanded=True) as status:
        status.write("Searching internet...")
        results = []
        try:
            with DDGS() as ddgs:
                news_gen = ddgs.text(f"{ticker} stock news", max_results=5)
                for r in news_gen:
                    results.append(r)
        except Exception as e:
            status.update(label="Search Failed", state="error")
            return

        status.write("Memorizing data...")
        for article in results:
            full_text = f"{article['title']}. {article['body']}"
            embedding = model.encode(full_text).tolist()
            data = {
                "ticker": ticker.upper(),
                "headline": article['title'],
                "content": article['body'],
                "published_at": datetime.utcnow().isoformat(),
                "embedding": embedding
            }
            try:
                supabase.table('market_news').insert(data).execute()
            except:
                continue
        
        status.update(label="Knowledge Base Updated!", state="complete", expanded=False)

# --- MAIN UI ---
st.title("🛡️ Sentinel Terminal")

col1, col2 = st.columns([1, 4])
with col1:
    active_ticker = st.text_input("TICKER", value="NVDA").upper()

show_market_data(active_ticker)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Ask about {active_ticker}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. Search DB with Ticker Filter
        query_vector = model.encode(prompt).tolist()
        
        # Try to call the filtered function first
        try:
            response = supabase.rpc(
                'match_documents', 
                {
                    'query_embedding': query_vector, 
                    'match_threshold': 0.5, 
                    'match_count': 5,
                    'filter_ticker': active_ticker
                }
            ).execute()
            matches = response.data
        except:
            # Fallback if you haven't updated the SQL function yet
            response = supabase.rpc(
                'match_documents', 
                {'query_embedding': query_vector, 'match_threshold': 0.5, 'match_count': 5}
            ).execute()
            matches = response.data

        # 2. If no matches, Research & Retry
        if not matches:
            perform_live_research(active_ticker)
            # Retry Search
            try:
                response = supabase.rpc('match_documents', {'query_embedding': query_vector, 'match_threshold': 0.5, 'match_count': 5, 'filter_ticker': active_ticker}).execute()
            except:
                response = supabase.rpc('match_documents', {'query_embedding': query_vector, 'match_threshold': 0.5, 'match_count': 5}).execute()
            matches = response.data

        # 3. Generate Answer
        context_str = "\n".join([f"- {m['headline']}: {m['content']}" for m in matches])
        
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are a financial analyst. Answer using this context. If context is empty, admit it. Context: {context_str}"},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
        if matches:
            with st.expander("📚 Sources"):
                for m in matches:
                    st.write(f"- {m['headline']}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})