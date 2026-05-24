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

def get_text_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Calls OpenAI API to generate multiple embeddings in a single batch network request.
    This is up to 100x faster than calling get_text_embedding sequentially.
    """
    try:
        response = openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
    except Exception as e:
        print(f"❌ Error generating batch embeddings: {e}")
        raise e

def generate_chat_response(system_prompt: str, user_prompt: str) -> str:
    """
    Calls OpenAI Chat Completion API to generate an answer.
    Uses 'gpt-4o-mini' and sets temperature=0.0 to prevent hallucinations.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0  # Crucial: 0.0 forces the LLM to be deterministic
        )
        return response.choices[0].message.content or "I don't know."
    except Exception as e:
        print(f"❌ Error in chat completion: {e}")
        raise e