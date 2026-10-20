"""Exact maximum welfare among stable matchings of a small revealed market.

Utility ties are refined by the lower partner index, consistently with the
information module's DA. Optimality is with respect to that strict refinement,
not the larger set of weakly stable matchings under unrefined utility ties.
"""
from __future__ import annotations

from itertools import permutations
import numpy as np

from .information import OptimalReference, deferred_acceptance


def exact_stable_surplus(world, discovered=None):
    """Return maximum outside-relative surplus subject to revealed stability.

    Edges must be revealed and give both endpoints strictly positive surplus.
    Unmatched agents contribute zero. Inspection costs are excluded: the graph
    is held fixed. This benchmark does not maximize welfare over all matchings.

    In strict one-to-one matching with incomplete lists, all stable matchings
    have the same unmatched agents. Therefore it suffices to enumerate all
    bijections between the matched endpoint sets of one DA result, rejecting
    unacceptable assignments and blocking pairs. This exhausts every stable
    candidate without assuming that either proposer-optimal DA maximizes total
    welfare. If k pairs occur in DA, at most k! assignments are examined.

    Requires a market side of size at most eight; the algorithm is an exact
    small-market research reference, not a scalable production solver.
    """
    nl, nr = world.true_left.shape
    if min(nl, nr) > 8:
        raise ValueError('exact stable reference requires a side of at most 8 agents')
    if discovered is None:
        mask = np.ones((nl, nr), dtype=bool)
    else:
        mask = np.asarray(discovered)
        if mask.dtype != np.bool_ or mask.shape != (nl, nr):
            raise ValueError('discovered must be a boolean matrix with market shape')
    left = world.true_left-world.outside_left[:, None]
    right = world.true_right-world.outside_right[None, :]
    acceptable = mask & (left > 0) & (right > 0)
    initial = deferred_acceptance(world, mask)
    active_left = np.flatnonzero(initial >= 0)
    active_right = sorted(int(initial[i]) for i in active_left)
    weights = left+right
    best = initial.copy()
    best_surplus = float(sum(weights[i, j] for i, j in enumerate(best) if j >= 0))
    # Lexicographic ordinal ranks represent utility followed by index refinement.
    # A final sentinel column represents being unmatched, worse than all edges.
    rank_left = np.full((nl, nr+1), nr, dtype=int)
    rank_right = np.full((nr, nl+1), nl, dtype=int)
    for i in range(nl):
        order = np.lexsort((np.arange(nr), -left[i]))
        rank_left[i, order] = np.arange(nr)
    for j in range(nr):
        order = np.lexsort((np.arange(nl), -right[:, j]))
        rank_right[j, order] = np.arange(nl)
    edge_left, edge_right = np.nonzero(acceptable)
    edge_rank_left = rank_left[edge_left, edge_right]
    edge_rank_right = rank_right[edge_right, edge_left]
    for assignment in permutations(active_right):
        partners = np.asarray(assignment, dtype=int)
        if not np.all(acceptable[active_left, partners]):
            continue
        surplus = float(weights[active_left, partners].sum())
        if surplus <= best_surplus:
            continue
        matching = np.full(nl, -1, dtype=int)
        matching[active_left] = partners
        inverse = np.full(nr, nl, dtype=int)
        inverse[partners] = active_left
        current_left = rank_left[np.arange(nl), np.where(matching < 0, nr, matching)]
        current_right = rank_right[np.arange(nr), inverse]
        blocks = ((edge_rank_left < current_left[edge_left])
                  & (edge_rank_right < current_right[edge_right]))
        if not np.any(blocks):
            best, best_surplus = matching, surplus
    return OptimalReference(best_surplus, best, len(active_left))
