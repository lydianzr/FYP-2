"""Bootstrap confidence intervals, McNemar's exact test, and the pre-declared
significance rule.

Resampling is over DOCUMENTS, never over fields: fields within one document are
correlated, so resampling fields would give intervals that are far too narrow.
`paired_bootstrap_diff` resamples the same document indices for both conditions,
which is the correct interval for a difference between two systems evaluated on
the same test set.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence

from modules import config

N_BOOT = 1000      # as pre-registered in the proposal; 10k adds precision you
                   # cannot use and multiplies the runtime of every table


@dataclass
class CI:
    point: float
    lo: float
    hi: float
    n: int
    n_boot: int = N_BOOT

    def __str__(self) -> str:
        return f"{self.point:.3f} [{self.lo:.3f}, {self.hi:.3f}]"

    def as_dict(self) -> dict:
        return {"value": self.point, "ci_lo": self.lo, "ci_hi": self.hi,
                "n": self.n, "n_boot": self.n_boot}


def bootstrap_ci(values: Sequence[float], n_boot: int = N_BOOT, alpha: float = 0.05,
                 seed: int = config.SEED) -> CI:
    """Percentile bootstrap CI of the mean of per-document scores."""
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0:
        raise ValueError("bootstrap_ci: no values")
    point = sum(vals) / n
    if n == 1:
        return CI(point, point, point, n, n_boot)
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(vals, k=n)) / n for _ in range(n_boot))
    return CI(point, means[int(alpha / 2 * n_boot)],
              means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))], n, n_boot)


def bootstrap_ci_fn(items: Sequence, stat: Callable[[Sequence], float],
                    n_boot: int = N_BOOT, alpha: float = 0.05,
                    seed: int = config.SEED) -> CI:
    """CI for a statistic that is NOT a mean -- e.g. micro-F1, which must be
    recomputed from pooled counts on each resample rather than averaged."""
    n = len(items)
    if n == 0:
        raise ValueError("bootstrap_ci_fn: no items")
    point = stat(items)
    rng = random.Random(seed)
    boots = sorted(stat(rng.choices(items, k=n)) for _ in range(n_boot))
    return CI(point, boots[int(alpha / 2 * n_boot)],
              boots[min(n_boot - 1, int((1 - alpha / 2) * n_boot))], n, n_boot)


def paired_bootstrap_diff(a: Sequence[float], b: Sequence[float],
                          n_boot: int = N_BOOT, alpha: float = 0.05,
                          seed: int = config.SEED) -> CI:
    """CI for mean(a) - mean(b) on the same documents. If it excludes 0, the
    difference is significant at alpha."""
    if len(a) != len(b):
        raise ValueError(f"paired_bootstrap_diff: unequal lengths {len(a)} vs {len(b)}")
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    if n == 0:
        raise ValueError("paired_bootstrap_diff: no complete pairs")
    point = sum(x - y for x, y in pairs) / n
    rng = random.Random(seed)
    diffs = []
    idx = range(n)
    for _ in range(n_boot):
        pick = [pairs[rng.choice(idx)] for _ in idx]
        diffs.append(sum(x - y for x, y in pick) / n)
    diffs.sort()
    return CI(point, diffs[int(alpha / 2 * n_boot)],
              diffs[min(n_boot - 1, int((1 - alpha / 2) * n_boot))], n, n_boot)


def mcnemar_exact(correct_a: Sequence[bool], correct_b: Sequence[bool]) -> dict:
    """Two-sided exact McNemar on paired correctness vectors."""
    if len(correct_a) != len(correct_b):
        raise ValueError("mcnemar_exact: unequal lengths")
    b = sum(1 for x, y in zip(correct_a, correct_b) if x and not y)
    c = sum(1 for x, y in zip(correct_a, correct_b) if not x and y)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "n_discordant": 0, "p_value": 1.0}
    k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"b": b, "c": c, "n_discordant": n, "p_value": p}


SIGNIFICANCE_RULE = (
    "A difference is reported as significant only if the paired bootstrap CI of "
    "the difference excludes zero AND McNemar's exact p < 0.05. Declared before "
    "any results were produced; applied identically to every comparison."
)


def is_significant(diff_ci: CI, mcnemar: dict, alpha: float = 0.05) -> bool:
    ci_excludes_zero = (diff_ci.lo > 0) or (diff_ci.hi < 0)
    return bool(ci_excludes_zero and mcnemar["p_value"] < alpha)


def compare(name_a: str, scores_a: Sequence[float], correct_a: Sequence[bool],
            name_b: str, scores_b: Sequence[float], correct_b: Sequence[bool]) -> dict:
    """One row of the pairwise comparison table."""
    diff = paired_bootstrap_diff(scores_a, scores_b)
    mc = mcnemar_exact(correct_a, correct_b)
    return {"condition_a": name_a, "condition_b": name_b,
            "mean_a": sum(scores_a) / len(scores_a),
            "mean_b": sum(scores_b) / len(scores_b),
            "diff": diff.point, "diff_ci_lo": diff.lo, "diff_ci_hi": diff.hi,
            "mcnemar_b": mc["b"], "mcnemar_c": mc["c"], "p_value": mc["p_value"],
            "significant": is_significant(diff, mc)}
