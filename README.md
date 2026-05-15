# 🧠 AI Second Brain

> Upload any PDF and chat with it in plain English — powered by Claude API, ChromaDB, and FastAPI.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![React](https://img.shields.io/badge/React-Vite-purple)
![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-orange)
![Groq](https://img.shields.io/badge/LLM-Groq_LLaMA3-red)

---

## 🚀 What It Does

Most people drown in documents — PDFs, reports, contracts, manuals — and waste hours searching for answers they already have.

**AI Second Brain** solves this. Upload any PDF and ask questions in plain English. The system finds the most relevant content and answers instantly — with source page citations.

**Example:**
> Upload a 20-page workflow document → Ask *"What happens if the lead is not qualified?"* → Get a precise answer with page references in seconds.

---

## ✨ Features

- 📄 **PDF Upload** — drag and drop any PDF up to 20MB
- 💬 **Natural Language Chat** — ask questions like you're talking to a human
- 🔍 **Semantic Search** — finds answers by meaning, not just keywords
- 📎 **Source Attribution** — every answer cites the exact page numbers
- ⚡ **Fast Responses** — powered by Groq's LLaMA 3.3 70B
- 🧩 **Session Management** — conversation history maintained per session

---

## 🏗️ Architecture

```
User uploads PDF
      ↓
FastAPI Backend
      ↓
pdfplumber → extracts text with page tracking
      ↓
tiktoken → chunks text (500 tokens, 50 overlap)
      ↓
sentence-transformers → generates embeddings
      ↓
ChromaDB → stores vectors locally
      ↓
User asks a question
      ↓
ChromaDB → retrieves top 5 relevant chunks
      ↓
Groq API (LLaMA 3.3 70B) → generates answer
      ↓
React UI → displays answer + source pages
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Vector Database | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq API — LLaMA 3.3 70B |
| PDF Processing | pdfplumber |
| Tokenization | tiktoken |

---

## 📦 Installation

### Prerequisites
- Python 3.11
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/NirdoshAI/ai-second-brain.git
cd ai-second-brain/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Start backend
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🎯 How to Use

1. Open the app at `http://localhost:5173`
2. Click **Choose File** → select any PDF
3. Click **Upload** → wait for processing
4. Type your question in the chat box
5. Get instant answers with page citations

---

## 📁 Project Structure

```
ai-second-brain/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + endpoints
│   │   ├── pdf_processor.py # PDF text extraction
│   │   ├── chunker.py       # Text chunking logic
│   │   ├── embedder.py      # ChromaDB + embeddings
│   │   ├── retriever.py     # Semantic search
│   │   ├── ai_client.py     # Groq API integration
│   │   ├── session.py       # Session management
│   │   └── models.py        # Pydantic models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   └── package.json
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload and process a PDF |
| POST | `/query` | Ask a question about the PDF |
| GET | `/health` | Check system health |

---

## 🌱 Roadmap

- [ ] Multiple PDF support
- [ ] Google Drive integration via MCP
- [ ] n8n automation for auto-ingestion
- [ ] Web search agent (ask questions beyond the PDF)
- [ ] Deploy to Railway

---

## 👨‍💻 Built By

**Nirdosh Kapoor** — AI Automation Engineer  
[GitHub](https://github.com/NirdoshAI) · [Upwork](https://upwork.com) · [YouTube — SochKaRaaz](https://youtube.com)

Built as part of **Anthropic Claude Code 101** course project.

---

## 📄 License

MIT License — free to use and modify.
