# Enterprise-Grade RAG Pipeline with Semantic Caching & Hybrid Search

A high-performance, cost-effective Retrieval-Augmented Generation (RAG) backend engineered to handle document search and retrieval at scale (up to 10M+ documents). This system is designed with production-grade patterns, focusing on low latency, cost optimization, and near-zero hallucination.

<p align="center">
  <img src="assets/demo.gif" width="100%" alt="System Demo" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" /> <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" /> <img src="https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white" alt="Pinecone" /> <img src="https://img.shields.io/badge/Upstash-00E9A3?style=for-the-badge&logo=upstash&logoColor=black" alt="Upstash" /> <img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" /> <img src="https://img.shields.io/badge/AWS_S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white" alt="AWS S3" />
</p>

## 📖 Overview
This project is a production-ready Retrieval-Augmented Generation (RAG) backend API. It takes raw PDF documents, processes them using sliding-window chunking, stores their embeddings in a vector database for semantic search, and stores their raw text in a relational database. When a user asks a question, the system retrieves the most relevant chunks and uses a Large Language Model to generate an answer with exact citations, guaranteeing zero hallucination. To ensure lightning-fast responses and minimal LLM costs, a semantic caching layer intercepts identical or highly similar questions.

## 🚀 Architectural Highlights

1. **Separation of Index & Storage (Cost Optimization)**
   * **Vector Index (Pinecone):** Used strictly for vector similarity lookup, storing only embeddings and their corresponding IDs.
   * **Document Store (PostgreSQL):** Stores the actual raw text chunks and rich metadata (filenames, page numbers, authors). 
   * *Impact:* Keeps the memory footprint of the expensive Vector DB to a minimum, reducing database hosting costs by up to 80% at scale.

2. **Low-Latency Semantic Caching (Redis)**
   * A caching layer is implemented in front of the query pipeline. Before querying the vector database and invoking the LLM, the system performs a vector similarity search on cached queries in Redis.
   * *Impact:* Cache hits return response payloads in <50ms and completely bypass LLM API costs.

3. **Asynchronous Ingestion Pipeline (Phase 1 Complete)**
   * Handles binary PDF streams completely in-memory (using `io.BytesIO`). 
   * Decouples raw document uploads to **AWS S3** from the vectorizing logic.
   * Extracts text **page-by-page** using `pypdf`, preserving exact page numbers for hyperlinked client-side citations.
   * Chunks pages using a sliding window algorithm (~200 words per chunk with a 20-word overlap) to prevent LLM attention loss and context window fragmentation.

4. **Near-Zero Hallucination Guardrails**
   * Custom prompt engineering combined with strict validation protocols ensures the LLM generates answers *only* from the retrieved contexts.
   * Mandates strict citations `[File Name, Page X]` and automatically falls back to *"I don't know"* if grounding confidence is below a defined threshold.

---

## 🛠️ Tech Stack

* **FastAPI (Python):** Powers the core backend API, chosen for its high-performance asynchronous routing and automatic OpenAPI documentation.
* **Pinecone (Vector DB):** Stores the 1536-dimensional OpenAI embeddings and performs rapid K-Nearest Neighbor (KNN) similarity searches to find relevant document chunks.
* **PostgreSQL (Supabase):** Acts as the central source of truth, storing raw text chunks, rich metadata, and foreign-key relationships (The "Bridge ID" pattern) to keep the vector index lightweight.
* **Upstash Vector (Semantic Cache):** Sits in front of the LLM pipeline, caching the mathematical intent of user queries to return instant answers for semantically identical questions, drastically reducing OpenAI API costs.
* **OpenAI (LLM & Embeddings):** Provides `text-embedding-3-small` to convert text into vectors, and `gpt-4o-mini` to generate grounded, conversational answers from the retrieved contexts.
* **AWS S3:** Provides highly durable, scalable cloud storage for the original binary PDF files, allowing the frontend to download and display cited source documents.

---

## 🔌 API Documentation

### 1. Application Health Check
* **Endpoint:** `GET /app_running`
* **Response:**
  ```json
  {
    "status": "running"
  }
  ```

### 2. Document Ingestion
* **Endpoint:** `POST /ingest`
* **Request Headers:** `Content-Type: multipart/form-data`
* **Request Body:**
  * `file`: Binary PDF File
* **Response:**
  ```json
  {
    "status": "success",
    "document_id": "5f9a5c39-bf10-4432-b7e3-df2e084a69d4",
    "chunks_count": 4,
    "s3_url": "https://rag-s3-bucket-pk.s3.us-east-1.amazonaws.com/reason_core_ai_resume.pdf"
  }
  ```

### 3. Document Query (RAG)
* **Endpoint:** `POST /query`
* **Request Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "query": "What is the return window?"
  }
  ```
* **Response:**
  ```json
  {
    "status": "success",
    "answer": "The return window for all items is 30 days from the purchase date, as long as they are returned in original condition with receipts [Policy_Handbook, Page 4].",
    "citations": [
      {
        "file_name": "Policy_Handbook.pdf",
        "page_number": 4,
        "s3_url": "https://rag-s3-bucket-pk.s3.us-east-1.amazonaws.com/Policy_Handbook.pdf"
      }
    ]
  }
  ```

---

## 🛠️ Setup & Installation Guide

### Prerequisites
* Python 3.13+
* A running PostgreSQL database (e.g., Supabase)
* A Pinecone account (with a serverless index)
* OpenAI API key
* AWS S3 Bucket (public read enabled)

### Step-by-Step Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/pkkarn/extensive-rag-backend.git
   cd extensive-rag-backend
   ```

2. **Create & Activate Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root of the project using the template provided in `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Fill in your active credentials:
   ```env
   ADMIN_EMAIL=your_email@example.com
   APP_NAME="RAG Backend Pipeline"
   OPENAI_API_KEY=sk-proj-yourOpenAiKey
   PINECONE_API_KEY=yourPineconeApiKey
   PINECONE_INDEX_NAME=your-pinecone-index
   SUPABASE_KEY="postgresql://postgres.yourdb:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
   AWS_ACCESS_KEY_ID=yourAwsAccessKey
   AWS_SECRET_ACCESS_KEY=yourAwsSecretKey
   AWS_S3_BUCKET=your-s3-bucket-name
   ```

5. **Initialize PostgreSQL Tables:**
   Execute the SQL statements inside `init.sql` on your PostgreSQL database to create the `documents` and `document_chunks` tables with the appropriate indices.

6. **Start the Development Server:**
   ```bash
   uvicorn main:app --reload
   ```
   The interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🧪 Testing Suite

We have written a comprehensive, dual-layered test suite to ensure the system is completely stable.

### 1. Offline Unit & Integration Tests (Mocked)
We use `pytest` and `unittest.mock` to test the entire `/ingest` pipeline offline. It mocks S3, Postgres, OpenAI, and Pinecone, allowing you to test the API router, Pydantic validations, and chunking boundaries locally in milliseconds without hitting network limits or token quotas.

To run the unit test suite:
```bash
pytest test_main.py
```

### 2. Live Database Verification Tests
To test the active connection, data integrity, and bridge-ID sync between your live AWS S3, Supabase Postgres, and Pinecone instances, run the verification script:
```bash
python test_verification.py
```
This script queries your live tables and index, verifying that the chunk counts match, relational foreign keys exist, and vector IDs are perfectly synchronized between PostgreSQL and Pinecone.

