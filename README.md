# 📄 Ultra Doc-Intelligence

An AI-powered logistics document assistant that allows users to upload documents (PDF, DOCX, TXT), ask natural language questions, and extract structured shipment data — all grounded in document content using Retrieval-Augmented Generation (RAG).

---

## 🏗️ Architecture

```
Streamlit UI (app.py)  ⇄  FastAPI Backend (main.py)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   utils.py            rag_pipeline.py         extractor.py
(Document loading)   (FAISS + embeddings)     (Gemini extraction)
                               │
                    Google Gemini (LLM)
```

---

## 🔄 Workflow

1. Upload document → parsed and chunked
2. Chunks → embedded using HuggingFace model
3. Stored in FAISS vector database
4. User asks question → top-k chunks retrieved
5. Gemini generates answer using only retrieved context
6. Confidence + guardrails applied
7. Structured extraction via `/extract`

---

## 📁 Project Structure

```
ultra-doc-intelligence/
├── backend/
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── extractor.py
│   └── utils.py
├── frontend/
│   └── app.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ Chunking Strategy

| Parameter     | Value |
| ------------- | ----- |
| chunk_size    | 800   |
| chunk_overlap | 150   |

* Uses `RecursiveCharacterTextSplitter`
* Preserves semantic structure
* Improves retrieval accuracy

---

## 🔍 Retrieval Setup

* **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
* **Vector Store:** FAISS
* **Retriever:** Top-3 similarity search
* **Framework:** LangChain RetrievalQA

---

## 🛡️ Guardrails

Two-layer protection:

1. **Confidence check**

   * Low confidence → return `"Not found in document"`

2. **LLM self-check**

   * If model says "not found" → respected

---

## 📊 Confidence Scoring

```
coverage_score = min(1.0, num_docs / 3)
richness_score = min(1.0, avg_length / 500)

confidence = (0.4 * coverage_score) + (0.6 * richness_score)
```

---

## ⚠️ Limitations

* Scanned PDFs (no OCR)
* Small documents → low confidence
* In-memory FAISS (resets on restart)
* Requires API keys

---

## 🚀 Local Setup

### 1. Clone repo

```bash
git clone https://github.com/YOUR_USERNAME/ultra-doc-intelligence.git
cd ultra-doc-intelligence
```

### 2. Create environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

Create `.env`:

```
GOOGLE_API_KEY=your_google_api_key
HF_TOKEN=your_huggingface_token
```

---

### 5. Run Backend

```bash
uvicorn backend.main:app --reload
```

### 6. Run Frontend

```bash
streamlit run frontend/app.py
```

---

## ☁️ Deployment (Google Cloud Run)

### 1. Build Image

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/doc-intelligence
```

### 2. Deploy

```bash
gcloud run deploy doc-intelligence \
  --image gcr.io/YOUR_PROJECT_ID/doc-intelligence \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars HF_TOKEN=your_hf_token,GOOGLE_API_KEY=your_google_api_key
```

---

## 🔌 API Endpoints

| Method | Endpoint   | Description             |
| ------ | ---------- | ----------------------- |
| GET    | `/`        | Health check            |
| POST   | `/upload`  | Upload document         |
| POST   | `/ask`     | Ask question            |
| POST   | `/extract` | Extract structured data |

---

## 📦 Tech Stack

| Component  | Technology    |
| ---------- | ------------- |
| LLM        | Google Gemini |
| Embeddings | HuggingFace   |
| Vector DB  | FAISS         |
| Backend    | FastAPI       |
| Frontend   | Streamlit     |
| Framework  | LangChain     |

---

## 💡 Future Improvements

* Persistent vector store
* OCR support
* Multi-document queries
* Streaming responses
* Authentication layer

---

## 👨‍💻 Author

Built as an end-to-end AI document intelligence system using RAG + LLMs.
