-- Create the documents table (with user_id!)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'pkkarn', -- Links this document to pkkarn
    file_name VARCHAR(255) NOT NULL,
    s3_url VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the document_chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT,
    raw_text TEXT NOT NULL,
    pinecone_vector_id VARCHAR(255) NOT NULL
);

-- Create an index on pinecone_vector_id so lookups are lightning fast
CREATE INDEX idx_chunks_vector_id ON document_chunks(pinecone_vector_id);