import os
from config import settings
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor


# Load the environment variables from your .env file
# load_dotenv()

DATABASE_URL = settings.database_url

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    Using RealDictCursor returns database rows as Python dictionaries (like JS objects),
    instead of default tuples.
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def get_user_by_email(conn, email: str):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
        return cur.fetchone()

def insert_user(conn, user_id: str, email: str, hashed_password: str):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, email, hashed_password) VALUES (%s, %s, %s);",
            (user_id, email, hashed_password)
        )

def insert_document(conn, doc_id: str, user_id: str, file_name: str, s3_url: str, status: str = 'PENDING'):
    """
    Inserts a new document master record into the PostgreSQL database.
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO documents (id, user_id, file_name, s3_url, status) VALUES (%s, %s, %s, %s, %s);",
            (doc_id, user_id, file_name, s3_url, status)
        )

def update_document_status(conn, doc_id: str, status: str):
    """
    Updates the status of a document.
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE documents SET status = %s WHERE id = %s;",
            (status, doc_id)
        )

def get_document_status(conn, doc_id: str) -> str | None:
    """
    Retrieves the current processing status of a document.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM documents WHERE id = %s;", (doc_id,))
        result = cur.fetchone()
        if result:
            return result['status']
        return None

def insert_document_chunk(conn, doc_id: str, chunk_index: int, page_number: int, raw_text: str, pinecone_vector_id: str):
    """
    Inserts a single document chunk record into the PostgreSQL database.
    """
    import uuid
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO document_chunks (id, document_id, chunk_index, page_number, raw_text, pinecone_vector_id)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                str(uuid.uuid4()),
                doc_id,
                chunk_index,
                page_number,
                raw_text,
                pinecone_vector_id
            )
        )

def insert_document_chunks_batch(conn, chunks_data: list[tuple]):
    """
    Inserts a batch of document chunk records into the PostgreSQL database.
    chunks_data: [(id, doc_id, chunk_index, page_number, raw_text, pinecone_vector_id), ...]
    """
    from psycopg2.extras import execute_values
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO document_chunks (id, document_id, chunk_index, page_number, raw_text, pinecone_vector_id)
            VALUES %s;
            """,
            chunks_data
        )

def get_chunks_and_document_by_vector_ids(conn, vector_ids: list[str]) -> list[dict]:
    """
    Retrieves the raw text chunks, page numbers, filenames, and S3 URLs 
    associated with a list of Pinecone vector IDs.
    """
    with conn.cursor() as cur:
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
        return cur.fetchall()

def test_connection():
    """
    Simple helper to test if our connection string works.
    """
    try:
        # 1. Connect
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 2. Execute a test query
        cur.execute("SELECT version();")
        result: Any = cur.fetchone()
        
        print("✅ Successfully connected to Supabase PostgreSQL!")
        if result:
            print(f"Database version: {result['version']}")

        
        # 3. Clean up
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Error connecting to the database:")
        print(e)

# This block only runs if you run this file directly (e.g. python postgres.py)
if __name__ == "__main__":
    test_connection()