"""Exhaustive checks independent of the invariant-matched-set reduction."""
import itertools
import numpy as np
import pytest

from stablematch.information import (World, generate_world, full_information_da,
                                     exact_maximum_surplus, deferred_acceptance)
from stablematch.stable_optimum import exact_stable_surplus


def brute_stable(world, mask):
    nl, nr = mask.shape
    left = world.true_left-world.outside_left[:, None]
    right = world.true_right-world.outside_right[None, :]
    candidates = []
    for matching in itertools.product(range(-1, nr), repeat=nl):
        used = [j for j in matching if j >= 0]
        if len(used) != len(set(used)):
            continue
        if any(not mask[i,j] or left[i,j] <= 0 or right[i,j] <= 0
               for i,j in enumerate(matching) if j >= 0):
            continue
        inverse = {j:i for i,j in enumerate(matching) if j >= 0}
        stable = True
        for i,j in itertools.product(range(nl),range(nr)):
            if not mask[i,j] or left[i,j] <= 0 or right[i,j] <= 0:
                continue
            old_j, old_i = matching[i], inverse.get(j,-1)
            prefers_l = old_j < 0 or (left[i,j],-j) > (left[i,old_j],-old_j)
            prefers_r = old_i < 0 or (right[i,j],-i) > (right[old_i,j],-old_i)
            if prefers_l and prefers_r:
                stable = False
                break
        if stable:
            total = sum(left[i,j]+right[i,j] for i,j in enumerate(matching) if j >= 0)
            candidates.append((total, matching))
    return candidates


@pytest.mark.parametrize('shape',[(1,3),(3,1),(2,3),(3,2),(3,3)])
def test_exact_matches_independent_full_enumeration(shape):
    for seed in range(15):
        world = generate_world(*shape, seed=seed, outside_left=-.3, outside_right=-.4)
        mask = np.random.default_rng(seed+20).random(shape) > .25
        candidates = brute_stable(world,mask)
        result = exact_stable_surplus(world,mask)
        assert result.surplus == pytest.approx(max(value for value,_ in candidates))
        assert tuple(result.matching) in [matching for _,matching in candidates]
        assert result.match_count == np.count_nonzero(result.matching >= 0)
        assert result.surplus <= exact_maximum_surplus(world,mask).surplus+1e-12
        for proposer in ('left','right'):
            matching = deferred_acceptance(world,mask,proposer)
            value = sum(world.true_left[i,j]-world.outside_left[i]+
                        world.true_right[i,j]-world.outside_right[j]
                        for i,j in enumerate(matching) if j >= 0)
            assert result.surplus >= value-1e-12


def test_unique_stable_matching_can_have_lower_welfare_than_unconstrained():
    values = np.array([[9.,8.],[8.,1.]])
    world = World(values,values,values,values,np.zeros(2),np.zeros(2))
    optimum = exact_stable_surplus(world)
    assert optimum.surplus == 20
    np.testing.assert_array_equal(optimum.matching,[0,1])
    assert exact_maximum_surplus(world).surplus == 32


def test_best_stable_need_not_be_left_da():
    left = np.array([[4.,3.],[3.,4.]])
    right = np.array([[1.,9.],[9.,1.]])
    world = World(left,right,left,right,np.zeros(2),np.zeros(2))
    assert full_information_da(world,'left').gross_surplus == 10
    optimum = exact_stable_surplus(world)
    assert optimum.surplus == 24
    np.testing.assert_array_equal(optimum.matching,[1,0])


def test_stable_optimum_can_strictly_improve_both_da_extremes():
    rng = np.random.default_rng(7)
    left, right = rng.uniform(.1,10,(4,4)), rng.uniform(.1,10,(4,4))
    world = World(left,right,left,right,np.zeros(4),np.zeros(4))
    result = exact_stable_surplus(world)
    for side in ('left','right'):
        assert result.surplus > full_information_da(world,side).gross_surplus+.1
    candidates = brute_stable(world,np.ones((4,4),dtype=bool))
    assert result.surplus == pytest.approx(max(value for value,_ in candidates))
    np.testing.assert_array_equal(result.matching,[1,0,3,2])


def test_ties_use_lower_partner_index_strict_refinement():
    values = np.ones((3,2))
    world = World(values,values,values,values,np.zeros(3),np.zeros(2))
    result = exact_stable_surplus(world)
    np.testing.assert_array_equal(result.matching,[0,1,-1])
    assert result.surplus == 4
    candidates = brute_stable(world,np.ones((3,2),dtype=bool))
    assert len(candidates) == 1


def test_random_tied_preferences_match_refined_brute_force():
    for seed in range(15):
        rng = np.random.default_rng(seed)
        left, right = rng.integers(0,4,(3,3)), rng.integers(0,4,(3,3))
        world = World(left,right,left,right,np.zeros(3),np.zeros(3))
        mask = rng.random((3,3)) > .2
        candidates = brute_stable(world,mask)
        result = exact_stable_surplus(world,mask)
        assert result.surplus == max(value for value,_ in candidates)
        assert tuple(result.matching) in [matching for _,matching in candidates]


def test_empty_graph_and_nonpositive_outside_surplus():
    world = generate_world(4,2,seed=0)
    empty = exact_stable_surplus(world,np.zeros((4,2),dtype=bool))
    assert empty.surplus == 0 and empty.match_count == 0
    np.testing.assert_array_equal(empty.matching,[-1]*4)
    high = generate_world(3,2,outside_left=100)
    assert exact_stable_surplus(high).match_count == 0


def test_masks_and_size_limit():
    with pytest.raises(ValueError):
        exact_stable_surplus(generate_world(9,9))
    with pytest.raises(ValueError):
        exact_stable_surplus(generate_world(2,3),np.ones((2,3)))
    with pytest.raises(ValueError):
        exact_stable_surplus(generate_world(2,3),np.ones((3,2),dtype=bool))


def test_nonzero_outside_options_shift_welfare_not_tie_order():
    left = np.array([[5.,4.],[4.,5.]])
    right = np.array([[3.,10.],[10.,3.]])
    world = World(left,right,left,right,np.array([1.,2.]),np.array([2.,1.]))
    result = exact_stable_surplus(world)
    candidates = brute_stable(world,np.ones((2,2),dtype=bool))
    assert result.surplus == max(value for value,_ in candidates)
