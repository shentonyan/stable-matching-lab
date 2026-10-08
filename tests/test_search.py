import numpy as np

from stablematch.gs import blocking_pairs
from stablematch.search import (
    EventSimulator,
    Phi,
    make_stats_one_sided,
    phi,
    solve_threshold,
    stats_two_sided_k1,
)


def test_k1_event_simulation_matches_closed_form_stats():
    sim = EventSimulator(K=1, n_events=60000, seed=0)
    for a in (-0.5, 0.0, 0.7):
        p, g = sim(a)
        p0, g0 = stats_two_sided_k1(a)
        assert abs(p - p0) < 0.01
        assert abs(g - g0) < 0.01


def test_k1_equilibrium_matches_closed_form():
    for c, delta in ((0.05, 0.9), (0.2, 0.8), (0.02, 0.95)):
        exact = solve_threshold(stats_two_sided_k1, 1, c, delta)
        sim = solve_threshold(EventSimulator(1, 40000, 1), 1, c, delta, tol=1e-3)
        assert abs(exact.threshold - sim.threshold) < 0.05


def test_closed_form_fixed_point_satisfies_its_own_equation():
    c, delta = 0.1, 0.9
    eq = solve_threshold(stats_two_sided_k1, 1, c, delta, tol=1e-10)
    a, q = eq.threshold, 1 - Phi(eq.threshold)
    lhs = a * (1 - delta * (1 - q * q))
    rhs = -c * (1 - delta) + delta * q * phi(a)
    assert abs(lhs - rhs) < 1e-6


def test_one_sided_k1_equals_mccall_condition():
    # K = 1, one-sided, cost paid every period, flow 0 while single:
    # the reservation a satisfies a + c = delta / (1 - delta) * E[(u - a)^+].
    c, delta = 0.05, 0.9
    eq = solve_threshold(make_stats_one_sided(1), 1, c, delta, tol=1e-8)
    a = eq.threshold
    expected_excess = phi(a) - a * (1 - Phi(a))
    assert abs((a + c) - delta / (1 - delta) * expected_excess) < 2e-3


def test_threshold_falls_with_cost():
    for K in (1, 3):
        stats = make_stats_one_sided(K)
        ths = [solve_threshold(stats, K, c, 0.9).threshold for c in (0.01, 0.05, 0.2)]
        assert ths[0] > ths[1] > ths[2]


def test_event_outcomes_are_stable_within_the_event():
    sim = EventSimulator(K=6, n_events=50, seed=3)
    a = 0.0
    mutual = (sim.UM > a) & np.transpose(sim.UW > a, (0, 2, 1))
    from stablematch.gs import deferred_acceptance

    for e in range(sim.N):
        am = mutual[e]
        pm = [[j for j in sim.order_m[e][i] if am[i, j]] for i in range(6)]
        pw = [[i for i in sim.order_w[e][j] if am[i, j]] for j in range(6)]
        assert blocking_pairs(pm, pw, deferred_acceptance(pm, pw)) == []
