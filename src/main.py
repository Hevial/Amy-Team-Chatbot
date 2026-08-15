"""
FastAPI entry point for the Amy Team Chatbot API.

Provides endpoints for health checking and RAG querying. The LlamaIndex
query engine is initialized once during the application lifespan to
minimize latency on incoming requests.

"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core.base.response.schema import Response

from src import __version__
from src.config import settings
from src.engine import HybridRAGEngine, get_indexed_document_count
from src.models import HealthResponse, QueryRequest, QueryResponse, SourceNode

logger = logging.getLogger(__name__)

# Global reference to the query engine
query_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI.
    
    Initializes the RAG query engine at startup and cleans up at shutdown.
    This ensures the vector store is loaded into memory only once.
    """
    global query_engine
    logger.info("Initializing application lifespan...")
    try:
        query_engine = HybridRAGEngine()
        logger.info("Hybrid RAG Engine initialized successfully.")
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to initialize query engine: %s", e)
        # We don't raise here to allow the API to start (e.g., for health checks)
        # but the /query endpoint will fail gracefully.
    
    yield
    
    logger.info("Application shutting down...")
    query_engine = None


# Initialize FastAPI app
app = FastAPI(
    title="Amy Team Chatbot API",
    description="RAG-powered Assistant Coach for Amnesia Esports.",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to Swagger UI documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Check API and Database Health",
)
async def health_check():
    """Verify that the API is running and the vector database is accessible."""
    doc_count = get_indexed_document_count()
    return HealthResponse(
        status="healthy" if doc_count > 0 else "degraded",
        version=__version__,
        documents_indexed=doc_count,
        environment=settings.log_level,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        google_search_enabled=settings.enable_google_search,
    )


@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["RAG"],
    summary="Query the Assistant Coach",
)
async def query_assistant(request: QueryRequest):
    """
    Ask a question to the Amy Assistant Coach.
    
    The engine retrieves relevant context from the team's documents and 
    generates a precise, cited answer using Google Gemini.
    """
    
    if query_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query engine is not initialized. Check server logs.",
        )

    start_time = time.perf_counter()
    
    try:
        # If the user specified a custom top_k for this request, we update the engine temporarily.
        # Note: In a highly concurrent prod app, we'd use a custom retriever per request instead of mutating the global engine.
        # For this POC, mutating the engine is sufficient.
        if request.top_k and request.top_k != settings.similarity_top_k:
            query_engine.update_prompts({"similarity_top_k": request.top_k})
            
        # Execute the Hybrid RAG query
        logger.info("Executing hybrid query: '%s'", request.question)
        answer, internal_nodes, web_nodes = query_engine.query(
            question=request.question,
            enable_google_search=request.enable_google_search,
            top_k=request.top_k,
        )
        
        # Parse the source nodes used for the answer
        sources = []
        
        # Internal Document Citations
        for node in internal_nodes:
            text_content = node["text"]
            text_snippet = text_content[:500] + "..." if len(text_content) > 500 else text_content
            sources.append(
                SourceNode(
                    source_type="document",
                    text=text_snippet,
                    file_name=node.get("file_name", "Unknown"),
                    score=node.get("score"),
                    metadata=node.get("metadata", {}),
                )
            )
            
        # Web Search Citations
        for node in web_nodes:
            sources.append(
                SourceNode(
                    source_type="web",
                    text=node["title"],  # Web chunks typically only contain URI/Title in Grounding metadata
                    url=node["url"],
                    title=node["title"],
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info("Query completed in %.2f ms.", elapsed_ms)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            llm_model=settings.llm_model,
            query_time_ms=elapsed_ms,
        )

    except Exception as e:
        logger.exception("Error processing query.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the response: {e!s}",
        )
