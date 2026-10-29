# scripts/convert_formats.py
import os
import glob
import pandas as pd
import pdfplumber
from pdf2docx import Converter

DOCILE_BASE = "data/raw/docile"
OUTPUT_DIR = "data/raw/converted"

def convert_sample_subset():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Search recursively to handle nested or flattened DocILE directory layouts
    pdf_files = sorted(glob.glob(f"{DOCILE_BASE}/**/*.pdf", recursive=True))
    
    if not pdf_files:
        print(f"[Convert Formats] No PDFs found under '{DOCILE_BASE}'. Please check dataset extraction.")
        return

    selected_files = pdf_files[:15]
    print(f"[Convert Formats] Found {len(pdf_files)} PDFs. Converting top {len(selected_files)} into DOCX, TXT, and XLSX...")

    for i, pdf_path in enumerate(selected_files):
        base_name = f"docile_sample_{i+1:02d}"

        # Group 1 (Files 1-5): Convert to DOCX
        if i < 5:
            docx_path = os.path.join(OUTPUT_DIR, f"{base_name}.docx")
            try:
                cv = Converter(pdf_path)
                cv.convert(docx_path)
                cv.close()
                print(f"[{i+1}/15] Converted to DOCX: {docx_path}")
            except Exception as e:
                print(f"[{i+1}/15] DOCX conversion failed for {pdf_path}: {e}")

        # Group 2 (Files 6-10): Convert to TXT
        elif i < 10:
            txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text_content = "\n".join([page.extract_text() or "" for page in pdf.pages])
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                print(f"[{i+1}/15] Converted to TXT:  {txt_path}")
            except Exception as e:
                print(f"[{i+1}/15] TXT conversion failed for {pdf_path}: {e}")

        # Group 3 (Files 11-15): Convert to XLSX
        else:
            xlsx_path = os.path.join(OUTPUT_DIR, f"{base_name}.xlsx")
            try:
                rows = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                rows.append(row)
                df = pd.DataFrame(rows) if rows else pd.DataFrame([["No extracted table content"]])
                df.to_excel(xlsx_path, index=False, header=False)
                print(f"[{i+1}/15] Converted to XLSX: {xlsx_path}")
            except Exception as e:
                print(f"[{i+1}/15] XLSX conversion failed for {pdf_path}: {e}")

    print("[Convert Formats] Multi-format conversion complete.")

if __name__ == "__main__":
    convert_sample_subset()