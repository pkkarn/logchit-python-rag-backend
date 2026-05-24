from database.postgres import get_db_connection
from database.vector import index
import json

doc_id = "5f9a5c39-bf10-4432-b7e3-df2e084a69d4"

print("🔍 Verification Test: Checking Postgres & Pinecone...")

# 1. Check PostgreSQL
try:
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Query documents table
    cur.execute("SELECT * FROM documents WHERE id = %s;", (doc_id,))
    doc_row = cur.fetchone()
    
    if doc_row:
        print("\n✅ Postgres [documents] entry exists:")
        print(f"   ID: {doc_row['id']}")
        print(f"   File Name: {doc_row['file_name']}")
        print(f"   S3 URL: {doc_row['s3_url']}")
        print(f"   User ID: {doc_row['user_id']}")
    else:
        print("\n❌ Postgres [documents] entry NOT found!")
        
    # Query document_chunks table
    cur.execute("SELECT id, chunk_index, page_number, pinecone_vector_id, LENGTH(raw_text) as text_len FROM document_chunks WHERE document_id = %s ORDER BY chunk_index;", (doc_id,))
    chunk_rows = cur.fetchall()
    
    print(f"\n✅ Postgres [document_chunks] entries found: {len(chunk_rows)}")
    for idx, row in enumerate(chunk_rows):
        print(f"   Chunk {row['chunk_index']} (Page {row['page_number']}): Bridge ID = '{row['pinecone_vector_id']}', Text Size = {row['text_len']} chars")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error querying PostgreSQL: {e}")

# 2. Check Pinecone
try:
    stats = index.describe_index_stats()
    print("\n✅ Pinecone Index Connection Success:")
    print(f"   Total Vector Count in Index: {stats['total_vector_count']}")
    
    # Let's check if the vector IDs exist in Pinecone by querying with a dummy vector
    # (since we know the dimension is 1536)
    dummy_vector = [0.0] * 1536
    results = index.query(
        vector=dummy_vector,
        top_k=5,
        filter={"document_id": doc_id}
    )
    
    print(f"\n✅ Pinecone Search Verification (using document_id filter):")
    print(f"   Found {len(results.matches)} matched vectors in Pinecone for this document ID:")
    for match in results.matches:
        print(f"   - Match ID: '{match.id}' (Similarity score with dummy vector: {match.score})")
        
except Exception as e:
    print(f"❌ Error querying Pinecone: {e}")
