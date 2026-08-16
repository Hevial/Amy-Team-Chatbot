"""
Data Ingestion Pipeline for Amy Team Chatbot.

Reads documents from the configured data directory, generates embeddings
using Google Gemini, and stores them in a persistent ChromaDB vector database.

This script is designed to be run as a standalone CLI tool before starting
the API server. It supports incremental updates and full re-indexing.

Usage:
    python -m scripts.ingest           # Index new documents
    python -m scripts.ingest --clear   # Wipe and rebuild the entire index
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.firestore import FirestoreVectorStore

# Resolve the project root so imports work when running as a module.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def validate_environment() -> None:
    """Ensure all required configuration is present before proceeding."""
    if not settings.google_api_key:
        logger.error(
            "GOOGLE_API_KEY is not set. "
            "Copy .env.example to .env and add your API key from https://aistudio.google.com/app/apikey"
        )
        sys.exit(1)

    data_path = Path(settings.data_dir)
    if not data_path.exists():
        logger.error("Data directory '%s' does not exist.", settings.data_dir)
        sys.exit(1)

    # Check that there are actually documents to ingest.
    doc_files = list(data_path.rglob("*"))
    doc_files = [f for f in doc_files if f.is_file() and f.name != ".gitkeep"]
    if not doc_files:
        logger.error("No documents found in '%s'.", settings.data_dir)
        sys.exit(1)

    logger.info("Found %d document(s) in '%s'.", len(doc_files), settings.data_dir)


def clear_collection(chroma_client: ClientAPI | None = None) -> None:
    """Delete the existing collection for a fresh re-index."""
    try:
        if settings.vector_store_type.lower() == "firestore":
            import google.auth
            from google.cloud import firestore
            
            project_id = settings.firestore_project_id
            if not project_id:
                credentials, project_id = google.auth.default()
                
            if project_id:
                db = firestore.Client(project=project_id, database=settings.firestore_database_id)
                docs = db.collection(settings.collection_name).limit(500).stream()
                batch = db.batch()
                deleted = 0
                for doc in docs:
                    batch.delete(doc.reference)
                    deleted += 1
                if deleted > 0:
                    batch.commit()
                logger.info("Cleared existing Firestore collection '%s' (up to 500 docs).", settings.collection_name)
        else:
            if chroma_client:
                chroma_client.delete_collection(settings.collection_name)
                logger.info("Cleared existing ChromaDB collection '%s'.", settings.collection_name)
    except ValueError:
        logger.info("No existing collection '%s' to clear.", settings.collection_name)
    except Exception as e:
        logger.warning("Could not clear collection: %s", e)


def run_ingestion(clear: bool = False) -> None:
    """Execute the full ingestion pipeline.

    Steps:
        1. Configure the embedding model (Google Gemini text-embedding-004).
        2. Load documents from the data directory.
        3. Initialize ChromaDB with persistent storage.
        4. Optionally clear the existing collection.
        5. Build the VectorStoreIndex and persist embeddings.

    Args:
        clear: If True, delete the existing collection before re-indexing.
    """
    start_time = time.perf_counter()

    # ---- Step 1: Configure LlamaIndex global settings ----
    logger.info("Configuring embedding model: Google GenAI (%s)", settings.embedding_model)
    Settings.embed_model = GoogleGenAIEmbedding(
        model_name=settings.embedding_model,
        api_key=settings.google_api_key,
    )
    Settings.node_parser = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # ---- Step 2: Load documents ----
    logger.info("Loading documents from '%s'...", settings.data_dir)
    documents = SimpleDirectoryReader(
        input_dir=settings.data_dir,
        recursive=True,
        filename_as_id=True,
    ).load_data()
    logger.info("Loaded %d document(s).", len(documents))

    # ---- Step 3 & 4: Initialize Vector Store and Optionally clear ----
    if settings.vector_store_type.lower() == "firestore":
        logger.info("Initializing Firestore Vector Store...")
        if clear:
            clear_collection()
            
        import google.auth
        from google.cloud import firestore
        
        project_id = settings.firestore_project_id
        if not project_id:
            try:
                credentials, project_id = google.auth.default()
            except Exception as e:
                logger.warning("Could not get default GCP project: %s", e)
        
        if not project_id:
            raise ValueError("FIRESTORE_PROJECT_ID must be set when using firestore vector store.")
            
        db = firestore.Client(project=project_id, database=settings.firestore_database_id)
        vector_store = FirestoreVectorStore(
            collection_name=settings.collection_name,
            db=db
        )
    else:
        chroma_db_path = Path(settings.chroma_db_dir)
        chroma_db_path.mkdir(parents=True, exist_ok=True)
    
        logger.info("Initializing ChromaDB at '%s'...", chroma_db_path)
        chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
    
        if clear:
            clear_collection(chroma_client)
    
        chroma_collection = chroma_client.get_or_create_collection(settings.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # ---- Step 5: Build the index (this generates embeddings) ----
    logger.info("Building vector index — generating embeddings...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    # ---- Report results ----
    elapsed = time.perf_counter() - start_time
    node_count = len(index.docstore.docs)
    logger.info(
        "Ingestion complete: %d chunks indexed in %.2fs.",
        node_count,
        elapsed,
    )
    if settings.vector_store_type.lower() == "firestore":
        logger.info(
            "Firestore collection '%s' populated successfully.",
            settings.collection_name,
        )
    else:
        chroma_db_path = Path(settings.chroma_db_dir)
        logger.info(
            "ChromaDB collection '%s' persisted at '%s'.",
            settings.collection_name,
            chroma_db_path,
        )


def main() -> None:
    """CLI entry point for the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Amy Team Chatbot — Data Ingestion Pipeline",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the existing vector store before re-indexing all documents.",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Amy Team Chatbot — Data Ingestion Pipeline")
    logger.info("=" * 60)

    validate_environment()
    run_ingestion(clear=args.clear)

    logger.info("=" * 60)
    logger.info("Done. You can now start the API server with: uvicorn src.main:app")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
