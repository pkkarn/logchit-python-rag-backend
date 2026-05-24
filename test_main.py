import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_app_running():
    response = client.get("/app_running")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}

@patch("services.ingestion_service.upload_pdf_to_s3")
@patch("services.ingestion_service.get_db_connection")
@patch("services.ingestion_service.extract_chunks_from_pdf")
@patch("services.ingestion_service.get_text_embedding")
@patch("services.ingestion_service.upsert_chunk_vector")
def test_ingest(
    mock_upsert_vector,
    mock_get_embedding,
    mock_extract_chunks,
    mock_get_db,
    mock_upload_s3
):
    """
    Mock test to verify the complete /ingest pipeline offline.
    Mocks AWS S3, PostgreSQL database, OpenAI embeddings, and Pinecone vector DB.
    """
    # 1. Setup mock return values for external services
    mock_upload_s3.return_value = "https://mock-bucket.s3.amazonaws.com/test.pdf"
    
    # Mock Postgres Connection & Cursor
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value = mock_cur
    mock_get_db.return_value = mock_conn
    
    # Mock PDF Chunker returning 2 test chunks
    mock_extract_chunks.return_value = [
        {"page_number": 1, "chunk_index": 0, "text": "This is chunk 1 text from page 1."},
        {"page_number": 1, "chunk_index": 1, "text": "This is chunk 2 text from page 1."}
    ]
    
    # Mock OpenAI returning a dummy 1536-dimensional vector
    mock_get_embedding.return_value = [0.0] * 1536
    
    # 2. Simulate binary file upload to FastAPI /ingest endpoint
    pdf_content = b"%PDF-1.4 dummy PDF raw binary data"
    response = client.post(
        "/ingest",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    
    # 3. Assertions
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["chunks_count"] == 2
    assert "document_id" in json_data
    assert json_data["s3_url"] == "https://mock-bucket.s3.amazonaws.com/test.pdf"
    
    # Verify that each helper was invoked the correct amount of times
    mock_upload_s3.assert_called_once()
    mock_get_db.assert_called_once()
    mock_conn.commit.assert_called_once()
    
    # 2 chunks should trigger 2 Pinecone upserts and 2 OpenAI embedding calls
    assert mock_upsert_vector.call_count == 2
    assert mock_get_embedding.call_count == 2
    
    # Verify that the DB query was run for the document and both chunks
    # (1 master insert + 2 chunk inserts = 3 queries)
    assert mock_cur.execute.call_count == 3
