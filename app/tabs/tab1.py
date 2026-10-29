# app/tabs/tab1.py
import os
import tempfile
import streamlit as st
from modules.loaders import load_document

def render_tab1():
    st.header("1. RAG Assistant")
    st.write("Upload logistics documents to index them into the local hybrid vector store (ChromaDB + SQLite) and ask questions with source citations.")

    col_upload, col_preview = st.columns([1, 1])

    with col_upload:
        st.subheader("Document Ingestion & Indexing")
        uploaded_file = st.file_uploader(
            "Upload Logistics Document for RAG Indexing",
            type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]
        )

        if uploaded_file and st.button("📥 Index Document into RAG Engine", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            with st.spinner("Extracting schema and vectorizing..."):
                try:
                    # Ingest and extract structured representation
                    from modules.extract import HybridConsensusExtractor
                    extractor = HybridConsensusExtractor()
                    extracted_json = extractor.extract(tmp_path)

                    # Index into local RAG engine
                    st.session_state.rag_assistant.index_document(extracted_json)
                    st.success(f"Successfully indexed document `{uploaded_file.name}` into RAG system!")
                    st.session_state["last_indexed_doc"] = extracted_json
                except Exception as e:
                    st.error(f"Failed to index document: {e}")

    with col_preview:
        st.subheader("Indexed Document Context")
        if "last_indexed_doc" in st.session_state:
            st.json(st.session_state["last_indexed_doc"])
        else:
            st.info("No document indexed in this session yet. Upload a document on the left or use pre-indexed baseline documents.")

    st.markdown("---")
    st.subheader("💬 Interactive RAG Q&A Assistant")

    # Render Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "citations" in message and message["citations"]:
                with st.expander("📌 Source Field Citations"):
                    st.json(message["citations"])

    # User Query Input
    if user_query := st.chat_input("Ask about logistics documents (e.g., 'What is the total amount for Apex Logistics?'):"):
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Executing hybrid retrieval (BGE-M3 + BM25) and dispatching SQL tools..."):
                rag_response = st.session_state.rag_assistant.answer_query(user_query)
                answer_text = rag_response.get("answer", "No relevant data found.")
                citations = rag_response.get("citations", [])

                st.markdown(answer_text)
                if citations:
                    with st.expander("📌 Source Field Citations"):
                        st.json(citations)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer_text,
                    "citations": citations
                })