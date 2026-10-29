"""Bootstrap confidence intervals and McNemar's test."""
import math
import random


def bootstrap_ci(values: list[float], n_boot: int = 10_000, alpha: float = 0.05, seed: int = 42):
    """Percentile bootstrap CI of the mean. Returns (mean, lo, hi)."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(n_boot))
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return sum(values) / n, lo, hi


def mcnemar_exact(correct_a: list[bool], correct_b: list[bool]) -> float:
    """Two-sided exact McNemar p-value on paired correctness vectors."""
    b = sum(1 for x, y in zip(correct_a, correct_b) if x and not y)
    c = sum(1 for x, y in zip(correct_a, correct_b) if not x and y)
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * p)
