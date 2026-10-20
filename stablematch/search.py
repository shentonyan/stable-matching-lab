"""Costly search with batch dating and a pooled reservation-value closure.

Environment (iid refreshed opportunities, balanced event sizes)
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

Pooled fixed-point closure (not a proved strategic equilibrium)
-------------------------------------------------------------
Let V be the value of being single at the start of a period. With p the
per-period probability of being matched and g = E[u * 1{matched}],

    V = -c*K + delta * ( g / (1 - delta) + (1 - p) * V ).

An agent accepts a partner iff u / (1 - delta) >= V, i.e. u >= a with
a = (1 - delta) * V. The outside option is therefore not a parameter: the
threshold ``a`` solves a = (1 - delta) * V(a), where p and g pool the two
sides using the same cutoff. DA can give the sides different utilities, so
this scalar accounting identity does not establish each side's best response.
See search_audit.py and docs/theory.md for separate deviation diagnostics.

Special cases with closed forms are used as checks:
* K = 1, two-sided: p = q^2, g = q * phi(a), q = 1 - Phi(a).
* one-sided benchmark (every partner accepts anyone, you pick the best of
  your K dates): p = 1 - Phi(a)^K, g = E[max * 1{max >= a}].

Limits: iid fresh opportunities are assumed, not a demographic equilibrium;
there is no persistent sorting or heterogeneity. The historical Equilibrium
class/API name is retained for backward compatibility with saved experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, pi, sqrt

import numpy as np


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
    """Bracket bisection for a pooled value closure, not Nash certification.

    Finite Monte Carlo stats may be discontinuous. Bracket width controls
    cutoff precision, not the residual of h or existence/uniqueness.
    """
    if (not isinstance(K, (int, np.integer)) or isinstance(K, bool) or K < 1
            or not np.isfinite(c) or c < 0 or not 0 < delta < 1
            or not np.isfinite([lo, hi, tol]).all() or lo >= hi or tol <= 0):
        raise ValueError("require positive integer K, c >= 0, 0 < delta < 1 and finite lo < hi, tol > 0")

    def h(a: float) -> float:
        p, g = stats(a)
        if not np.isfinite([p, g]).all() or not 0 <= p <= 1:
            raise ValueError("stats must return finite match probability in [0,1] and utility")
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

    Utilities are drawn once (common random numbers) to reduce comparison
    noise. Finite-sample p(a), g(a) are step functions, not smooth functions.
    """

    def __init__(self, K: int, n_events: int, seed: int):
        if any(not isinstance(n, (int, np.integer)) or isinstance(n, bool) or n < 1
               for n in (K, n_events)):
            raise ValueError("K and n_events must be positive integers")
        rng = np.random.default_rng(seed)
        self.K, self.N = K, n_events
        self.UM = rng.standard_normal((n_events, K, K))  # [e, man, woman]
        self.UW = rng.standard_normal((n_events, K, K))  # [e, woman, man]
        self._order_m = np.argsort(-self.UM, axis=2)
        self.order_m = self._order_m.tolist()
        self.order_w = np.argsort(-self.UW, axis=2).tolist()
        self._rank_w = np.argsort(np.asarray(self.order_w), axis=2)

    def __call__(self, a: float):
        match = self.matchings(a)
        events, men = np.nonzero(match >= 0)
        women = match[events, men]
        total_u = (self.UM[events, men, women]
                   + self.UW[events, women, men]).sum()
        return len(events) / (self.N * self.K), float(total_u / (2 * self.N * self.K))

    def matchings(self, a: float) -> np.ndarray:
        """Return proposer-optimal DA matches, shape (events, men).

        Free men propose in parallel across independent events. Each woman
        keeps her best proposal or incumbent. Rejected men continue next
        round; each man makes at most K proposals. Preferences remain strict
        (the same argsort tie order as the scalar implementation).
        """
        K, N = self.K, self.N
        mutual = (self.UM > a) & np.transpose(self.UW > a, (0, 2, 1))
        rank_w = self._rank_w
        acceptable_order = np.take_along_axis(mutual, self._order_m, axis=2)
        # Stable partition retains each man's true order and skips all
        # unacceptable pairs rather than spending rounds proposing to them.
        partition = np.argsort(~acceptable_order, axis=2, kind="stable")
        order = np.take_along_axis(self._order_m, partition, axis=2)
        counts = mutual.sum(axis=2)
        # K denotes an empty receiver; every actual rank is smaller.
        best = np.full((N, K), K, dtype=np.intp)
        match = np.full((N, K), -1, dtype=np.intp)
        holder = np.full((N, K), -1, dtype=np.intp)
        nxt = np.zeros((N, K), dtype=np.intp)
        while True:
            events, men = np.nonzero((match < 0) & (nxt < counts))
            if not len(events):
                return match
            women = order[events, men, nxt[events, men]]
            nxt[events, men] += 1
            ranks = rank_w[events, women, men]
            # Include incumbents, and resolve competing proposals atomically.
            np.minimum.at(best, (events, women), ranks)
            won = ranks == best[events, women]
            events, men, women = events[won], men[won], women[won]
            # Displace the former holder before installing each new one.
            previous = holder[events, women]
            displaced = previous >= 0
            match[events[displaced], previous[displaced]] = -1
            holder[events, women] = men
            match[events, men] = women
