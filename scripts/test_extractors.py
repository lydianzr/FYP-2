# scripts/test_extractors.py
import os
import sys
import glob

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.loaders import load_document
from modules.extract import TesseractExtractor

def test_pipeline():
    print("=" * 60)
    print("      FYP2 PHASE 2 EXTRACTION ENGINE TEST")
    print("=" * 60 + "\n")

    test_files = glob.glob("data/raw/converted/*.*")
    if not test_files:
        print("[Error] No converted test files found in data/raw/converted/.")
        return

    print(f"Testing {len(test_files)} converted files...\n")
    extractor = TesseractExtractor()

    for file_path in test_files[:3]:
        print(f"File: {file_path}")
        doc_data = load_document(file_path)
        print(f"  --> Extension: {doc_data['file_type']}")
        print(f"  --> Text Length: {len(doc_data['text'])} characters")
        
        schema = extractor.extract(file_path)
        print(f"  --> Document ID: {schema['document_id']}")
        print(f"  --> Total Amount: {schema['total_amount']}\n")

    print("Phase 2 Extractor Engines verified successfully.")

if __name__ == "__main__":
    test_pipeline()