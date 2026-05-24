import io
from fastapi import UploadFile
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from config import settings
from fastapi import FastAPI, UploadFile, File
from database.postgres import get_db_connection
from database.vector import upsert_chunk_vector, query_similar_vectors
from services.s3_service import upload_pdf_to_s3
from services.chunker import extract_chunks_from_pdf
from services.embedding import get_text_embedding
from services.embedding import generate_chat_response

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
    try:
        # 1. Generate vector embedding for the user's natural language query
        query_vector = get_text_embedding(request.query)
        
        # 2. Query Pinecone for the top 3 closest vectors
        query_response = query_similar_vectors(query_vector, top_k=3)

        if not query_response or not query_response.matches:
            return {
                "answer": "I don't know.",
                "citations": []
            }

        # Extract the matching Pinecone IDs (which are our bridge IDs)
        vector_ids = [match.id for match in query_response.matches]
        
        # Safety check: if Pinecone found nothing, return "I don't know" immediately
        if not vector_ids:
            return {
                "answer": "I don't know.",
                "citations": []
            }
            
        # 3. Query PostgreSQL to get the raw text chunks & S3 links using the bridge IDs
        conn = get_db_connection()
        cur = conn.cursor()
        
        sql = """
            SELECT 
                chunks.raw_text, 
                chunks.page_number, 
                docs.file_name, 
                docs.s3_url
            FROM document_chunks chunks
            JOIN documents docs ON chunks.document_id = docs.id
            WHERE chunks.pinecone_vector_id = ANY(%s);
        """
        cur.execute(sql, (vector_ids,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if not rows:
            return {
                "answer": "I don't know.",
                "citations": []
            }
            
        # 4. Compile the retrieved snippets into a single "Context" block
        context_str = ""
        citations = []
        for row in rows:
            context_str += f"--- \nSource: [{row['file_name']}, Page {row['page_number']}]\nText: {row['raw_text']}\n"
            
            # Pack citation details to return to the client
            citations.append({
                "file_name": row["file_name"],
                "page_number": row["page_number"],
                "s3_url": row["s3_url"]
            })
            
        # 5. Define our strict zero-hallucination System Prompt
        system_prompt = (
            "You are a helpful, enterprise-grade document assistant.\n"
            "Answer the user's question using ONLY the context provided below.\n"
            "If the answer cannot be found in the context, you MUST reply exactly with: 'I don't know.'\n"
            "For every claim you make, append the citation format [File Name, Page X] directly at the end of the sentence.\n"
            "Do not make assumptions, do not add conversational filler, and do not use outside knowledge."
        )
        
        # Inject the context and user query
        user_prompt = f"Context:\n{context_str}\n\nQuestion: {request.query}"
        
        # 6. Call our OpenAI LLM to generate the grounded answer
        answer = generate_chat_response(system_prompt, user_prompt)
        
        return {
            "status": "success",
            "answer": answer,
            "citations": citations
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }