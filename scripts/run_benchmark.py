# scripts/run_benchmark.py
import os
import sys
import glob
import json
import time
import pandas as pd
from typing import List, Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.loaders import load_document
from modules.extract import (
    TesseractExtractor,
    PaddleOCRExtractor,
    GPT4oExtractor,
    HybridConsensusExtractor
)
from modules.eval import BenchmarkEvaluator

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
GT_DIR = os.path.join(PROJECT_ROOT, "data/canonical_gt")
CONVERTED_DIR = os.path.join(PROJECT_ROOT, "data/raw/converted")


def run_full_benchmark(paradigms: List[str] = None, max_docs: int = 10):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    evaluator = BenchmarkEvaluator()
    
    # Instantiate available extractors
    available_extractors = {
        "OCR_Tesseract": TesseractExtractor(),
        "Hybrid_Consensus": HybridConsensusExtractor()
    }

    try:
        from modules.extract.ocr_extractor import PADDLE_AVAILABLE
        if PADDLE_AVAILABLE:
            available_extractors["OCR2_Paddle"] = PaddleOCRExtractor()
    except Exception:
        pass

    try:
        from modules.extract.mllm_extractor import OPENAI_AVAILABLE
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            available_extractors["MLLM_GPT4o"] = GPT4oExtractor()
    except Exception:
        pass

    selected_paradigms = paradigms or list(available_extractors.keys())
    
    gt_files = sorted(glob.glob(os.path.join(GT_DIR, "*.json")))[:max_docs]
    converted_files = sorted(glob.glob(os.path.join(CONVERTED_DIR, "*.*")))[:max_docs]

    if not gt_files:
        print("[Benchmark Error] No Ground Truth files found in data/canonical_gt/.")
        return

    print("=" * 70)
    print(f"      STARTING BENCHMARK RUN ({len(gt_files)} Docs | {len(selected_paradigms)} Paradigms)")
    print("=" * 70 + "\n")

    benchmark_records = []

    for paradigm_name in selected_paradigms:
        extractor = available_extractors.get(paradigm_name)
        if not extractor:
            print(f"[Skip] Extractor '{paradigm_name}' not configured.")
            continue

        print(f"--> Running Benchmark for Paradigm: {paradigm_name}...")

        for idx, gt_path in enumerate(gt_files):
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_schema = json.load(f)

            # Match ground truth file with raw test file if available
            test_file = converted_files[idx % len(converted_files)] if converted_files else gt_path
            doc_ext = os.path.splitext(test_file)[1].lower()

            start_time = time.time()
            try:
                pred_schema = extractor.extract(test_file)
            except Exception as e:
                print(f"  [Extraction Error] {paradigm_name} failed on {test_file}: {e}")
                continue
            latency = time.time() - start_time

            # Estimate API costs ($0.005 flat dummy for MLLM, $0 for local OCR)
            cost = 0.005 if "MLLM" in paradigm_name else 0.0

            # Evaluate
            eval_metrics = evaluator.evaluate_document(
                pred_schema=pred_schema,
                gt_schema=gt_schema,
                latency_seconds=latency,
                cost_usd=cost
            )

            # Flatten record for Pandas CSV export
            record = {
                "document_id": gt_schema.get("document_id"),
                "paradigm": paradigm_name,
                "file_format": doc_ext,
                "macro_exact_match": eval_metrics["macro_exact_match"],
                "macro_anls": eval_metrics["macro_anls"],
                "line_item_f1": eval_metrics["line_item_f1"],
                "latency_seconds": eval_metrics["latency_seconds"],
                "cost_usd": eval_metrics["cost_usd"]
            }

            # Append individual field exact match scores
            for field, details in eval_metrics["field_details"].items():
                record[f"field_em_{field}"] = details["exact_match"]

            benchmark_records.append(record)

    # Save outputs to CSV and JSON
    if benchmark_records:
        df = pd.DataFrame(benchmark_records)
        csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
        df.to_csv(csv_path, index=False)
        print(f"\n[Success] Benchmark results saved to: {csv_path}")

        # Summary Aggregation Report
        summary_df = df.groupby("paradigm")[["macro_exact_match", "macro_anls", "line_item_f1", "latency_seconds", "cost_usd"]].mean().reset_index()
        summary_path = os.path.join(RESULTS_DIR, "summary_metrics.csv")
        summary_df.to_csv(summary_path, index=False)

        print("\n=== BENCHMARK SUMMARY TABLE ===")
        print(summary_df.to_string(index=False))
        print("=" * 70 + "\n")


if __name__ == "__main__":
    run_full_benchmark()