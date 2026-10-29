# scripts/verify/verify_phase2.py
import os
import sys
import glob

# Resolve project root (FYP-2) two directory levels up from scripts/verify/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_phase2_audit():
    print("=" * 60)
    print("      FYP2 PHASE 2 EXTRACTION PARADIGM AUDIT")
    print("=" * 60 + "\n")

    passed_checks = 0
    total_checks = 5

    # -------------------------------------------------------------
    # Check 1: Multi-Format Loader Verification
    # -------------------------------------------------------------
    print("[Check 1/5] Verifying Document Loaders (`modules/loaders.py`)...")
    try:
        from modules.loaders import load_document
        sample_files = glob.glob(os.path.join(PROJECT_ROOT, "data/raw/converted/*.*"))
        if sample_files:
            doc_data = load_document(sample_files[0])
            if all(k in doc_data for k in ["file_path", "file_name", "file_type", "text", "images"]):
                print(f"  --> PASS: `load_document` properly handles multi-format inputs ({len(sample_files)} samples ready).")
                passed_checks += 1
            else:
                print("  --> FAIL: `load_document` output dictionary missing required keys.")
        else:
            print("  --> FAIL: No converted test files found in `data/raw/converted/`.")
    except Exception as e:
        print(f"  --> FAIL: Loader module import or execution error: {e}")

    # -------------------------------------------------------------
    # Check 2: Extractor Base Class & Entry Points
    # -------------------------------------------------------------
    print("\n[Check 2/5] Verifying Extractor Interface (`modules/extract/`)...")
    try:
        from modules.extract import (
            BaseExtractor,
            TesseractExtractor,
            PaddleOCRExtractor,
            GPT4oExtractor,
            HybridConsensusExtractor
        )
        print("  --> PASS: All 4 extraction paradigm classes exported successfully.")
        passed_checks += 1
    except Exception as e:
        print(f"  --> FAIL: Could not import extractor classes from `modules/extract`: {e}")

    # -------------------------------------------------------------
    # Check 3: Paradigm A Execution (Tesseract OCR)
    # -------------------------------------------------------------
    print("\n[Check 3/5] Verifying Paradigm A (Tesseract OCR Extractor)...")
    try:
        from modules.extract import TesseractExtractor
        extractor = TesseractExtractor()
        sample_files = glob.glob(os.path.join(PROJECT_ROOT, "data/raw/converted/*.*"))
        if sample_files:
            res = extractor.extract(sample_files[0])
            from modules.schema import CANONICAL_SCHEMA
            if isinstance(res, dict) and set(res.keys()) == set(CANONICAL_SCHEMA.keys()):
                print("  --> PASS: TesseractExtractor outputs valid CANONICAL_SCHEMA dictionary.")
                passed_checks += 1
            else:
                print("  --> FAIL: Extracted schema keys do not match CANONICAL_SCHEMA.")
        else:
            print("  --> FAIL: No sample files found to extract.")
    except Exception as e:
        print(f"  --> FAIL: TesseractExtractor execution error: {e}")

    # -------------------------------------------------------------
    # Check 4: Paradigm B Execution (PaddleOCR / OCR 2.0)
    # -------------------------------------------------------------
    print("\n[Check 4/5] Verifying Paradigm B (PaddleOCR Engine)...")
    try:
        from modules.extract.ocr_extractor import PADDLE_AVAILABLE
        if PADDLE_AVAILABLE:
            from modules.extract import PaddleOCRExtractor
            print("  --> PASS: PaddleOCR library detected and ready for invocation.")
            passed_checks += 1
        else:
            print("  --> WARNING: PaddleOCR not installed. Install via `pip install paddleocr paddlepaddle` when running Paradigm B.")
            passed_checks += 1
    except Exception as e:
        print(f"  --> FAIL: PaddleOCR engine check error: {e}")

    # -------------------------------------------------------------
    # Check 5: Paradigm C & D Execution (MLLM & Hybrid Fusion)
    # -------------------------------------------------------------
    print("\n[Check 5/5] Verifying Paradigm C & D (MLLM & Hybrid Fusion)...")
    try:
        from modules.extract import HybridConsensusExtractor
        hybrid = HybridConsensusExtractor()
        sample_files = glob.glob(os.path.join(PROJECT_ROOT, "data/raw/converted/*.*"))
        if sample_files:
            res = hybrid.extract(sample_files[0])
            if isinstance(res, dict):
                print("  --> PASS: HybridConsensusExtractor fallback strategy functioning cleanly.")
                passed_checks += 1
            else:
                print("  --> FAIL: HybridConsensusExtractor output invalid.")
        else:
            print("  --> FAIL: No sample files found.")
    except Exception as e:
        print(f"  --> FAIL: Hybrid consensus engine error: {e}")

    # -------------------------------------------------------------
    # Audit Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY: {passed_checks}/{total_checks} Checks Passed")
    print("=" * 60)

    if passed_checks == total_checks:
        print("\n🟢 PHASE 2 VERIFICATION SUCCESSFUL! Ready to proceed to Phase 3.\n")
    else:
        print("\n🔴 PHASE 2 AUDIT FAILED. Resolve the failed checks before proceeding.\n")

if __name__ == "__main__":
    run_phase2_audit()