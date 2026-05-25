from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel
from config import settings
from services.ingestion_service import enqueue_document_ingestion
from services.query_service import execute_rag_query
from routers import auth
from dependencies import get_current_user
from database.postgres import get_db_connection, get_document_status, get_document_by_id, delete_document_record
from services.s3_service import delete_pdf_from_s3
from database.vector import delete_vectors_by_document

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

@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    """
    Ingests a raw PDF document stream into S3, page-aware chunks, 
    relational PostgreSQL tables, and Pinecone vector indexes.
    """
    try:
        file_bytes = await file.read()
        
        # Enforce 10MB file size limit to prevent unbounded OpenAI token usage
        MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum allowed size is 10MB.")

        filename = file.filename or "document.pdf"
        
        result = enqueue_document_ingestion(file_bytes, filename, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{document_id}")
def check_document_status(document_id: str, current_user: str = Depends(get_current_user)):
    """
    Poll this endpoint to check if the background worker has finished processing the document.
    """
    conn = get_db_connection()
    try:
        doc_status = get_document_status(conn, document_id)
        if not doc_status:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"document_id": document_id, "status": doc_status}
    finally:
        conn.close()

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

@app.delete("/document/{document_id}")
def delete_document(document_id: str, current_user: str = Depends(get_current_user)):
    """
    Permanently deletes a document and all its chunks from S3, Pinecone, and PostgreSQL.
    """
    conn = get_db_connection()
    try:
        doc = get_document_by_id(conn, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        if doc['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")

        # 1. Delete from S3
        if doc.get('s3_url'):
            delete_pdf_from_s3(doc['s3_url'])
            
        # 2. Delete vectors from Pinecone
        delete_vectors_by_document(document_id)
        
        # 3. Delete from Postgres (cascades to chunks)
        delete_document_record(conn, document_id)
        conn.commit()
        
        return {"status": "success", "message": f"Document {document_id} permanently deleted."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()