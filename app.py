import streamlit as st
import time
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
st.set_page_config(page_title="Sentinel Terminal", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stMetric {
        background-color: #0E1117;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SETUP CREDENTIALS ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"❌ Secrets missing: {e}")
    st.stop()

# --- LOAD AI MODEL ---
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- FUNCTION: FETCH LIVE DATA (Native Streamlit Charts) ---
@st.fragment(run_every=30)
def show_market_data(ticker):
    if not ticker: return
    try:
        stock = yf.Ticker(ticker)
        # Get fast price info
        info = stock.fast_info
        price = info.last_price
        change = price - info.previous_close
        pct = (change / info.previous_close) * 100
        
        col1, col2 = st.columns([1, 3])
        with col1:
            # Native Streamlit Metric (Fast & Clean)
            st.metric(f"{ticker} Price", f"${price:.2f}", f"{change:.2f} ({pct:.2f}%)")
        
        with col2:
            # Native Streamlit Line Chart (No Plotly required)
            hist = stock.history(period="1mo")
            st.line_chart(hist['Close'], height=150, color="#00FF00")
            
    except Exception:
        st.warning("Waiting for market data...")

# --- FUNCTION: LIVE RESEARCHER (DuckDuckGo) ---
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
        new_rows = []
        for article in results:
            text = f"{article['title']}. {article['body']}"
            embedding = model.encode(text).tolist()
            
            new_rows.append({
                "ticker": ticker,
                "headline": article['title'],
                "content": article['body'],
                "published_at": datetime.utcnow().isoformat(),
                "embedding": embedding
            })
            
        if new_rows:
            try:
                supabase.table('market_news').insert(new_rows).execute()
            except Exception as e:
                print(f"DB Insert Error: {e}")
                
        status.update(label="Knowledge Base Updated!", state="complete", expanded=False)

# --- MAIN UI ---
st.title("🛡️ Sentinel Terminal")

# Ticker Input
active_ticker = st.text_input("ACTIVE TICKER", value="NVDA").upper()

# Show Data (Auto-refreshes every 30s)
show_market_data(active_ticker)

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle User Input
if prompt := st.chat_input(f"Ask about {active_ticker}..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # A. Encode Question
        query_vector = model.encode(prompt).tolist()
        
        # B. Search Database (With Filter Fix)
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
        except Exception:
            # Fallback if SQL function isn't updated yet
            matches = []

        # C. If No Data, Research & Retry
        if not matches:
            perform_live_research(active_ticker)
            # Retry Search
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

        # D. Generate Answer
        if matches:
            context_str = "\n\n".join([f"Headline: {m['headline']}\nBody: {m['content']}" for m in matches])
        else:
            context_str = "No specific news found."

        # Stream Response
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a financial analyst. Answer the user question based ONLY on the provided Context. If the context doesn't answer it, say so. Context: {context_str}"
                },
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
        
        # Show Sources Dropdown
        if matches:
            with st.expander("📚 Sources"):
                for m in matches:
                    st.markdown(f"**{m['headline']}**")

    # Save to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})