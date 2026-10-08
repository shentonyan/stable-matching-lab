"""Costly two-sided search with batch dating and an endogenous outside option.

Environment (stationary, symmetric)
-----------------------------------
* Each period every single person attends an event with K men and K women.
  Everyone meets everyone of the other sex, so each person has K dates and
  pays ``c`` per date (cost K*c per period).
* For each ordered pair the utility u is an independent N(0, 1) draw that is
  revealed only on the date. Utility is not transferable.
* A pair can form only if both utilities are at least the threshold ``a``.
  Within an event the mutually acceptable pairs are matched by men-proposing
  deferred acceptance on the true utilities (stable within the event).
* A match is permanent: the person gets flow utility u in every later period,
  discounted by ``delta``. Matched people leave and are replaced by fresh
  singles, so the pool is stationary and identically distributed.

Equilibrium
-----------
Let V be the value of being single at the start of a period. With p the
per-period probability of being matched and g = E[u * 1{matched}],

    V = -c*K + delta * ( g / (1 - delta) + (1 - p) * V ).

An agent accepts a partner iff u / (1 - delta) >= V, i.e. u >= a with
a = (1 - delta) * V. The outside option is therefore not a parameter: the
threshold ``a`` is the fixed point of a = (1 - delta) * V(a), where p and g
depend on everyone using the same threshold ``a``.

Special cases with closed forms are used as checks:
* K = 1, two-sided: p = q^2, g = q * phi(a), q = 1 - Phi(a).
* one-sided benchmark (every partner accepts anyone, you pick the best of
  your K dates): p = 1 - Phi(a)^K, g = E[max * 1{max >= a}].

Limits: all agents are identical ex ante and utilities are iid, so there is
no sorting or heterogeneity; agents report truthfully inside an event.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, pi, sqrt

import numpy as np

from .gs import deferred_acceptance


def phi(x: float) -> float:
    return exp(-x * x / 2) / sqrt(2 * pi)


def Phi(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


@dataclass(frozen=True)
class Equilibrium:
    K: int
    c: float
    delta: float
    threshold: float  # a = outside option = (1 - delta) * V
    value: float  # V
    match_prob: float  # p, per person per period
    partner_utility: float  # E[u | matched]
    periods_to_match: float  # 1 / p
    dates_to_match: float  # K / p


def _value(K: int, c: float, delta: float, p: float, g: float) -> float:
    return (-c * K + delta * g / (1 - delta)) / (1 - delta * (1 - p))


def solve_threshold(stats, K: int, c: float, delta: float,
                    lo: float = -8.0, hi: float = 8.0, tol: float = 1e-4) -> Equilibrium:
    """Bisection on h(a) = (1 - delta) V(a) - a, with (p, g) = stats(a)."""

    def h(a: float) -> float:
        p, g = stats(a)
        return (1 - delta) * _value(K, c, delta, p, g) - a

    if h(lo) < 0 or h(hi) > 0:
        raise RuntimeError("no sign change in the search bracket")
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if h(mid) > 0:
            lo = mid
        else:
            hi = mid
    a = (lo + hi) / 2
    p, g = stats(a)
    V = _value(K, c, delta, p, g)
    return Equilibrium(
        K=K, c=c, delta=delta, threshold=a, value=V, match_prob=p,
        partner_utility=g / p if p > 0 else float("nan"),
        periods_to_match=1 / p if p > 0 else float("inf"),
        dates_to_match=K / p if p > 0 else float("inf"),
    )


def stats_two_sided_k1(a: float):
    q = 1 - Phi(a)
    return q * q, q * phi(a)


def make_stats_one_sided(K: int):
    xs = np.linspace(-8, 8, 16001)
    cdf = 0.5 * (1 + np.vectorize(erf)(xs / sqrt(2)))
    pdf = np.exp(-xs ** 2 / 2) / sqrt(2 * pi)
    fmax = K * pdf * cdf ** (K - 1)
    integrand = xs * fmax
    dx = xs[1] - xs[0]
    # tail[i] = integral from xs[i] to +inf of x f_max(x) dx (trapezoid)
    seg = 0.5 * (integrand[1:] + integrand[:-1]) * dx
    tail = np.concatenate([np.cumsum(seg[::-1])[::-1], [0.0]])

    def stats(a: float):
        return 1 - Phi(a) ** K, float(np.interp(a, xs, tail))

    return stats


class EventSimulator:
    """Monte Carlo (p, g) for K-vs-K events at a common threshold.

    Utilities are drawn once (common random numbers) so that p(a), g(a) are
    smooth enough for bisection across thresholds.
    """

    def __init__(self, K: int, n_events: int, seed: int):
        rng = np.random.default_rng(seed)
        self.K, self.N = K, n_events
        self.UM = rng.standard_normal((n_events, K, K))  # [e, man, woman]
        self.UW = rng.standard_normal((n_events, K, K))  # [e, woman, man]
        self.order_m = np.argsort(-self.UM, axis=2).tolist()
        self.order_w = np.argsort(-self.UW, axis=2).tolist()

    def __call__(self, a: float):
        K, N = self.K, self.N
        mutual = (self.UM > a) & np.transpose(self.UW > a, (0, 2, 1))
        pairs, total_u = 0, 0.0
        for e in range(N):
            am = mutual[e]
            if not am.any():
                continue
            pm = [[j for j in self.order_m[e][i] if am[i, j]] for i in range(K)]
            pw = [[i for i in self.order_w[e][j] if am[i, j]] for j in range(K)]
            match = deferred_acceptance(pm, pw)
            for i, j in enumerate(match):
                if j != -1:
                    pairs += 1
                    total_u += self.UM[e, i, j] + self.UW[e, j, i]
        return pairs / (N * K), total_u / (2 * N * K)
