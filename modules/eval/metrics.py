from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from modules.eval.normalise import norm_field, norm_line_item
from modules.schema import BY_NAME, LINE_ITEM_NUMERIC


class Outcome(str, Enum):
    TP = "TP"                        # gt has a value, prediction matches
    FP_HALLUCINATION = "FP_HALL"     # gt is null, prediction invented a value
    FP_WRONG = "FP_WRONG"            # gt has a value, prediction has a different one
    FN = "FN"                        # gt has a value, prediction is null
    TN = "TN"                        # both null: correct abstention, excluded from F1
    SKIPPED = "SKIP"                 # field not attempted by this condition


NUMERIC_TOL = 0.01      # money/weight: within one cent / 10 g counts as a match


def classify(name: str, pred: Any, gt: Any, *, normalised: bool = False) -> Outcome:
    p = pred if normalised else norm_field(name, pred)
    g = gt if normalised else norm_field(name, gt)
    if g is None and p is None:
        return Outcome.TN
    if g is None:
        return Outcome.FP_HALLUCINATION
    if p is None:
        return Outcome.FN
    return Outcome.TP if _match(name, p, g) else Outcome.FP_WRONG


def _match(name: str, p: Any, g: Any) -> bool:
    spec = BY_NAME.get(name)
    if spec and spec.dtype == "bool":
        return bool(p) == bool(g)
    if isinstance(p, (int, float)) and isinstance(g, (int, float)):
        return abs(float(p) - float(g)) <= NUMERIC_TOL
    return str(p) == str(g)


@dataclass
class Counts:
    tp: int = 0
    fp_hall: int = 0
    fp_wrong: int = 0
    fn: int = 0
    tn: int = 0
    skipped: int = 0

    def add(self, o: Outcome, k: int = 1) -> None:
        setattr(self, _ATTR[o], getattr(self, _ATTR[o]) + k)

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(*(getattr(self, a) + getattr(other, a) for a in
                        ("tp", "fp_hall", "fp_wrong", "fn", "tn", "skipped")))

    # A wrong value is one false positive AND one false negative: the correct
    # value was not produced, and an incorrect one was.
    @property
    def fp(self) -> int:
        return self.fp_hall + self.fp_wrong

    @property
    def fn_total(self) -> int:
        return self.fn + self.fp_wrong

    @property
    def n_gt_present(self) -> int:
        return self.tp + self.fp_wrong + self.fn

    @property
    def n_gt_null(self) -> int:
        return self.tn + self.fp_hall

    @property
    def precision(self) -> float | None:
        """None only when there is nothing to score at all (no predictions and
        no ground-truth values). A model that predicted nothing on a document
        that *does* have values scores 0.0, not None -- otherwise producing
        nothing would quietly remove the document from the mean."""
        d = self.tp + self.fp
        if d == 0:
            return None if self.n_gt_present == 0 else 0.0
        return self.tp / d

    @property
    def recall(self) -> float | None:
        d = self.tp + self.fn_total
        return None if d == 0 else self.tp / d      # d == 0: no GT values exist

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None and r is None:
            return None                             # all true negatives
        p = 0.0 if p is None else p
        r = 0.0 if r is None else r
        return 0.0 if p + r == 0 else 2 * p * r / (p + r)

    @property
    def false_answer_rate(self) -> float | None:
        """Corrected FAR. Denominator is the GT-null fields only, which is what
        makes it independent of recall."""
        d = self.n_gt_null
        return None if d == 0 else self.fp_hall / d

    @property
    def accuracy(self) -> float | None:
        d = self.tp + self.tn + self.fp + self.fn
        return None if d == 0 else (self.tp + self.tn) / d

    def as_dict(self) -> dict[str, Any]:
        return {"tp": self.tp, "fp_hallucination": self.fp_hall,
                "fp_wrong_value": self.fp_wrong, "fn": self.fn, "tn": self.tn,
                "skipped": self.skipped,
                "precision": self.precision, "recall": self.recall, "f1": self.f1,
                "false_answer_rate": self.false_answer_rate,
                "n_gt_present": self.n_gt_present, "n_gt_null": self.n_gt_null}


_ATTR = {Outcome.TP: "tp", Outcome.FP_HALLUCINATION: "fp_hall",
         Outcome.FP_WRONG: "fp_wrong", Outcome.FN: "fn", Outcome.TN: "tn",
         Outcome.SKIPPED: "skipped"}


def counts_from(outcomes: Iterable[Outcome]) -> Counts:
    c = Counts()
    for o in outcomes:
        c.add(o)
    return c


# ------------------------------------------------------------ string distance
def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        cur = [i + 1]
        for j, c2 in enumerate(s2):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (c1 != c2)))
        prev = cur
    return prev[-1]


def compute_anls(pred: Any, gt: Any, threshold: float = 0.5) -> float | None:
    """ANLS, reported as a secondary metric only. Returns None when both sides
    are null so the caller excludes the field instead of scoring it 1.0."""
    if gt is None and pred is None:
        return None
    if gt is None or pred is None:
        return 0.0
    a, b = str(pred).strip().lower(), str(gt).strip().lower()
    if a == b:
        return 1.0
    m = max(len(a), len(b))
    if m == 0:
        return None
    nl = levenshtein_distance(a, b) / m
    return (1.0 - nl) if nl < threshold else 0.0


def compute_cer(pred: Any, gt: Any) -> float | None:
    """Character error rate, for task D (handwritten). Capped at 1.0 so a
    runaway hallucination cannot produce a CER of 12 and distort the mean."""
    if gt is None:
        return None
    g = str(gt)
    if not g:
        return None
    p = "" if pred is None else str(pred)
    return min(1.0, levenshtein_distance(p, g) / len(g))


# -------------------------------------------------------- task B: line items
def compute_line_item_f1(pred_items: list[dict] | None,
                         gt_items: list[dict] | None,
                         threshold: float = 0.7) -> tuple[float, float, float]:
    """Greedy best-match on normalised rows. Precision/recall/F1 over rows.

    Note the empty-vs-empty case returns (1,1,1): for tables, "no table and
    none predicted" is a genuine success, unlike the scalar-field case.
    """
    pred = [norm_line_item(r) for r in (pred_items or []) if isinstance(r, dict)]
    gt = [norm_line_item(r) for r in (gt_items or []) if isinstance(r, dict)]
    if not gt and not pred:
        return 1.0, 1.0, 1.0
    if not gt or not pred:
        return 0.0, 0.0, 0.0

    taken: set[int] = set()
    matched = 0
    for p in pred:
        best_i, best_s = None, 0.0
        for i, g in enumerate(gt):
            if i in taken:
                continue
            s = _row_similarity(p, g)
            if s > best_s and s >= threshold:
                best_i, best_s = i, s
        if best_i is not None:
            taken.add(best_i)
            matched += 1

    precision = matched / len(pred)
    recall = matched / len(gt)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def _row_similarity(p: dict, g: dict) -> float:
    scores: list[float] = []
    for k, gv in g.items():
        if gv is None:
            continue
        pv = p.get(k)
        if k in LINE_ITEM_NUMERIC:
            if pv is None:
                scores.append(0.0)
            else:
                scores.append(1.0 if abs(float(pv) - float(gv)) <= NUMERIC_TOL else 0.0)
        else:
            s = compute_anls(pv, gv)
            scores.append(0.0 if s is None else s)
    return sum(scores) / len(scores) if scores else 0.0


# -------------------------------------------------------- aggregate helpers
def micro(counts: Iterable[Counts]) -> Counts:
    total = Counts()
    for c in counts:
        total = total + c
    return total


def macro(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def outcome_histogram(outcomes: Iterable[Outcome]) -> dict[str, int]:
    return dict(Counter(o.value for o in outcomes))
