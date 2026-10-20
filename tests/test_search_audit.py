import numpy as np
import pytest

from stablematch.search import EventSimulator, _value, solve_threshold
from stablematch.search_audit import focal_outcomes, renewal_value, paired_value_interval


def test_k1_focal_outcomes_have_known_bilateral_cutoff():
    sim = EventSimulator(1, 100, 2)
    for side in ("left", "right"):
        matched, utility = focal_outcomes(sim, .1, .7, side)
        own, other = (sim.UM[:, 0, 0], sim.UW[:, 0, 0]) if side == "left" else (sim.UW[:, 0, 0], sim.UM[:, 0, 0])
        expected = (own > .7) & (other > .1)
        np.testing.assert_array_equal(matched, expected)
        np.testing.assert_array_equal(utility, own * expected)


def test_common_cutoff_reconciles_with_pooled_statistics():
    sim = EventSimulator(4, 50, 5)
    match = sim.matchings(.3)
    p, g = sim(.3)
    e, i = np.nonzero(match >= 0)
    j = match[e, i]
    assert p == len(e) / (sim.N * sim.K)
    assert g == pytest.approx((sim.UM[e, i, j] + sim.UW[e, j, i]).sum() / (2*sim.N*sim.K))
    matched, utility = focal_outcomes(sim, .3, .3, "left")
    np.testing.assert_array_equal(matched, match[:, 0] >= 0)
    expected = np.array([sim.UM[e, 0, w] if w >= 0 else 0. for e, w in enumerate(match[:, 0])])
    np.testing.assert_array_equal(utility, expected)
    matched_r, utility_r = focal_outcomes(sim, .3, .3, "right")
    expected_r = np.array([sim.UW[e, 0, list(row).index(0)] if 0 in row else 0.
                           for e, row in enumerate(match)])
    np.testing.assert_array_equal(matched_r, (match == 0).any(axis=1))
    np.testing.assert_array_equal(utility_r, expected_r)


def test_renewal_and_identical_policy_bootstrap():
    outcome = (np.array([1., 0., 1.]), np.array([1., 0., 2.]))
    assert renewal_value(outcome, 2, .1, .9) == pytest.approx(_value(2, .1, .9, 2/3, 1))
    assert paired_value_interval(outcome, outcome, 2, .1, .9, draws=20) == [0., 0.]


def test_invalid_side_and_discount_rejected():
    with pytest.raises(ValueError):
        focal_outcomes(EventSimulator(1, 1, 0), 0, 0, "unknown")
    with pytest.raises(ValueError):
        renewal_value((np.ones(2), np.ones(2)), 1, .1, 1.)


@pytest.mark.parametrize("kwargs", [{"tol": 0}, {"delta": 1}, {"c": -1}, {"K": 0}, {"hi": float("nan")}])
def test_invalid_root_inputs_fail_instead_of_hanging(kwargs):
    options = dict(K=1, c=.1, delta=.9, tol=.001)
    options.update(kwargs)
    with pytest.raises(ValueError):
        solve_threshold(lambda a: (.5, .5), **options)


def test_nonfinite_statistics_fail_closed():
    with pytest.raises(ValueError):
        solve_threshold(lambda a: (float("nan"), 0), 1, .1, .9)
