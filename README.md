# FYP-2: Document Extraction Benchmark + RAG Assistant

Benchmarks five extraction conditions (OCR+regex, LLM-on-text, GPT-4o vision, Qwen2-VL, ...)
across document types, derives a routing policy, and serves a hybrid-retrieval RAG assistant.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # then fill in keys
```

Tesseract must be installed on the system (`apt install tesseract-ocr` / `brew install tesseract`).

## Run

```bash
streamlit run app.py
pytest -q
ruff check .
```

## Pipeline

```bash
python scripts/download_datasets.py        # -> data/raw/ (gitignored)
python scripts/make_synthetic.py           # -> data/synthetic/
python scripts/run_extraction_benchmark.py # -> data/metrics/*.csv  (long-running)
python scripts/build_index.py              # -> data/index/ (gitignored)
python scripts/run_rag_eval.py             # -> data/metrics/ragas_results.csv
```

## Layout

| Path | Purpose |
|---|---|
| `modules/ocr/` | Tesseract, PaddleOCR engines (conditions 1-2) |
| `modules/extract/` | Extractors; all return the dict shape locked in `base.py` |
| `modules/eval/` | Metrics (P/R/F1, FAR, CER, TEDS), stats, batch runner |
| `modules/index/` | SQLite fields, bge-m3 vectors, BM25, hybrid fusion, Gemini tools |
| `notebooks/` | 00 audit -> 05 ablation |
| `data/testset/` | Manifest, ground truth (committed), frozen splits |
| `docs/` | Timeline, model versions, dataset licences, weekly log |

## Rules

- Never commit `.env`, `data/raw/`, `data/index/`.
- `data/testset/splits.json` is frozen at milestone M1. Do not edit afterwards.
- Model versions are pinned in `modules/config.py` and recorded in `docs/model_versions.md`.
