import io
from fastapi import UploadFile
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from config import settings
from fastapi import FastAPI, UploadFile, File
from database.postgres import get_db_connection
from database.vector import upsert_chunk_vector
from services.s3_service import upload_pdf_to_s3
from services.chunker import extract_chunks_from_pdf
from services.embedding import get_text_embedding

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.get("/app_running")
def app_running():
    return {"status": "running"}

# @app.get("/test")
def test():
    return {
        "admin_email": settings.admin_email,
        "app_name": settings.app_name,
        "pinecone_api_key": settings.pinecone_api_key,
        "openai_api_key": settings.openai_api_key,
        "upstash_api_key": settings.upstash_api_key,
        "supabase_key": settings.supabase_key,
    }

app.add_api_route("/test", test)

@app.post("/ingest")
async def ingest(file: UploadFile = File(...) ):
    try:
        # Boilerplate: TODO Implement ingestion
        file_bytes = await file.read()
        filename = file.filename or "document.pdf"
        s3_url = upload_pdf_to_s3(io.BytesIO(file_bytes), filename)
        
        document_id = str(uuid.uuid4())
        # 3. Connect to Supabase Postgres
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO documents (id, user_id, file_name, s3_url) VALUES (%s, %s, %s, %s);",
            (document_id, "pkkarn", filename, s3_url)
        )

        chunks = extract_chunks_from_pdf(file_bytes)

        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            # Generate vector embedding from OpenAI
            vector = get_text_embedding(chunk["text"])
            upsert_chunk_vector(
                vector_id=chunk_id,
                vector=vector,
                metadata={"document_id": document_id}
            )

            cur.execute(
                """
                INSERT INTO document_chunks (id, document_id, chunk_index, page_number, raw_text, pinecone_vector_id)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    str(uuid.uuid4()),
                    document_id,
                    chunk["chunk_index"],
                    chunk["page_number"],
                    chunk["text"],
                    chunk_id,
                )
            )

        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "s3_url": s3_url
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/query")
def query(request: QueryRequest):
    # Boilerplate: TODO Implement query
    return {"answer": f"Echo: {request.query}"}

