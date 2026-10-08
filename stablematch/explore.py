"""Manipulation explorer: brute-force every possible misreport of one agent.

For a profile of true (complete) preferences we ask, for every agent on the
proposing side (men) and the receiving side (women): is there any ordered
list (any subset, any order) the agent could submit that gives her/him a
strictly better partner, judged by the true preferences, under
men-proposing deferred acceptance? Being unmatched ranks below everyone.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from .gs import deferred_acceptance, invert, stable_matchings


def ordered_sublists(items: list[int]):
    """Every ordered list built from a subset of ``items`` (incl. empty)."""
    for k in range(len(items) + 1):
        for perm in itertools.permutations(items, k):
            yield list(perm)


@dataclass
class ProfileResult:
    n_stable: int
    men_gain: bool
    women_gain: bool
    women_gain_by_truncation: bool  # a gaining misreport that is a prefix of the truth
    n_women_gaining: int


def _true_rank(prefs_i: list[int], partner: int) -> int:
    return prefs_i.index(partner) if partner != -1 else len(prefs_i)


def scan_profile(men: list[list[int]], women: list[list[int]]) -> ProfileResult:
    n = len(men)
    others = list(range(n))
    strategies = list(ordered_sublists(others))

    base_m = deferred_acceptance(men, women)
    base_w = invert(base_m, n)

    men_gain = False
    for m in range(n):
        base_rank = _true_rank(men[m], base_m[m])
        for s in strategies:
            lied = [list(l) for l in men]
            lied[m] = s
            mt = deferred_acceptance(lied, women)
            if _true_rank(men[m], mt[m]) < base_rank:
                men_gain = True
                break
        if men_gain:
            break

    n_women_gaining = 0
    by_trunc = False
    for w in range(n):
        base_rank = _true_rank(women[w], base_w[w])
        gained = False
        for s in strategies:
            lied = [list(l) for l in women]
            lied[w] = s
            mt_w = invert(deferred_acceptance(men, lied), n)
            if _true_rank(women[w], mt_w[w]) < base_rank:
                gained = True
                if s == women[w][: len(s)]:
                    by_trunc = True
        n_women_gaining += gained

    return ProfileResult(
        n_stable=len(stable_matchings(men, women)),
        men_gain=men_gain,
        women_gain=n_women_gaining > 0,
        women_gain_by_truncation=by_trunc,
        n_women_gaining=n_women_gaining,
    )
