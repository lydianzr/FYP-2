import streamlit as st
from utils import page_header, chip

page_header(
    "RAG Assistant",
    "Powered by the extraction pipeline (RO1) using models chosen by the comparative study (RO2). "
    "Retrieval fuses the structured field index with page-image embeddings (ColPali).",
    [("RO3 · Multimodal RAG", "chip-accent"), ("bge-m3 + ColQwen2", "")],
)

# ---- index status bar ----
s1, s2 = st.columns([11, 1.5], vertical_alignment="center")
with s1:
    st.markdown(
        '<div class="panel" style="padding:10px 14px;margin:0;font-size:12px">'
        '<span class="label" style="margin-right:10px">Index built from</span>'
        f'{chip(str(st.session_state.n_docs) + " docs", "chip-good", True)}'
        f'{chip(str(st.session_state.n_fields) + " fields extracted", "chip-good", True)}'
        '<span class="soft"> · Routed via RO2 findings: </span>'
        f'{chip("AWB → Qwen2-VL", "", True)}{chip("Invoice → GPT-4o", "", True)}{chip("BOL → LayoutLMv3", "", True)}'
        '<span class="soft" style="margin-left:12px;font-size:11px">rebuilt 4 min ago</span></div>',
        unsafe_allow_html=True)
with s2:
    if st.button("Rebuild index", use_container_width=True):
        with st.spinner("Rebuilding…"):
            import time; time.sleep(1)
        st.toast("Index rebuilt")

st.write("")
left, mid, right = st.columns([3, 6, 3])

# =============== LEFT: collection ===============
with left:
    with st.container(border=True):
        h1, h2 = st.columns([2, 1.3], vertical_alignment="center")
        h1.markdown('<div class="title" style="margin:0">Collection</div>', unsafe_allow_html=True)
        with h2:
            st.page_link("tabs/tab1.py", label="+ Upload")

        st.markdown(f'<div class="label">Documents · {st.session_state.n_docs}</div>', unsafe_allow_html=True)
        rows = []
        for i, (t, name, sub) in enumerate(DOCS):
            sub_html = f'<div class="soft" style="font-size:11px;margin-top:4px">{sub}</div>' if sub else ""
            rows.append(f'<div class="docrow {"sel" if i == 0 else ""}"><span class="chip mono" style="font-size:10px">{t}</span> {name}{sub_html}</div>')
        rows.append(f'<div class="soft" style="text-align:center;font-size:11px">+ {st.session_state.n_docs - len(DOCS)} more</div>')
        st.markdown("".join(rows), unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="label">Filter by type</div>', unsafe_allow_html=True)
        selected_types = [n for n, c in DOC_TYPES if st.checkbox(f"{n}  ({c})", value=True, key=f"f_{n}")]

        st.divider()
        st.markdown('<div class="label">Retrieval mode</div>', unsafe_allow_html=True)
        mode = st.radio("mode", ["Multimodal", "Text-only"], horizontal=True, label_visibility="collapsed")
        st.caption("Text = bge-m3 + BM25 hybrid. Multimodal = ColQwen2 page-image vectors.")

# =============== CENTER: chat ===============
with mid:
    with st.container(border=True):
        st.markdown(
            '<div style="display:flex;justify-content:space-between;align-items:center">'
            '<div style="font-size:14px;font-weight:500"><span style="color:#4ade80">●</span> Session · logistics_Q3_2025</div>'
            f'{chip("RAGAS · Faithfulness 0.87")}</div>', unsafe_allow_html=True)
        st.divider()

        chat_box = st.container(height=470, border=False)
        with chat_box:
            for role, content in st.session_state.messages:
                with st.chat_message(role):
                    if role == "assistant":
                        st.caption("Assistant · Gemini 2.5 Flash")
                    st.markdown(content, unsafe_allow_html=True)

        # suggestion chips
        st.markdown('<span class="soft" style="font-size:11px">Suggested:</span>', unsafe_allow_html=True)
        sc = st.columns(len(SUGGESTED))
        picked = None
        for col, text in zip(sc, SUGGESTED):
            if col.button(text, key=f"sg_{text}", use_container_width=True):
                picked = text

        prompt = st.chat_input("Ask about your documents…") or picked
        st.caption("⏎ send  ·  structured queries only possible via RO1 field index  ·  Top-k = 6 · Reranker = bge-reranker-v2")

    if prompt:
        st.session_state.messages.append(("user", prompt))
        st.session_state.messages.append(("assistant", answer_query(prompt, mode, top_k=6)))
        st.rerun()

# =============== RIGHT: evidence ===============
with right:
    html = ['<div class="panel"><div style="display:flex;justify-content:space-between"><div class="title">Retrieved Evidence</div>'
            f'{chip("last turn", "", True)}</div>']
    for e in EVIDENCE:
        g = "".join(chip(t, k, True) for t, k in e["grounds"])
        html.append(
            '<div class="panel-2" style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px">{chip(e["rank"], e["cls"], True)}'
            f'<span class="soft" style="font-size:11px">{e["kind"]}</span></div>'
            f'<div style="font-size:12px;font-weight:500;margin-bottom:4px">{e["title"]}</div>'
            f'<div class="doc-thumb">{e["body"]}</div>'
            f'<div style="margin-top:6px;font-size:10px"><span class="soft">grounds:</span> {g} '
            f'<span class="soft">via</span> {chip(e["model"], "", True)}</div></div>')
    html.append('<div class="label" style="margin-top:14px">RAGAS · this session</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">')
    for name, val, color in RAGAS:
        html.append(f'<div class="panel-2" style="text-align:center;padding:8px"><div class="soft" style="font-size:10px">{name}</div>'
                    f'<div class="metric-num" style="color:{color}">{val}</div></div>')
    html.append('</div></div>')
    st.markdown("".join(html), unsafe_allow_html=True)
