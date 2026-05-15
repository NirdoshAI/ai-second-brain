"""
Embedder module for the AI Second Brain backend.

This module is responsible for generating vector embeddings from text chunks and
storing them in ChromaDB. It exposes a single public function, `embed_and_store`,
which replaces the active-session collection on every call so that each new PDF
upload starts with a clean slate.

The ChromaDB client is created once at import time as a module-level singleton so
that the same in-memory database is reused across all requests within a single
server process lifetime.
"""

import json

import chromadb
import chromadb.utils.embedding_functions as embedding_functions

from app.models import Chunk

# ---------------------------------------------------------------------------
# Module-level constants and singletons
# ---------------------------------------------------------------------------

COLLECTION_NAME = "active_session"

# EphemeralClient keeps everything in memory — no disk persistence needed for MVP.
_chroma_client = chromadb.EphemeralClient()

# Reuse the same embedding function instance across calls to avoid reloading the
# model weights on every request.
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def embed_and_store(chunks: list[Chunk]) -> int:
    """Embed *chunks* and store them in the ChromaDB active-session collection.

    The existing ``active_session`` collection (if any) is deleted before a new
    one is created, satisfying the requirement that each upload starts with a
    fresh vector store (Requirement 3.5).

    ChromaDB computes the embeddings automatically using the
    ``SentenceTransformerEmbeddingFunction`` attached to the collection, so this
    function only needs to supply raw text documents and metadata.

    ``page_numbers`` is JSON-serialised to a string because ChromaDB metadata
    values must be scalars (Requirement 3.4).

    Args:
        chunks: A list of :class:`~app.models.Chunk` objects produced by the
            Chunker.  Must not be empty.

    Returns:
        The number of chunks successfully stored (equal to ``len(chunks)``).

    Raises:
        RuntimeError: If any ChromaDB operation fails.  The original exception
            message is included so the FastAPI error handler can surface a
            meaningful HTTP 500 response (Requirement 3.6).
    """
    try:
        # Delete the previous session collection if it exists so that a new
        # upload never inherits stale embeddings from a prior PDF.
        try:
            _chroma_client.delete_collection(COLLECTION_NAME)
        except Exception:
            # Collection did not exist — that is fine, nothing to delete.
            pass

        collection = _chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=_embedding_fn,
        )

        ids = [chunk.id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source_file": chunk.source_file,
                "page_numbers": json.dumps(chunk.page_numbers),
            }
            for chunk in chunks
        ]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

        return len(chunks)

    except Exception as e:
        raise RuntimeError(f"Failed to store embeddings: {e}") from e
