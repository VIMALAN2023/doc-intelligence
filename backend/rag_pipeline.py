import os
os.environ["HF_HOME"] = "/tmp"

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings


def create_vector_store(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.from_documents(chunks, embeddings)


def get_llm(api_key: str):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def build_qa_chain(vector_store, api_key: str):
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},  # bumped from 3 → 4 to capture more context
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a logistics AI assistant. Answer the question using ONLY the context below.

Instructions:
- Read ALL the context carefully before answering.
- Extract every relevant piece of information related to the question, even if it is spread across multiple sections.
- For questions about "customer details", "parties", "shipper", "consignee", or "contacts" — return all names, addresses, phone numbers, emails, and reference numbers found in the context.
- Provide a complete, structured answer. Do not skip any relevant detail.
- Do NOT use any external knowledge beyond the context.
- Only say "Not found in document" if the context truly contains zero information related to the question.

Context:
{context}

Question:
{question}

Answer:""",
    )

    llm = get_llm(api_key)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    return qa_chain


def compute_confidence(source_docs) -> float:
    """
    Confidence based on:
    - Number of chunks retrieved (coverage)
    - Average chunk length (content richness)
    """
    if not source_docs:
        return 0.0

    num_docs = len(source_docs)
    avg_length = sum(len(doc.page_content) for doc in source_docs) / num_docs

    coverage_score = min(1.0, num_docs / 3)
    richness_score = min(1.0, avg_length / 500)

    confidence = (coverage_score * 0.4) + (richness_score * 0.6)
    return round(confidence, 2)
	
	
#rag_pipeline.py