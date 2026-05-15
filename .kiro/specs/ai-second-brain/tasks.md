# Implementation Plan: AI Second Brain

## Overview

Implement a two-tier RAG web application: a Python + FastAPI backend that handles PDF ingestion, chunking, embedding, retrieval, and Claude-powered answer generation, paired with a React + Vite frontend for upload and chat. Tasks are ordered so each step builds on the previous, ending with full integration.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `backend/` directory with `pyproject.toml` (or `requirements.txt`) listing: `fastapi`, `uvicorn`, `pymupdf`, `tiktoken`, `chromadb`, `sentence-transformers`, `anthropic`, `python-multipart`, `pydantic`
  - Create `frontend/` directory and scaffold a Vite + React project (`npm create vite@latest frontend -- --template react`)
  - Add `react-markdown` to frontend dependencies
  - Create `backend/app/__init__.py` and stub `main.py` with a bare FastAPI app instance
  - Create `backend/.env.example` with `ANTHROPIC_API_KEY=` placeholder
  - _Requirements: 1.3, 6.2, 9.1_

- [x] 2. Implement backend data models and session state
  - [x] 2.1 Define all Pydantic API models and internal dataclasses
    - Create `backend/app/models.py` with `PageText`, `Chunk`, `QueryRequest`, `QueryResponse`, `UploadResponse`, `HealthResponse`, `SourceAttribution`, `SessionState`
    - _Requirements: 2.1, 3.2, 5.1, 6.6, 7.2_
  - [x] 2.2 Implement module-level session singleton
    - Create `backend/app/session.py` with a `SessionState` instance and helper functions `get_session()`, `set_session()`, `clear_session()`
    - _Requirements: 8.4, 3.5_

- [x] 3. Implement PDF_Processor
  - [x] 3.1 Implement `extract_text` function
    - Create `backend/app/pdf_processor.py`
    - Use `fitz.open(stream=pdf_bytes, filetype="pdf")` to open from memory
    - Call `page.get_text("text")` per page; strip whitespace; skip blank pages without failing
    - Return `list[PageText]` (1-indexed page numbers)
    - Raise `ValueError("No extractable text found in the uploaded PDF.")` if total text is empty
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 3.2 Write unit tests for `extract_text`
    - Test with a valid multi-page PDF fixture
    - Test that `ValueError` is raised for an image-only (no-text) PDF
    - Test that page numbers are 1-indexed and preserved correctly
    - _Requirements: 2.1, 2.3, 2.4_

- [x] 4. Implement Chunker
  - [x] 4.1 Implement `chunk_pages` function
    - Create `backend/app/chunker.py`
    - Use `tiktoken` with `cl100k_base` encoding to tokenize concatenated page text
    - Build a token-to-page mapping during concatenation to track page spans per chunk
    - Slide a window of `chunk_size=500` tokens advancing by `chunk_size - overlap` (450) tokens per step
    - Assign a UUID to each `Chunk`; attach `source_file` and `page_numbers` metadata
    - _Requirements: 3.1, 3.2_
  - [ ]* 4.2 Write unit tests for `chunk_pages`
    - Test that no chunk exceeds 500 tokens
    - Test that consecutive chunks share exactly 50 tokens of overlap
    - Test that `page_numbers` metadata correctly reflects which pages a chunk spans
    - Test with a single-page document and a multi-page document
    - _Requirements: 3.1, 3.2_

- [x] 5. Implement Embedder
  - [x] 5.1 Implement `embed_and_store` function
    - Create `backend/app/embedder.py`
    - Use `SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")` from `chromadb.utils.embedding_functions`
    - Delete the existing `active_session` collection if present, then create a fresh one with the embedding function
    - Call `collection.add(ids=..., documents=..., metadatas=...)` — ChromaDB computes embeddings automatically
    - Store `page_numbers` metadata as a JSON string (ChromaDB requires scalar metadata values)
    - Wrap in try/except; re-raise failures as `RuntimeError` for HTTP 500 propagation
    - _Requirements: 3.3, 3.4, 3.5, 3.6_
  - [ ]* 5.2 Write unit tests for `embed_and_store`
    - Test that a fresh collection is created and old one deleted on each call
    - Test that all chunks are stored with correct metadata
    - Test that a `RuntimeError` is raised on ChromaDB failure (mock the client)
    - _Requirements: 3.4, 3.5, 3.6_

- [x] 6. Implement Retriever
  - [x] 6.1 Implement `retrieve` function
    - Create `backend/app/retriever.py`
    - Use `collection.query(query_texts=[question], n_results=5)` — ChromaDB uses the collection's embedding function for query embedding automatically
    - Reconstruct `Chunk` objects from returned `documents`, `ids`, and `metadatas` (parse `page_numbers` from JSON string)
    - Raise `LookupError` if the `active_session` collection does not exist
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [ ]* 6.2 Write unit tests for `retrieve`
    - Test that top-5 chunks are returned for a valid query
    - Test that `LookupError` is raised when no active session collection exists
    - Test that `page_numbers` metadata is correctly deserialized from JSON string
    - _Requirements: 5.1, 5.2, 5.4_

- [x] 7. Implement AI_Client
  - [x] 7.1 Implement `generate_answer` function
    - Create `backend/app/ai_client.py`
    - Build the system prompt instructing Claude to answer only from provided context, with the exact fallback phrase from Requirement 6.4
    - Format retrieved chunks as numbered passages with source attribution in the user message
    - Call `client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1024, system=..., messages=[...])`
    - Deduplicate sources by `(source_file, page_numbers)` before building `AnswerResponse`
    - Catch `anthropic.APIError` and re-raise as `RuntimeError("AI service unavailable.")`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - [ ]* 7.2 Write unit tests for `generate_answer`
    - Test that the prompt includes all retrieved chunk texts
    - Test that sources are deduplicated correctly
    - Test that `RuntimeError` is raised when `anthropic.APIError` occurs (mock the client)
    - _Requirements: 6.1, 6.4, 6.5, 6.6_

- [x] 8. Implement FastAPI endpoints and wire backend together
  - [x] 8.1 Implement `POST /upload` endpoint in `main.py`
    - Accept `multipart/form-data` with a `file` field
    - Validate: content-type or filename ends with `.pdf`, size ≤ 20 MB — return HTTP 422 with descriptive message on failure
    - Call `extract_text` → `chunk_pages` → `embed_and_store` in sequence
    - Update session state on success; return `UploadResponse`
    - Map `ValueError` → HTTP 422, `RuntimeError` → HTTP 500
    - _Requirements: 1.3, 1.5, 1.6, 1.8, 1.9, 2.3, 3.6_
  - [x] 8.2 Implement `POST /query` endpoint in `main.py`
    - Accept `application/json` with `QueryRequest`
    - Return HTTP 400 if no active session; call `retrieve` then `generate_answer`
    - Map `LookupError` → HTTP 400, `RuntimeError` → HTTP 502
    - Return `QueryResponse` with answer and sources
    - _Requirements: 4.3, 5.4, 6.5_
  - [x] 8.3 Implement `GET /health` endpoint in `main.py`
    - Return `{"status": "ok"}` with HTTP 200 when ChromaDB is reachable
    - Return `{"status": "degraded", "detail": "ChromaDB unreachable"}` with HTTP 503 when it is not
    - _Requirements: 9.1, 9.2_
  - [x] 8.4 Add CORS middleware to FastAPI app
    - Allow requests from the Vite dev server origin (`http://localhost:5173`) and any configured production origin
    - _Requirements: 1.3, 4.3_
  - [ ]* 8.5 Write integration tests for all three endpoints
    - Test `/upload` happy path, 422 on oversized file, 422 on non-PDF, 422 on image-only PDF
    - Test `/query` happy path, 400 when no session, 502 on Claude API error (mock `generate_answer`)
    - Test `/health` returns 200 normally and 503 when ChromaDB is mocked as unreachable
    - _Requirements: 1.5, 1.6, 2.3, 5.4, 6.5, 9.1, 9.2_

- [x] 9. Checkpoint — Ensure all backend tests pass
  - Run `pytest` in `backend/`; fix any failures before proceeding to frontend work.

- [x] 10. Implement frontend API client and session hook
  - [x] 10.1 Create `src/api/client.js` with fetch wrappers
    - Implement `uploadPDF(file)` — POST to `/upload` with `FormData`; return parsed JSON or throw with error detail
    - Implement `queryDocument(question)` — POST to `/query` with JSON body; return parsed JSON or throw with error detail
    - Implement `checkHealth()` — GET `/health`; return parsed JSON
    - _Requirements: 1.3, 4.3_
  - [x] 10.2 Implement `useSession` hook in `src/hooks/useSession.js`
    - Manage `filename`, `uploadStatus` (`'idle' | 'uploading' | 'success' | 'error'`), and `uploadError` state
    - Expose `uploadFile(file)` action that calls `uploadPDF`, updates state, and returns the response
    - _Requirements: 1.4, 1.7, 1.8, 8.1, 8.2_
  - [x] 10.3 Implement `useChat` hook in `src/hooks/useChat.js`
    - Manage `messages` array and `isLoading` state
    - Expose `sendQuestion(question)` action that appends the user message immediately, calls `queryDocument`, then appends the assistant message (or an error message)
    - Expose `clearMessages()` to reset conversation history on new upload
    - _Requirements: 4.4, 4.5, 7.1, 7.3, 7.4, 8.3_

- [x] 11. Implement frontend UI components
  - [x] 11.1 Implement `LoadingSpinner.jsx`
    - Simple accessible spinner component used by both upload and chat panels
    - _Requirements: 1.4, 4.4_
  - [x] 11.2 Implement `SourceBadge.jsx`
    - Display `"filename.pdf · p. 3–4"` format for a single `SourceAttribution` object
    - Handle single page vs. page range display
    - _Requirements: 7.2_
  - [x] 11.3 Implement `MessageBubble.jsx`
    - Render user messages and assistant messages with distinct visual styles
    - For assistant messages, render `content` through `react-markdown` for bold, italic, and list support
    - Render a `SourceBadge` for each source attribution beneath assistant messages
    - For error messages (`isError: true`), render with an error style
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  - [x] 11.4 Implement `UploadPanel.jsx`
    - File picker input restricted to `.pdf` MIME type; display selected file name before submission
    - Upload button that calls `uploadFile` from `useSession`; show `LoadingSpinner` and disable controls while uploading
    - Display success confirmation with file name on success
    - Display error message from backend on failure
    - On successful upload, call `clearMessages()` from `useChat` to reset conversation history
    - _Requirements: 1.1, 1.2, 1.4, 1.7, 1.8, 8.3_
  - [x] 11.5 Implement `ChatPanel.jsx`
    - Scrollable conversation history rendering a `MessageBubble` per message
    - Text input and submit button; disable both and show `LoadingSpinner` while `isLoading` is true
    - Display "Upload a PDF to start chatting." and disable input when no session is active
    - Prevent submission of empty questions with an inline validation message
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 7.4_

- [x] 12. Implement `App.jsx` and wire frontend together
  - Set up `SessionContext` and `ChatContext` providers wrapping the full app
  - Render `UploadPanel` and `ChatPanel` side by side (or stacked on narrow viewports)
  - Display the currently loaded PDF filename prominently when a session is active; show upload prompt when no session is active
  - _Requirements: 8.1, 8.2_

- [x] 13. Final checkpoint — Ensure all tests pass and the app runs end-to-end
  - Run `pytest` in `backend/` to confirm all backend tests pass
  - Start the FastAPI server (`uvicorn app.main:app --reload`) and the Vite dev server (`npm run dev`) manually to verify the full upload → chat flow
  - Ensure all tests pass; ask the user if questions arise.

## Notes

- Sub-tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation before moving to the next layer
- The design has no Correctness Properties section, so property-based tests are not applicable; unit and integration tests are used instead
- The `ANTHROPIC_API_KEY` environment variable must be set before running the backend
