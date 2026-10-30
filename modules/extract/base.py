"""The frozen extraction output contract. Every condition C1..C6 returns this.

FIX #2: extractors used to return a flat dict with no confidence, no bbox, no
latency and no cost, while evaluator.evaluate_document() expected latency and
cost as arguments that nobody produced. Routing (RO2) needs confidence; the
efficiency axis of the comparison needs latency and cost; field-level citations
(RO3) need bbox.

FIX #4: `except Exception: return get_empty_schema()` turned an API failure into
"the model extracted nothing" -- a 0.0 score indistinguishable from a genuine
model weakness. run() now records the error and the runner reports failures as
a separate column instead of silently averaging them into the scores.
"""
from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

from modules.parsing import parse_bool, parse_number, parse_text
from modules.schema import BY_NAME, FIELD_NAMES, LIST_FIELDS, get_empty_schema

CONTRACT_VERSION = "1.0"


@dataclass
class FieldValue:
    """One extracted field. `confidence` semantics differ per engine and are
    documented in docs/confidence_provenance.md -- they are comparable only
    after per-engine calibration, which is why routing uses rank, not raw value."""
    value: Any = None
    confidence: float | None = None
    bbox: list[float] | None = None   # [x0, y0, x1, y1] in page pixels
    page: int | None = None
    source: str | None = None         # "regex" | "llm" | "mllm" | "fused:<engine>"


@dataclass
class ExtractionResult:
    doc_id: str
    condition: str                    # "C1".."C6"
    model_version: str
    prompt_version: str = "none"
    fields: dict[str, FieldValue] = field(default_factory=dict)
    latency_s: float = 0.0
    cost_usd: float = 0.0
    in_tokens: int = 0
    out_tokens: int = 0
    n_pages: int = 1
    error: str | None = None          # None == the call succeeded
    raw_response: str | None = None
    contract_version: str = CONTRACT_VERSION

    @property
    def ok(self) -> bool:
        return self.error is None

    def values(self) -> dict[str, Any]:
        """Plain canonical dict, for the evaluator and for indexing."""
        out = get_empty_schema()
        for k, fv in self.fields.items():
            if k in out:
                out[k] = fv.value
        return out

    def confidences(self) -> dict[str, float | None]:
        return {k: fv.confidence for k, fv in self.fields.items()}

    def mean_confidence(self) -> float | None:
        vals = [fv.confidence for fv in self.fields.values()
                if fv.confidence is not None and fv.value is not None]
        return sum(vals) / len(vals) if vals else None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fields"] = {k: asdict(v) for k, v in self.fields.items()}
        return d


class BaseExtractor(ABC):
    """Subclasses implement _extract(). run() owns timing, error capture and
    contract enforcement so no subclass can get those wrong."""

    condition: str = "C0"
    model_version: str = "unknown"
    prompt_version: str = "none"

    @abstractmethod
    def _extract(self, file_path: str) -> tuple[dict[str, FieldValue], dict[str, Any]]:
        """Returns (fields, meta). meta may carry raw_response, in_tokens,
        out_tokens, cost_usd, n_pages. Raise on failure -- do not swallow."""

    def run(self, file_path: str, doc_id: str | None = None) -> ExtractionResult:
        doc_id = doc_id or _stem(file_path)
        res = ExtractionResult(
            doc_id=doc_id,
            condition=self.condition,
            model_version=self.model_version,
            prompt_version=self.prompt_version,
        )
        t0 = time.perf_counter()
        try:
            fields, meta = self._extract(file_path)
            res.fields = self._coerce(fields)
            res.raw_response = meta.get("raw_response")
            res.in_tokens = int(meta.get("in_tokens", 0))
            res.out_tokens = int(meta.get("out_tokens", 0))
            res.cost_usd = float(meta.get("cost_usd", 0.0))
            res.n_pages = int(meta.get("n_pages", 1))
        except Exception as exc:                      # noqa: BLE001 -- recorded, not hidden
            res.error = f"{type(exc).__name__}: {exc}"
            res.raw_response = traceback.format_exc(limit=3)
            res.fields = {}
        res.latency_s = round(time.perf_counter() - t0, 4)
        return res

    # Back-compat shim so existing notebooks calling .extract() still work.
    def extract(self, file_path: str) -> dict[str, Any]:
        return self.run(file_path).values()

    @staticmethod
    def _coerce(fields: dict[str, Any]) -> dict[str, FieldValue]:
        """Drop unknown keys, wrap bare values, cast to the declared dtype.
        This is what makes the contract test pass for all six conditions."""
        out: dict[str, FieldValue] = {}
        for name in FIELD_NAMES:
            if name not in fields:
                continue
            raw = fields[name]
            fv = raw if isinstance(raw, FieldValue) else FieldValue(value=raw)
            fv.value = _cast(name, fv.value)
            if fv.confidence is not None:
                fv.confidence = max(0.0, min(1.0, float(fv.confidence)))
            out[name] = fv
        return out


def _cast(name: str, v: Any) -> Any:
    """Uses the same primitives as the evaluator (modules/parsing.py) so a value
    can never be parsed one way here and another way at scoring time."""
    spec = BY_NAME[name]
    if v is None:
        return None
    if spec.dtype == "float":
        return parse_number(v)
    if spec.dtype == "bool":
        return parse_bool(v)
    if spec.dtype == "list":
        return v if isinstance(v, list) else []
    return parse_text(v)


def _stem(path: str) -> str:
    import os
    return os.path.splitext(os.path.basename(path))[0]
