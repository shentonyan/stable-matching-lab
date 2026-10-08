"""Deferred acceptance (Gale-Shapley) with incomplete preference lists.

Conventions
-----------
* Agents on each side are integers 0..n-1.
* ``prefs[i]`` is agent i's ranked list of acceptable agents on the other side,
  best first. An agent missing from the list is unacceptable. Lists may be
  shorter than the other side (truncation / incomplete lists).
* A pair (m, w) is *mutually acceptable* only if each lists the other.
* A matching is represented as ``match[i] = j`` or ``-1`` if i is unmatched.
"""

from __future__ import annotations

from typing import Iterator, Sequence

Prefs = Sequence[Sequence[int]]
INF = 10**9


def _rank_tables(prefs: Prefs) -> list[dict[int, int]]:
    return [{a: k for k, a in enumerate(lst)} for lst in prefs]


def deferred_acceptance(proposer_prefs: Prefs, receiver_prefs: Prefs) -> list[int]:
    """Proposer-proposing deferred acceptance.

    Returns ``match_p`` with ``match_p[p]`` the receiver matched to proposer p,
    or -1 if p ends up unmatched.
    """
    n_p, n_r = len(proposer_prefs), len(receiver_prefs)
    rank = _rank_tables(receiver_prefs)
    nxt = [0] * n_p
    holder = [-1] * n_r
    free = list(range(n_p - 1, -1, -1))
    while free:
        p = free.pop()
        lst = proposer_prefs[p]
        while nxt[p] < len(lst):
            r = lst[nxt[p]]
            nxt[p] += 1
            rk = rank[r].get(p)
            if rk is None:  # r finds p unacceptable
                continue
            cur = holder[r]
            if cur == -1:
                holder[r] = p
                break
            if rk < rank[r][cur]:
                holder[r] = p
                free.append(cur)
                break
        # if the list is exhausted p simply stays unmatched
    match_p = [-1] * n_p
    for r, p in enumerate(holder):
        if p != -1:
            match_p[p] = r
    return match_p


def invert(match: Sequence[int], n_other: int) -> list[int]:
    """Turn match[i]=j into the matching seen from the other side."""
    inv = [-1] * n_other
    for i, j in enumerate(match):
        if j != -1:
            inv[j] = i
    return inv


def blocking_pairs(
    men_prefs: Prefs, women_prefs: Prefs, match_m: Sequence[int]
) -> list[tuple[int, int]]:
    """All pairs (m, w) that are mutually acceptable, not matched together,
    and both strictly prefer each other to their current situation
    (being unmatched is worse than any acceptable partner)."""
    mr = _rank_tables(men_prefs)
    wr = _rank_tables(women_prefs)
    match_w = invert(match_m, len(women_prefs))
    out: list[tuple[int, int]] = []
    for m, lst in enumerate(men_prefs):
        cur_m = mr[m].get(match_m[m], INF) if match_m[m] != -1 else INF
        for w in lst:
            if mr[m][w] >= cur_m:
                break
            if m not in wr[w]:
                continue
            cur_w = wr[w].get(match_w[w], INF) if match_w[w] != -1 else INF
            if wr[w][m] < cur_w:
                out.append((m, w))
    return out


def is_stable(
    men_prefs: Prefs, women_prefs: Prefs, match_m: Sequence[int]
) -> bool:
    """Valid (injective), individually rational, and no blocking pair."""
    mr = _rank_tables(men_prefs)
    wr = _rank_tables(women_prefs)
    seen: set[int] = set()
    for m, w in enumerate(match_m):
        if w == -1:
            continue
        if w in seen or w not in mr[m] or m not in wr[w]:
            return False
        seen.add(w)
    return not blocking_pairs(men_prefs, women_prefs, match_m)


def all_matchings(men_prefs: Prefs, women_prefs: Prefs) -> Iterator[list[int]]:
    """Enumerate every matching using only mutually acceptable pairs
    (brute force; for tests and tiny instances)."""
    n_m = len(men_prefs)
    wr = _rank_tables(women_prefs)
    cur = [-1] * n_m
    used: set[int] = set()

    def rec(m: int) -> Iterator[list[int]]:
        if m == n_m:
            yield list(cur)
            return
        cur[m] = -1
        yield from rec(m + 1)
        for w in men_prefs[m]:
            if w not in used and m in wr[w]:
                used.add(w)
                cur[m] = w
                yield from rec(m + 1)
                used.discard(w)
        cur[m] = -1

    yield from rec(0)


def stable_matchings(men_prefs: Prefs, women_prefs: Prefs) -> list[list[int]]:
    """All stable matchings (brute force)."""
    return [
        mt for mt in all_matchings(men_prefs, women_prefs)
        if is_stable(men_prefs, women_prefs, mt)
    ]


def deferred_acceptance_capacity(
    proposer_prefs: Prefs,
    receiver_scores: Sequence[dict[int, float]],
    capacity: Sequence[int],
) -> list[int]:
    """Many-to-one deferred acceptance (college admissions).

    Proposers propose down their lists. Receiver r holds at most
    ``capacity[r]`` proposers, keeping those with the highest
    ``receiver_scores[r][p]`` (a proposer missing from the dict is
    unacceptable). Returns ``assign[p]`` = receiver or -1.
    """
    n_p, n_r = len(proposer_prefs), len(capacity)
    nxt = [0] * n_p
    held: list[list[int]] = [[] for _ in range(n_r)]
    free = list(range(n_p - 1, -1, -1))
    while free:
        p = free.pop()
        lst = proposer_prefs[p]
        while nxt[p] < len(lst):
            r = lst[nxt[p]]
            nxt[p] += 1
            if p not in receiver_scores[r] or capacity[r] <= 0:
                continue
            held[r].append(p)
            if len(held[r]) <= capacity[r]:
                break
            worst = min(held[r], key=lambda q: receiver_scores[r][q])
            held[r].remove(worst)
            if worst != p:
                free.append(worst)
                break
            # p itself was the worst: keep proposing
    assign = [-1] * n_p
    for r, ps in enumerate(held):
        for p in ps:
            assign[p] = r
    return assign
