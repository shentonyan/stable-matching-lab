"""Unilateral threshold deviations in the legacy reset-pool search model.

These diagnostics do not certify a Nash equilibrium. They retain the old
model's fresh iid opponents each period and fixed K, and test only stationary
threshold strategies, with all other agents using one common cutoff.
"""
from __future__ import annotations

import numpy as np

from .gs import deferred_acceptance
from .search import EventSimulator, _value


def focal_outcomes(sim: EventSimulator, common: float, deviation: float,
                   side: str) -> tuple[np.ndarray, np.ndarray]:
    """Per-event match indicator and u*indicator for agent 0 on one side.

    The focal agent alone uses `deviation`; all other agents use `common`.
    Unmatched utility is zero, not a missing observation. Utilities and tie
    orders come from the same simulator for paired policy comparisons.
    """
    if side not in ("left", "right"):
        raise ValueError("side must be left or right")
    if not np.isfinite(common) or not np.isfinite(deviation):
        raise ValueError("cutoffs must be finite")
    am = sim.UM > common
    aw = sim.UW > common
    if side == "left":
        am[:, 0, :] = sim.UM[:, 0, :] > deviation
    else:
        aw[:, 0, :] = sim.UW[:, 0, :] > deviation
    mutual = am & aw.transpose(0, 2, 1)
    matched, utility = np.zeros(sim.N), np.zeros(sim.N)
    for e in range(sim.N):
        pm = [[j for j in sim.order_m[e][i] if mutual[e, i, j]] for i in range(sim.K)]
        pw = [[i for i in sim.order_w[e][j] if mutual[e, i, j]] for j in range(sim.K)]
        match = deferred_acceptance(pm, pw)
        if side == "left":
            if match[0] >= 0:
                matched[e], utility[e] = 1, sim.UM[e, 0, match[0]]
        elif 0 in match:
            i = match.index(0)
            matched[e], utility[e] = 1, sim.UW[e, 0, i]
    return matched, utility


def renewal_value(outcomes, K: int, c: float, delta: float) -> float:
    """Legacy Bellman value of the focal stationary threshold policy."""
    if (not isinstance(K, (int, np.integer)) or isinstance(K, bool) or K < 1
            or not np.isfinite(c) or c < 0 or not 0 < delta < 1):
        raise ValueError("require K >= 1, c >= 0 and 0 < delta < 1")
    matched, utility = (np.asarray(x, dtype=float) for x in outcomes)
    if (matched.ndim != 1 or matched.size == 0 or utility.shape != matched.shape
            or not np.isfinite(matched).all() or not np.isfinite(utility).all()
            or not np.isin(matched, [0, 1]).all()
            or np.any(utility[matched == 0] != 0)):
        raise ValueError("need aligned finite indicators and utility, zero utility when unmatched")
    return float(_value(K, c, delta, np.mean(matched), np.mean(utility)))


def paired_value_interval(baseline, candidate, K, c, delta, seed=0, draws=1000):
    """Percentile bootstrap interval for a held-out difference in V.

    Resample whole independent events, keeping policies paired. Candidate
    selection must take place on separate training events before calling.
    This covers Monte Carlo uncertainty conditional on model parameters.
    """
    renewal_value(baseline, K, c, delta)
    renewal_value(candidate, K, c, delta)
    baseline = tuple(np.asarray(x) for x in baseline)
    candidate = tuple(np.asarray(x) for x in candidate)
    if (not isinstance(draws, (int, np.integer)) or isinstance(draws, bool) or draws < 1
            or len(baseline[0]) < 2 or len(candidate[0]) != len(baseline[0])):
        raise ValueError("need paired events and positive bootstrap draws")
    rng = np.random.default_rng(seed)
    gains = []
    for _ in range(draws):
        idx = rng.integers(len(baseline[0]), size=len(baseline[0]))
        b = tuple(x[idx] for x in baseline)
        d = tuple(x[idx] for x in candidate)
        gains.append(renewal_value(d, K, c, delta) - renewal_value(b, K, c, delta))
    return [float(x) for x in np.quantile(gains, [.025, .975])]
