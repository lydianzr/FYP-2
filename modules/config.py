"""Central config: paths, pinned model versions, API key loading."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv optional
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
SYNTHETIC = DATA / "synthetic"
TESTSET = DATA / "testset"
GROUND_TRUTH = TESTSET / "ground_truth"
MANIFEST = TESTSET / "manifest.csv"
SPLITS = TESTSET / "splits.json"
CORPUS = DATA / "corpus"
METRICS = DATA / "metrics"
INDEX = DATA / "index"
CHROMA_DIR = INDEX / "chroma"
FIELDS_DB = INDEX / "fields.db"

# Pin exact versions. Mirror any change in docs/model_versions.md.
MODELS = {
    "gpt4o": "gpt-4o-2024-08-06",
    "gemini": "gemini-1.5-pro-002",
    "qwen2vl": "Qwen/Qwen2-VL-7B-Instruct",
    "embedding": "BAAI/bge-m3",
    "reranker": "BAAI/bge-reranker-v2-m3",
    "layoutlmv3": "microsoft/layoutlmv3-base",
}

SEED = 42


def get_key(name: str, required: bool = True) -> str | None:
    val = os.getenv(name)
    if required and not val:
        raise RuntimeError(f"Missing env var {name}. Copy .env.example to .env and fill it in.")
    return val
