"""
Centralized application configuration using Pydantic Settings.

All settings are loaded from environment variables or a `.env` file.
This module provides a single, validated, and typed configuration object
that is shared across the entire application.

Usage:
    from src.config import settings
    print(settings.llm_model)
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        google_api_key (str | None): API key for Google AI Studio (Gemini).
        groq_api_key (str | None): API key for Groq API (fallback).
        llm_model (str): Primary LLM identifier, dynamically loaded from LLM_MODEL or defaulting to gemini-2.0-flash.
        embedding_model (str): Primary Embedding identifier, dynamically loaded from EMBEDDING_MODEL or defaulting to text-embedding-004.
        enable_google_search (bool): Toggle to enable or disable native Google Search grounding.
        google_cloud_project (str | None): Google Cloud Project ID for deployment.
        google_cloud_location (str): Google Cloud region (default: europe-west1).
        data_dir (str): Path to the directory containing source documents.
        chroma_db_dir (str): Path for ChromaDB persistent storage on disk.
        collection_name (str): Name of the ChromaDB collection to use.
        host (str): Host address for the FastAPI server.
        port (int): Port number for the FastAPI server.
        log_level (str): Logging verbosity level.
        similarity_top_k (int): Number of top similar chunks to retrieve per query.
        chunk_size (int): Maximum number of tokens per document chunk.
        chunk_overlap (int): Number of overlapping tokens between consecutive chunks.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- Integrations ----
    # API Keys are automatically loaded from the .env file
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    
    # ---- Models & Capabilities ----
    llm_model: str = Field(default="gemini-2.0-flash", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-004", alias="EMBEDDING_MODEL")
    enable_google_search: bool = Field(default=True, alias="ENABLE_GOOGLE_SEARCH")

    # ---- Google Cloud Platform Settings ----
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="europe-west1", alias="GOOGLE_CLOUD_LOCATION")

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
