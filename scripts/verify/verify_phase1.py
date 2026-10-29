# scripts/verify/verify_phase1.py
import os
import sys
import glob
import json

# Resolve project root (FYP-2) two directory levels up from scripts/verify/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_phase1_audit():
    print("=" * 60)
    print("      FYP2 PHASE 1 INTEGRITY & VERIFICATION AUDIT")
    print("=" * 60 + "\n")

    passed_checks = 0
    total_checks = 5

    # -------------------------------------------------------------
    # Check 1: Directory Structure Verification
    # -------------------------------------------------------------
    print("[Check 1/5] Verifying Directory Structure...")
    required_dirs = [
        "data/raw/funsd",
        "data/raw/docile",
        "data/raw/converted",
        "data/canonical_gt",
        "modules",
        "scripts",
        "results"
    ]
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    
    if not missing_dirs:
        print("  --> PASS: All 7 required directories exist.")
        passed_checks += 1
    else:
        print(f"  --> FAIL: Missing directories: {missing_dirs}")

    # -------------------------------------------------------------
    # Check 2: Schema Module & Contract Integrity
    # -------------------------------------------------------------
    print("\n[Check 2/5] Verifying `modules/schema.py` Contract...")
    try:
        from modules.schema import get_empty_schema, CANONICAL_SCHEMA
        empty_schema = get_empty_schema()
        
        required_keys = [
            "document_type", "document_id", "date", "shipper_name", 
            "consignee_name", "origin", "destination", "total_amount", 
            "total_weight_kg", "line_items", "has_signature", "has_stamp"
        ]
        
        missing_keys = [k for k in required_keys if k not in empty_schema]
        if not missing_keys and len(empty_schema) == len(CANONICAL_SCHEMA):
            print("  --> PASS: `CANONICAL_SCHEMA` is properly exported with all required fields.")
            passed_checks += 1
        else:
            print(f"  --> FAIL: Schema missing fields: {missing_keys}")
    except Exception as e:
        print(f"  --> FAIL: Could not import `modules/schema.py`: {e}")

    # -------------------------------------------------------------
    # Check 3: Raw Datasets Ingestion (FUNSD & DocILE)
    # -------------------------------------------------------------
    print("\n[Check 3/5] Verifying Raw Dataset Ingestion...")
    funsd_files = glob.glob("data/raw/funsd/**", recursive=True)
    docile_pdfs = glob.glob("data/raw/docile/**/*.pdf", recursive=True)

    has_funsd = len(funsd_files) > 5
    has_docile = len(docile_pdfs) > 0

    if has_funsd and has_docile:
        print(f"  --> PASS: FUNSD ingested ({len(funsd_files)} assets) | DocILE ingested ({len(docile_pdfs)} PDFs).")
        passed_checks += 1
    else:
        if not has_funsd:
            print("  --> FAIL: FUNSD dataset files missing in `data/raw/funsd/`.")
        if not has_docile:
            print("  --> FAIL: DocILE PDF files missing in `data/raw/docile/`.")

    # -------------------------------------------------------------
    # Check 4: Multi-Format Conversion Output (FR-2)
    # -------------------------------------------------------------
    print("\n[Check 4/5] Verifying Multi-Format Converted Subset...")
    docx_count = len(glob.glob("data/raw/converted/*.docx"))
    txt_count = len(glob.glob("data/raw/converted/*.txt"))
    xlsx_count = len(glob.glob("data/raw/converted/*.xlsx"))

    if docx_count > 0 and txt_count > 0 and xlsx_count > 0:
        print(f"  --> PASS: Converted files ready ({docx_count} .docx, {txt_count} .txt, {xlsx_count} .xlsx).")
        passed_checks += 1
    else:
        print(f"  --> FAIL: Incomplete converted files (.docx: {docx_count}, .txt: {txt_count}, .xlsx: {xlsx_count}).")
        print("      Run `python scripts/convert_formats.py` to fix.")

    # -------------------------------------------------------------
    # Check 5: Ground Truth Canonical Normalization
    # -------------------------------------------------------------
    print("\n[Check 5/5] Verifying Canonical Ground Truth JSONs...")
    gt_json_files = glob.glob("data/canonical_gt/*.json")

    if len(gt_json_files) > 0:
        # Validate sample file structure against CANONICAL_SCHEMA
        sample_path = gt_json_files[0]
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                sample_json = json.load(f)
            
            from modules.schema import CANONICAL_SCHEMA
            isValid = all(k in sample_json for k in CANONICAL_SCHEMA.keys())

            if isValid:
                print(f"  --> PASS: Found {len(gt_json_files)} ground truth JSONs matching CANONICAL_SCHEMA.")
                passed_checks += 1
            else:
                print(f"  --> FAIL: Sample GT JSON '{sample_path}' does not match `CANONICAL_SCHEMA` keys.")
        except Exception as e:
            print(f"  --> FAIL: Error reading ground truth JSON: {e}")
    else:
        print("  --> FAIL: No ground truth JSON files found in `data/canonical_gt/`.")
        print("      Run `python scripts/normalize_gt.py` to fix.")

    # -------------------------------------------------------------
    # Final Audit Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY: {passed_checks}/{total_checks} Checks Passed")
    print("=" * 60)

    if passed_checks == total_checks:
        print("\n🟢 PHASE 1 VERIFICATION SUCCESSFUL! Ready to proceed to Phase 2.\n")
    else:
        print("\n🔴 PHASE 1 AUDIT FAILED. Resolve the failed checks before proceeding.\n")

if __name__ == "__main__":
    run_phase1_audit()