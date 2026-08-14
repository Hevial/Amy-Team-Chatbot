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
from src.engine import create_query_engine, get_indexed_document_count
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
        query_engine = create_query_engine()
        logger.info("RAG Query Engine initialized successfully.")
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
            
        # Execute the RAG query
        logger.info("Executing query: '%s'", request.question)
        response: Response = query_engine.query(request.question)
        
        # Parse the source nodes used for the answer
        sources = []
        if response.source_nodes:
            for node_with_score in response.source_nodes:
                node = node_with_score.node
                sources.append(
                    SourceNode(
                        text=node.get_content()[:500] + "..." if len(node.get_content()) > 500 else node.get_content(),
                        file_name=node.metadata.get("file_name", "Unknown"),
                        score=node_with_score.score,
                        metadata=node.metadata,
                    )
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info("Query completed in %.2f ms.", elapsed_ms)
        
        return QueryResponse(
            answer=str(response),
            sources=sources,
            query_time_ms=elapsed_ms,
        )

    except Exception as e:
        logger.exception("Error processing query.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the response: {e!s}",
        )
