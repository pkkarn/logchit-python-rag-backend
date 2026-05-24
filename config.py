from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "PROD_RAG"
    admin_email: str = "pk2psp@gmail.com"
    pinecone_api_key: str
    pinecone_index_name: str
    openai_api_key: str
    redis_url: str
    database_url: str
    upstash_vector_rest_url: Optional[str] = None
    upstash_vector_rest_token: Optional[str] = None
    supabase_key: Optional[str] = None

    # JWT Authentication
    jwt_secret_key: str = "your-super-secret-jwt-key" # In production, set this in .env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AWS S3
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_bucket_name: str
    sqs_queue_url: str

settings = Settings()
