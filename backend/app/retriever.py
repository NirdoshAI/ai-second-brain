"""
Retriever module for the AI Second Brain backend.

Delegates to the TF-IDF retrieval function in the embedder module.
"""

from app.models import Chunk
from app.embedder import retrieve as _retrieve


def retrieve(question: str, n_results: int = 5) -> list[Chunk]:
    """Query the active-session store for chunks relevant to *question*.

    Args:
        question: The natural-language question to search for.
        n_results: Maximum number of chunks to return. Defaults to ``5``.

    Returns:
        A list of :class:`~app.models.Chunk` objects ordered by descending
        relevance.

    Raises:
        LookupError: If no document has been uploaded yet.
    """
    return _retrieve(question, n_results)
