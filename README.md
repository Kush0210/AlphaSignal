# 🛡️ Sentinel: Autonomous Financial Intelligence Agent

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Architecture](https://img.shields.io/badge/Architecture-Serverless-orange)
![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20pgvector-green)
![AI](https://img.shields.io/badge/AI-Llama3%20%2B%20RAG-purple)
![Cost](https://img.shields.io/badge/Cost-%240.00-brightgreen)

## 📖 Overview
**Sentinel** is an end-to-end **Financial RAG (Retrieval-Augmented Generation)** system that autonomously aggregates, analyzes, and visualizes market data. 

Unlike traditional dashboards that rely on static data, Sentinel utilizes a **serverless ETL pipeline** to ingest unstructured news data, converts it into high-dimensional vector embeddings, and uses a Large Language Model (Llama 3 via Groq) to provide semantic search and reasoning capabilities for retail investors.

The entire architecture runs on a **$0 cost basis** using ephemeral compute (GitHub Actions) and free-tier cloud resources.

---

## 🏗️ Architecture

The system follows a modern **Serverless + Vector Search** pattern:

```mermaid
graph TD
    A[Github Actions (Cron Job)] -->|Triggers Daily| B(ETL Script)
    B -->|Fetch Prices| C[yfinance API]
    B -->|Fetch News| D[DuckDuckGo Search]
    B -->|Generate Embeddings| E[Local SentenceTransformer]
    E -->|Upsert Vectors| F[(Supabase / pgvector)]
    G[User (Streamlit App)] -->|Query| F
    F -->|Context Retrieval| G
    G -->|Context + Prompt| H[Groq API (Llama 3)]
    H -->|Actionable Insight| G

Here is a professional, portfolio-ready README.md.This file is the "face" of your project. When a recruiter or hiring manager opens your GitHub link, this is the first thing they see. I have written it to highlight the keywords that ATS (Applicant Tracking Systems) and engineering managers look for (e.g., "Serverless," "Vector Database," "RAG," "CI/CD").Copy the code below and save it as README.md in your main folder.Markdown# 🛡️ Sentinel: Autonomous Financial Intelligence Agent

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Architecture](https://img.shields.io/badge/Architecture-Serverless-orange)
![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20pgvector-green)
![AI](https://img.shields.io/badge/AI-Llama3%20%2B%20RAG-purple)
![Cost](https://img.shields.io/badge/Cost-%240.00-brightgreen)

## 📖 Overview
**Sentinel** is an end-to-end **Financial RAG (Retrieval-Augmented Generation)** system that autonomously aggregates, analyzes, and visualizes market data. 

Unlike traditional dashboards that rely on static data, Sentinel utilizes a **serverless ETL pipeline** to ingest unstructured news data, converts it into high-dimensional vector embeddings, and uses a Large Language Model (Llama 3 via Groq) to provide semantic search and reasoning capabilities for retail investors.

The entire architecture runs on a **$0 cost basis** using ephemeral compute (GitHub Actions) and free-tier cloud resources.

---

## 🏗️ Architecture

The system follows a modern **Serverless + Vector Search** pattern:

```mermaid
graph TD
    A[Github Actions (Cron Job)] -->|Triggers Daily| B(ETL Script)
    B -->|Fetch Prices| C[yfinance API]
    B -->|Fetch News| D[DuckDuckGo Search]
    B -->|Generate Embeddings| E[Local SentenceTransformer]
    E -->|Upsert Vectors| F[(Supabase / pgvector)]
    G[User (Streamlit App)] -->|Query| F
    F -->|Context Retrieval| G
    G -->|Context + Prompt| H[Groq API (Llama 3)]
    H -->|Actionable Insight| G

Here is a professional, portfolio-ready README.md.This file is the "face" of your project. When a recruiter or hiring manager opens your GitHub link, this is the first thing they see. I have written it to highlight the keywords that ATS (Applicant Tracking Systems) and engineering managers look for (e.g., "Serverless," "Vector Database," "RAG," "CI/CD").Copy the code below and save it as README.md in your main folder.Markdown# 🛡️ Sentinel: Autonomous Financial Intelligence Agent

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Architecture](https://img.shields.io/badge/Architecture-Serverless-orange)
![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20pgvector-green)
![AI](https://img.shields.io/badge/AI-Llama3%20%2B%20RAG-purple)
![Cost](https://img.shields.io/badge/Cost-%240.00-brightgreen)

## 📖 Overview
**Sentinel** is an end-to-end **Financial RAG (Retrieval-Augmented Generation)** system that autonomously aggregates, analyzes, and visualizes market data. 

Unlike traditional dashboards that rely on static data, Sentinel utilizes a **serverless ETL pipeline** to ingest unstructured news data, converts it into high-dimensional vector embeddings, and uses a Large Language Model (Llama 3 via Groq) to provide semantic search and reasoning capabilities for retail investors.

The entire architecture runs on a **$0 cost basis** using ephemeral compute (GitHub Actions) and free-tier cloud resources.

---

## 🏗️ Architecture

The system follows a modern **Serverless + Vector Search** pattern:

```mermaid
graph TD
    A[Github Actions (Cron Job)] -->|Triggers Daily| B(ETL Script)
    B -->|Fetch Prices| C[yfinance API]
    B -->|Fetch News| D[DuckDuckGo Search]
    B -->|Generate Embeddings| E[Local SentenceTransformer]
    E -->|Upsert Vectors| F[(Supabase / pgvector)]
    G[User (Streamlit App)] -->|Query| F
    F -->|Context Retrieval| G
    G -->|Context + Prompt| H[Groq API (Llama 3)]
    H -->|Actionable Insight| G

🚀 Setup & Installation
1. Clone the Repository

git clone [https://github.com/yourusername/sentinel-financial-agent.git](https://github.com/yourusername/sentinel-financial-agent.git)
cd sentinel-financial-agent

Here is a professional, portfolio-ready README.md.This file is the "face" of your project. When a recruiter or hiring manager opens your GitHub link, this is the first thing they see. I have written it to highlight the keywords that ATS (Applicant Tracking Systems) and engineering managers look for (e.g., "Serverless," "Vector Database," "RAG," "CI/CD").Copy the code below and save it as README.md in your main folder.Markdown# 🛡️ Sentinel: Autonomous Financial Intelligence Agent

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Architecture](https://img.shields.io/badge/Architecture-Serverless-orange)
![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20pgvector-green)
![AI](https://img.shields.io/badge/AI-Llama3%20%2B%20RAG-purple)
![Cost](https://img.shields.io/badge/Cost-%240.00-brightgreen)

## 📖 Overview
**Sentinel** is an end-to-end **Financial RAG (Retrieval-Augmented Generation)** system that autonomously aggregates, analyzes, and visualizes market data. 

Unlike traditional dashboards that rely on static data, Sentinel utilizes a **serverless ETL pipeline** to ingest unstructured news data, converts it into high-dimensional vector embeddings, and uses a Large Language Model (Llama 3 via Groq) to provide semantic search and reasoning capabilities for retail investors.

The entire architecture runs on a **$0 cost basis** using ephemeral compute (GitHub Actions) and free-tier cloud resources.

---

## 🏗️ Architecture

The system follows a modern **Serverless + Vector Search** pattern:

```mermaid
graph TD
    A[Github Actions (Cron Job)] -->|Triggers Daily| B(ETL Script)
    B -->|Fetch Prices| C[yfinance API]
    B -->|Fetch News| D[DuckDuckGo Search]
    B -->|Generate Embeddings| E[Local SentenceTransformer]
    E -->|Upsert Vectors| F[(Supabase / pgvector)]
    G[User (Streamlit App)] -->|Query| F
    F -->|Context Retrieval| G
    G -->|Context + Prompt| H[Groq API (Llama 3)]
    H -->|Actionable Insight| G

🚀 Setup & Installation

1. Clone the Repository
git clone https://github.com/Kush0210/AlphaSignal.git
cd sentinel-financial-agent

2. Environment VariablesCreate a .env file (for local testing) or add these to your GitHub Repository Secrets:

SUPABASE_URL="your_supabase_project_url"
SUPABASE_KEY="your_supabase_anon_key"
GROQ_API_KEY="your_groq_api_key" # Only needed for the Streamlit App

3. Database Setup (SQL)
Run this SQL command in your Supabase SQL Editor to enable vector search:

-- Enable the vector extension
create extension vector;

-- Create the table for storing news and embeddings
create table market_news (
  id bigint primary key generated always as identity,
  ticker text,
  headline text,
  content text,
  published_at timestamp,
  embedding vector(384)
);

-- Create a similarity search function (RPC)
create or replace function match_documents (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  headline text,
  similarity float
)
language sql stable
as $$
  select
    market_news.id,
    market_news.content,
    market_news.headline,
    1 - (market_news.embedding <=> query_embedding) as similarity
  from market_news
  where 1 - (market_news.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;

4. Run Locally
To test the ETL pipeline on your machine:

pip install -r requirements.txt
python etl.py
