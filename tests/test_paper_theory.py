"""Exact finite witnesses for paper/theory-notes.md."""
from fractions import Fraction as Q
from itertools import combinations, product

import numpy as np

from stablematch.gs import all_matchings, deferred_acceptance, stable_matchings
from stablematch.information import World, exact_maximum_surplus


def preferences(u, v, edges):
    n, m = len(u), len(v)
    acceptable = {(i, j) for i, j in edges if u[i][j] > 0 and v[j][i] > 0}
    left = [sorted([j for j in range(m) if (i, j) in acceptable],
                   key=lambda j: -u[i][j]) for i in range(n)]
    right = [sorted([i for i in range(n) if (i, j) in acceptable],
                    key=lambda i: -v[j][i]) for j in range(m)]
    return left, right


def surplus(u, v, match):
    return sum((u[i][j] + v[j][i] for i, j in enumerate(match) if j >= 0), Q(0))


def test_vanishing_ratio_unique_stability_with_bounded_rational_utilities():
    for denominator in (3, 5, 10, 100, 1000, 10**9):
        eps = Q(1, denominator)
        u = [[eps, 2*eps], [Q(0), Q(1)]]
        v = [[Q(1), Q(0)], [2*eps, eps]]
        assert all(0 <= x <= 1 for matrix in (u, v) for row in matrix for x in row)
        initial = {(0, 0), (1, 1)}
        full = initial | {(0, 1)}
        p0, r0 = preferences(u, v, initial)
        p1, r1 = preferences(u, v, full)
        assert stable_matchings(p0, r0) == [[0, 1]]
        assert stable_matchings(p1, r1) == [[1, -1]]
        assert deferred_acceptance(p0, r0) == [0, 1]
        assert deferred_acceptance(p1, r1) == [1, -1]
        before = surplus(u, v, [0, 1])
        after = surplus(u, v, [1, -1])
        assert before == 2 + 2*eps and after == 4*eps
        assert after / before == 2*eps / (1+eps)
        assert max(surplus(u, v, mt) for mt in all_matchings(p1, r1)) == before
        # Swapping proposer roles returns the inverse of the same unique outcome.
        assert deferred_acceptance(r0, p0) == [0, 1]
        assert deferred_acceptance(r1, p1) == [-1, 0]


def test_three_gap_identity_on_every_subgraph_and_independent_dp_reference():
    u = [[Q(3), Q(2)], [Q(2), Q(3)]]
    v = [[Q(1), Q(100)], [Q(100), Q(1)]]
    edges = list(product(range(2), repeat=2))
    fullp, fullr = preferences(u, v, set(edges))
    full = max(surplus(u, v, mt) for mt in all_matchings(fullp, fullr))
    world = World(np.array(u, float), np.array(v, float).T,
                  np.zeros((2, 2)), np.zeros((2, 2)), np.zeros(2), np.zeros(2))
    assert full == 204
    assert exact_maximum_surplus(world).surplus == float(full)
    for size in range(5):
        for subset in combinations(edges, size):
            lp, rp = preferences(u, v, set(subset))
            planner = max(surplus(u, v, mt) for mt in all_matchings(lp, rp))
            stable = max(surplus(u, v, mt) for mt in stable_matchings(lp, rp))
            da = surplus(u, v, deferred_acceptance(lp, rp))
            gaps = (full-planner, planner-stable, stable-da)
            assert all(g >= 0 for g in gaps)
            assert sum(gaps) == full-da
            mask = np.zeros((2, 2), dtype=bool)
            for i, j in subset:
                mask[i, j] = True
            assert exact_maximum_surplus(world, mask).surplus == float(planner)
    assert surplus(u, v, deferred_acceptance(fullp, fullr)) == 8
    assert max(surplus(u, v, mt) for mt in stable_matchings(fullp, fullr)) == 204


def test_finite_cost_envelopes_and_minimum_budget_ties_exhaustively():
    budgets = (0, 1, 2, 3)
    costs = [Q(i, 4) for i in range(25)]
    # No monotonicity imposed on the three nonzero-budget gross values.
    for gross_tail in product(range(6), repeat=3):
        gross = (0, *gross_tail)

        def optimum(cost):
            values = [g-cost*b for g, b in zip(gross, budgets)]
            best = max(values)
            return best, min(b for b, value in zip(budgets, values) if value == best)

        solutions = [optimum(cost) for cost in costs]
        assert all(a[0] >= b[0] and a[1] >= b[1]
                   for a, b in zip(solutions, solutions[1:]))
        # Equal cost spacing gives the convexity second-difference inequality.
        assert all(2*solutions[i][0] <= solutions[i-1][0]+solutions[i+1][0]
                   for i in range(1, len(solutions)-1))
        assert solutions[-1] == (Q(0), 0)


def test_cost_cancellation_and_pairwise_switching_threshold_exactly():
    ga, gb, ba, bb = Q(7, 3), Q(19, 6), 2, 5
    threshold = (gb-ga)/(bb-ba)
    assert threshold == Q(5, 18)
    for cost in (Q(0), threshold/2, threshold, 2*threshold, Q(1)):
        assert ((gb-cost*bb >= ga-cost*ba) == (cost <= threshold))
        assert (gb-cost*ba)-(ga-cost*ba) == gb-ga
