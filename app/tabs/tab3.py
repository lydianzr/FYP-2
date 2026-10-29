# app/tabs/tab3.py
import os
import glob
import tempfile
import json
import streamlit as st
from modules.loaders import load_document
from modules.extract import TesseractExtractor, HybridConsensusExtractor
from modules.eval import BenchmarkEvaluator

def render_tab3(project_root: str):
    st.header("3. Try It Yourself (Live Playground)")
    st.write("Upload a single document or select a sample to execute extraction paradigms side-by-side and evaluate schema accuracy in real time.")

    col1, col2 = st.columns([1, 1])
    target_path = None

    with col1:
        st.subheader("1. Input Document")
        uploaded_file = st.file_uploader(
            "Upload Target Document",
            type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]
        )
        sample_files = sorted(glob.glob(os.path.join(project_root, "data/raw/converted/*.*")))
        selected_sample = st.selectbox("Or choose a benchmark sample:", ["(Upload Custom File)"] + sample_files)

        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                target_path = tmp.name
        elif selected_sample != "(Upload Custom File)":
            target_path = selected_sample

    with col2:
        st.subheader("2. Select Paradigms to Run")
        p_tesseract = st.checkbox("Paradigm A: Tesseract OCR", value=True)
        p_paddle = st.checkbox("Paradigm B: PaddleOCR", value=False)
        p_mllm = st.checkbox("Paradigm C: Multi-MLLM (GPT-4o)", value=False)
        p_hybrid = st.checkbox("Paradigm D: Hybrid Consensus", value=True)

        run_triggered = st.button("🚀 Run Side-by-Side Comparison", use_container_width=True)

    if run_triggered and target_path and os.path.exists(target_path):
        st.markdown("---")
        st.subheader("Live Extraction Side-by-Side Comparison")

        results = {}

        if p_tesseract:
            with st.spinner("Executing Paradigm A (Tesseract)..."):
                ext = TesseractExtractor()
                results["Paradigm A (Tesseract)"] = ext.extract(target_path)

        if p_paddle:
            with st.spinner("Executing Paradigm B (PaddleOCR)..."):
                try:
                    from modules.extract import PaddleOCRExtractor
                    ext = PaddleOCRExtractor()
                    results["Paradigm B (PaddleOCR)"] = ext.extract(target_path)
                except Exception:
                    results["Paradigm B (PaddleOCR)"] = {"error": "PaddleOCR unavailable"}

        if p_mllm:
            with st.spinner("Executing Paradigm C (MLLM)..."):
                try:
                    from modules.extract import GPT4oExtractor
                    ext = GPT4oExtractor()
                    results["Paradigm C (MLLM)"] = ext.extract(target_path)
                except Exception:
                    results["Paradigm C (MLLM)"] = {"error": "MLLM API unavailable"}

        if p_hybrid:
            with st.spinner("Executing Paradigm D (Hybrid Consensus)..."):
                ext = HybridConsensusExtractor()
                results["Paradigm D (Hybrid Consensus)"] = ext.extract(target_path)

        # Output columns
        cols = st.columns(len(results))
        for idx, (p_name, pred_json) in enumerate(results.items()):
            with cols[idx]:
                st.markdown(f"**{p_name}**")
                st.json(pred_json)

        # Optional Ground Truth Evaluation
        gt_files = sorted(glob.glob(os.path.join(project_root, "data/canonical_gt/*.json")))
        if gt_files:
            st.markdown("---")
            st.subheader("Ground Truth Validation (Scorecard)")
            selected_gt = st.selectbox("Select Ground Truth JSON for Evaluation:", gt_files)
            with open(selected_gt, "r", encoding="utf-8") as f:
                gt_json = json.load(f)

            evaluator = BenchmarkEvaluator()
            scorecard_rows = []

            for p_name, pred_json in results.items():
                if "error" not in pred_json:
                    ev = evaluator.evaluate_document(pred_json, gt_json)
                    scorecard_rows.append({
                        "Paradigm": p_name,
                        "Macro ANLS": ev["macro_anls"],
                        "Macro Exact Match": ev["macro_exact_match"],
                        "Line-Item F1": ev["line_item_f1"]
                    })

            if scorecard_rows:
                st.table(pd.DataFrame(scorecard_rows))