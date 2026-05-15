"""
Retriever module for the AI Second Brain backend.

This module is responsible for querying the ChromaDB vector store to find the
most semantically similar chunks for a given user question. It reuses the same
ChromaDB singleton client and collection name defined in the Embedder module,
ensuring that query embeddings are generated with the same model that was used
during the ingestion phase (Requirement 5.2).

The single public function, ``retrieve``, returns a ranked list of
:class:`~app.models.Chunk` objects ready to be passed to the AI client as
grounding context.
"""

import json

import chromadb

from app.models import Chunk
from app.embedder import _chroma_client, COLLECTION_NAME


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def retrieve(question: str, n_results: int = 5) -> list[Chunk]:
    """Query the active-session collection for chunks relevant to *question*.

    ChromaDB automatically embeds *question* using the embedding function that
    was attached to the collection at creation time (``all-MiniLM-L6-v2``), so
    no explicit embedding step is required here (Requirement 5.2).

    The top *n_results* most semantically similar chunks are returned in
    descending relevance order as reconstructed :class:`~app.models.Chunk`
    objects (Requirement 5.1).

    Args:
        question: The natural-language question to search for.
        n_results: Maximum number of chunks to return.  Defaults to ``5``.

    Returns:
        A list of :class:`~app.models.Chunk` objects reconstructed from the
        ChromaDB query results, ordered by descending similarity.

    Raises:
        LookupError: If the ``active_session`` collection does not exist, which
            means no PDF has been uploaded yet (Requirement 5.4).  The caller
            (FastAPI endpoint) should map this to an HTTP 400 response.
    """
    # Verify that an active session collection exists before querying.
    try:
        collection = _chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        raise LookupError("No document loaded. Please upload a PDF first.")

    results = collection.query(query_texts=[question], n_results=n_results)

    # Reconstruct Chunk objects from the flat result arrays.
    # ChromaDB returns nested lists (one inner list per query), so we index [0]
    # to get the results for our single query.
    chunks: list[Chunk] = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    for i in range(len(ids)):
        chunk = Chunk(
            id=ids[i],
            text=documents[i],
            source_file=metadatas[i]["source_file"],
            page_numbers=json.loads(metadatas[i]["page_numbers"]),
        )
        chunks.append(chunk)

    return chunks
