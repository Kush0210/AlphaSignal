import os
import time
from datetime import datetime
import yfinance as yf
from duckduckgo_search import DDGS
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# --- SETUP ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("❌ Supabase URL or Key is missing.")

supabase: Client = create_client(url, key)

print("🧠 Loading AI Model (MiniLM)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_and_store_data(ticker):
    print(f"\n🚀 Processing {ticker}...")
    
    # 1. Get News via DuckDuckGo
    results = []
    try:
        with DDGS() as ddgs:
            news_gen = ddgs.text(f"{ticker} stock news", max_results=5)
            for r in news_gen:
                results.append(r)
    except Exception as e:
        print(f"   ⚠️ Search failed for {ticker}: {e}")
        return

    # 2. Vectorize & Save
    count = 0
    for article in results:
        # Create text chunk
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
            count += 1
        except Exception as e:
            print(f"   ❌ DB Error: {e}")
            
    print(f"   ✅ Saved {count} articles.")

if __name__ == "__main__":
    # Add your stocks here
    watchlist = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "PLTR", "COIN"]
    
    for symbol in watchlist:
        fetch_and_store_data(symbol)
        time.sleep(3) # Polite delay
    
    print("--- Starting ETL Job ---")
    for symbol in watchlist:
        fetch_and_store_data(symbol)
        
    print("\n--- ETL Job Complete ---")