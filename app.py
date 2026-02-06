import streamlit as st
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sentinel Financial Agent", page_icon="📈")

# --- 1. SETUP: Load Secrets & Connect ---
# These must be set in Streamlit Cloud "Secrets" later
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    groq_api_key = st.secrets["GROQ_API_KEY"]
except FileNotFoundError:
    st.error("Secrets not found. Please set SUPABASE_URL, SUPABASE_KEY, and GROQ_API_KEY.")
    st.stop()

supabase: Client = create_client(supabase_url, supabase_key)
client = Groq(api_key=groq_api_key)

# --- 2. CACHING THE AI MODEL ---
# We use @st.cache_resource so we only download the model ONCE.
# This prevents the app from crashing on the free tier.
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- UI LAYOUT ---
st.title("🛡️ Sentinel: AI Financial Analyst")
st.markdown("Ask questions about your watchlist stocks (NVDA, TSLA, etc.)")

# Input Box
query = st.text_input("Ask a question:", placeholder="Why did Nvidia drop today?")

if query:
    with st.spinner("Analyzing market data..."):
        # --- STEP 1: EMBED THE QUERY ---
        # Convert user question to vector
        query_vector = model.encode(query).tolist()

        # --- STEP 2: SEARCH DATABASE (RAG) ---
        # Call the 'match_documents' SQL function we made earlier
        response = supabase.rpc(
            'match_documents', 
            {
                'query_embedding': query_vector, 
                'match_threshold': 0.3, # Lower threshold = more results
                'match_count': 3
            }
        ).execute()
        
        # Check if we found anything
        matches = response.data
        if not matches:
            st.warning("No relevant news found in the database. (Did the ETL job run?)")
            context_text = "No specific news found."
        else:
            # Combine the top 3 news articles into one block of text
            context_text = "\n\n".join([
                f"Headline: {item['headline']}\nContent: {item['content']}" 
                for item in matches
            ])
            
            # Show sources (for transparency)
            with st.expander("View Source Documents"):
                for item in matches:
                    st.write(f"- **{item['headline']}**")

        # --- STEP 3: ASK THE LLM (GROQ) ---
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior financial analyst. Answer the user question based ONLY on the provided Context. If the context doesn't answer it, say so. Keep it concise and professional."
                },
                {
                    "role": "user",
                    "content": f"Context: {context_text}\n\nQuestion: {query}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
        )

        # --- STEP 4: DISPLAY RESULT ---
        st.markdown("### 🤖 Analysis")
        st.write(chat_completion.choices[0].message.content)