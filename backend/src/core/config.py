from pydantic_settings import BaseSettings
from functools import lru_cache # 싱글톤 보장

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # ChromaDB
    chroma_server_host: str = "localhost"
    chroma_server_http_port: int = 8000
    chroma_collection_name: str = "law_chunks"

    # SQLite
    sqlite_db_path: str = "./volume/chat_history.db"

    # 법령정보센터
    law_api_key: str

    # 서비스
    backend_url: str = "http://localhost:8080"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()