# tests/test_extract_contract.py
import unittest
from modules.extract.base import BaseExtractor


class DummyExtractor(BaseExtractor):
    def extract(self, file_path: str):
        return self._clean_schema({"document_id": "TEST-001"})


class TestExtractContract(unittest.TestCase):

    def test_clean_schema_enforcement(self):
        extractor = DummyExtractor()
        res = extractor.extract("dummy.txt")
        self.assertEqual(res["document_id"], "TEST-001")
        self.assertIn("line_items", res)
        self.assertIn("has_signature", res)


if __name__ == "__main__":
    unittest.main()