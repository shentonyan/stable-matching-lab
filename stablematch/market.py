"""A deliberately simple dating-market simulation.

This is a stylised model, not a calibrated one. Every modelling choice is a
parameter of ``Params`` so that conclusions can be checked against it.

Model
-----
* n men and n women, each with a trait vector x in R^d and a scalar
  "common appeal" a (what everyone agrees on).
* True utility of i for j:  u_ij = sim(x_i, x_j) + lam * a_j + eps_ij,
  where sim is a standardised similarity and eps_ij ~ N(0, sigma_e) is
  idiosyncratic taste that only shows up when the two actually meet.
* A questionnaire sees traits and appeal but not eps_ij, and adds its own
  noise: uhat_ij = sim + lam * a_j + N(0, sigma_q).
* Outside option: agent i will only commit to a partner j if u_ij exceeds
  r_i, the ``outside_q`` quantile of i's own true utilities over the pool.
  A date between i and j succeeds only if both exceed their thresholds.
  There is no commitment device: a pair that fails simply stays single.

Mechanisms (all give each person about ``dates`` dates)
-------------------------------------------------------
* ``one_shot``  : one run of men-proposing deferred acceptance on uhat
                  (1 date per person).
* ``cycles``    : ``dates`` repeated cycles; each cycle runs deferred
                  acceptance on uhat among people still single, excluding
                  pairs already tried; one date per person per cycle.
* ``events``    : people are assigned to events by trait affinity using
                  many-to-one deferred acceptance (``dates`` seats per sex
                  per event); inside an event everyone meets everyone, eps
                  is revealed, and pairs are formed by deferred acceptance
                  on true utility among mutually acceptable pairs.
* ``oracle``    : deferred acceptance on the TRUE utilities with outside
                  options. Not feasible (needs n^2 dates); a reference line.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .gs import deferred_acceptance, deferred_acceptance_capacity


@dataclass
class Params:
    n: int = 60
    d: int = 4
    sigma_q: float = 0.5
    sigma_e: float = 0.5
    lam: float = 0.5
    outside_q: float = 0.5
    dates: int = 5  # dates per person in `cycles` and `events`


@dataclass
class World:
    p: Params
    u_m: np.ndarray  # u_m[m, w]: true utility of man m for woman w
    u_w: np.ndarray  # u_w[w, m]
    uh_m: np.ndarray  # questionnaire estimates
    uh_w: np.ndarray
    r_m: np.ndarray
    r_w: np.ndarray
    x_m: np.ndarray
    x_w: np.ndarray
    theme: np.ndarray  # event themes used by the `events` mechanism

    def ok(self, m: int, w: int) -> bool:
        return self.u_m[m, w] > self.r_m[m] and self.u_w[w, m] > self.r_w[w]


def _std_sim(xa: np.ndarray, xb: np.ndarray, mu: float, sd: float) -> np.ndarray:
    d2 = ((xa[:, None, :] - xb[None, :, :]) ** 2).sum(-1)
    return (-d2 - mu) / sd


def make_world(p: Params, rng: np.random.Generator) -> World:
    x_m = rng.standard_normal((p.n, p.d))
    x_w = rng.standard_normal((p.n, p.d))
    a_m = rng.standard_normal(p.n)
    a_w = rng.standard_normal(p.n)
    d2 = ((x_m[:, None, :] - x_w[None, :, :]) ** 2).sum(-1)
    mu, sd = -d2.mean(), d2.std()
    sim = _std_sim(x_m, x_w, mu, sd)  # (m, w); symmetric in the pair
    core_m = sim + p.lam * a_w[None, :]
    core_w = sim.T + p.lam * a_m[None, :]
    u_m = core_m + p.sigma_e * rng.standard_normal((p.n, p.n))
    u_w = core_w + p.sigma_e * rng.standard_normal((p.n, p.n))
    uh_m = core_m + p.sigma_q * rng.standard_normal((p.n, p.n))
    uh_w = core_w + p.sigma_q * rng.standard_normal((p.n, p.n))
    r_m = np.quantile(u_m, p.outside_q, axis=1)
    r_w = np.quantile(u_w, p.outside_q, axis=1)
    theme = rng.standard_normal((int(np.ceil(p.n / p.dates)), p.d))
    return World(p, u_m, u_w, uh_m, uh_w, r_m, r_w, x_m, x_w, theme)


def _prefs_from_scores(scores: np.ndarray, allowed) -> list[list[int]]:
    """Ranked lists from a score matrix; ``allowed[i]`` is a set/array of j."""
    out = []
    for i in range(scores.shape[0]):
        js = list(allowed[i])
        js.sort(key=lambda j: -scores[i, j])
        out.append(js)
    return out


def one_shot(w: World):
    n = w.p.n
    full = [list(range(n))] * n
    pm = _prefs_from_scores(w.uh_m, full)
    pw = _prefs_from_scores(w.uh_w, full)
    match = deferred_acceptance(pm, pw)
    dates = sum(1 for x in match if x != -1)
    couples = [(m, x) for m, x in enumerate(match) if x != -1 and w.ok(m, x)]
    return couples, dates


def cycles(w: World):
    n, rounds = w.p.n, w.p.dates
    single_m, single_w = set(range(n)), set(range(n))
    tried: set[tuple[int, int]] = set()
    couples, dates = [], 0
    for _ in range(rounds):
        sm, sw = sorted(single_m), sorted(single_w)
        if not sm or not sw:
            break
        allowed_m = [[x for x in sw if (m, x) not in tried] for m in sm]
        allowed_w = [[m for m in sm if (m, x) not in tried] for x in sw]
        pm = _prefs_from_scores(w.uh_m[np.ix_(sm, sw)], [
            [sw.index(x) for x in lst] for lst in allowed_m])
        pw = _prefs_from_scores(w.uh_w[np.ix_(sw, sm)], [
            [sm.index(m) for m in lst] for lst in allowed_w])
        match = deferred_acceptance(pm, pw)
        for i, j in enumerate(match):
            if j == -1:
                continue
            m, x = sm[i], sw[j]
            dates += 1
            tried.add((m, x))
            if w.ok(m, x):
                couples.append((m, x))
                single_m.discard(m)
                single_w.discard(x)
    return couples, dates


def events(w: World):
    n, k = w.p.n, w.p.dates
    n_events = int(np.ceil(n / k))
    theme = w.theme

    def side(x):
        d2 = ((x[:, None, :] - theme[None, :, :]) ** 2).sum(-1)  # (agents, events)
        prefs = [list(np.argsort(d2[i])) for i in range(n)]
        scores = [{i: -d2[i, e] for i in range(n)} for e in range(n_events)]
        return deferred_acceptance_capacity(prefs, scores, [k] * n_events)

    ev_m, ev_w = side(w.x_m), side(w.x_w)
    couples, dates = [], 0
    for e in range(n_events):
        ms = [m for m in range(n) if ev_m[m] == e]
        ws = [x for x in range(n) if ev_w[x] == e]
        dates += len(ms) * len(ws)
        pm = [sorted([j for j, x in enumerate(ws) if w.ok(m, x)],
                     key=lambda j: -w.u_m[m, ws[j]]) for m in ms]
        pw = [sorted([i for i, m in enumerate(ms) if w.ok(m, x)],
                     key=lambda i: -w.u_w[x, ms[i]]) for x in ws]
        match = deferred_acceptance(pm, pw) if ms and ws else []
        couples += [(ms[i], ws[j]) for i, j in enumerate(match) if j != -1]
    return couples, dates


def oracle(w: World):
    n = w.p.n
    pm = [sorted([x for x in range(n) if w.ok(m, x)], key=lambda x: -w.u_m[m, x])
          for m in range(n)]
    pw = [sorted([m for m in range(n) if w.ok(m, x)], key=lambda m: -w.u_w[x, m])
          for x in range(n)]
    match = deferred_acceptance(pm, pw)
    return [(m, x) for m, x in enumerate(match) if x != -1], n * n


MECHANISMS = {"one_shot": one_shot, "cycles": cycles, "events": events, "oracle": oracle}


def evaluate(w: World, couples, dates) -> dict:
    n = w.p.n
    partner_m = {m: x for m, x in couples}
    partner_w = {x: m for m, x in couples}
    cur_m = np.array([w.u_m[m, partner_m[m]] if m in partner_m else w.r_m[m] for m in range(n)])
    cur_w = np.array([w.u_w[x, partner_w[x]] if x in partner_w else w.r_w[x] for x in range(n)])
    better_m = w.u_m > cur_m[:, None]
    better_w = (w.u_w > cur_w[:, None]).T
    block = better_m & better_w
    for m, x in couples:
        block[m, x] = False
    welfare = (
        sum(w.u_m[m, x] + w.u_w[x, m] for m, x in couples) / (2 * len(couples))
        if couples else float("nan")
    )
    return {
        "fraction_coupled": len(couples) / n,
        "dates_per_person": dates / n,
        "mean_utility_of_coupled": welfare,
        "blocking_pairs_per_person": block.sum() / n,
    }
