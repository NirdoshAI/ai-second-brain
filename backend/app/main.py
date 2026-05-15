"""
AI Second Brain — FastAPI application entry point.

This module wires together all backend components into a runnable FastAPI
application.  It exposes three HTTP endpoints:

- ``POST /upload``  — accepts a PDF file, runs the full ingestion pipeline
  (extract → chunk → embed), and activates a new session.
- ``POST /query``   — accepts a natural-language question, retrieves relevant
  chunks from the active session, and returns a Claude-generated answer with
  source attribution.
- ``GET  /health``  — returns the operational status of the service and its
  ChromaDB dependency.

CORS is configured to allow requests from the Vite dev server
(``http://localhost:5173``) and a local React dev server
(``http://localhost:3000``).
"""

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import HealthResponse, QueryRequest, QueryResponse, UploadResponse
from app.pdf_processor import extract_text
from app.chunker import chunk_pages
from app.embedder import embed_and_store, _chroma_client
from app.retriever import retrieve
from app.ai_client import generate_answer
from app.session import get_session, set_session

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Second Brain", version="1.0.0")

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    """Ingest a PDF file and store its embeddings in the active session.

    Validates the file type and size, then runs the full processing pipeline:
    text extraction → chunking → embedding → vector storage.  On success the
    session is updated so that subsequent ``/query`` calls operate on this PDF.

    Args:
        file: The uploaded file received as ``multipart/form-data``.

    Returns:
        An :class:`~app.models.UploadResponse` with the filename, chunk count,
        and a human-readable success message.

    Raises:
        HTTPException 422: If the file is not a PDF or exceeds 20 MB, or if
            the PDF contains no extractable text.
        HTTPException 500: If embedding or vector storage fails.
    """
    # --- Validate file type ---------------------------------------------------
    filename = file.filename or ""
    is_pdf_name = filename.lower().endswith(".pdf")
    is_pdf_content_type = file.content_type == "application/pdf"

    if not (is_pdf_name or is_pdf_content_type):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    # --- Read and validate file size -----------------------------------------
    pdf_bytes = await file.read()

    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File size exceeds the 20 MB limit.")

    # --- Run ingestion pipeline -----------------------------------------------
    try:
        pages = extract_text(pdf_bytes, filename)
        chunks = chunk_pages(pages, filename)
        chunk_count = embed_and_store(chunks)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # --- Activate session and return response ---------------------------------
    set_session(filename)

    return UploadResponse(
        filename=filename,
        chunk_count=chunk_count,
        message=f"Successfully processed '{filename}' into {chunk_count} chunks.",
    )


@app.post("/query", response_model=QueryResponse)
def query_document(request: QueryRequest) -> QueryResponse:
    """Answer a natural-language question using the active PDF session.

    Retrieves the most relevant chunks from ChromaDB and passes them together
    with the question to Claude to generate a grounded answer.

    Args:
        request: A :class:`~app.models.QueryRequest` containing the question.

    Returns:
        A :class:`~app.models.QueryResponse` with the answer text and source
        attribution metadata.

    Raises:
        HTTPException 400: If no PDF session is currently active, or if the
            vector store has no active collection.
        HTTPException 502: If the Claude API returns an error.
    """
    # --- Guard: require an active session ------------------------------------
    if not get_session().is_active:
        raise HTTPException(
            status_code=400,
            detail="No document loaded. Please upload a PDF first.",
        )

    # --- Retrieve and generate -----------------------------------------------
    try:
        chunks = retrieve(request.question)
        answer, sources = generate_answer(request.question, chunks)
    except LookupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return QueryResponse(answer=answer, sources=sources)


@app.get("/health", response_model=HealthResponse)
def health_check() -> JSONResponse:
    """Return the operational status of the service and its dependencies.

    Attempts a ChromaDB heartbeat to verify that the vector store is reachable.

    Returns:
        HTTP 200 with ``{"status": "ok"}`` when everything is healthy.
        HTTP 503 with ``{"status": "degraded", "detail": "ChromaDB unreachable"}``
        when ChromaDB cannot be reached.
    """
    try:
        _chroma_client.heartbeat()
        return JSONResponse(
            status_code=200,
            content=HealthResponse(status="ok").model_dump(exclude_none=True),
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content=HealthResponse(
                status="degraded", detail="ChromaDB unreachable"
            ).model_dump(),
        )
