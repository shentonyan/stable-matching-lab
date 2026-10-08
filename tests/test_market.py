import numpy as np

from stablematch.market import MECHANISMS, Params, evaluate, make_world


def test_oracle_has_no_blocking_pairs_and_all_couples_are_acceptable():
    for seed in range(20):
        w = make_world(Params(n=30), np.random.default_rng(seed))
        couples, dates = MECHANISMS["oracle"](w)
        res = evaluate(w, couples, dates)
        assert res["blocking_pairs_per_person"] == 0
        assert all(w.ok(m, x) for m, x in couples)


def test_every_mechanism_returns_a_valid_matching_of_acceptable_pairs():
    for seed in range(20):
        w = make_world(Params(n=30), np.random.default_rng(seed))
        for name, fn in MECHANISMS.items():
            couples, _ = fn(w)
            ms = [m for m, _ in couples]
            xs = [x for _, x in couples]
            assert len(set(ms)) == len(ms) and len(set(xs)) == len(xs), name
            assert all(w.ok(m, x) for m, x in couples), name
