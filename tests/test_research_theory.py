"""Finite witnesses for the claims in docs/theory.md; no sampling involved."""
from itertools import combinations, product

import numpy as np

from stablematch.gs import (all_matchings, blocking_pairs, deferred_acceptance,
                            is_stable)


def prefs(um, uw, edges):
    n = len(um)
    return (
        [sorted([j for j in range(n) if (i, j) in edges],
                key=lambda j: -um[i, j]) for i in range(n)],
        [sorted([i for i in range(n) if (i, j) in edges],
                key=lambda i: -uw[j, i]) for j in range(n)],
    )


def welfare(um, uw, match):
    return sum(um[i, j] + uw[j, i] for i, j in enumerate(match) if j >= 0)


def test_every_two_by_two_strict_incomplete_profile_is_stable():
    # Each list is empty, a singleton, or one of two complete strict orders.
    lists = [[], [0], [1], [0, 1], [1, 0]]
    checked = 0
    for profile in product(lists, repeat=4):
        pm, pw = profile[:2], profile[2:]
        assert is_stable(pm, pw, deferred_acceptance(pm, pw))
        checked += 1
    assert checked == 625


def test_more_information_can_reduce_da_welfare_and_cardinality():
    um = np.array([[4, 5], [0, 100]])
    uw = np.array([[100, 0], [5, 4]])
    small = {(0, 0), (1, 1)}
    full = small | {(0, 1)}
    pm, pw = prefs(um, uw, small)
    a = deferred_acceptance(pm, pw)
    pm, pw = prefs(um, uw, full)
    b = deferred_acceptance(pm, pw)
    assert a == [0, 1] and b == [1, -1]
    assert (welfare(um, uw, a), welfare(um, uw, b)) == (208, 10)
    assert blocking_pairs(pm, pw, a) == [(0, 1)]
    assert is_stable(pm, pw, b)
    # Exhaust all feasible matchings, rather than assuming a welfare benchmark.
    assert max(welfare(um, uw, mt) for mt in all_matchings(pm, pw)) == 208


def test_more_stable_matches_can_still_mean_lower_welfare():
    um = np.array([[100, 4], [4, 0]])
    uw = np.array([[4, 5], [4, 0]])
    pm0, pw0 = prefs(um, uw, {(0, 0)})
    pm1, pw1 = prefs(um, uw, {(0, 0), (0, 1), (1, 0)})
    a, b = deferred_acceptance(pm0, pw0), deferred_acceptance(pm1, pw1)
    assert a == [0, -1] and b == [1, 0]
    assert is_stable(pm0, pw0, a) and is_stable(pm1, pw1, b)
    assert (welfare(um, uw, a), welfare(um, uw, b)) == (104, 17)


def test_finite_inspection_saturation_and_double_counting_identity():
    # Exhaust every graph in a 2x3 market, including empty and complete graphs.
    universe = list(product(range(2), range(3)))
    maximum_edges = [0] * 5
    for size in range(len(universe) + 1):
        for subset in combinations(universe, size):
            degree_a = [sum(i == a for i, _ in subset) for a in range(2)]
            degree_b = [sum(j == b for _, j in subset) for b in range(3)]
            assert sum(degree_a) + sum(degree_b) == 2 * size
            for cap in range(5):
                if max(degree_a + degree_b) <= cap:
                    assert size <= min(2 * 3, 2 * cap, 3 * cap)
                    maximum_edges[cap] = max(maximum_edges[cap], size)
    assert maximum_edges == [0, 2, 4, 6, 6]
    # At k=3 both A agents may inspect all B agents, but B degrees are only 2.
    full = set(universe)
    assert len(full) == 6
    assert max(sum(j == b for _, j in full) for b in range(3)) == 2
