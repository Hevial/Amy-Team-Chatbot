"""
RAG Query Engine for Amy Team Chatbot.

This module initializes the LlamaIndex query engine by loading an existing
ChromaDB vector store and configuring the Google Gemini LLM with a custom
system prompt tailored for esports coaching and rulebook assistance.

The engine is designed to be initialized once at application startup and
shared across all incoming API requests.

Usage:
    from src.engine import create_query_engine
    engine = create_query_engine()
    response = engine.query("What is the disconnection rule?")
"""

import logging
from pathlib import Path

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt — Defines the assistant's behavior and constraints.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are **Amy**, the AI Assistant Coach for **Amnesia Esports**.

Your role is to provide accurate, concise, and actionable answers to questions
about tournament rules, game mechanics, patch notes, and team strategy.

## Instructions:
1. **Always cite your sources.** When referencing a document, mention the
   file name and the relevant section (e.g., "According to the Tournament
   Rulebook, Section 3.1...").
2. **Stay within the provided context.** Only answer based on the retrieved
   documents. If the information is not available, say: "I don't have enough
   information in the current documents to answer this question."
3. **Be precise and direct.** Esports professionals need quick, clear answers
   — especially during live tournament situations.
4. **Use structured formatting** when listing rules, stats, or comparisons
   (bullet points, tables, numbered lists).
5. **Language:** Always respond in the same language as the user's question.
"""


def create_query_engine(similarity_top_k: int | None = None):
    """Create and configure the RAG query engine.

    Loads the existing ChromaDB collection (populated by the ingestion script),
    configures the Gemini LLM and embedding model, and returns a ready-to-use
    query engine instance.

    Args:
        similarity_top_k: Number of top similar chunks to retrieve per query.
                          Defaults to the value in application settings.

    Returns:
        A LlamaIndex query engine configured with Gemini LLM, ChromaDB
        retrieval, and the esports coaching system prompt.

    Raises:
        FileNotFoundError: If the ChromaDB directory does not exist.
        ValueError: If the ChromaDB collection is empty (no documents indexed).
    """
    top_k = similarity_top_k or settings.similarity_top_k

    # ---- Validate that the vector store exists ----
    chroma_db_path = Path(settings.chroma_db_dir)
    if not chroma_db_path.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found at '{chroma_db_path}'. "
            "Run 'python -m scripts.ingest' first to index your documents."
        )

    # ---- Configure LlamaIndex global settings ----
    logger.info("Configuring LLM: %s", settings.llm_model)
    Settings.llm = GoogleGenAI(
        model=settings.llm_model,
        api_key=settings.google_api_key,
    )

    logger.info("Configuring embedding model: %s", settings.embedding_model)
    Settings.embed_model = GoogleGenAIEmbedding(
        model_name=settings.embedding_model,
        api_key=settings.google_api_key,
    )

    Settings.node_parser = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # ---- Load existing ChromaDB collection ----
    logger.info(
        "Loading ChromaDB collection '%s' from '%s'...",
        settings.collection_name,
        chroma_db_path,
    )
    chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
    chroma_collection = chroma_client.get_or_create_collection(settings.collection_name)

    doc_count = chroma_collection.count()
    if doc_count == 0:
        raise ValueError(
            f"ChromaDB collection '{settings.collection_name}' is empty. "
            "Run 'python -m scripts.ingest' first to index your documents."
        )

    logger.info("Loaded %d indexed chunks from ChromaDB.", doc_count)

    # ---- Build the query engine ----
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        system_prompt=SYSTEM_PROMPT,
    )

    logger.info("Query engine ready (top_k=%d).", top_k)
    return query_engine


def get_indexed_document_count() -> int:
    """Return the number of indexed chunks in the ChromaDB collection.

    This is used by the health check endpoint to report index status
    without initializing the full query engine.

    Returns:
        The number of chunks in the collection, or 0 if unavailable.
    """
    try:
        chroma_db_path = Path(settings.chroma_db_dir)
        if not chroma_db_path.exists():
            return 0
        chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
        collection = chroma_client.get_or_create_collection(settings.collection_name)
        return collection.count()
    except Exception:
        logger.warning("Could not read ChromaDB collection count.", exc_info=True)
        return 0
