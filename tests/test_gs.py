import random

from stablematch.gs import (
    blocking_pairs,
    deferred_acceptance,
    deferred_acceptance_capacity,
    invert,
    is_stable,
    stable_matchings,
)


def random_instance(rng, n_m, n_w, complete=True):
    def lst(n_other):
        items = list(range(n_other))
        rng.shuffle(items)
        if not complete:
            items = items[: rng.randint(0, n_other)]
        return items

    return [lst(n_w) for _ in range(n_m)], [lst(n_m) for _ in range(n_w)]


def test_textbook_example_from_earlier_discussion():
    men = [[0, 1], [1, 0]]  # m0: w0>w1 ; m1: w1>w0
    women = [[1, 0], [0, 1]]  # w0: m1>m0 ; w1: m0>m1
    assert deferred_acceptance(men, women) == [0, 1]
    # women-proposing gives the women-optimal stable matching
    assert invert(deferred_acceptance(women, men), 2) == [1, 0]


def test_truncation_example_helps_the_receiver():
    men = [[0, 1], [1, 0]]
    women = [[1, 0], [0, 1]]
    assert deferred_acceptance(men, women) == [0, 1]
    lying_women = [[1], [0, 1]]  # w0 declares m0 unacceptable
    mt = deferred_acceptance(men, lying_women)
    assert mt == [1, 0]  # m0-w1, m1-w0: w0 now gets her true favourite m1


def test_output_is_stable_random_complete_and_incomplete():
    rng = random.Random(0)
    for complete in (True, False):
        for _ in range(300):
            n_m, n_w = rng.randint(1, 6), rng.randint(1, 6)
            men, women = random_instance(rng, n_m, n_w, complete)
            mt = deferred_acceptance(men, women)
            assert is_stable(men, women, mt)
            assert blocking_pairs(men, women, mt) == []


def test_proposer_optimal_and_receiver_pessimal():
    rng = random.Random(1)
    for _ in range(200):
        n = rng.randint(2, 5)
        men, women = random_instance(rng, n, n)
        mt = deferred_acceptance(men, women)
        mr = [{w: k for k, w in enumerate(l)} for l in men]
        wr = [{m: k for k, m in enumerate(l)} for l in women]
        for other in stable_matchings(men, women):
            for m in range(n):
                assert mr[m][mt[m]] <= mr[m][other[m]]
            mt_w, ot_w = invert(mt, n), invert(other, n)
            for w in range(n):
                assert wr[w][mt_w[w]] >= wr[w][ot_w[w]]


def test_rural_hospitals_same_set_matched():
    rng = random.Random(2)
    for _ in range(200):
        n_m, n_w = rng.randint(1, 5), rng.randint(1, 5)
        men, women = random_instance(rng, n_m, n_w, complete=False)
        sets = {
            frozenset(m for m, w in enumerate(mt) if w != -1)
            for mt in stable_matchings(men, women)
        }
        assert len(sets) == 1


def test_capacity_version_reduces_to_one_to_one():
    rng = random.Random(3)
    for _ in range(100):
        n = rng.randint(1, 6)
        men, women = random_instance(rng, n, n)
        scores = [{m: -k for k, m in enumerate(l)} for l in women]
        assert deferred_acceptance_capacity(men, scores, [1] * n) == deferred_acceptance(
            men, women
        )


def test_capacity_respected():
    rng = random.Random(4)
    for _ in range(100):
        n_p, n_r = rng.randint(1, 10), rng.randint(1, 4)
        props = []
        for _ in range(n_p):
            items = list(range(n_r))
            rng.shuffle(items)
            props.append(items)
        scores = [{p: rng.random() for p in range(n_p)} for _ in range(n_r)]
        cap = [rng.randint(0, 3) for _ in range(n_r)]
        assign = deferred_acceptance_capacity(props, scores, cap)
        for r in range(n_r):
            assert sum(1 for a in assign if a == r) <= cap[r]
