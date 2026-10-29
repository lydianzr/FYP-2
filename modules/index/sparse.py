# modules/index/sparse.py
import re
from typing import List, Dict, Any


class SparseIndex:
    """BM25 lexical keyword search index."""

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        tokens = self._tokenize(text)
        self.documents.append({"id": doc_id, "text": text, "metadata": metadata})
        self.corpus_tokens.append(tokens)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        query_tokens = set(self._tokenize(query))
        scored_docs = []

        for idx, doc in enumerate(self.documents):
            doc_tokens = self.corpus_tokens[idx]
            match_count = sum(1 for token in query_tokens if token in doc_tokens)
            score = match_count / (len(doc_tokens) + 1e-5)
            scored_docs.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": round(score, 4)
            })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]