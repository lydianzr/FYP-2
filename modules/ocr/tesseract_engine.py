"""Condition 1: Tesseract OCR engine."""
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    words: list[dict]  # [{"text": str, "bbox": [x0, y0, x1, y1], "conf": float}]


def run(image_path: str) -> OCRResult:
    # TODO: pytesseract.image_to_data -> OCRResult
    raise NotImplementedError
