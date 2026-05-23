from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class IngestRequest(BaseModel):
    document_id: str
    text: str

# @app.get("/test")
def test():
    return {"status": "tested"}

app.add_api_route("/test", test)

@app.post("/ingest")
def ingest(request: IngestRequest):
    # Boilerplate: TODO Implement ingestion
    return {"status": "ingested", "document_id": request.document_id}

@app.post("/query")
def query(request: QueryRequest):
    # Boilerplate: TODO Implement query
    return {"answer": f"Echo: {request.query}"}
