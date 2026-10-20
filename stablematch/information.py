"""Finite information-constrained matching experiments, not an equilibrium model.

One inspection reveals both utilities on one unique edge. Utilities and observable
scores share standard-normal latent units. Welfare is utility above each agent's
absolute outside option; unmatched agents receive zero incremental welfare.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import numpy as np

from .gs import deferred_acceptance as _da


@dataclass(frozen=True)
class World:
    true_left: np.ndarray
    true_right: np.ndarray
    score_left: np.ndarray
    score_right: np.ndarray
    outside_left: np.ndarray
    outside_right: np.ndarray

    def __post_init__(self):
        for name in ('true_left', 'true_right', 'score_left', 'score_right',
                     'outside_left', 'outside_right'):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            if not np.all(np.isfinite(value)):
                raise ValueError(f'{name} must be finite')
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        shape = self.true_left.shape
        if len(shape) != 2 or min(shape) < 1:
            raise ValueError('utility matrices must have positive dimensions')
        if any(getattr(self, k).shape != shape for k in
               ('true_right', 'score_left', 'score_right')):
            raise ValueError('all utility and score matrices must have equal shape')
        if self.outside_left.shape != (shape[0],) or self.outside_right.shape != (shape[1],):
            raise ValueError('outside options must be vectors matching the two sides')


def generate_world(n_left=40, n_right=40, seed=0, common_appeal=0.5,
                   reciprocity=0.5, noise=1.0, outside_left=0.0, outside_right=0.0):
    """Gaussian synthetic world; parameters are assumptions, not fitted estimates.

    Common appeal is the fraction of utility variance due to partner popularity.
    Reciprocity is correlation of the remaining pair-specific compatibility.
    Scores equal true utilities plus independent Gaussian noise (standard deviation
    ``noise``); this is an observable ranking signal, not a posterior expectation.
    """
    if any(not isinstance(n, (int, np.integer)) or isinstance(n, bool) or n < 1
           for n in (n_left, n_right)):
        raise ValueError('market sizes must be positive integers')
    if not np.isfinite(common_appeal) or not 0 <= common_appeal <= 1:
        raise ValueError('common_appeal must be in [0, 1]')
    if not np.isfinite(reciprocity) or not -1 <= reciprocity <= 1:
        raise ValueError('reciprocity must be in [-1, 1]')
    if not np.isfinite(noise) or noise < 0:
        raise ValueError('noise must be finite and nonnegative')
    rng = np.random.default_rng(seed)
    shape = (n_left, n_right)
    compatibility = rng.normal(size=shape)
    left = np.sqrt(common_appeal)*rng.normal(size=n_right)[None, :] + np.sqrt(1-common_appeal)*compatibility
    right = np.sqrt(common_appeal)*rng.normal(size=n_left)[:, None] + np.sqrt(1-common_appeal)*(reciprocity*compatibility + np.sqrt(1-reciprocity**2)*rng.normal(size=shape))
    return World(left, right, left + noise*rng.normal(size=shape),
                 right + noise*rng.normal(size=shape),
                 np.broadcast_to(outside_left, (n_left,)),
                 np.broadcast_to(outside_right, (n_right,)))


def _mask(world, discovered):
    mask = np.asarray(discovered)
    if mask.shape != world.true_left.shape or mask.dtype != np.bool_:
        raise ValueError('discovered must be a boolean matrix with market shape')
    return mask


def _surplus(world):
    return (world.true_left-world.outside_left[:, None],
            world.true_right-world.outside_right[None, :])


def deferred_acceptance(world, discovered, proposer='left'):
    """DA on inspected, strictly individually rational edges; ties use index order."""
    mask = _mask(world, discovered)
    left, right = _surplus(world)
    acceptable = mask & (left > 0) & (right > 0)
    lp = [sorted(np.flatnonzero(acceptable[i]), key=lambda j: (-left[i, j], j))
          for i in range(left.shape[0])]
    rp = [sorted(np.flatnonzero(acceptable[:, j]), key=lambda i: (-right[i, j], i))
          for j in range(left.shape[1])]
    if proposer == 'left':
        return np.asarray(_da(lp, rp), dtype=int)
    if proposer != 'right':
        raise ValueError('proposer must be left or right')
    result = np.full(left.shape[0], -1, dtype=int)
    for j, i in enumerate(_da(rp, lp)):
        if i >= 0:
            result[i] = j
    return result


def _utilities(world, matching):
    matching = np.asarray(matching)
    nl, nr = world.true_left.shape
    if matching.shape != (nl,) or not np.issubdtype(matching.dtype, np.integer):
        raise ValueError('matching must be an integer vector for the left side')
    used = matching[matching >= 0]
    if np.any(matching < -1) or np.any(used >= nr) or len(set(used)) != len(used):
        raise ValueError('invalid matching')
    ul, ur = np.zeros(nl), np.zeros(nr)
    l, r = _surplus(world)
    for i, j in enumerate(matching):
        if j >= 0:
            ul[i], ur[j] = l[i, j], r[i, j]
    return ul, ur


def blocking_pairs(world, matching, discovered=None):
    """Number of strict blocking pairs; omitted mask means all latent true edges.

    Under utility ties this is weak stability: both agents must strictly improve.
    """
    ul, ur = _utilities(world, matching)
    left, right = _surplus(world)
    mask = np.ones(left.shape, dtype=bool) if discovered is None else _mask(world, discovered)
    return int(np.count_nonzero(mask & (left > ul[:, None]) & (right > ur[None, :])))


@dataclass
class Outcome:
    discovered: np.ndarray
    matching: np.ndarray
    match_count: int
    match_fraction: float
    gross_surplus: float
    net_surplus: float
    utility_left: np.ndarray
    utility_right: np.ndarray
    revealed_blocking_pairs: int
    global_blocking_pairs: int
    min_side_access: float
    exposure_left: np.ndarray
    exposure_right: np.ndarray
    min_side_exposure: float
    utility_gini: float


def _outcome(world, discovered, matching, pair_cost):
    ul, ur = _utilities(world, matching)
    nl, nr = world.true_left.shape
    m = int(np.count_nonzero(matching >= 0))
    utilities = np.sort(np.concatenate((ul, ur)))
    total = float(utilities.sum())
    gini = (float(np.sum((2*np.arange(1, len(utilities)+1)-len(utilities)-1)*utilities)
                  / (len(utilities)*total)) if total > 0 else 0.0)
    el, er = discovered.sum(axis=1), discovered.sum(axis=0)
    return Outcome(discovered.copy(), matching.copy(), m, 2*m/(nl+nr), total,
                   total-pair_cost*int(discovered.sum()), ul, ur,
                   blocking_pairs(world, matching, discovered), blocking_pairs(world, matching),
                   min(m/nl, m/nr), el, er,
                   min(float(np.mean(el > 0)), float(np.mean(er > 0))), gini)


def run_policy(world, budget, policy='random', seed=0, pair_cost=0.0,
               proposer='left', coverage_strength=1.0):
    """Inspect exactly min(budget, all edges) unique pairs and then run DA.

    Score policies rank positive bilateral score surplus. Coverage discounts
    repeatedly exposed endpoints by (1+degree)^coverage_strength on both sides.
    Signals do not imply acceptability: only revealed true utility determines it.
    All policies are allocation heuristics, not optimal information acquisition.
    """
    if not isinstance(budget, (int, np.integer)) or isinstance(budget, bool) or budget < 0:
        raise ValueError('budget must be a nonnegative integer')
    if not np.isfinite(pair_cost) or pair_cost < 0:
        raise ValueError('pair_cost must be finite and nonnegative')
    if not np.isfinite(coverage_strength) or coverage_strength < 0:
        raise ValueError('coverage_strength must be finite and nonnegative')
    if policy not in ('random', 'score_greedy', 'coverage'):
        raise ValueError('unknown inspection policy')
    shape = world.true_left.shape
    count = min(budget, int(np.prod(shape)))
    mask = np.zeros(shape, dtype=bool)
    if policy == 'random':
        mask.flat[np.random.default_rng(seed).choice(mask.size, count, replace=False)] = True
    else:
        sl = np.maximum(world.score_left-world.outside_left[:, None], 0)
        sr = np.maximum(world.score_right-world.outside_right[None, :], 0)
        # Both endpoints must have positive predicted incremental utility.
        priority = np.where((sl > 0) & (sr > 0), sl+sr, 0)
        if policy == 'score_greedy':
            mask.flat[np.argsort(-priority.ravel(), kind='stable')[:count]] = True
        else:
            for _ in range(count):
                discount = ((1+mask.sum(axis=1))[:, None] * (1+mask.sum(axis=0))[None, :])**coverage_strength
                ranked = priority/discount
                # Positive baseline gives coverage meaning when all scores are poor.
                ranked = ranked + 1e-6/discount
                ranked[mask] = -np.inf
                mask.flat[int(np.argmax(ranked))] = True
    return _outcome(world, mask, deferred_acceptance(world, mask, proposer), pair_cost)


def full_information_da(world, proposer='left'):
    """Stable full-information reference; this is not a welfare optimum."""
    mask = np.ones(world.true_left.shape, dtype=bool)
    return _outcome(world, mask, deferred_acceptance(world, mask, proposer), 0.0)


@dataclass
class OptimalReference:
    surplus: float
    matching: np.ndarray
    match_count: int


def exact_maximum_surplus(world, discovered=None):
    """Unconstrained maximum welfare among individually rational matchings.

    Exponential dynamic program intended for small reference markets only.
    It need not be stable. Unmatched agents have zero incremental welfare.
    """
    nl, nr = world.true_left.shape
    if min(nl, nr) > 18:
        raise ValueError('exact reference requires a side with at most 18 agents')
    left, right = _surplus(world)
    mask = np.ones(left.shape, dtype=bool) if discovered is None else _mask(world, discovered)
    weights = left+right
    valid = mask & (left > 0) & (right > 0)
    transpose = nr > nl
    if transpose:
        weights, valid = weights.T, valid.T
    rows, cols = weights.shape

    @lru_cache(None)
    def solve(i, used):
        if i == rows:
            return 0.0, ()
        value, tail = solve(i+1, used)
        path = (-1,)+tail
        for j in np.flatnonzero(valid[i]):
            if not used & (1 << int(j)):
                rest, suffix = solve(i+1, used | (1 << int(j)))
                candidate = float(weights[i, j])+rest
                if candidate > value:
                    value, path = candidate, (int(j),)+suffix
        return value, path

    value, path = solve(0, 0)
    matching = np.full(nl, -1, dtype=int)
    if transpose:
        for j, i in enumerate(path):
            if i >= 0:
                matching[i] = j
    else:
        matching[:] = path
    return OptimalReference(value, matching, int(np.count_nonzero(matching >= 0)))
