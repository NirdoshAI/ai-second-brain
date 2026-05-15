# Requirements Document

## Introduction

The AI Second Brain is a single-page web application that allows a user to upload a PDF document and then ask natural language questions about its contents. The system processes the PDF, stores its content in a vector database (ChromaDB), and uses Claude (claude-sonnet-4-20250514) to generate answers grounded in the uploaded document. The goal is a minimal, focused tool: one PDF at a time, one chat interface.

The stack is:
- **Frontend**: React + Vite
- **Backend**: Python + FastAPI
- **Vector DB**: ChromaDB
- **AI**: Claude API (claude-sonnet-4-20250514)

---

## Glossary

- **System**: The AI Second Brain application as a whole.
- **Frontend**: The React + Vite single-page application served to the user's browser.
- **Backend**: The Python + FastAPI server that handles PDF processing, vector storage, and AI queries.
- **PDF_Processor**: The backend component responsible for extracting text from uploaded PDF files.
- **Chunker**: The backend component responsible for splitting extracted text into overlapping chunks suitable for embedding.
- **Embedder**: The backend component responsible for generating vector embeddings from text chunks.
- **Vector_Store**: The ChromaDB instance that stores and retrieves embedded text chunks.
- **Retriever**: The backend component that queries the Vector_Store to find chunks relevant to a user question.
- **AI_Client**: The backend component that communicates with the Claude API.
- **Chat_Interface**: The frontend component where the user types questions and reads answers.
- **Upload_Interface**: The frontend component where the user selects and uploads a PDF file.
- **Session**: A single active PDF context — one uploaded PDF and its associated embeddings.
- **Chunk**: A fixed-size, optionally overlapping segment of extracted PDF text used for embedding and retrieval.
- **Context_Window**: The set of retrieved chunks passed to the Claude API as grounding context for a question.

---

## Requirements

### Requirement 1: PDF Upload

**User Story:** As a user, I want to upload a PDF file from the browser, so that the system can process its contents and make them available for question answering.

#### Acceptance Criteria

1. THE Upload_Interface SHALL accept PDF files via a file picker input restricted to `.pdf` MIME type.
2. WHEN the user selects a PDF file, THE Upload_Interface SHALL display the selected file name before submission.
3. WHEN the user submits the PDF, THE Frontend SHALL send the file to the Backend via a multipart/form-data HTTP POST request.
4. WHILE the PDF is being uploaded and processed, THE Upload_Interface SHALL display a loading indicator and disable the upload controls.
5. WHEN the Backend receives the PDF, THE Backend SHALL validate that the file is a non-empty PDF with a maximum size of 20 MB.
6. IF the uploaded file exceeds 20 MB or is not a valid PDF, THEN THE Backend SHALL return an HTTP 422 response with a descriptive error message.
7. IF the uploaded file exceeds 20 MB or is not a valid PDF, THEN THE Upload_Interface SHALL display the error message returned by the Backend.
8. WHEN the PDF upload and processing completes successfully, THE Upload_Interface SHALL display a success confirmation including the file name.
9. WHEN a new PDF is uploaded successfully, THE System SHALL replace any previously active Session with the new one.

---

### Requirement 2: PDF Text Extraction

**User Story:** As a user, I want the system to extract text from my uploaded PDF, so that its content can be indexed and searched.

#### Acceptance Criteria

1. WHEN a valid PDF is received, THE PDF_Processor SHALL extract all readable text from every page of the document.
2. WHEN text extraction completes, THE PDF_Processor SHALL pass the full extracted text to the Chunker.
3. IF a PDF contains no extractable text (e.g., a scanned image-only PDF), THEN THE Backend SHALL return an HTTP 422 response with the message "No extractable text found in the uploaded PDF."
4. THE PDF_Processor SHALL preserve page boundaries in the extracted text to enable page-level attribution in responses.

---

### Requirement 3: Text Chunking and Embedding

**User Story:** As a developer, I want the extracted text to be split into chunks and embedded, so that semantically relevant passages can be retrieved efficiently.

#### Acceptance Criteria

1. THE Chunker SHALL split extracted text into chunks of at most 500 tokens with an overlap of 50 tokens between consecutive chunks.
2. THE Chunker SHALL attach metadata to each chunk containing at minimum: the source file name and the page number(s) the chunk originates from.
3. WHEN chunking is complete, THE Embedder SHALL generate a vector embedding for each chunk.
4. WHEN all embeddings are generated, THE Embedder SHALL store each chunk and its embedding in the Vector_Store under a collection scoped to the current Session.
5. WHEN a new Session begins, THE Vector_Store SHALL delete the collection from the previous Session before creating the new one.
6. IF embedding generation fails for any chunk, THEN THE Backend SHALL return an HTTP 500 response with a descriptive error message and abort the upload.

---

### Requirement 4: Question Input

**User Story:** As a user, I want to type a question about the uploaded PDF in a chat interface, so that I can get answers grounded in the document.

#### Acceptance Criteria

1. THE Chat_Interface SHALL provide a text input field and a submit button for entering questions.
2. WHILE no PDF has been successfully uploaded in the current Session, THE Chat_Interface SHALL disable the question input and display the message "Upload a PDF to start chatting."
3. WHEN the user submits a question, THE Frontend SHALL send the question text to the Backend via an HTTP POST request.
4. WHILE a question is being processed, THE Chat_Interface SHALL display a loading indicator and disable the question input and submit button.
5. THE Chat_Interface SHALL display the user's question in the conversation history immediately upon submission.
6. IF the user submits an empty question, THEN THE Frontend SHALL not send the request and SHALL display an inline validation message.

---

### Requirement 5: Relevant Chunk Retrieval

**User Story:** As a developer, I want the system to retrieve the most relevant chunks from ChromaDB for a given question, so that Claude receives focused, accurate context.

#### Acceptance Criteria

1. WHEN a question is received, THE Retriever SHALL query the Vector_Store using the question's embedding to retrieve the top 5 most semantically similar chunks.
2. THE Retriever SHALL use the same embedding model for query embedding as was used during the chunking phase to ensure vector space consistency.
3. WHEN retrieval is complete, THE Retriever SHALL pass the retrieved chunks and the original question to the AI_Client.
4. IF the Vector_Store contains no active Session collection, THEN THE Backend SHALL return an HTTP 400 response with the message "No document loaded. Please upload a PDF first."

---

### Requirement 6: AI Answer Generation

**User Story:** As a user, I want Claude to answer my question based on the content of the uploaded PDF, so that I receive accurate, document-grounded responses.

#### Acceptance Criteria

1. WHEN the AI_Client receives retrieved chunks and a question, THE AI_Client SHALL construct a prompt that includes the retrieved chunks as context and instructs Claude to answer using only the provided context.
2. THE AI_Client SHALL call the Claude API using the model `claude-sonnet-4-20250514`.
3. WHEN the Claude API returns a response, THE AI_Client SHALL extract the answer text and return it to the Backend response handler.
4. IF the retrieved context does not contain information sufficient to answer the question, THE AI_Client SHALL instruct Claude to respond with "I could not find an answer to that question in the uploaded document."
5. IF the Claude API returns an error, THEN THE Backend SHALL return an HTTP 502 response with the message "AI service unavailable. Please try again."
6. THE AI_Client SHALL include the source chunk metadata (file name, page numbers) in the response so the Frontend can display attribution.

---

### Requirement 7: Answer Display

**User Story:** As a user, I want to see Claude's answer displayed in the chat interface with source attribution, so that I can read the response and know where it came from.

#### Acceptance Criteria

1. WHEN the Backend returns a successful answer, THE Chat_Interface SHALL append the answer to the conversation history below the corresponding user question.
2. THE Chat_Interface SHALL display the source attribution (file name and page number(s)) beneath each AI answer.
3. WHEN an error response is received from the Backend, THE Chat_Interface SHALL display the error message in the conversation history in place of an answer.
4. THE Chat_Interface SHALL maintain the full conversation history for the current Session and display all prior question-answer pairs above the current input.
5. THE Chat_Interface SHALL render answer text with basic markdown formatting support (bold, italic, bullet lists, numbered lists).

---

### Requirement 8: Session State Management

**User Story:** As a user, I want the application to clearly reflect which PDF is currently loaded and the state of my session, so that I always know what context the AI is working from.

#### Acceptance Criteria

1. THE Frontend SHALL display the name of the currently loaded PDF at all times when a Session is active.
2. WHEN no Session is active, THE Frontend SHALL display a prompt instructing the user to upload a PDF.
3. WHEN a new PDF is uploaded successfully, THE Frontend SHALL clear the conversation history from the previous Session.
4. THE System SHALL maintain Session state on the Backend so that the Frontend can be refreshed without losing the active PDF context within the same server process lifetime.

---

### Requirement 9: API Health and Readiness

**User Story:** As a developer, I want the Backend to expose a health check endpoint, so that I can verify the service is running and its dependencies are reachable.

#### Acceptance Criteria

1. THE Backend SHALL expose a `GET /health` endpoint that returns HTTP 200 with a JSON body `{"status": "ok"}` when the service is operational.
2. WHEN the Vector_Store is unreachable, THE Backend SHALL return HTTP 503 from the `/health` endpoint with a JSON body indicating the degraded dependency.
