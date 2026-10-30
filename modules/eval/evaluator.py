"""Document- and corpus-level evaluation.

Takes ExtractionResult objects (not bare dicts), so latency, cost and API
failures are carried through instead of being arguments nobody supplies. A
failed extraction is reported in `n_errors` and excluded from the score means,
with the failure rate itself reported as a result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from modules.eval import metrics as M
from modules.eval.normalise import norm_field
from modules.extract.base import ExtractionResult
from modules.schema import (BOOL_FIELDS, FIELD_NAMES, LIST_FIELDS, SCALAR_FIELDS,
                            fields_for_task)

TASK_A = fields_for_task("A")
TASK_B = fields_for_task("B")
TASK_C = fields_for_task("C")


@dataclass
class DocScore:
    doc_id: str
    condition: str
    doc_type: str | None = None
    outcomes: dict[str, M.Outcome] = field(default_factory=dict)
    counts_a: M.Counts = field(default_factory=M.Counts)
    counts_c: M.Counts = field(default_factory=M.Counts)
    line_item_p: float = 0.0
    line_item_r: float = 0.0
    line_item_f1: float = 0.0
    anls: float | None = None
    cer: float | None = None
    latency_s: float = 0.0
    cost_usd: float = 0.0
    error: str | None = None
    per_field: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def counts(self) -> M.Counts:
        return self.counts_a + self.counts_c

    def correct_vector(self, fields: Iterable[str] | None = None) -> list[bool]:
        """Per-field correctness, for McNemar. TN counts as correct (the model
        rightly abstained); SKIPPED is excluded by the caller via field list."""
        names = list(fields or [n for n in FIELD_NAMES if n not in LIST_FIELDS])
        return [self.outcomes.get(n) in (M.Outcome.TP, M.Outcome.TN) for n in names]

    def as_row(self) -> dict[str, Any]:
        c = self.counts
        return {"doc_id": self.doc_id, "condition": self.condition,
                "doc_type": self.doc_type, "ok": self.ok, "error": self.error,
                "field_precision": c.precision, "field_recall": c.recall,
                "field_f1": c.f1, "false_answer_rate": c.false_answer_rate,
                "task_a_f1": self.counts_a.f1, "task_c_accuracy": self.counts_c.accuracy,
                "line_item_f1": self.line_item_f1, "anls": self.anls, "cer": self.cer,
                "latency_s": self.latency_s, "cost_usd": self.cost_usd,
                **{f"n_{k}": v for k, v in c.as_dict().items() if isinstance(v, int)}}


class BenchmarkEvaluator:
    def __init__(self, *, handwritten_fields: tuple[str, ...] = ()) -> None:
        # Task D (stretch): fields known to be handwritten, scored with CER.
        self.handwritten_fields = handwritten_fields

    def evaluate_document(self, result: ExtractionResult, gt: dict[str, Any],
                          doc_type: str | None = None) -> DocScore:
        score = DocScore(doc_id=result.doc_id, condition=result.condition,
                         doc_type=doc_type or gt.get("document_type"),
                         latency_s=result.latency_s, cost_usd=result.cost_usd,
                         error=result.error)
        if not result.ok:
            # No scores at all. Averaging a failed API call as 0.0 would
            # misattribute an infrastructure fault to the model.
            return score

        pred = result.values()
        anls_vals: list[float] = []
        cer_vals: list[float] = []

        for name in FIELD_NAMES:
            if name in LIST_FIELDS:
                continue
            attempted = name in result.fields
            p_raw = pred.get(name)
            p, g = norm_field(name, p_raw), norm_field(name, gt.get(name))
            if not attempted and g is not None:
                outcome = M.Outcome.FN            # not attempted but expected
            elif not attempted:
                outcome = M.Outcome.TN
            else:
                outcome = M.classify(name, p, g, normalised=True)
            score.outcomes[name] = outcome

            bucket = score.counts_c if name in TASK_C else score.counts_a
            bucket.add(outcome)

            if name in SCALAR_FIELDS:
                a = M.compute_anls(p, g)
                if a is not None:
                    anls_vals.append(a)
            if name in self.handwritten_fields:
                c = M.compute_cer(p_raw, gt.get(name))
                if c is not None:
                    cer_vals.append(c)

            fv = result.fields.get(name)
            score.per_field[name] = {
                "pred": p_raw, "pred_norm": p, "gt": gt.get(name), "gt_norm": g,
                "outcome": outcome.value,
                "confidence": getattr(fv, "confidence", None),
                "bbox": getattr(fv, "bbox", None),
                "source": getattr(fv, "source", None),
            }

        p, r, f1 = M.compute_line_item_f1(pred.get("line_items"), gt.get("line_items"))
        score.line_item_p, score.line_item_r, score.line_item_f1 = p, r, f1
        score.anls = M.macro(anls_vals)
        score.cer = M.macro(cer_vals)
        return score

    # ------------------------------------------------------------ corpus level
    def aggregate(self, scores: list[DocScore]) -> dict[str, Any]:
        ok = [s for s in scores if s.ok]
        n, n_ok = len(scores), len(ok)
        micro_all = M.micro(s.counts for s in ok)
        return {
            "n_docs": n,
            "n_scored": n_ok,
            "n_errors": n - n_ok,
            "error_rate": (n - n_ok) / n if n else None,
            # Micro: pooled over all fields. The headline RO1 number.
            "micro_precision": micro_all.precision,
            "micro_recall": micro_all.recall,
            "micro_f1": micro_all.f1,
            "false_answer_rate": micro_all.false_answer_rate,
            # Macro: mean of per-document F1. Reported alongside, because micro
            # is dominated by documents that happen to have more filled fields.
            "macro_f1": M.macro([s.counts.f1 for s in ok]),
            "task_a_micro_f1": M.micro(s.counts_a for s in ok).f1,
            "task_b_line_item_f1": M.macro([s.line_item_f1 for s in ok]),
            "task_c_accuracy": M.micro(s.counts_c for s in ok).accuracy,
            "anls": M.macro([s.anls for s in ok]),
            "cer": M.macro([s.cer for s in ok]),
            "median_latency_s": _median([s.latency_s for s in ok]),
            "mean_latency_s": M.macro([s.latency_s for s in ok]),
            "total_cost_usd": round(sum(s.cost_usd for s in scores), 4),
            "cost_per_doc_usd": round(sum(s.cost_usd for s in scores) / n, 6) if n else None,
            "counts": micro_all.as_dict(),
        }

    def per_field_table(self, scores: list[DocScore]) -> dict[str, dict[str, Any]]:
        """Which fields are hard. Drives the error-analysis chapter."""
        out: dict[str, dict[str, Any]] = {}
        for name in FIELD_NAMES:
            if name in LIST_FIELDS:
                continue
            c = M.Counts()
            for s in scores:
                if s.ok and name in s.outcomes:
                    c.add(s.outcomes[name])
            out[name] = c.as_dict()
        return out

    def per_doc_type_table(self, scores: list[DocScore]) -> dict[str, dict[str, Any]]:
        """The input to routing: per document type, how did this condition do."""
        groups: dict[str, list[DocScore]] = {}
        for s in scores:
            groups.setdefault(str(s.doc_type or "unknown"), []).append(s)
        return {k: self.aggregate(v) for k, v in groups.items()}


def _median(vals: list[float]) -> float | None:
    if not vals:
        return None
    v = sorted(vals)
    mid = len(v) // 2
    return v[mid] if len(v) % 2 else (v[mid - 1] + v[mid]) / 2
