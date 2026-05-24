import json
from upstash_semantic_cache import SemanticCache
from config import settings

def _get_semantic_cache() -> SemanticCache | None:
    """
    Initializes and returns the Upstash Semantic Cache instance.
    Returns None if the Upstash Vector credentials are not set.
    """
    if not settings.upstash_vector_rest_url or not settings.upstash_vector_rest_token:
        print("⚠️ Semantic Cache is disabled. Missing Upstash Vector credentials.")
        return None

    try:
        # min_proximity: 0.95 means queries must be 95% semantically identical to be a hit
        return SemanticCache(
            url=settings.upstash_vector_rest_url,
            token=settings.upstash_vector_rest_token,
            min_proximity=0.95
        )
    except Exception as e:
        print(f"⚠️ Failed to initialize Semantic Cache: {e}")
        return None

def get_cached_answer(query_text: str) -> dict | None:
    """
    Checks the semantic cache for an extremely similar prior question.
    Returns the parsed dictionary (answer and citations) if found, else None.
    """
    cache = _get_semantic_cache()
    if not cache:
        return None

    try:
        result = cache.get(query_text)
        if result:
            print(f"🎯 Semantic Cache HIT for query: '{query_text}'")
            # The result is a JSON string, we parse it back to a dictionary
            return json.loads(result)
        
        print(f"🔄 Semantic Cache MISS for query: '{query_text}'")
        return None
    except Exception as e:
        print(f"⚠️ Error reading from semantic cache: {e}")
        return None

def set_cached_answer(query_text: str, answer_data: dict) -> None:
    """
    Saves the user's question and the LLM's full answer to the semantic cache.
    """
    cache = _get_semantic_cache()
    if not cache:
        return

    try:
        # Serialize the entire answer dictionary (including citations) as a JSON string
        serialized_data = json.dumps(answer_data)
        cache.set(query_text, serialized_data)
        print(f"💾 Saved answer to Semantic Cache for query: '{query_text}'")
    except Exception as e:
        print(f"⚠️ Error writing to semantic cache: {e}")
