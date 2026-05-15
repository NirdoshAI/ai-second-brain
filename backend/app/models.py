"""
Data models for the AI Second Brain backend.

This module defines:
- Internal dataclasses used within the processing pipeline (PageText, Chunk)
- Pydantic models used for API request/response serialization (SourceAttribution,
  UploadResponse, QueryRequest, QueryResponse, HealthResponse, SessionState)
"""

from dataclasses import dataclass, field
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Internal dataclasses (used within the processing pipeline, not serialized
# directly to/from API JSON)
# ---------------------------------------------------------------------------


@dataclass
class PageText:
    """Holds the extracted text for a single PDF page."""

    page_number: int  # 1-indexed
    text: str


@dataclass
class Chunk:
    """A token-based text chunk produced by the Chunker, ready for embedding."""

    id: str                    # UUID string — stable ChromaDB document ID
    text: str                  # Raw chunk text
    source_file: str           # Original PDF filename
    page_numbers: list[int] = field(default_factory=list)  # Pages this chunk spans


# ---------------------------------------------------------------------------
# Pydantic models (used for API request/response validation and serialization)
# ---------------------------------------------------------------------------


class SourceAttribution(BaseModel):
    """Source metadata attached to an AI answer, pointing back to the PDF origin."""

    source_file: str
    page_numbers: list[int]


class UploadResponse(BaseModel):
    """Response body returned after a successful PDF upload and processing."""

    filename: str
    chunk_count: int
    message: str


class QueryRequest(BaseModel):
    """Request body for the POST /query endpoint."""

    question: str


class QueryResponse(BaseModel):
    """Response body returned by the POST /query endpoint."""

    answer: str
    sources: list[SourceAttribution]


class HealthResponse(BaseModel):
    """Response body returned by the GET /health endpoint."""

    status: str
    detail: str | None = None


class SessionState(BaseModel):
    """Represents the current active-session state exposed via the API."""

    filename: str | None = None
    is_active: bool = False
