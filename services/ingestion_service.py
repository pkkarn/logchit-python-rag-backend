import io
import uuid
from database.postgres import get_db_connection, insert_document, insert_document_chunk
from database.vector import upsert_chunk_vector
from services.s3_service import upload_pdf_to_s3
from services.chunker import extract_chunks_from_pdf
from services.embedding import get_text_embedding

def process_document_ingestion(file_bytes: bytes, filename: str) -> dict:
    """
    Coordinates the multi-system pipeline to ingest a PDF:
    1. Uploads binary stream to AWS S3.
    2. Generates a unique document ID.
    3. Connects to PostgreSQL and inserts document master record.
    4. Extracts text page-by-page and chunks it.
    5. Loops through chunks to generate vector embeddings and:
       - Upserts vectors into Pinecone (vector index).
       - Inserts chunk rows into PostgreSQL.
    6. Commits the transaction and cleans up.
    """
    # Upload to S3
    s3_url = upload_pdf_to_s3(io.BytesIO(file_bytes), filename)
    
    document_id = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        # Create document master row
        insert_document(conn, document_id, "pkkarn", filename, s3_url)

        # Extract chunks
        chunks = extract_chunks_from_pdf(file_bytes)

        # Process chunks
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            
            # Generate embedding
            vector = get_text_embedding(chunk["text"])
            
            # Save in Pinecone
            upsert_chunk_vector(
                vector_id=chunk_id,
                vector=vector,
                metadata={"document_id": document_id}
            )

            # Save in PostgreSQL
            insert_document_chunk(
                conn=conn,
                doc_id=document_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                raw_text=chunk["text"],
                pinecone_vector_id=chunk_id
            )

        # Commit transaction
        conn.commit()
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "s3_url": s3_url
        }
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during document ingestion: {e}")
        raise e
    finally:
        conn.close()
