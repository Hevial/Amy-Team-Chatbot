"""
Hybrid RAG Query Engine for Amy Team Chatbot.

This module provides the `HybridRAGEngine` class which combines local document
retrieval (ChromaDB + LlamaIndex) with live web search grounding (Google GenAI).
"""

import logging
from pathlib import Path
from typing import Any

import chromadb
from google import genai
from google.genai import types
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.firestore import FirestoreVectorStore

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
1. **Domain Boundaries (CRITICAL):** You are an Esports Coach. If the user asks 
   you to write code, you may ONLY do so if it is strictly related to gaming,
   Esports, or Amnesia's tools (e.g., game config files, Riot API scripts). 
   Politely decline all generic coding requests (e.g., building an e-commerce site)
   or unrelated topics.
2. **Always cite your sources.** When referencing a document, mention the
   file name and the relevant section.
3. **Stay within the provided context or Search.** Use the provided internal
   documents. If the information is not available and you have access to Google Search,
   use it to find the answer on the live web.
4. **Be precise and direct.** Esports professionals need quick, clear answers.
5. **Language:** Always respond in the same language as the user's question.
"""


class HybridRAGEngine:
    """Combines ChromaDB vector retrieval with Google Gemini Native Search Grounding."""

    def __init__(self):
        """Initializes the retriever and the Gemini AI client."""
        logger.info("Configuring embedding model: Google GenAI (%s)", settings.embedding_model)
        self.embed_model = GoogleGenAIEmbedding(
            model_name=settings.embedding_model, api_key=settings.google_api_key
        )

        if settings.vector_store_type.lower() == "firestore":
            logger.info("Initializing Firestore connection...")
            import google.auth
            from google.cloud import firestore
            
            # Use provided project ID or fallback to Application Default Credentials
            project_id = settings.firestore_project_id
            if not project_id:
                try:
                    credentials, project_id = google.auth.default()
                except Exception as e:
                    logger.warning("Could not get default GCP project: %s", e)
            
            if not project_id:
                raise ValueError("FIRESTORE_PROJECT_ID must be set when using firestore vector store.")
                
            logger.info("Connecting to Firestore in project '%s', database '%s'", project_id, settings.firestore_database_id)
            db = firestore.Client(project=project_id, database=settings.firestore_database_id)
            self.vector_store = FirestoreVectorStore(
                collection_name=settings.collection_name,
                db=db
            )
        else:
            logger.info("Initializing ChromaDB connection...")
            chroma_db_path = Path(settings.chroma_db_dir)
            if not chroma_db_path.exists():
                raise FileNotFoundError(
                    f"ChromaDB directory not found at '{chroma_db_path}'. "
                    "Run 'python -m scripts.ingest' first to index your documents."
                )
            
            self.chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
            self.collection = self.chroma_client.get_or_create_collection(settings.collection_name)
            
            doc_count = self.collection.count()
            if doc_count == 0:
                logger.warning("ChromaDB collection is empty. Please run the ingest script.")
                
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model,
        )
        self.retriever = self.index.as_retriever(similarity_top_k=settings.similarity_top_k)

        logger.info("Configuring Google GenAI Client...")
        self.ai_client = genai.Client(api_key=settings.google_api_key)

    def query(
        self, question: str, enable_google_search: bool = False, top_k: int | None = None
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Executes a hybrid query combining local context and optional Google Search.

        Args:
            question: The user's prompt.
            enable_google_search: Whether to enable Google Search Grounding for this query.
                Already resolved by the caller — this engine does not check settings.
            top_k: Optional override for the number of internal chunks to retrieve.

        Returns:
            A tuple containing:
            - The text response from the LLM.
            - A list of internal document chunks used.
            - A list of web search chunks used (if any).
        """
        # 1. Retrieve internal documents
        if top_k is not None and top_k != settings.similarity_top_k:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
        else:
            retriever = self.retriever

        nodes = retriever.retrieve(question)

        context_str = ""
        for i, n in enumerate(nodes):
            file_name = n.metadata.get("file_name", "Unknown")
            context_str += f"--- Document {i + 1} ({file_name}) ---\n{n.text}\n\n"

        if context_str:
            prompt = f"User Question: {question}\n\nInternal Knowledge Base:\n{context_str}"
        else:
            prompt = f"User Question: {question}\n\nInternal Knowledge Base: (None available)"

        # 2. Configure Google GenAI call
        tools = []
        if enable_google_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            tools=tools if tools else None,
        )

        logger.info(
            "Generating content with model: %s (Google Search: %s)", settings.llm_model, bool(tools)
        )

        # 3. Call the model
        response = self.ai_client.models.generate_content(
            model=settings.llm_model, contents=prompt, config=config
        )

        # 4. Extract citations and web sources if Google Search was used
        web_sources = []
        if response.candidates and response.candidates[0].grounding_metadata:
            metadata = response.candidates[0].grounding_metadata
            if metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if chunk.web:
                        web_sources.append(
                            {
                                "title": chunk.web.title,
                                "url": chunk.web.uri,
                            }
                        )

        internal_sources = []
        for n in nodes:
            internal_sources.append(
                {
                    "text": n.text,
                    "file_name": n.metadata.get("file_name", "Unknown"),
                    "score": n.score,
                    "metadata": n.metadata,
                }
            )

        return response.text or "", internal_sources, web_sources


def get_indexed_document_count() -> int:
    """Return the number of indexed chunks in the active Vector Store."""
    try:
        if settings.vector_store_type.lower() == "firestore":
            import google.auth
            from google.cloud import firestore
            
            project_id = settings.firestore_project_id
            if not project_id:
                credentials, project_id = google.auth.default()
                
            if project_id:
                db = firestore.Client(project=project_id, database=settings.firestore_database_id)
                docs = db.collection(settings.collection_name).count().get()
                # AggregateQuerySnapshot returns a list of results
                if docs and len(docs) > 0:
                    return docs[0][0].value
            return 0
        else:
            chroma_db_path = Path(settings.chroma_db_dir)
            if not chroma_db_path.exists():
                return 0
            chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
            collection = chroma_client.get_or_create_collection(settings.collection_name)
            return collection.count()
    except Exception:
        logger.warning("Could not read active Vector Store collection count.", exc_info=True)
        return 0
