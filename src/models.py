"""
Pydantic models for API request and response schemas.

These models define the contracts for the FastAPI endpoints and provide
automatic validation and documentation in the Swagger UI.
"""

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload for the RAG query endpoint."""

    question: str = Field(
        ...,
        description="The question to ask the Assistant Coach.",
        example="What is the disconnection rule for Valorant tournaments?",
    )
    top_k: int | None = Field(
        default=None,
        description="Override the default number of similar chunks to retrieve.",
        ge=1,
        le=20,
    )
    enable_google_search: bool = Field(
        default=True,
        description="Whether to use Google Search Grounding for live web info.",
    )


class SourceNode(BaseModel):
    """Represents a retrieved document chunk or web search result used to generate the answer."""

    source_type: str = Field(..., description="Type of source: 'document' or 'web'.")
    text: str = Field(..., description="The text content or snippet of the retrieved chunk.")
    file_name: str | None = Field(default=None, description="The source file name (if document).")
    url: str | None = Field(default=None, description="The source URL (if web search).")
    title: str | None = Field(default=None, description="Title of the web page or document.")
    score: float | None = Field(default=None, description="Similarity score of the chunk.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata.")


class QueryResponse(BaseModel):
    """Response payload containing the LLM answer and source citations."""

    answer: str = Field(..., description="The generated answer from the LLM.")
    sources: list[SourceNode] = Field(
        default_factory=list,
        description="List of document chunks and web results used as context.",
    )
    llm_model: str | None = Field(default=None, description="The LLM model used for generation.")
    query_time_ms: float = Field(..., description="Time taken to process the query in milliseconds.")


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint."""

    status: str = Field(..., description="Current status of the API.")
    version: str = Field(..., description="API version.")
    documents_indexed: int = Field(..., description="Number of document chunks currently in the vector store.")
    environment: str = Field(..., description="Current deployment environment.")
    llm_model: str = Field(..., description="Configured LLM model.")
    embedding_model: str = Field(..., description="Configured embedding model.")
    google_search_enabled: bool = Field(..., description="Whether Google Search Grounding is enabled globally.")
