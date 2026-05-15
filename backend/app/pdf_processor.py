"""
PDF processing module for the AI Second Brain backend.

This module is responsible for extracting readable text from uploaded PDF files
using pdfplumber. It preserves page boundaries so that downstream components
can attach page-level attribution to retrieved chunks.
"""

import io

import pdfplumber

from app.models import PageText


def extract_text(pdf_bytes: bytes, filename: str) -> list[PageText]:
    """Extract text from a PDF supplied as raw bytes.

    Opens the PDF from an in-memory byte stream using pdfplumber, iterates
    over every page, and collects the stripped text for each non-blank page.
    Page numbers are 1-indexed to match human-readable references.

    Args:
        pdf_bytes: The raw binary content of the PDF file.
        filename:  The original filename, used only for contextual error
                   messages (not stored in the returned objects).

    Returns:
        A list of :class:`~app.models.PageText` instances, one per page that
        contains extractable text.  Blank pages are silently skipped.

    Raises:
        ValueError: If the PDF contains no extractable text at all (e.g. a
                    scanned image-only document), with the message
                    ``"No extractable text found in the uploaded PDF."``.
    """
    pages: list[PageText] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            raw_text = page.extract_text() or ""
            stripped = raw_text.strip()

            # Skip blank pages without raising an error
            if not stripped:
                continue

            pages.append(PageText(page_number=page_index + 1, text=stripped))

    # If every page was blank (image-only PDF), raise a descriptive error
    if not pages:
        raise ValueError("No extractable text found in the uploaded PDF.")

    return pages
