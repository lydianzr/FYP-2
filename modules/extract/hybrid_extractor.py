# modules/extract/hybrid_extractor.py
import os
from modules.schema import get_empty_schema
from modules.extract.base import BaseExtractor
from modules.extract.ocr_extractor import TesseractExtractor
from modules.extract.mllm_extractor import GPT4oExtractor, OPENAI_AVAILABLE

class HybridConsensusExtractor(BaseExtractor):
    """Paradigm D: Hybrid Consensus Fusion (OCR + MLLM)."""
    
    def __init__(self, api_key: str = None):
        self.ocr_engine = TesseractExtractor()
        self.mllm_engine = GPT4oExtractor(api_key=api_key) if OPENAI_AVAILABLE else None

    def extract(self, file_path: str) -> dict:
        ocr_result = self.ocr_engine.extract(file_path)
        mllm_result = self.mllm_engine.extract(file_path) if self.mllm_engine else get_empty_schema()

        consensus_schema = get_empty_schema()
        for key in consensus_schema.keys():
            mllm_val = mllm_result.get(key)
            ocr_val = ocr_result.get(key)
            
            # Precedence rule: Use MLLM output if non-empty, fallback to OCR
            if mllm_val not in [None, "", [], False]:
                consensus_schema[key] = mllm_val
            else:
                consensus_schema[key] = ocr_val

        return consensus_schema