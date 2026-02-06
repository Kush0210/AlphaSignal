import os
import json
from datetime import datetime
import yfinance as yf
from duckduckgo_search import DDGS
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# 1. SETUP: Load Secrets and Connect to Database
# These keys will be pulled from GitHub Secrets (or your local environment)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or Key is missing. Check your environment variables.")

supabase: Client = create_client(url, key)

# 2. SETUP: Load the AI Model
# We use a small, fast model that fits in free tier memory
print("Loading AI Model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_and_store_data(ticker):
    print(f"Processing {ticker}...")
    
    # --- Part A: Get Stock Data ---
    stock = yf.Ticker(ticker)
    # Get today's data (simplified for this example)
    hist = stock.history(period="1d")
    
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        print(f"  Price: {current_price}")
    else:
        print("  Could not fetch price data.")
        current_price = 0.0

    # --- Part B: Get News & Embed It ---
    print(f"  Fetching news for {ticker}...")
    results = []
    
    # Use DuckDuckGo to search for recent news
    with DDGS() as ddgs:
        # We search for "Ticker Stock News" and get 5 results
        news_gen = ddgs.text(f"{ticker} stock news", max_results=5)
        for r in news_gen:
            results.append(r)

    # --- Part C: Process and Upload ---
    for article in results:
        headline = article.get('title')
        body = article.get('body')
        
        # Create a rich text for the AI to read later
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
        # We use 'upsert' or simple 'insert'. 
        try:
            response = supabase.table('market_news').insert(data).execute()
            print(f"    Saved: {headline[:30]}...")
        except Exception as e:
            print(f"    Error saving article: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # You can add as many stocks as you want here
    watchlist = ["NVDA", "TSLA", "AAPL", "AMD"]
    
    for symbol in watchlist:
        fetch_and_store_data(symbol)
        
    print("ETL Job Complete.")