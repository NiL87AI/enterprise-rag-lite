from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"  # <-- CAMBIATO QUI: da "all-minilm" a "nomic-embed-text"
    collection_name: str = "enterprise_docs"
    chunk_size: int = 500
    chunk_overlap: int = 100
    confidence_threshold: float = 0.6
    
    class Config:
        env_file = ".env"

settings = Settings()