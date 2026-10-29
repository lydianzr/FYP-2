# tests/test_index.py
import unittest
from modules.rag import RAGAssistant

class TestRAGIndex(unittest.TestCase):
    def test_full_pipeline(self):
        assistant = RAGAssistant()
        sample = {
            "document_id": "TEST-INV-99",
            "document_type": "Invoice",
            "supplier_name": "Apex Logistics",
            "total_amount": 1250.00,
            "currency": "USD"
        }
        assistant.index_document(sample)
        res = assistant.answer_query("Apex Logistics total")
        self.assertIn("1250", str(res["answer"]))

if __name__ == "__main__":
    unittest.main()