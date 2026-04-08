from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def load_document(file_path: str):
    ext = os.path.splitext(file_path)[-1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".txt":
        # Try common encodings to avoid crash on non-UTF-8 files
        for enc in ("utf-8", "utf-8-sig", "latin-1", "windows-1252"):
            try:
                loader = TextLoader(file_path, encoding=enc)
                return loader.load()
            except (UnicodeDecodeError, RuntimeError):
                continue
        raise ValueError(
            f"Could not decode '{file_path}' with any supported encoding "
            "(utf-8, latin-1, windows-1252)."
        )
    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Allowed: .pdf, .docx, .txt"
        )

    return loader.load()


def chunk_documents(docs):
    """
    Chunking strategy:
    - chunk_size=800 : balances context richness vs retrieval precision
    - chunk_overlap=150: preserves cross-boundary context for better RAG recall
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    return splitter.split_documents(docs)