"""Entry point:  streamlit run main.py"""
import streamlit as st
from utils import inject_css, brand_header, pipeline_strip

st.set_page_config(page_title="IDP + RAG", page_icon="📄", layout="wide")
inject_css()

# ---- shared state (lives across tabs) ----
st.session_state.setdefault("n_docs", 47)
st.session_state.setdefault("n_fields", 516)

pages = [
    st.Page("tabs/tab1.py", title="RAG Assistant", icon="💬", url_path="rag", default=True),
    st.Page("tabs/tab2.py", title="Benchmark Dashboard", icon="📊", url_path="bench"),
    st.Page("tabs/tab3.py", title="Try It Yourself", icon="🧪", url_path="try"),
]
pg = st.navigation(pages, position="top")

brand_header()
pipeline_strip(pg.url_path)
pg.run()

st.markdown('<div class="soft" style="text-align:center;font-size:12px;padding:24px 0">'
            'FYP2 · WIA3003 · Dr. Liew Wei Shiung · INNONICS Sdn. Bhd. · Faculty of Computer Science, University of Malaya</div>',
            unsafe_allow_html=True)
