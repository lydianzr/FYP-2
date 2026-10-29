# scripts/normalize_gt.py
import json
import os
import glob
import sys

# Ensure root directory is in PATH for importing modules.schema
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.schema import get_empty_schema

DOCILE_BASE = "data/raw/docile"
FUNSD_BASE = "data/raw/funsd"
OUTPUT_GT_DIR = "data/canonical_gt"

FIELD_MAP = {
    # DocILE field mappings
    "account_num": "document_id",
    "invoice_id": "document_id",
    "issue_date": "date",
    "vendor_name": "shipper_name",
    "customer_name": "consignee_name",
    "amount_total": "total_amount",
    # FUNSD field mappings
    "header": "document_type",
    "question": "shipper_name",
    "answer": "consignee_name"
}

def normalize_docile():
    os.makedirs(OUTPUT_GT_DIR, exist_ok=True)
    json_files = glob.glob(f"{DOCILE_BASE}/**/annotations/*.json", recursive=True)
    print(f"[Normalize GT] Found {len(json_files)} DocILE annotation files.")

    for file_path in json_files:
        doc_id = os.path.splitext(os.path.basename(file_path))[0]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            schema = get_empty_schema()
            schema["document_id"] = f"docile_{doc_id}"
            schema["document_type"] = "Invoice"

            for field in raw_data.get("field_values", []):
                raw_key = field.get("field_type")
                val = field.get("text")
                if raw_key in FIELD_MAP:
                    target_key = FIELD_MAP[raw_key]
                    if target_key == "total_amount":
                        try:
                            schema[target_key] = float(str(val).replace("$", "").replace(",", "").strip())
                        except ValueError:
                            schema[target_key] = val
                    else:
                        schema[target_key] = val

            out_path = os.path.join(OUTPUT_GT_DIR, f"docile_{doc_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2)
        except Exception as e:
            print(f"[Normalize GT] Error processing DocILE file {file_path}: {e}")

def normalize_funsd():
    os.makedirs(OUTPUT_GT_DIR, exist_ok=True)
    json_files = glob.glob(f"{FUNSD_BASE}/**/annotations/*.json", recursive=True)
    print(f"[Normalize GT] Found {len(json_files)} FUNSD annotation files.")

    for file_path in json_files:
        doc_id = os.path.splitext(os.path.basename(file_path))[0]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            schema = get_empty_schema()
            schema["document_id"] = f"funsd_{doc_id}"
            schema["document_type"] = "Form"
            schema["has_signature"] = True  # Scanned forms flag

            for box in raw_data.get("form", []):
                label = box.get("label")
                text = box.get("text")
                if label in FIELD_MAP:
                    target_key = FIELD_MAP[label]
                    if schema[target_key] is None:
                        schema[target_key] = text

            out_path = os.path.join(OUTPUT_GT_DIR, f"funsd_{doc_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2)
        except Exception as e:
            print(f"[Normalize GT] Error processing FUNSD file {file_path}: {e}")

if __name__ == "__main__":
    print("=== Normalizing Ground Truth Annotations ===")
    normalize_docile()
    normalize_funsd()
    print("=== Normalization Completed Successfully ===")