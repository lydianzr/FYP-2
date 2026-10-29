# modules/extract/mllm_extractor.py
import os
import json
from typing import Dict, Any
from modules.schema import get_empty_schema
from modules.loaders import load_document
from modules.extract.base import BaseExtractor

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class BaseMLLMExtractor(BaseExtractor):
    """Abstract base for all Multimodal LLM extractors."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name

    def _build_prompt(self, document_text: str) -> str:
        return f"""
You are a precise logistics document extraction system.
Extract fields from the document text below and output valid raw JSON matching this schema exactly:

{json.dumps(get_empty_schema(), indent=2)}

Document Text Content:
{document_text[:4000]}
"""


# -------------------------------------------------------------------
# 1. OpenAI MLLM Family (GPT-4o, GPT-4o-mini)
# -------------------------------------------------------------------
class GPT4oExtractor(BaseMLLMExtractor):
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None):
        super().__init__(model_name=model_name)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Run `pip install openai`.")
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def extract(self, file_path: str) -> Dict[str, Any]:
        doc_data = load_document(file_path)
        prompt = self._build_prompt(doc_data["text"])

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You extract structured document data. Respond strictly with raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            raw_json = json.loads(response.choices[0].message.content)
            return self._clean_schema(raw_json)
        except Exception as e:
            print(f"[{self.model_name}] Extraction failed: {e}")
            return get_empty_schema()


# -------------------------------------------------------------------
# 2. Open-Source Local / API MLLM (Qwen2-VL via Transformers/Ollama)
# -------------------------------------------------------------------
class Qwen2VLExtractor(BaseMLLMExtractor):
    def __init__(self, model_name: str = "qwen2-vl", api_base: str = "http://localhost:11434/v1"):
        super().__init__(model_name=model_name)
        # Compatible with local OpenAI-style endpoints (Ollama, vLLM, LM Studio)
        if OPENAI_AVAILABLE:
            self.client = openai.OpenAI(base_url=api_base, api_key="ollama")
        else:
            self.client = None

    def extract(self, file_path: str) -> Dict[str, Any]:
        if not self.client:
            print("[Qwen2VLExtractor] Local API client unavailable.")
            return get_empty_schema()

        doc_data = load_document(file_path)
        prompt = self._build_prompt(doc_data["text"])

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Respond strictly with raw JSON matching the schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            raw_json = json.loads(response.choices[0].message.content)
            return self._clean_schema(raw_json)
        except Exception as e:
            print(f"[{self.model_name}] Extraction failed: {e}")
            return get_empty_schema()