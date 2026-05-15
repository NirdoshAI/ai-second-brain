"""
Chunker module for the AI Second Brain backend.

This module is responsible for splitting extracted PDF page text into
fixed-size, overlapping token-based chunks suitable for embedding and
retrieval. It uses the ``cl100k_base`` tiktoken encoding (the same
encoding used by OpenAI's text-embedding models) so that chunk sizes
are measured in tokens rather than characters.

Typical usage::

    from app.chunker import chunk_pages
    from app.models import PageText

    pages = [PageText(page_number=1, text="..."), ...]
    chunks = chunk_pages(pages, source_file="report.pdf")
"""

import uuid

import tiktoken

from app.models import Chunk, PageText


def chunk_pages(
    pages: list[PageText],
    source_file: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split a list of PDF pages into overlapping token-based chunks.

    The function concatenates all page texts into a single token stream
    while building a ``token_page_map`` that records which page number
    each token position belongs to.  A sliding window of ``chunk_size``
    tokens is then advanced by ``chunk_size - overlap`` tokens per step,
    producing chunks that share ``overlap`` tokens with their neighbours.

    Each :class:`~app.models.Chunk` is assigned a fresh UUID and carries
    the ``source_file`` name together with the sorted, deduplicated list
    of page numbers covered by its token range.

    Args:
        pages: Ordered list of :class:`~app.models.PageText` objects
            produced by the PDF processor.  Page numbers are expected to
            be 1-indexed.
        source_file: The original PDF filename to attach as metadata on
            every chunk.
        chunk_size: Maximum number of tokens per chunk.  Defaults to
            ``500`` as required by Requirement 3.1.
        overlap: Number of tokens shared between consecutive chunks.
            Defaults to ``50`` as required by Requirement 3.1.

    Returns:
        A list of :class:`~app.models.Chunk` objects.  Returns an empty
        list when ``pages`` is empty or all pages contain only whitespace.

    Raises:
        ValueError: If ``overlap`` is greater than or equal to
            ``chunk_size``, which would cause an infinite loop.
    """
    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
        )

    enc = tiktoken.get_encoding("cl100k_base")

    # ------------------------------------------------------------------
    # Phase 1: Concatenate all page tokens and build token-to-page map.
    # ------------------------------------------------------------------
    all_tokens: list[int] = []
    token_page_map: list[int] = []  # index = token position, value = page number

    for page in pages:
        page_tokens = enc.encode(page.text)
        all_tokens.extend(page_tokens)
        token_page_map.extend([page.page_number] * len(page_tokens))

    if not all_tokens:
        return []

    # ------------------------------------------------------------------
    # Phase 2: Slide a window over the token stream.
    # ------------------------------------------------------------------
    step = chunk_size - overlap
    chunks: list[Chunk] = []

    start = 0
    while start < len(all_tokens):
        end = min(start + chunk_size, len(all_tokens))

        token_slice = all_tokens[start:end]

        # Decode the token slice back to text.
        chunk_text = enc.decode(token_slice)

        # Determine which pages this chunk spans.
        page_numbers = sorted(set(token_page_map[start:end]))

        chunk = Chunk(
            id=str(uuid.uuid4()),
            text=chunk_text,
            source_file=source_file,
            page_numbers=page_numbers,
        )
        chunks.append(chunk)

        # Advance the window; stop if we have already consumed all tokens.
        if end == len(all_tokens):
            break
        start += step

    return chunks
