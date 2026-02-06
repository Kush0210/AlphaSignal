import os
import json
from datetime import datetime
import yfinance as yf
from duckduckgo_search import DDGS
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# --- 1. SETUP: Load Secrets & Connect ---
# These keys are pulled from the environment variables (set in GitHub Secrets)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("❌ Supabase URL or Key is missing. Check your environment variables.")

supabase: Client = create_client(url, key)

# --- 2. SETUP: Load the AI Model ---
# We use a compact model that fits in the free tier memory (approx 80MB)
print("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_and_store_data(ticker):
    print(f"\n🚀 Processing {ticker}...")
    
    # --- Part A: Get Stock Data (Price Check) ---
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        print(f"   💰 Price: ${current_price:.2f}")
    else:
        print("   ⚠️ Could not fetch price data.")

    # --- Part B: Get News & Embed It ---
    print(f"   📰 Fetching news...")
    results = []
    
    # Use DuckDuckGo to search for recent news (Free API)
    with DDGS() as ddgs:
        # Search for "Ticker Stock News" and get top 5 results
        news_gen = ddgs.text(f"{ticker} stock news", max_results=5)
        for r in news_gen:
            results.append(r)

    # --- Part C: Process and Upload to Supabase ---
    count = 0
    for article in results:
        headline = article.get('title')
        body = article.get('body')
        
        # Combine text for better AI understanding
        full_text = f"{headline}. {body}"
        
        # 1. Vectorize: Turn text into numbers (The "Magic" Step)
        embedding = model.encode(full_text).tolist()
        
        # 2. Prepare the data payload
        data = {
            "ticker": ticker,
            "headline": headline,
            "content": body,
            "published_at": datetime.utcnow().isoformat(),
            "embedding": embedding  # This goes into the vector column
        }
        
        # 3. Insert into Supabase
        try:
            response = supabase.table('market_news').insert(data).execute()
            count += 1
        except Exception as e:
            print(f"   ❌ Error saving article: {e}")
            
    print(f"   ✅ Saved {count} new articles for {ticker}.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # You can edit this list to track different stocks
    watchlist = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT"]
    
    print("--- Starting ETL Job ---")
    for symbol in watchlist:
        fetch_and_store_data(symbol)
        
    print("\n--- ETL Job Complete ---")