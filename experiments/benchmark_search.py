"""Benchmark the batch kernel against the original scalar event loop.

Run from the repository root: python experiments/benchmark_search.py
Construction is excluded; all timings use identical draws and thresholds.
"""
import json
import platform
import sys
from pathlib import Path
from statistics import median
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from stablematch.gs import deferred_acceptance
from stablematch.search import EventSimulator, solve_threshold


def scalar_stats(sim, a):
    mutual = (sim.UM > a) & (sim.UW > a).transpose(0, 2, 1)
    pairs, total = 0, 0.0
    for e in range(sim.N):
        am = mutual[e]
        if not am.any():
            continue
        pm = [[w for w in sim.order_m[e][m] if am[m, w]] for m in range(sim.K)]
        pw = [[m for m in sim.order_w[e][w] if am[m, w]] for w in range(sim.K)]
        for m, w in enumerate(deferred_acceptance(pm, pw)):
            if w != -1:
                pairs += 1
                total += sim.UM[e, m, w] + sim.UW[e, w, m]
    return pairs / (sim.N * sim.K), total / (2 * sim.N * sim.K)


def timed(fn):
    samples = []
    for _ in range(3):
        start = perf_counter()
        result = [fn(a) for a in (-0.5, 0.0, 0.8)]
        samples.append(perf_counter() - start)
    return median(samples), result


if __name__ == "__main__":
    rows = []
    for K in (1, 8, 24, 48):
        sim = EventSimulator(K, 1000, 0)
        old, expected = timed(lambda a: scalar_stats(sim, a))
        new, actual = timed(sim)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
        rows.append(dict(K=K, events=sim.N, scalar_seconds=old,
                         batch_seconds=new, speedup=old / new))
    sim = EventSimulator(24, 1000, 0)
    start = perf_counter()
    expected_eq = solve_threshold(lambda a: scalar_stats(sim, a), 24, 0.1, 0.9)
    scalar_seconds = perf_counter() - start
    start = perf_counter()
    actual_eq = solve_threshold(sim, 24, 0.1, 0.9)
    batch_seconds = perf_counter() - start
    for key, value in vars(expected_eq).items():
        np.testing.assert_allclose(vars(actual_eq)[key], value, rtol=1e-12, atol=1e-12)
    print(json.dumps(dict(python=platform.python_version(), numpy=np.__version__,
                         timings=rows, equilibrium=dict(K=24, events=1000,
                         c=0.1, delta=0.9, scalar_seconds=scalar_seconds,
                         batch_seconds=batch_seconds,
                         speedup=scalar_seconds / batch_seconds,
                         threshold=actual_eq.threshold)), indent=2))
