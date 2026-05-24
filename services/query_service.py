from database.postgres import get_db_connection, get_chunks_and_document_by_vector_ids
from database.vector import query_similar_vectors
from services.embedding import get_text_embedding, generate_chat_response
from database.cache import get_cached_answer, set_cached_answer

def execute_rag_query(query_text: str) -> dict:
    """
    Coordinates the multi-system RAG pipeline:
    1. Embeds the user's natural language query using OpenAI.
    2. Queries Pinecone to retrieve top 3 closest vector IDs.
    3. Fetches raw text and citation links from PostgreSQL.
    4. Compiles matching chunks into a grounded Context.
    5. Calls OpenAI with strict system prompts to prevent hallucination.
    6. Returns the grounded answer and citations list.
    """
    try:
        # 0. Check Semantic Cache
        cached_result = get_cached_answer(query_text)
        if cached_result:
            return cached_result

        # 1. Generate embedding for query
        query_vector = get_text_embedding(query_text)

        # 2. Query Pinecone for top 3 closest vectors
        query_response = query_similar_vectors(query_vector, top_k=3)

        if not query_response or not query_response.matches:
            return {
                "answer": "I don't know.",
                "citations": []
            }

        # Extract vector IDs
        vector_ids = [match.id for match in query_response.matches]

        if not vector_ids:
            return {
                "answer": "I don't know.",
                "citations": []
            }

        # 3. Retrieve raw text chunks and S3 links from PostgreSQL
        conn = get_db_connection()
        try:
            rows = get_chunks_and_document_by_vector_ids(conn, vector_ids)
        finally:
            conn.close()

        if not rows:
            return {
                "answer": "I don't know.",
                "citations": []
            }

        # 4. Compile retrieved snippets into Context block
        context_str = ""
        citations = []
        for row in rows:
            context_str += f"--- \nSource: [{row['file_name']}, Page {row['page_number']}]\nText: {row['raw_text']}\n"
            
            # Pack citation details
            citations.append({
                "file_name": row["file_name"],
                "page_number": row["page_number"],
                "s3_url": row["s3_url"]
            })

        # 5. Zero-hallucination System Prompt
        system_prompt = (
            "You are a helpful, enterprise-grade document assistant.\n"
            "Answer the user's question using ONLY the context provided below.\n"
            "If the answer cannot be found in the context, you MUST reply exactly with: 'I don't know.'\n"
            "For every claim you make, append the citation format [File Name, Page X] directly at the end of the sentence.\n"
            "Do not make assumptions, do not add conversational filler, and do not use outside knowledge."
        )

        # Inject context and query
        user_prompt = f"Context:\n{context_str}\n\nQuestion: {query_text}"

        # 6. Call OpenAI LLM to generate answer
        answer = generate_chat_response(system_prompt, user_prompt)

        final_response = {
            "status": "success",
            "answer": answer,
            "citations": citations
        }
        
        # 7. Save to Semantic Cache
        set_cached_answer(query_text, final_response)

        return final_response
    except Exception as e:
        print(f"❌ Error during RAG query: {e}")
        raise e
