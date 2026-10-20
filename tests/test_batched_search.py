"""Compare complete batch outcomes with the independent scalar DA oracle."""
import numpy as np
import pytest

from stablematch.gs import deferred_acceptance, is_stable
from stablematch.search import EventSimulator


def scalar_matches(sim, a):
    mutual = (sim.UM > a) & (sim.UW > a).transpose(0, 2, 1)
    out = []
    for e in range(sim.N):
        pm = [[w for w in sim.order_m[e][m] if mutual[e, m, w]]
              for m in range(sim.K)]
        pw = [[m for m in sim.order_w[e][w] if mutual[e, m, w]]
              for w in range(sim.K)]
        match = deferred_acceptance(pm, pw)
        assert is_stable(pm, pw, match)
        out.append(match)
    return np.array(out)


@pytest.mark.parametrize("K", [1, 2, 6, 16])
@pytest.mark.parametrize("seed", [0, 7, 21])
def test_batch_matches_scalar_for_every_agent(K, seed):
    sim = EventSimulator(K, 40, seed)
    for a in (-np.inf, -1.0, 0.0, 1.5, np.inf):
        expected = scalar_matches(sim, a)
        np.testing.assert_array_equal(sim.matchings(a), expected)
        events, men = np.nonzero(expected >= 0)
        women = expected[events, men]
        g = (sim.UM[events, men, women] + sim.UW[events, women, men]).sum() / (2 * sim.N * K)
        assert sim(a) == pytest.approx((len(events) / (sim.N * K), g))


def test_repeated_thresholds_do_not_retain_holders():
    sim = EventSimulator(8, 30, 5)
    first = sim.matchings(0.0)
    sim.matchings(-np.inf)
    sim.matchings(np.inf)
    np.testing.assert_array_equal(sim.matchings(0.0), first)


def test_threshold_boundary_is_strict():
    sim = EventSimulator(1, 1, 0)
    a = min(sim.UM[0, 0, 0], sim.UW[0, 0, 0])
    assert sim.matchings(a).tolist() == [[-1]]
    assert sim.matchings(np.nextafter(a, -np.inf)).tolist() == [[0]]
