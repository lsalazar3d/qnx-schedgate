from __future__ import annotations

import math

from .model import ThreadSpec


def utilization(threads: list[ThreadSpec]) -> float:
    total = 0.0
    for thread in threads:
        if thread.period_ns <= 0:
            continue
        total += thread.wcet_ns / thread.period_ns
    return total


def liu_layland_bound(n: int) -> float:
    if n <= 0:
        return 1.0
    return n * (2 ** (1 / n) - 1)


def hyperbolic_bound_ok(threads: list[ThreadSpec]) -> bool:
    """Exact hyperbolic bound: product (Ui + 1) <= 2."""
    periodic = [t for t in threads if t.period_ns > 0 and t.wcet_ns > 0]
    if not periodic:
        return True
    product = 1.0
    for thread in periodic:
        product *= 1.0 + (thread.wcet_ns / thread.period_ns)
    return product <= 2.0 + 1e-12


def rate_monotonic_ok(threads: list[ThreadSpec]) -> tuple[bool | None, float, float]:
    periodic = [t for t in threads if t.period_ns > 0]
    if not periodic:
        return None, 0.0, 1.0
    u = utilization(periodic)
    bound = liu_layland_bound(len(periodic))
    if u <= bound:
        return True, u, bound
    # Liu-Layland is sufficient but not necessary; fall back to hyperbolic.
    if hyperbolic_bound_ok(periodic):
        return True, u, bound
    return False, u, bound
