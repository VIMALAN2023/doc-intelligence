from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import shutil
import os

from utils import load_document, chunk_documents
from rag_pipeline import create_vector_store, build_qa_chain, compute_confidence
from extractor import extract_shipment_data

load_dotenv()

app = FastAPI(title="Ultra Doc-Intelligence API")

VECTOR_STORE = None
QA_CHAIN = None
DOC_TEXT = ""

API_KEY = os.getenv("GOOGLE_API_KEY")


@app.get("/")
def root():
    return {"status": "running", "message": "Ultra Doc-Intelligence API is live"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global VECTOR_STORE, QA_CHAIN, DOC_TEXT

    allowed_types = [".pdf", ".docx", ".txt"]
    ext = os.path.splitext(file.filename)[-1].lower()

    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed_types}",
        )

    file_path = f"temp_{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        docs = load_document(file_path)

        if not docs:
            raise HTTPException(
                status_code=400, detail="Document appears to be empty or unreadable."
            )

        DOC_TEXT = " ".join([d.page_content for d in docs])
        chunks = chunk_documents(docs)
        VECTOR_STORE = create_vector_store(chunks)
        QA_CHAIN = build_qa_chain(VECTOR_STORE, API_KEY)

        return {
            "message": "Document processed successfully",
            "chunks_created": len(chunks),
            "filename": file.filename,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(req: QuestionRequest):
    global QA_CHAIN

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if QA_CHAIN is None:
        return {
            "answer": "Please upload a document first.",
            "confidence": 0.0,
            "sources": [],
        }

    try:
        result = QA_CHAIN.invoke({"query": req.question})

        answer = result.get("result", "").strip()
        source_docs = result.get("source_documents", [])
        sources = [doc.page_content[:300] for doc in source_docs]
        confidence = compute_confidence(source_docs)

        # Guardrail 1: no source chunks retrieved at all
        if not source_docs:
            return {
                "answer": "Not found in document",
                "confidence": 0.0,
                "sources": [],
            }

        # Guardrail 2: LLM explicitly said not found AND confidence is also low
        # Do NOT suppress the answer when confidence is high — trust the LLM + sources
        llm_says_not_found = "not found in document" in answer.lower()
        if llm_says_not_found and confidence < 0.4:
            return {
                "answer": "Not found in document",
                "confidence": confidence,
                "sources": sources,
            }

        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


@app.post("/extract")
async def extract():
    global DOC_TEXT

    if not DOC_TEXT or not DOC_TEXT.strip():
        raise HTTPException(
            status_code=400,
            detail="No document loaded. Please upload a document first.",
        )

    return extract_shipment_data(DOC_TEXT, API_KEY)
	
	
