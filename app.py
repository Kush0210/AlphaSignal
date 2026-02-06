import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
from tavily import TavilyClient

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sentinel Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {
        background-color: #0E1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #262730;
    }
    .source-card {
        padding: 10px;
        margin-bottom: 8px;
        background-color: #262730;
        border-radius: 5px;
        border-left: 4px solid #00C0F2;
    }
</style>
""", unsafe_allow_html=True)

# --- SETUP CREDENTIALS ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    st.error(f"❌ Connection Error: {e}. Check your Streamlit Secrets.")
    st.stop()

# --- LOAD NEW AI MODEL (BGE-Small) ---
@st.cache_resource
def load_model():
    # BGE-Small is SOTA for this size. 384 dimensions.
    return SentenceTransformer('BAAI/bge-small-en-v1.5')

model = load_model()

# --- FRAGMENT: LIVE MARKET DATA (Auto-Refreshes) ---
@st.fragment(run_every=30)
def show_market_data(ticker):
    if not ticker: return
    
    # Fetch Data
    try:
        stock = yf.Ticker(ticker)
        # Fast Info is faster than history
        info = stock.fast_info 
        current = info.last_price
        prev = info.previous_close
        change = current - prev
        pct = (change / prev) * 100
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric(
                label=f"{ticker} PRICE",
                value=f"${current:.2f}",
                delta=f"{change:.2f} ({pct:.2f}%)"
            )
        
        with col2:
            # minimal line chart
            hist = stock.history(period="1mo")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist['Close'],
                mode='lines', 
                line=dict(color='#00C0F2', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 192, 242, 0.1)'
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=100,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
            
    except:
        st.warning("Data currently unavailable.")

# --- AGENT: TAVILY RESEARCHER ---
def perform_live_research(ticker):
    with st.status(f"🌐 Sentinel Agent researching {ticker}...", expanded=True) as status:
        
        # 1. Search Tavily
        status.write("Querying Neural Search Index...")
        try:
            # Advanced search gives deeper financial context
            response = tavily.search(
                query=f"Why is {ticker} stock moving today? latest news and analysis", 
                search_depth="advanced",
                max_results=5
            )
        except Exception as e:
            status.update(label="Search Failed", state="error")
            st.error(str(e))
            return

        # 2. Vectorize & Save
        status.write(f"Processing {len(response['results'])} insights...")
        
        new_docs = []
        for result in response['results']:
            text_chunk = f"{result['title']}. {result['content']}"
            embedding = model.encode(text_chunk).tolist()
            
            new_docs.append({
                "ticker": ticker.upper(),
                "headline": result['title'],
                "content": result['content'],
                "published_at": datetime.utcnow().isoformat(),
                "embedding": embedding
            })
            
        # Bulk Insert for speed
        if new_docs:
            supabase.table('market_news').insert(new_docs).execute()
        
        status.update(label="Knowledge Base Updated", state="complete", expanded=False)

# --- MAIN UI ---
st.title("🛡️ Sentinel Pro")

# Ticker Selection
col1, col2 = st.columns([1, 4])
with col1:
    active_ticker = st.text_input("TICKER", value="NVDA").upper()

show_market_data(active_ticker)

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Ask Sentinel..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # A. Semantic Search
        query_vector = model.encode(prompt).tolist()
        db_response = supabase.rpc(
            'match_documents', 
            {'query_embedding': query_vector, 'match_threshold': 0.4, 'match_count': 5}
        ).execute()
        
        matches = db_response.data
        
        # B. Self-Healing (If no data, Research!)
        if not matches:
            perform_live_research(active_ticker)
            # Re-search after learning
            db_response = supabase.rpc(
                'match_documents', 
                {'query_embedding': query_vector, 'match_threshold': 0.4, 'match_count': 5}
            ).execute()
            matches = db_response.data

        # C. Construct Prompt
        context_str = "\n".join([f"- {m['headline']}: {m['content']}" for m in matches])
        
        system_prompt = f"""
        You are Sentinel, an elite financial intelligence AI. 
        Synthesize the provided context to answer the user's question.
        Focus on CAUSALITY (Why did X happen?).
        If the context is empty, state clearly that you have no data on this topic yet.
        
        Context:
        {context_str}
        """

        # D. Generate (Streamed)
        full_response = ""
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
        # E. Sources Dropdown
        if matches:
            with st.expander("📚 Analyzed Sources"):
                for m in matches:
                    st.markdown(f"""
                    <div class="source-card">
                        <b>{m['headline']}</b><br>
                        <span style="font-size:12px;color:#aaa">{m['content'][:100]}...</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})