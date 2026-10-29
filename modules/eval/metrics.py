# modules/eval/metrics.py
import re
from typing import Any, Dict, List, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein distance between two strings using DP."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_anls(pred: Any, gt: Any, threshold: float = 0.5) -> float:
    """
    Computes Average Normalized Levenshtein Similarity (ANLS).
    
    Formula:
    Normalized Distance: NL(s_pred, s_gt) = d(s_pred, s_gt) / max(|s_pred|, |s_gt|)
    ANLS Score = 1 - NL(s_pred, s_gt) if NL < threshold else 0.0
    """
    if gt is None and pred is None:
        return 1.0
    if gt is None or pred is None:
        return 0.0

    s_pred = str(pred).strip().lower()
    s_gt = str(gt).strip().lower()

    if s_pred == s_gt:
        return 1.0

    max_len = max(len(s_pred), len(s_gt))
    if max_len == 0:
        return 1.0

    dist = levenshtein_distance(s_pred, s_gt)
    norm_dist = dist / max_len

    return (1.0 - norm_dist) if norm_dist < threshold else 0.0


def compute_exact_match(pred: Any, gt: Any) -> float:
    """Evaluates strict exact match after string normalization."""
    if gt is None and pred is None:
        return 1.0
    if gt is None or pred is None:
        return 0.0

    # Numeric comparison
    if isinstance(gt, (int, float)) or isinstance(pred, (int, float)):
        try:
            return 1.0 if abs(float(pred) - float(gt)) < 1e-4 else 0.0
        except (ValueError, TypeError):
            return 0.0

    s_pred = str(pred).strip().lower()
    s_gt = str(gt).strip().lower()
    return 1.0 if s_pred == s_gt else 0.0


def compute_line_item_f1(pred_items: List[Dict], gt_items: List[Dict]) -> Tuple[float, float, float]:
    """
    Computes Precision, Recall, and F1-Score for extracted table line items.
    """
    if not gt_items and not pred_items:
        return 1.0, 1.0, 1.0
    if not gt_items or not pred_items:
        return 0.0, 0.0, 0.0

    matched = 0
    gt_matched_indices = set()

    for pred in pred_items:
        best_match_idx = None
        best_score = 0.0

        for idx, gt in enumerate(gt_items):
            if idx in gt_matched_indices:
                continue

            # Compare key-value overlap in line item dict
            scores = []
            for key in gt.keys():
                gt_val = gt.get(key)
                pred_val = pred.get(key)
                scores.append(compute_anls(pred_val, gt_val))

            avg_score = sum(scores) / len(scores) if scores else 0.0
            if avg_score > best_score and avg_score >= 0.7:
                best_score = avg_score
                best_match_idx = idx

        if best_match_idx is not None:
            matched += 1
            gt_matched_indices.add(best_match_idx)

    precision = matched / len(pred_items) if pred_items else 0.0
    recall = matched / len(gt_items) if gt_items else 0.0
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    return precision, recall, f1