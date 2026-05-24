from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from config import settings
from services.ingestion_service import process_document_ingestion
from services.query_service import execute_rag_query
from routers import auth
from dependencies import get_current_user

app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade RAG backend with semantic caching and hybrid search.",
    version="1.0.0"
)

app.include_router(auth.router)

class QueryRequest(BaseModel):
    query: str

@app.get("/app_running")
def app_running():
    """
    Service health check endpoint.
    """
    return {"status": "running"}

@app.get("/test")
def test_config():
    """
    Verifies that system configuration settings are loaded properly.
    """
    return {
        "admin_email": settings.admin_email,
        "app_name": settings.app_name,
        "pinecone_api_key": settings.pinecone_api_key,
        "openai_api_key": settings.openai_api_key,
        "upstash_vector_rest_url": settings.upstash_vector_rest_url,
        "upstash_vector_rest_token": settings.upstash_vector_rest_token,
        "supabase_key": settings.supabase_key,
    }

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    """
    Ingests a raw PDF document stream into S3, page-aware chunks, 
    relational PostgreSQL tables, and Pinecone vector indexes.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "document.pdf"
        
        result = process_document_ingestion(file_bytes, filename, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query_document(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """
    Processes a natural language query over ingested documents using the 
    grounded RAG pipeline (Retrieval-Augmented Generation).
    """
    try:
        result = execute_rag_query(request.query, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))