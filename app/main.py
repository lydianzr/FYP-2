# app/main.py
import os
import sys
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.rag import RAGAssistant
from app.tabs import render_tab1, render_tab2, render_tab3

# Streamlit Configuration
st.set_page_config(
    page_title="Logistics Benchmarking & RAG Platform",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "rag_assistant" not in st.session_state:
    st.session_state.rag_assistant = RAGAssistant()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header
st.title("📦 Logistics Document Benchmarking & RAG System")
st.markdown("Production-ready Document AI platform for benchmark analysis, multi-paradigm extraction, and hybrid RAG search.")

# 3 Focused Functional Pages
tab1, tab2, tab3 = st.tabs([
    "💬 1. RAG Assistant",
    "📊 2. Benchmark Dashboard",
    "⚡ 3. Try It Yourself"
])

with tab1:
    render_tab1()

with tab2:
    render_tab2(PROJECT_ROOT)

with tab3:
    render_tab3(PROJECT_ROOT)