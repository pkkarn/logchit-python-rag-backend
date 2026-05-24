import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

pdf_path = "/Users/pkkarn/CodeKill/hunt/job_hunt/ds_algo_strategy/projects/extensive_rag_backend/test/test.pdf"

if not os.path.exists(pdf_path):
    print(f"❌ Error: Test PDF file not found at {pdf_path}")
    exit(1)

print("🚀 Starting upload test to S3 via FastAPI...")
try:
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/ingest",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
except Exception as e:
    print(f"❌ Error running upload test: {e}")
