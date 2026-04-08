import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 120  # seconds — LLM calls can be slow

st.set_page_config(page_title="Ultra Doc-Intelligence", page_icon="📄")
st.title("📄 Ultra Doc-Intelligence")
st.caption("Upload a logistics document and ask questions or extract structured data.")

# Session state init
if "uploaded" not in st.session_state:
    st.session_state.uploaded = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── Upload Section ──────────────────────────────────────────────
st.header("1. Upload Document")

if st.session_state.uploaded:
    st.success("✅ A document is currently loaded.")
    if st.button("🔄 Upload a New Document"):
        st.session_state.uploaded = False
        st.session_state.uploader_key += 1  # forces file_uploader to fully reset
        st.rerun()

uploaded_file = st.file_uploader(
    "Choose a PDF, DOCX, or TXT file",
    type=["pdf", "docx", "txt"],
    key=f"uploader_{st.session_state.uploader_key}",
)

if uploaded_file and not st.session_state.uploaded:
    with st.spinner("Processing document..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(
                f"{BACKEND_URL}/upload", files=files, timeout=REQUEST_TIMEOUT
            )
        except requests.exceptions.Timeout:
            st.error("❌ Upload timed out. The document may be too large or the server is busy.")
            st.stop()
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach the backend. Make sure `uvicorn main:app` is running.")
            st.stop()

    if response.status_code == 200:
        data = response.json()
        st.success(
            f"✅ '{uploaded_file.name}' uploaded! Chunks created: {data.get('chunks_created', 'N/A')}"
        )
        st.session_state.uploaded = True
        st.rerun()
    else:
        st.error(f"❌ Upload failed: {response.text}")

# ── Ask Questions Section ────────────────────────────────────────
st.header("2. Ask a Question")
question = st.text_input("Enter your question about the document")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    elif not st.session_state.uploaded:
        st.warning("Please upload a document first.")
    else:
        with st.spinner("Thinking..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"question": question},
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Please try again.")
                st.stop()
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the backend. Make sure `uvicorn main:app` is running.")
                st.stop()

        if res.status_code != 200:
            st.error(f"Backend error: {res.text}")
        else:
            data = res.json()

            st.subheader("Answer")
            st.write(data.get("answer", "No answer returned."))

            confidence = data.get("confidence", 0)
            st.subheader("Confidence Score")
            st.progress(float(confidence))
            st.caption(f"{confidence * 100:.0f}% confidence")

            sources = data.get("sources", [])
            if sources:
                st.subheader("Supporting Sources")
                for i, s in enumerate(sources, 1):
                    with st.expander(f"Source chunk {i}"):
                        st.write(s)

# ── Structured Extraction Section ───────────────────────────────
st.header("3. Extract Structured Data")

if st.button("Extract Shipment Data"):
    if not st.session_state.uploaded:
        st.warning("Please upload a document first.")
    else:
        with st.spinner("Extracting structured data..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/extract", timeout=REQUEST_TIMEOUT
                )
            except requests.exceptions.Timeout:
                st.error("❌ Extraction timed out. Please try again.")
                st.stop()
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the backend. Make sure `uvicorn main:app` is running.")
                st.stop()

        if res.status_code == 200:
            st.subheader("Extracted Fields")
            st.json(res.json())
        else:
            st.error(f"Extraction failed: {res.text}")