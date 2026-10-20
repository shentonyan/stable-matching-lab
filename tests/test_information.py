import itertools
import numpy as np
import pytest

from stablematch.information import (World, generate_world, run_policy,
    deferred_acceptance, blocking_pairs, full_information_da, exact_maximum_surplus)


@pytest.mark.parametrize('policy', ['random', 'score_greedy', 'coverage'])
@pytest.mark.parametrize('shape', [(3, 7), (8, 2)])
def test_budget_repeatability_stability_and_cost(policy, shape):
    world = generate_world(*shape, seed=11)
    for budget in (0, 1, 9, 1000):
        result = run_policy(world, budget, policy, seed=17, pair_cost=.3)
        again = run_policy(world, budget, policy, seed=17, pair_cost=.3)
        assert result.discovered.sum() == min(budget, np.prod(shape))
        np.testing.assert_array_equal(result.discovered, again.discovered)
        np.testing.assert_array_equal(result.matching, again.matching)
        assert result.revealed_blocking_pairs == 0
        assert result.net_surplus == pytest.approx(result.gross_surplus-.3*min(budget,np.prod(shape)))
        assert result.gross_surplus == pytest.approx(result.utility_left.sum()+result.utility_right.sum())
        assert result.match_fraction == 2*result.match_count/sum(shape)
        assert np.all(result.utility_left >= 0) and np.all(result.utility_right >= 0)
        for i, j in enumerate(result.matching):
            if j >= 0:
                assert result.discovered[i, j]
        assert len(set(result.matching[result.matching >= 0])) == result.match_count


def test_global_and_revealed_stability_are_different():
    world = World(np.ones((2,2)),np.ones((2,2)),np.ones((2,2)),np.ones((2,2)),np.zeros(2),np.zeros(2))
    result = run_policy(world, 0)
    assert result.revealed_blocking_pairs == 0
    assert result.global_blocking_pairs == 4
    assert result.utility_gini == 0
    assert result.min_side_exposure == 0
    for proposer in ('left', 'right'):
        full = full_information_da(world, proposer)
        np.testing.assert_array_equal(full.matching, [0, 1])
        assert full.global_blocking_pairs == 0


def test_outside_options_absolute_and_strict():
    world = World(np.array([[2.,3.]]),np.array([[5.,5.]]),np.ones((1,2)),np.ones((1,2)),np.array([2.]),np.array([0.,6.]))
    assert full_information_da(world).match_count == 0
    world2 = World(np.array([[3.]]),np.array([[5.]]),np.ones((1,1)),np.ones((1,1)),np.array([2.]),np.array([3.]))
    result = run_policy(world2, 1, pair_cost=4)
    assert result.gross_surplus == 3
    assert result.net_surplus == -1


def test_proposer_switch_changes_stable_outcome():
    left = np.array([[4, 3], [3, 4]])
    right = np.array([[3, 4], [4, 3]])
    world = World(left,right,left,right,np.zeros(2),np.zeros(2))
    np.testing.assert_array_equal(full_information_da(world,'left').matching,[0,1])
    np.testing.assert_array_equal(full_information_da(world,'right').matching,[1,0])


@pytest.mark.parametrize('shape', [(2,3), (3,2), (3,3)])
def test_exact_reference_against_independent_brute_force(shape):
    for seed in range(5):
        world = generate_world(*shape, seed=seed, outside_left=-.5, outside_right=-.5)
        mask = np.random.default_rng(seed+8).random(shape) > .2
        best = 0.
        for matching in itertools.product(range(-1,shape[1]),repeat=shape[0]):
            selected = [j for j in matching if j >= 0]
            if len(selected) != len(set(selected)):
                continue
            total = 0.
            for i,j in enumerate(matching):
                if j < 0:
                    continue
                l = world.true_left[i,j]-world.outside_left[i]
                r = world.true_right[i,j]-world.outside_right[j]
                if not mask[i,j] or l <= 0 or r <= 0:
                    break
                total += l+r
            else:
                best = max(best,total)
        optimum = exact_maximum_surplus(world,mask)
        assert optimum.surplus == pytest.approx(best)
        actual = sum(world.true_left[i,j]-world.outside_left[i]+world.true_right[i,j]-world.outside_right[j]
                     for i,j in enumerate(optimum.matching) if j >= 0)
        assert actual == pytest.approx(best)
        da = deferred_acceptance(world,mask)
        assert blocking_pairs(world,da,mask) == 0


def test_generation_and_defensive_copies():
    first = generate_world(2,4,seed=4,noise=0)
    second = generate_world(2,4,seed=4,noise=0)
    np.testing.assert_array_equal(first.true_left,second.true_left)
    np.testing.assert_array_equal(first.score_left,first.true_left)
    assert not first.true_left.flags.writeable
    reciprocal = generate_world(3,5,seed=6,common_appeal=0,reciprocity=1)
    np.testing.assert_allclose(reciprocal.true_left,reciprocal.true_right)


@pytest.mark.parametrize('policy',['random','score_greedy','coverage'])
def test_inspections_never_consult_hidden_utilities(policy):
    original = generate_world(4,6,seed=2)
    changed = World(-original.true_left, -original.true_right,
                    original.score_left, original.score_right,
                    original.outside_left, original.outside_right)
    np.testing.assert_array_equal(run_policy(original,10,policy,seed=5).discovered,
                                  run_policy(changed,10,policy,seed=5).discovered)


def test_welfare_optimum_can_be_unstable():
    left = np.array([[9., 8.], [8., 1.]])
    right = np.array([[9., 8.], [8., 1.]])
    world = World(left,right,left,right,np.zeros(2),np.zeros(2))
    stable = full_information_da(world)
    optimum = exact_maximum_surplus(world)
    assert stable.gross_surplus == 20
    assert optimum.surplus == 32
    assert blocking_pairs(world,optimum.matching) == 1


@pytest.mark.parametrize('kwargs', [{'n_left':0},{'n_right':1.5},{'noise':-1},
    {'common_appeal':2},{'reciprocity':-2},{'noise':np.nan}])
def test_invalid_generation(kwargs):
    with pytest.raises(ValueError):
        generate_world(**kwargs)


@pytest.mark.parametrize('kwargs', [{'budget':-1},{'budget':1.2},{'budget':True},
    {'budget':1,'pair_cost':-1},{'budget':1,'coverage_strength':-1},
    {'budget':1,'policy':'invalid'},{'budget':1,'proposer':'invalid'}])
def test_invalid_policies(kwargs):
    with pytest.raises(ValueError):
        run_policy(generate_world(2,3),**kwargs)


def test_invalid_world_and_masks():
    with pytest.raises(ValueError):
        World(np.zeros((1,2)),np.zeros((2,1)),np.zeros((1,2)),np.zeros((1,2)),np.zeros(1),np.zeros(2))
    with pytest.raises(ValueError):
        deferred_acceptance(generate_world(2,3),np.ones((2,3)))
    with pytest.raises(ValueError):
        blocking_pairs(generate_world(2,3),np.array([0,0]))
