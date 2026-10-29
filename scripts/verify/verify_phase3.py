# scripts/verify/verify_phase3.py
import os
import sys
import glob
import json

# Resolve project root (FYP-2) two directory levels up from scripts/verify/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_phase3_audit():
    print("=" * 60)
    print("      FYP2 PHASE 3 EVALUATION PIPELINE AUDIT")
    print("=" * 60 + "\n")

    passed_checks = 0
    total_checks = 5

    # Check 1: Metric Engine Implementation
    print("[Check 1/5] Verifying Metric Computation Engine (`modules/eval/metrics.py`)...")
    try:
        from modules.eval.metrics import compute_exact_match, compute_anls, compute_line_item_f1
        
        em_pass = compute_exact_match("INV-101", "inv-101") == 1.0
        anls_pass = compute_anls("123 Main St", "123 Main St.") > 0.8
        _, _, f1_pass = compute_line_item_f1([{"desc": "Item A"}], [{"desc": "Item A"}])
        
        if em_pass and anls_pass and f1_pass == 1.0:
            print("  --> PASS: Math metrics (EM, ANLS, Line-Item F1) correctly calculated.")
            passed_checks += 1
        else:
            print("  --> FAIL: Metric calculation outputs incorrect.")
    except Exception as e:
        print(f"  --> FAIL: Metric module import/execution error: {e}")

    # Check 2: Benchmark Evaluator Integration
    print("\n[Check 2/5] Verifying Benchmark Evaluator (`modules/eval/evaluator.py`)...")
    try:
        from modules.eval import BenchmarkEvaluator
        from modules.schema import get_empty_schema
        
        evaluator = BenchmarkEvaluator()
        dummy_gt = get_empty_schema()
        dummy_gt["document_id"] = "DOC-001"
        dummy_gt["total_amount"] = 500.00
        
        dummy_pred = get_empty_schema()
        dummy_pred["document_id"] = "DOC-001"
        dummy_pred["total_amount"] = 500.00

        res = evaluator.evaluate_document(dummy_pred, dummy_gt, latency_seconds=0.12, cost_usd=0.001)
        if res["macro_exact_match"] == 1.0 and res["macro_anls"] == 1.0:
            print("  --> PASS: `BenchmarkEvaluator` generated accurate 100% score for identical inputs.")
            passed_checks += 1
        else:
            print("  --> FAIL: Evaluator returned incorrect aggregate scores.")
    except Exception as e:
        print(f"  --> FAIL: BenchmarkEvaluator execution error: {e}")

    # Check 3: Ground Truth Accessibility
    print("\n[Check 3/5] Verifying Ground Truth JSON Accessibility (`data/canonical_gt/`)...")
    gt_files = glob.glob(os.path.join(PROJECT_ROOT, "data/canonical_gt/*.json"))
    if gt_files:
        print(f"  --> PASS: Found {len(gt_files)} ground truth JSON targets ready for evaluation.")
        passed_checks += 1
    else:
        print("  --> FAIL: No ground truth JSON files found in `data/canonical_gt/`.")

    # Check 4: Benchmark Runner Presence
    print("\n[Check 4/5] Verifying Automated Benchmark Runner (`scripts/run_benchmark.py`)...")
    runner_path = os.path.join(PROJECT_ROOT, "scripts", "run_benchmark.py")
    if os.path.exists(runner_path):
        print("  --> PASS: `scripts/run_benchmark.py` runner script is present.")
        passed_checks += 1
    else:
        print("  --> FAIL: `scripts/run_benchmark.py` not found.")

    # Check 5: Extraction + Evaluation Loop Test
    print("\n[Check 5/5] Verifying Extraction + Evaluation Loop...")
    try:
        from modules.extract import TesseractExtractor
        from modules.eval import BenchmarkEvaluator
        
        sample_files = glob.glob(os.path.join(PROJECT_ROOT, "data/raw/converted/*.*"))
        if sample_files and gt_files:
            extractor = TesseractExtractor()
            evaluator = BenchmarkEvaluator()

            with open(gt_files[0], "r", encoding="utf-8") as f:
                gt_data = json.load(f)

            pred_data = extractor.extract(sample_files[0])
            eval_res = evaluator.evaluate_document(pred_data, gt_data)

            print("  --> PASS: End-to-end extraction + evaluation complete.")
            print(f"      Sample Doc ID GT: {gt_data.get('document_id')} | Pred: {pred_data.get('document_id')}")
            print(f"      Macro ANLS: {eval_res['macro_anls']} | Macro EM: {eval_res['macro_exact_match']}")
            passed_checks += 1
        else:
            print("  --> FAIL: Required sample files or ground truth missing.")
    except Exception as e:
        print(f"  --> FAIL: End-to-end extraction + evaluation loop failed: {e}")

    # Audit Summary
    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY: {passed_checks}/{total_checks} Checks Passed")
    print("=" * 60)

    if passed_checks == total_checks:
        print("\n🟢 PHASE 3 VERIFICATION SUCCESSFUL! Ready to run benchmark script or proceed to Phase 4.\n")
    else:
        print("\n🔴 PHASE 3 AUDIT FAILED. Resolve the failed checks before proceeding.\n")

if __name__ == "__main__":
    run_phase3_audit()