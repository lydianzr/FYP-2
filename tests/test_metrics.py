# tests/test_metrics.py
import unittest
from modules.eval.metrics import (
    compute_exact_match,
    compute_anls,
    compute_line_item_f1
)


class TestMetrics(unittest.TestCase):

    def test_exact_match(self):
        self.assertEqual(compute_exact_match("INV-100", "inv-100"), 1.0)
        self.assertEqual(compute_exact_match("INV-100", "INV-200"), 0.0)
        self.assertEqual(compute_exact_match(500.0, 500.00001), 1.0)

    def test_anls(self):
        self.assertGreater(compute_anls("Main Street", "Main Street."), 0.8)
        self.assertEqual(compute_anls("Completely Different", "Anything Else"), 0.0)

    def test_line_item_f1(self):
        pred = [{"description": "Port Handling", "amount": 100.0}]
        gt = [{"description": "Port Handling", "amount": 100.0}]
        p, r, f1 = compute_line_item_f1(pred, gt)
        self.assertEqual(f1, 1.0)


if __name__ == "__main__":
    unittest.main()