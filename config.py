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
    upstash_api_key: Optional[str] = None
    supabase_key: Optional[str] = None

    # AWS S3
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_bucket_name: str

settings = Settings()
