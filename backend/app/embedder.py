"""
Embedder module for the AI Second Brain backend.

Uses a lightweight in-memory TF-IDF store instead of a neural embedding model,
keeping RAM usage well under 100 MB so the app runs on Render's free tier.

The single public function ``embed_and_store`` replaces the active session on
every call so that each new PDF upload starts with a clean slate.
"""

import json
import math
import re
from collections import Counter

from app.models import Chunk

# ---------------------------------------------------------------------------
# Module-level in-memory store
# ---------------------------------------------------------------------------

# Each entry: {"chunk": Chunk, "tf": {term: freq}}
_store: list[dict] = []

# IDF cache: {term: idf_score} — rebuilt on every upload
_idf: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into word tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_tf(tokens: list[str]) -> dict[str, float]:
    """Compute term frequency (normalised) for a token list."""
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    return {term: count / total for term, count in counts.items()}


def _build_idf(tfs: list[dict[str, float]]) -> dict[str, float]:
    """Compute IDF scores across all documents."""
    n = len(tfs)
    idf: dict[str, float] = {}
    # Collect all unique terms
    all_terms: set[str] = set()
    for tf in tfs:
        all_terms.update(tf.keys())
    for term in all_terms:
        doc_count = sum(1 for tf in tfs if term in tf)
        idf[term] = math.log((n + 1) / (doc_count + 1)) + 1.0
    return idf


def _tfidf_vector(tf: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    """Multiply TF by IDF to get a TF-IDF vector."""
    return {term: tf_val * idf.get(term, 1.0) for term, tf_val in tf.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse TF-IDF vectors."""
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_and_store(chunks: list[Chunk]) -> int:
    """Index *chunks* using TF-IDF and store them in the in-memory store.

    Replaces any previously stored session so each upload starts fresh.

    Args:
        chunks: A list of :class:`~app.models.Chunk` objects produced by the
            Chunker. Must not be empty.

    Returns:
        The number of chunks successfully stored (equal to ``len(chunks)``).

    Raises:
        RuntimeError: If indexing fails.
    """
    global _store, _idf
    try:
        tfs = [_build_tf(_tokenize(chunk.text)) for chunk in chunks]
        _idf = _build_idf(tfs)
        _store = [{"chunk": chunk, "tf": tf} for chunk, tf in zip(chunks, tfs)]
        return len(chunks)
    except Exception as e:
        raise RuntimeError(f"Failed to store embeddings: {e}") from e


def retrieve(question: str, n_results: int = 5) -> list[Chunk]:
    """Return the top *n_results* chunks most relevant to *question*.

    Args:
        question: The natural-language question to search for.
        n_results: Maximum number of chunks to return. Defaults to ``5``.

    Returns:
        A list of :class:`~app.models.Chunk` objects ordered by descending
        relevance.

    Raises:
        LookupError: If no document has been uploaded yet.
    """
    if not _store:
        raise LookupError("No document loaded. Please upload a PDF first.")

    query_tf = _build_tf(_tokenize(question))
    query_vec = _tfidf_vector(query_tf, _idf)

    scored = []
    for entry in _store:
        doc_vec = _tfidf_vector(entry["tf"], _idf)
        score = _cosine_similarity(query_vec, doc_vec)
        scored.append((score, entry["chunk"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:n_results]]
