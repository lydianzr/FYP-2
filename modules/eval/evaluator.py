# modules/eval/evaluator.py
import time
from typing import Dict, Any
from modules.schema import CANONICAL_SCHEMA
from modules.eval.metrics import (
    compute_exact_match,
    compute_anls,
    compute_line_item_f1
)


class BenchmarkEvaluator:
    """Evaluates paradigm output against Canonical Ground Truth JSON."""

    def evaluate_document(
        self,
        pred_schema: Dict[str, Any],
        gt_schema: Dict[str, Any],
        latency_seconds: float = 0.0,
        cost_usd: float = 0.0
    ) -> Dict[str, Any]:
        """
        Runs comprehensive field-level, table-level, and efficiency evaluations.
        """
        field_results = {}
        exact_matches = []
        anls_scores = []

        scalar_fields = [
            k for k, v in CANONICAL_SCHEMA.items() 
            if k not in ["line_items", "has_signature", "has_stamp"]
        ]

        # 1. Scalar Field Evaluation
        for field in scalar_fields:
            pred_val = pred_schema.get(field)
            gt_val = gt_schema.get(field)

            em = compute_exact_match(pred_val, gt_val)
            anls = compute_anls(pred_val, gt_val)

            field_results[field] = {
                "pred": pred_val,
                "gt": gt_val,
                "exact_match": em,
                "anls": anls
            }

            exact_matches.append(em)
            anls_scores.append(anls)

        # 2. Boolean/Visual Field Evaluation
        for bool_field in ["has_signature", "has_stamp"]:
            pred_val = pred_schema.get(bool_field, False)
            gt_val = gt_schema.get(bool_field, False)
            em = 1.0 if bool(pred_val) == bool(gt_val) else 0.0
            
            field_results[bool_field] = {
                "pred": pred_val,
                "gt": gt_val,
                "exact_match": em,
                "anls": em
            }
            exact_matches.append(em)
            anls_scores.append(em)

        # 3. Structured Line-Item Table Evaluation
        pred_line_items = pred_schema.get("line_items", [])
        gt_line_items = gt_schema.get("line_items", [])
        precision, recall, line_item_f1 = compute_line_item_f1(pred_line_items, gt_line_items)

        # Aggregate Metrics
        macro_em = sum(exact_matches) / len(exact_matches) if exact_matches else 0.0
        macro_anls = sum(anls_scores) / len(anls_scores) if anls_scores else 0.0

        return {
            "document_id": gt_schema.get("document_id"),
            "macro_exact_match": round(macro_em, 4),
            "macro_anls": round(macro_anls, 4),
            "line_item_precision": round(precision, 4),
            "line_item_recall": round(recall, 4),
            "line_item_f1": round(line_item_f1, 4),
            "latency_seconds": round(latency_seconds, 4),
            "cost_usd": round(cost_usd, 6),
            "field_details": field_results
        }