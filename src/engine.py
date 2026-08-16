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
2. **Citations:** Do NOT insert source file names or citations directly into your answer text. 
   Instead, you must list the Document IDs of the internal documents you actually used to formulate your answer at the very end of your response, in this exact format: `USED_DOCS: [1, 3]`. If you didn't use any internal documents, do not include this tag.
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
        chroma_db_path = Path(settings.chroma_db_dir)
        if not chroma_db_path.exists():
            raise FileNotFoundError(
                f"ChromaDB directory not found at '{chroma_db_path}'. "
                "Run 'python -m scripts.ingest' first to index your documents."
            )

        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set in .env. Please get an API key from Google AI Studio."
            )

        logger.info("Initializing ChromaDB connection...")
        self.chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
        self.collection = self.chroma_client.get_or_create_collection(settings.collection_name)

        doc_count = self.collection.count()
        if doc_count == 0:
            logger.warning("ChromaDB collection is empty. Please run the ingest script.")

        logger.info("Configuring embedding model: Google GenAI (%s)", settings.embedding_model)
        self.embed_model = GoogleGenAIEmbedding(
            model_name=settings.embedding_model, api_key=settings.google_api_key
        )

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
            # We assign a 1-based Document ID to each chunk so the LLM can cite it secretly
            context_str += f"[Doc {i + 1}] (File: {file_name})\n{n.text}\n\n"

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

        internal_nodes = []
        for n in nodes:
            internal_nodes.append(
                {
                    "text": n.text,
                    "file_name": n.metadata.get("file_name", "Unknown"),
                    "score": n.score,
                    "metadata": n.metadata,
                }
            )

        answer = response.text or ""
        
        # Extract hidden citations generated by the LLM
        import re
        used_indices = []
        
        # Regex to find "USED_DOCS: [1, 3]" at the end of the string
        match = re.search(r"USED_DOCS:\s*\[(.*?)\]", answer)
        if match:
            indices_str = match.group(1)
            # Parse the indices and convert to 1-based integers
            used_indices = [int(x.strip()) for x in indices_str.split(",") if x.strip().isdigit()]
            
            # Remove the citation block from the final answer text sent to the user
            answer = answer[:match.start()].strip()
        
        # Filter internal sources: only keep the chunks whose 1-based index was cited by the LLM
        # Deduplicate by file_name so the UI doesn't show the same file multiple times
        internal_sources = []
        seen_files = set()
        for i, node in enumerate(internal_nodes):
            if (i + 1) in used_indices:
                file_name = node.get("file_name", "Unknown")
                if file_name not in seen_files:
                    internal_sources.append(node)
                    if file_name != "Unknown":
                        seen_files.add(file_name)

        return answer, internal_sources, web_sources


def get_indexed_document_count() -> int:
    """Return the number of indexed chunks in the ChromaDB collection."""
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
