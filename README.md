# AI Second Brain

A full-stack application that lets you upload a PDF document and ask natural-language questions about its contents. The backend extracts, chunks, and embeds the document text into a local vector store, then uses Claude to generate grounded answers with source attribution.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # then open .env and add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## Usage

1. Open `http://localhost:5173` in your browser.
2. Use the **Upload** panel on the left to select and upload a PDF file (up to 20 MB).
3. Once the upload succeeds, type a question in the chat panel on the right and press **Send**.
4. The assistant will answer using only the content of the uploaded document and show which pages the answer came from.

---

## Project Structure

```
backend/
  app/
    main.py          # FastAPI application and endpoints
    models.py        # Pydantic request/response models
    pdf_processor.py # PDF text extraction (PyMuPDF)
    chunker.py       # Token-aware text chunking
    embedder.py      # Sentence-transformer embeddings + ChromaDB storage
    retriever.py     # Semantic similarity retrieval
    ai_client.py     # Anthropic Claude API client
    session.py       # In-memory session state
  requirements.txt
  .env.example

frontend/
  src/
    App.jsx                    # Root component
    api/client.js              # Axios API client
    hooks/useSession.js        # Upload and session state
    hooks/useChat.js           # Chat message state
    components/
      UploadPanel.jsx          # PDF upload UI
      ChatPanel.jsx            # Chat interface
      MessageBubble.jsx        # Individual message rendering
      SourceBadge.jsx          # Source attribution badge
      LoadingSpinner.jsx       # Loading indicator
```
