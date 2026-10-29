# modules/index/tools.py
from typing import Dict, Any, List, Optional
from modules.index.structured import StructuredIndex


class RAGTools:
    """Function-calling dispatch tools for filter, aggregate, and document retrieval."""

    def __init__(self, structured_db: StructuredIndex):
        self.db = structured_db

    def filter(self, supplier: Optional[str] = None, min_amount: Optional[float] = None) -> List[Dict[str, Any]]:
        """Tool: Filter documents by metadata parameters."""
        return self.db.filter_documents(supplier=supplier, min_amount=min_amount)

    def aggregate(self, column: str = "total_amount", supplier: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Compute SQL sum aggregate across matching documents."""
        total = self.db.aggregate_sum(column=column, supplier=supplier)
        return {"aggregate_column": column, "supplier": supplier, "total_value": total}

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Tool: Fetch exact structured JSON document by document_id."""
        docs = self.db.filter_documents()
        for doc in docs:
            if doc["document_id"] == document_id:
                return doc
        return {"error": f"Document '{document_id}' not found."}