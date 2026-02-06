import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS

# --- PAGE CONFIGURATION (Browser Tab) ---
st.set_page_config(
    page_title="Sentinel Terminal",
    page_icon="🛡️",
    layout="wide", # Uses full screen width
    initial_sidebar_state="collapsed"
)

# --- CSS HACKS FOR "CLEAN" LOOK ---
st.markdown("""
<style>
    /* Hide Streamlit Header & Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Card Style for News */
    .news-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #1E1E1E;
        margin-bottom: 10px;
        border-left: 5px solid #00D4FF;
    }
    .news-title {
        color: #FFFFFF;
        font-weight: bold;
        font-size: 16px;
    }
    .news-meta {
        color: #AAAAAA;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- SETUP CREDENTIALS ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("❌ Secrets missing! Please update Streamlit Secrets.")
    st.stop()

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- NEW FEATURE: LIVE MARKET DATA FRAGMENT ---
# @st.fragment allows this specific function to auto-refresh every 10s
# WITHOUT reloading the whole chat or clearing the screen.
@st.fragment(run_every=30) 
def show_market_data(ticker):
    if not ticker:
        return

    cols = st.columns([1, 3])
    
    with cols[0]:
        # Fetch Live Data
        stock = yf.Ticker(ticker)
        # Fast info usually has 'last_price'
        try:
            info = stock.fast_info
            price = info.last_price
            prev_close = info.previous_close
            change = price - prev_close
            pct_change = (change / prev_close) * 100
            
            # 1. The Big Green/Red Number
            st.metric(
                label=f"{ticker.upper()} Live Price",
                value=f"${price:.2f}",
                delta=f"{change:.2f} ({pct_change:.2f}%)"
            )
        except:
            st.warning("Market data unavailable")

    with cols[1]:
        # 2. Interactive Chart
        try:
            hist = stock.history(period="1mo", interval="1d")
            
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close']
            )])
            
            fig.update_layout(
                height=300, 
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)', # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white")
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        except:
            st.write("Chart unavailable")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Sentinel AI v2.0")
    # You can add Model selection here later

# --- MAIN LAYOUT ---
st.title("🛡️ Sentinel Terminal")

# Top Bar: Stock Selector
col1, col2 = st.columns([3, 1])
with col1:
    selected_ticker = st.text_input("Active Ticker", value="NVDA", label_visibility="collapsed")

# --- CALL THE LIVE FRAGMENT ---
st.divider()
show_market_data(selected_ticker)
st.divider()

# --- CHAT INTERFACE ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LIVE RESEARCH FUNCTION (From previous step) ---
def perform_live_research(ticker):
    with st.status(f"🕵️ Agent researching {ticker}...", expanded=True) as status:
        status.write("Searching global news...")
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
            supabase.table('market_news').insert(data).execute()
        
        status.update(label="Knowledge Base Updated!", state="complete", expanded=False)

# --- USER INPUT ---
if prompt := st.chat_input("Ask about the market..."):
    # 1. Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # RAG Logic
        query_vector = model.encode(prompt).tolist()
        response = supabase.rpc(
            'match_documents', 
            {'query_embedding': query_vector, 'match_threshold': 0.3, 'match_count': 5}
        ).execute()
        
        matches = response.data

        # Auto-Research Trigger
        if not matches:
            # Try to infer ticker from the "Active Ticker" box or the prompt
            target_ticker = selected_ticker.upper()
            perform_live_research(target_ticker)
            # Re-search
            response = supabase.rpc(
                'match_documents', 
                {'query_embedding': query_vector, 'match_threshold': 0.3, 'match_count': 5}
            ).execute()
            matches = response.data

        # Construct Context
        context_text = ""
        if matches:
            context_text = "\n\n".join([f"Headline: {m['headline']}\nBody: {m['content']}" for m in matches])
        
        # Groq Call
        full_response = ""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system",
                 "content": f"You are a helpful financial analyst AI. Answer the user's question clearly and naturally using the provided news context. If the context doesn't have the answer, say so politely. Do not act like a command-line terminal. Context: {context_text}"
                },
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        # Stream the result (Typewriter effect)
        for chunk in completion:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
        # Show Sources in a sleek "Popover" (New Feature)
        if matches:
            with st.popover("📚 View Sources"):
                for m in matches:
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title">{m['headline']}</div>
                        <div class="news-meta">{m['published_at'][:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # 3. Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})