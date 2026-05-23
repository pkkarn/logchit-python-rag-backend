from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_app_running():
    response = client.get("/app_running")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}

def test_ingest():
    response = client.post("/ingest", json={"document_id": "123", "text": "sample text"})
    assert response.status_code == 200
    assert response.json() == {"status": "ingested", "document_id": "123"}

def test_query():
    response = client.post("/query", json={"query": "test query"})
    assert response.status_code == 200
    assert "answer" in response.json()
