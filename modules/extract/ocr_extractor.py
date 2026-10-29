# modules/extract/ocr_extractor.py
import os
import re
import pytesseract
from modules.schema import get_empty_schema
from modules.loaders import load_document
from modules.extract.base import BaseExtractor

# Auto-detect Tesseract binary path on Windows
if os.name == 'nt':
    default_win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    ]
    for path in default_win_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class TesseractExtractor(BaseExtractor):
    """Paradigm A: Traditional OCR + Heuristic Regex Rules."""
    
    def extract(self, file_path: str) -> dict:
        doc_data = load_document(file_path)
        schema = get_empty_schema()
        full_text = doc_data["text"]

        # Run OCR on page/embedded images if text is empty
        if not full_text.strip() and doc_data["images"]:
            try:
                ocr_texts = [pytesseract.image_to_string(img) for img in doc_data["images"]]
                full_text = "\n".join(ocr_texts)
            except pytesseract.TesseractNotFoundError:
                print(f"[TesseractExtractor] Warning: Tesseract executable not found. Skipping OCR for {file_path}.")
            except Exception as e:
                print(f"[TesseractExtractor] OCR failed: {e}")

        schema["document_id"] = self._regex_search(r"(?:Invoice|AWB|Doc)\s*#?\s*:?\s*([A-Z0-9-]+)", full_text)
        schema["date"] = self._regex_search(r"\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b", full_text)
        
        amount_match = re.search(r"(?:Total|Amount Due|Net Total)\s*:?\s*\$?([\d,]+\.\d{2})", full_text, re.IGNORECASE)
        if amount_match:
            try:
                schema["total_amount"] = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                pass

        schema["document_type"] = "Invoice" if "invoice" in full_text.lower() else "Logistics Document"
        return self._clean_schema(schema)

    def _regex_search(self, pattern: str, text: str):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None


class PaddleOCRExtractor(BaseExtractor):
    """Paradigm B: OCR 2.0 Engine."""
    
    def __init__(self, lang: str = "en"):
        if not PADDLE_AVAILABLE:
            raise ImportError("PaddleOCR not installed. Run `pip install paddleocr paddlepaddle`.")
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def extract(self, file_path: str) -> dict:
        doc_data = load_document(file_path)
        schema = get_empty_schema()
        
        extracted_lines = []
        if doc_data["images"]:
            import numpy as np
            for img in doc_data["images"]:
                result = self.ocr.ocr(np.array(img), cls=True)
                if result and result[0]:
                    for line in result[0]:
                        extracted_lines.append(line[1][0])

        full_text = "\n".join(extracted_lines) or doc_data["text"]

        schema["document_id"] = self._regex_search(r"(?:INV|AWB|NO\.?)\s*:?\s*([A-Z0-9-]+)", full_text)
        schema["date"] = self._regex_search(r"\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b", full_text)
        schema["document_type"] = "Logistics Form (OCR 2.0)"
        return self._clean_schema(schema)

    def _regex_search(self, pattern: str, text: str):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None