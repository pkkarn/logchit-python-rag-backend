import io
import uuid
from database.postgres import get_db_connection, insert_document, insert_document_chunks_batch
from database.vector import upsert_vectors_batch
from services.s3_service import upload_pdf_to_s3
from services.chunker import extract_chunks_from_pdf
from services.embedding import get_text_embeddings_batch
from services.sqs_service import send_message_to_queue

def enqueue_document_ingestion(file_bytes: bytes, filename: str, user_id: str) -> dict:
    """
    Synchronous HTTP endpoint handler.
    Uploads to S3, saves a PENDING record, and queues an SQS message.
    """
    s3_url = upload_pdf_to_s3(io.BytesIO(file_bytes), filename)
    document_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    try:
        insert_document(conn, document_id, user_id, filename, s3_url, status='PENDING')
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    # Send to SQS
    send_message_to_queue({
        "document_id": document_id,
        "user_id": user_id,
        "s3_url": s3_url
    })

    return {
        "status": "processing",
        "document_id": document_id,
        "message": "Document queued for processing."
    }

def process_document_background(file_bytes: bytes, document_id: str, user_id: str):
    """
    Background worker logic to process document chunks and batched API calls.
    """
    chunks = extract_chunks_from_pdf(file_bytes)
    if not chunks:
        return
        
    chunk_texts = [c["text"] for c in chunks]
    embeddings = get_text_embeddings_batch(chunk_texts)
    
    vectors_batch = []
    postgres_batch = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        vector = embeddings[i]
        
        vectors_batch.append((
            chunk_id,
            vector,
            {"document_id": document_id, "user_id": user_id}
        ))
        
        postgres_batch.append((
            chunk_id, 
            document_id, 
            chunk["chunk_index"], 
            chunk["page_number"], 
            chunk["text"], 
            chunk_id # pinecone_vector_id
        ))

    # Batch upsert to Pinecone
    upsert_vectors_batch(vectors_batch)

    # Batch insert to Postgres
    conn = get_db_connection()
    try:
        insert_document_chunks_batch(conn, postgres_batch)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
