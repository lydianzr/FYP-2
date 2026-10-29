# tests/test_rag_tools.py
import unittest
from modules.index.structured import StructuredIndex
from modules.index.tools import RAGTools

class TestRAGTools(unittest.TestCase):
    def test_tools(self):
        db = StructuredIndex()
        db.insert_document({"document_id": "TOOL-01", "supplier_name": "FastFreight", "total_amount": 300.0})
        tools = RAGTools(db)
        res = tools.aggregate(supplier="FastFreight")
        self.assertEqual(res["total_value"], 300.0)

if __name__ == "__main__":
    unittest.main()