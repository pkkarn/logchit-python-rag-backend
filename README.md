# Enterprise-Grade RAG Pipeline with Semantic Caching & Hybrid Search

A high-performance, cost-effective Retrieval-Augmented Generation (RAG) backend engineered to handle document search and retrieval at scale (up to 10M+ documents). This system is designed with production-grade patterns, focusing on low latency, cost optimization, and near-zero hallucination.

## 🚀 Architectural Highlights

1. **Separation of Index & Storage (Cost Optimization)**
   * **Vector Index (Pinecone):** Used strictly for vector similarity lookup, storing only embeddings and their corresponding IDs.
   * **Document Store (PostgreSQL):** Stores the actual raw text chunks and rich metadata (filenames, page numbers, authors). 
   * *Impact:* Keeps the memory footprint of the expensive Vector DB to a minimum, reducing database hosting costs by up to 80%.

2. **Low-Latency Semantic Caching (Redis)**
   * A caching layer is implemented in front of the query pipeline. Before querying the vector database and invoking the LLM, the system performs a vector similarity search on cached queries in Redis.
   * *Impact:* Cache hits return response payloads in <50ms and completely bypass LLM API costs.

3. **Asynchronous Ingestion Pipeline**
   * Document ingestion is decoupled from the main API thread using a message queue. Uploaded files are offloaded to background workers that handle chunking, embedding generation, and database updates.

4. **Near-Zero Hallucination Guardrails**
   * Custom prompt engineering combined with strict validation protocols ensures the LLM generates answers *only* from the retrieved contexts.
   * Mandates strict citations `[File Name, Page X]` and automatically falls back to *"I don't know"* if grounding confidence is below a defined threshold.

---

## 🛠️ Tech Stack

* **Backend Framework:** FastAPI (Python)
* **Databases:** PostgreSQL (Metadata & Chunks), Pinecone (Vector Index)
* **Caching:** Redis (Semantic Cache)
* **Testing:** Pytest & HTTPX
* **Deployment/Containers:** Docker (Optional / Planned)

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
* **Request Body:**
  ```json
  {
    "document_id": "doc_001",
    "text": "The refund policy allows customers to return products within 30 days of purchase for a full refund."
  }
  ```
* **Response:**
  ```json
  {
    "status": "ingested",
    "document_id": "doc_001"
  }
  ```

### 3. RAG Query
* **Endpoint:** `POST /query`
* **Request Body:**
  ```json
  {
    "query": "What is the return window?"
  }
  ```
* **Response:**
  ```json
  {
    "answer": "You can return products within 30 days of purchase for a full refund.",
    "citations": [
      {
        "document_id": "doc_001",
        "page_number": 1
      }
    ]
  }
  ```

---

## 🧪 Testing

The project uses `pytest` for endpoint and integration verification.

To run the test suite:
```bash
pytest test_main.py
```
