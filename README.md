# 📄 Ultra Doc-Intelligence

An AI-powered logistics document assistant that lets you upload documents (PDF, DOCX, TXT), ask natural language questions, and extract structured shipment data — all grounded in the document content via RAG.

---

## 🏗️ Architecture

```
┌─────────────────┐        HTTP Requests        ┌──────────────────────────┐
│   Streamlit UI  │ ◄─────────────────────────► │   FastAPI Backend        │
│   (app.py)      │                             │   (main.py)              │
└─────────────────┘                             └────────────┬─────────────┘
                                                             │
                        ┌────────────────────────────────────┼──────────────────────┐
                        │                                    │                      │
               ┌────────▼────────┐                ┌─────────▼──────────┐  ┌────────▼────────┐
               │  utils.py       │                │  rag_pipeline.py   │  │  extractor.py   │
               │  Doc Loading    │                │  FAISS + HuggingFace│  │  Gemini LLM     │
               │  Chunking       │                │  Embeddings + RAG  │  │  JSON Extraction│
               └─────────────────┘                └────────────────────┘  └─────────────────┘
                                                             │
                                                  ┌──────────▼──────────┐
                                                  │  Google Gemini LLM  │
                                                  │  (gemini-2.5-flash) │
                                                  └─────────────────────┘
```

**Flow:**
1. User uploads a document → parsed, chunked, embedded, stored in FAISS vector index
2. User asks a question → top-3 chunks retrieved → Gemini answers from context only
3. Guardrails check confidence + LLM response → return answer or "Not found in document"
4. Extract button → Gemini extracts structured shipment fields as JSON

---

## 📁 Project Structure

```
ultra-doc-intelligence/
├── main.py            # FastAPI backend (API endpoints)
├── app.py             # Streamlit frontend (UI)
├── rag_pipeline.py    # Vector store, retriever, QA chain, confidence scoring
├── extractor.py       # Structured shipment data extraction via LLM
├── utils.py           # Document loading and chunking
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── README.md
```

---

## ⚙️ Chunking Strategy

Implemented in `utils.py` using `RecursiveCharacterTextSplitter`:

| Parameter | Value | Reason |
|---|---|---|
| `chunk_size` | 800 tokens | Balances context richness vs retrieval precision |
| `chunk_overlap` | 150 tokens | Preserves cross-boundary context for better RAG recall |

The splitter splits on `\n\n`, `\n`, spaces — prioritizing natural paragraph breaks before hard splits. This keeps logically related sentences together (e.g., rate + carrier info on the same chunk).

---

## 🔍 Retrieval Method

- **Embeddings:** `all-MiniLM-L6-v2` via HuggingFace (local, no API key needed)
- **Vector Store:** FAISS (in-memory, fast similarity search)
- **Retriever:** Top-3 most similar chunks (`search_type="similarity"`, `k=3`)
- **QA Chain:** LangChain `RetrievalQA` with a strict prompt that instructs the LLM to answer only from retrieved context

---

## 🛡️ Guardrails Approach

Two-layer guardrail system:

**Layer 1 — Confidence threshold:**
- If fewer than expected chunks are retrieved OR confidence score < 0.1 → return `"Not found in document"`

**Layer 2 — LLM response check:**
- If the LLM itself responds with `"Not found in document"` (as instructed in the prompt) → pass that through directly

Both layers prevent hallucination by ensuring answers are only returned when grounded retrieval succeeds.

---

## 📊 Confidence Scoring Method

Heuristic scoring based on two signals from retrieved chunks:

```python
coverage_score = min(1.0, num_docs / 3)       # How many chunks retrieved (max at 3)
richness_score = min(1.0, avg_length / 500)    # How content-rich the chunks are

confidence = (coverage_score * 0.4) + (richness_score * 0.6)
```

- **Coverage (40%):** More retrieved chunks = higher confidence the answer exists
- **Richness (60%):** Longer, denser chunks = more context available to answer from
- Score range: `0.0` to `1.0`, displayed as a percentage in the UI

---

## ⚠️ Known Failure Cases

| Case | Behavior |
|---|---|
| Scanned/image-based PDFs | Text extraction fails — no content parsed |
| Very short documents (<3 chunks) | Low confidence score even if answer exists |
| Ambiguous questions | LLM may pick closest match rather than saying "not found" |
| Rate Confirmation with no shipper field | Extracted as `null` in structured output |
| Server restart | In-memory vector store is lost — document must be re-uploaded |

---

## 💡 Improvement Ideas

- **Persistent vector store** — Save FAISS index to disk so it survives restarts
- **Multi-document support** — Allow uploading and querying across multiple documents
- **Better confidence scoring** — Use actual FAISS similarity scores (L2 distance) instead of heuristics
- **OCR support** — Add Tesseract/PyMuPDF for scanned PDFs
- **Streaming answers** — Stream LLM responses token-by-token for better UX
- **Authentication** — Add API key auth to backend endpoints for production use

---

## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ultra-doc-intelligence.git
cd ultra-doc-intelligence
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your Google API key
```

`.env` file:
```
GOOGLE_API_KEY=your_google_api_key_here
```

Get your free Google API key at: https://aistudio.google.com/app/apikey

### 5. Start the FastAPI backend

```bash
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### 6. Start the Streamlit frontend (new terminal)

```bash
streamlit run app.py
```

UI runs at: http://localhost:8501

---

## 🌐 Hosted UI

**Streamlit Cloud (Free Hosting):**

1. Push your code to GitHub
2. Go to https://share.streamlit.io
3. Click **"New app"** → connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Add your `GOOGLE_API_KEY` under **Advanced settings → Secrets**:
   ```toml
   GOOGLE_API_KEY = "your_key_here"
   ```
6. Click **Deploy**

> ⚠️ **Important:** Streamlit Cloud runs only the frontend (`app.py`). The FastAPI backend (`main.py`) must be hosted separately (see below) and you must update `BACKEND_URL` in `app.py` to point to it.

**Backend Hosting Options (Free):**
- **Render.com** — Free tier, deploy as a Web Service, set `GOOGLE_API_KEY` in environment variables, start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
- **Railway.app** — Free tier, similar setup

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload a PDF, DOCX, or TXT document |
| `POST` | `/ask` | Ask a question about the uploaded document |
| `POST` | `/extract` | Extract structured shipment data as JSON |

### POST `/upload`
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@your_document.pdf"
```

### POST `/ask`
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the carrier rate?"}'
```

### POST `/extract`
```bash
curl -X POST http://localhost:8000/extract
```

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector Store | FAISS (in-memory) |
| RAG Framework | LangChain |
| Backend API | FastAPI |
| Frontend UI | Streamlit |
| PDF Parsing | PyPDFLoader |
| DOCX Parsing | Docx2txt |