# modules/rag.py
import json
from typing import Dict, Any, List
from modules.index.structured import StructuredIndex
from modules.index.vector import VectorIndex
from modules.index.sparse import SparseIndex
from modules.index.hybrid import HybridIndex
from modules.index.tools import RAGTools


class RAGAssistant:
    """RAG Controller: Runs queries, executes tools, and generates answers with field citations."""

    def __init__(self):
        self.structured_db = StructuredIndex()
        self.vector_idx = VectorIndex()
        self.sparse_idx = SparseIndex()
        self.hybrid_idx = HybridIndex(self.vector_idx, self.sparse_idx)
        self.tools = RAGTools(self.structured_db)

    def index_document(self, schema_dict: Dict[str, Any]):
        doc_id = str(schema_dict.get("document_id") or f"doc_{len(self.sparse_idx.documents) + 1}")
        
        # 1. Index in SQLite
        self.structured_db.insert_document(schema_dict)

        # 2. Construct text context
        text_context = (
            f"Doc ID: {doc_id} | Supplier: {schema_dict.get('supplier_name')} | "
            f"Type: {schema_dict.get('document_type')} | Date: {schema_dict.get('date')} | "
            f"Total: {schema_dict.get('total_amount')} {schema_dict.get('currency', 'USD')}"
        )

        meta = {
            "supplier": str(schema_dict.get("supplier_name", "")),
            "total_amount": float(schema_dict.get("total_amount") or 0.0)
        }

        # 3. Index in Vector and Sparse search engines
        self.vector_idx.add_document(doc_id, text_context, meta)
        self.sparse_idx.add_document(doc_id, text_context, meta)

    def answer_query(self, query: str) -> Dict[str, Any]:
        # Handle sum/aggregate intent via structured SQL tool
        if "total" in query.lower() or "sum" in query.lower():
            agg_res = self.tools.aggregate(column="total_amount")
            return {
                "query": query,
                "answer": f"The calculated total sum across indexed logistics documents is ${agg_res['total_value']:.2f}.",
                "citations": [
                    {
                        "source": "SQLite Structured Engine",
                        "field_level_citation": "documents.total_amount",
                        "confidence": 1.0
                    }
                ]
            }

        # Hybrid search over dense + sparse indexes
        retrieved = self.hybrid_idx.search(query, top_k=2)
        if not retrieved:
            return {"query": query, "answer": "No relevant logistics documents found.", "citations": []}

        top_match = retrieved[0]
        citations = [
            {
                "document_id": top_match["id"],
                "supplier": top_match["metadata"].get("supplier"),
                "source_engine": "Hybrid (BGE-M3 + BM25)",
                "hybrid_rrf_score": top_match.get("hybrid_rrf_score")
            }
        ]

        return {
            "query": query,
            "answer": f"Based on document {top_match['id']}, the context states: {top_match['text']}",
            "citations": citations
        }