# modules/index/hybrid.py
from typing import List, Dict, Any
from modules.index.vector import VectorIndex
from modules.index.sparse import SparseIndex


class HybridIndex:
    """Combines Vector and Sparse indexes using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, vector_idx: VectorIndex, sparse_idx: SparseIndex):
        self.vector_idx = vector_idx
        self.sparse_idx = sparse_idx

    def search(self, query: str, top_k: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        dense_results = self.vector_idx.search(query, top_k=top_k * 2)
        sparse_results = self.sparse_idx.search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Accumulate RRF scores from Dense Vector Search
        for rank, item in enumerate(dense_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            doc_map[doc_id] = item

        # Accumulate RRF scores from BM25 Keyword Search
        for rank, item in enumerate(sparse_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = item

        # Sort combined results by aggregated RRF score
        fused_results = []
        for doc_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            entry = doc_map[doc_id]
            entry["hybrid_rrf_score"] = round(score, 6)
            fused_results.append(entry)

        return fused_results[:top_k]