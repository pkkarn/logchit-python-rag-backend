from pinecone import Pinecone
from config import settings

pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index_name)

def upsert_chunk_vector(vector_id:str, vector: list[float], metadata: dict):
    """
    Upserts a single chunk vector into the Pinecone index.
    """
    try:
        index.upsert(
            vectors=[(
                vector_id, 
                vector, 
                metadata
            )]
        )
        print(f"✅ Successfully upserted vector: {vector_id}")
    except Exception as e:
        print(f"❌ Error upserting vector: {e}")

def query_similar_vectors(vector: list[float], top_k: int = 3, filter: dict = None):
    """
    Performs a similarity search in the Pinecone index.
    """
    try:
        results = index.query(
            vector=vector, 
            top_k=top_k, 
            include_metadata=True,
            filter=filter
        )
        return results
    except Exception as e:
        print(f"❌ Error querying vectors: {e}")
        return None

def pinecone_test_connection():
    """
    Verifies that we can connect to the index and describe its stats.
    """
    try:
        stats = index.describe_index_stats()
        print("✅ Successfully connected to Pinecone!")
        print(f"Index Stats: {stats}")
    except Exception as e:
        print("❌ Error connecting to Pinecone:")
        print(e)

if __name__ == "__main__":
    pinecone_test_connection()