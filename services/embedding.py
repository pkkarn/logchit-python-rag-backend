from openai import OpenAI
from config import settings

# Initialize the OpenAI client with your API key
openai_client = OpenAI(api_key=settings.openai_api_key)

def get_text_embedding(text: str) -> list[float]:
    """
    Calls OpenAI API to generate a 1536-dimensional embedding vector.
    Using 'text-embedding-3-small' (the most cost-effective and standard RAG model).
    """
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        raise e