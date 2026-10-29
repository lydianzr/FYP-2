"""Condition 2: PaddleOCR engine. Same interface as tesseract_engine."""
from modules.ocr.tesseract_engine import OCRResult


def run(image_path: str) -> OCRResult:
    # TODO: PaddleOCR -> OCRResult
    raise NotImplementedError
