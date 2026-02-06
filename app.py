import streamlit as st
import time
from datetime import datetime
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
st.set_page_config(page_title="Sentinel AI Agent", page_icon="🛡️")

# --- SETUP CREDENTIALS ---
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    groq_api_key = st.secrets["GROQ_API_KEY"]
except FileNotFoundError:
    st.error("Secrets not found!")
    st.stop()

supabase: Client = create_client(supabase_url, supabase_key)
client = Groq(api_key=groq_api_key)

# --- CACHED MODEL LOAD ---
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- FUNCTION: REAL-TIME RESEARCHER (The "Agent" part) ---
def perform_live_research(ticker):
    """Fetches news instantly for a missing stock."""
    st.toast(f"🕵️ Agent is researching {ticker}...", icon="🔍")
    
    # 1. Fetch News
    results = []
    try:
        with DDGS() as ddgs:
            news_gen = ddgs.text(f"{ticker} stock news", max_results=5)
            for r in news_gen:
                results.append(r)
    except Exception as e:
        st.error(f"Search failed: {e}")
        return

    # 2. Vectorize & Save
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
    
    st.toast(f"✅ Research complete for {ticker}!", icon="💾")
    time.sleep(1) # Give DB a moment to index

# --- MAIN UI ---
st.title("🛡️ Sentinel: Autonomous Financial Agent")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Ask about a stock:", placeholder="Why is PLTR up today?")
with col2:
    # Optional: Allow user to specify the ticker explicitly to force research
    forced_ticker = st.text_input("Ticker (Optional)", placeholder="e.g. PLTR")

if query:
    # --- STEP 1: EMBED QUESTION ---
    query_vector = model.encode(query).tolist()

    # --- STEP 2: SEARCH DATABASE ---
    response = supabase.rpc(
        'match_documents', 
        {'query_embedding': query_vector, 'match_threshold': 0.3, 'match_count': 3}
    ).execute()
    
    matches = response.data

    # --- STEP 3: "SELF-HEALING" LOGIC ---
    # If no results found, try to guess the ticker and research it live!
    if not matches:
        # Simple heuristic: specific ticker provided OR try to find uppercase word in query
        target_ticker = forced_ticker.upper() if forced_ticker else None
        
        # If user didn't type ticker box, try to guess from query (e.g. "PLTR" in "Why is PLTR up?")
        if not target_ticker:
            words = query.split()
            for w in words:
                clean_w = w.strip("?.!")
                if clean_w.isupper() and len(clean_w) <= 5:
                    target_ticker = clean_w
                    break
        
        if target_ticker:
            st.info(f"Database empty for {target_ticker}. Initializing Live Research Agent...")
            perform_live_research(target_ticker)
            
            # Re-run search after research
            response = supabase.rpc(
                'match_documents', 
                {'query_embedding': query_vector, 'match_threshold': 0.3, 'match_count': 3}
            ).execute()
            matches = response.data

    # --- STEP 4: DISPLAY RESULTS ---
    if matches:
        context_text = "\n\n".join([f"- {item['headline']}" for item in matches])
        
        # Generate Answer
        with st.spinner("Synthesizing answer..."):
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Use the provided news context to answer. If context is missing, admit it."},
                    {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {query}"}
                ],
                model="llama-3.3-70b-versatile",
            )
        
        st.markdown("### 🤖 Analysis")
        st.write(completion.choices[0].message.content)
        
        with st.expander("📚 Source Documents"):
            for item in matches:
                st.write(f"• {item['headline']}")
    else:
        st.warning("Still no data found. Try entering the Ticker symbol explicitly in the top right box.")