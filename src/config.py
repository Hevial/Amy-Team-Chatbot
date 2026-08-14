"""
Centralized application configuration using Pydantic Settings.

All settings are loaded from environment variables or a `.env` file.
This module provides a single, validated, and typed configuration object
that is shared across the entire application.

Usage:
    from src.config import settings
    print(settings.llm_model)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        google_api_key: API key for Google AI Studio (Gemini).
        llm_model: Gemini model identifier for text generation.
        embedding_model: Gemini model identifier for text embeddings.
        data_dir: Path to the directory containing source documents.
        chroma_db_dir: Path for ChromaDB persistent storage on disk.
        collection_name: Name of the ChromaDB collection to use.
        host: Host address for the FastAPI server.
        port: Port number for the FastAPI server.
        log_level: Logging verbosity level.
        similarity_top_k: Number of top similar chunks to retrieve per query.
        chunk_size: Maximum number of tokens per document chunk.
        chunk_overlap: Number of overlapping tokens between consecutive chunks.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Google AI Studio ---
    google_api_key: str = ""

    # --- LLM Configuration ---
    llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "text-embedding-004"

    # --- Data & Storage Paths ---
    data_dir: str = "./data/samples"
    chroma_db_dir: str = "./chroma_db"
    collection_name: str = "amnesia_docs"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"

    # --- RAG Engine ---
    similarity_top_k: int = 5
    chunk_size: int = 1024
    chunk_overlap: int = 128


# Singleton instance — import this across the application.
settings = Settings()
