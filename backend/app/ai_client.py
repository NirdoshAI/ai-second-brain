"""
AI client module for the AI Second Brain backend.

This module provides the interface to the Groq API (llama3 model). It constructs
prompts from retrieved document chunks, calls the Groq API, and returns a
structured answer with source attribution metadata.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from groq import Groq, APIError

from app.models import Chunk, SourceAttribution

# ---------------------------------------------------------------------------
# Module-level Groq client (reused across requests)
# ---------------------------------------------------------------------------

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions strictly based on the "
    "provided context passages from an uploaded document. "
    "Do not use any knowledge outside of the passages given to you. "
    "If the provided context does not contain enough information to answer the "
    "question, respond with exactly: "
    '"I could not find an answer to that question in the uploaded document." '
    "Do not speculate, infer beyond the text, or apologise — just use that "
    "exact phrase when the context is insufficient."
)


def generate_answer(
    question: str, chunks: list[Chunk]
) -> tuple[str, list[SourceAttribution]]:
    """Generate an answer to *question* grounded in the provided *chunks*.

    Constructs a numbered-passage user message from the retrieved chunks,
    calls the Groq API (llama3), and returns the answer text together with
    deduplicated source attribution objects.

    Args:
        question: The natural-language question submitted by the user.
        chunks:   The top-k document chunks retrieved from the vector store.

    Returns:
        A tuple of ``(answer_text, sources)`` where *answer_text* is the
        string returned by the model and *sources* is a deduplicated list of
        :class:`~app.models.SourceAttribution` objects derived from the
        chunk metadata.

    Raises:
        RuntimeError: If the Groq API returns an error response.
    """
    # ------------------------------------------------------------------
    # Build the user message: numbered passages followed by the question
    # ------------------------------------------------------------------
    passage_lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        pages_str = ", ".join(str(p) for p in chunk.page_numbers)
        header = f"[Passage {idx}] (source: {chunk.source_file}, pages: {pages_str})"
        passage_lines.append(f"{header}\n{chunk.text}")

    passages_block = "\n\n".join(passage_lines)
    user_message = f"{passages_block}\n\nQuestion: {question}"

    # ------------------------------------------------------------------
    # Call the Groq API
    # ------------------------------------------------------------------
    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
    except APIError:
        raise RuntimeError("AI service unavailable. Please try again.")

    answer_text: str = response.choices[0].message.content

    # ------------------------------------------------------------------
    # Build deduplicated SourceAttribution list
    # ------------------------------------------------------------------
    # Key: (source_file, tuple(sorted page_numbers)) — ensures that two
    # chunks from the same file and same pages collapse into one attribution.
    seen: dict[tuple[str, tuple[int, ...]], SourceAttribution] = {}
    for chunk in chunks:
        key = (chunk.source_file, tuple(chunk.page_numbers))
        if key not in seen:
            seen[key] = SourceAttribution(
                source_file=chunk.source_file,
                page_numbers=chunk.page_numbers,
            )

    sources = list(seen.values())

    return answer_text, sources
