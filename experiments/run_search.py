"""Equilibrium of the costly-search model over a grid of (c, delta, K).

usage: python experiments/run_search.py [N_EVENTS] [REPLICATES]
Writes results/search_all.csv and results/search_summary.md
"""

from __future__ import annotations

import csv
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stablematch.search import (  # noqa: E402
    EventSimulator,
    make_stats_one_sided,
    solve_threshold,
    stats_two_sided_k1,
)

RESULTS = Path(__file__).resolve().parents[1] / "results"
COSTS = (0.02, 0.05, 0.1, 0.2)
DELTAS = (0.8, 0.9, 0.95)
KS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48)
KS_ONE = KS + (64, 96, 128, 192, 256, 384, 512)


def work(args):
    K, rep, n_events = args
    sim = EventSimulator(K, n_events, seed=10_000 * K + rep)
    out = []
    for c in COSTS:
        for delta in DELTAS:
            eq = solve_threshold(sim, K, c, delta, tol=2e-3)
            out.append(("two_sided", rep, eq))
    return out


def main():
    n_events = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    jobs = [(K, r, n_events) for K in KS for r in range(reps)]
    rows = []
    with Pool() as pool:
        for res in pool.imap_unordered(work, jobs):
            for kind, rep, eq in res:
                rows.append((kind, rep, eq))
    with open(RESULTS / "search_raw_two_sided.pkl", "wb") as f:
        pickle.dump(rows, f)
    # closed-form / quadrature references (no Monte Carlo)
    for K in KS_ONE:
        st = make_stats_one_sided(K)
        for c in COSTS:
            for delta in DELTAS:
                # a very costly large batch can push the threshold far below -8
                rows.append(("one_sided", 0,
                             solve_threshold(st, K, c, delta, lo=-1000.0, hi=8.0, tol=1e-6)))
    for c in COSTS:
        for delta in DELTAS:
            rows.append(("two_sided_exact_K1", 0,
                         solve_threshold(stats_two_sided_k1, 1, c, delta, tol=1e-6)))

    with open(RESULTS / "search_all.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "rep", "K", "c", "delta", "threshold", "value", "match_prob",
                    "partner_utility", "periods_to_match", "dates_to_match"])
        for kind, rep, e in sorted(rows, key=lambda t: (t[0], t[2].c, t[2].delta, t[2].K, t[1])):
            w.writerow([kind, rep, e.K, e.c, e.delta, f"{e.threshold:.5f}", f"{e.value:.5f}",
                        f"{e.match_prob:.5f}", f"{e.partner_utility:.5f}",
                        f"{e.periods_to_match:.4f}", f"{e.dates_to_match:.4f}"])

    def agg(kind, c, delta, K, field):
        v = [getattr(e, field) for k, _, e in rows if k == kind and e.c == c
             and e.delta == delta and e.K == K]
        return float(np.mean(v)), (float(np.std(v, ddof=1)) if len(v) > 1 else 0.0)

    lines = [
        "# Costly-search model: equilibrium outside option by batch size\n",
        f"Two-sided rows: mean ± sd over {reps} Monte Carlo replicates, {n_events} events each. "
        "`a*` = equilibrium threshold = outside option (flow utility units, utilities ~ N(0,1)). "
        "`one-sided` = every partner accepts anyone (quadrature, no noise). The two-sided K grid is "
        f"{KS}; the one-sided K* is searched over {KS_ONE}.\n",
    ]
    best = []
    for c in COSTS:
        for delta in DELTAS:
            lines.append(f"\n## c = {c}, delta = {delta}\n")
            lines.append("| K | a* two-sided | a* one-sided | match prob / period | "
                         "periods to match | dates to match | partner utility |")
            lines.append("|---|---|---|---|---|---|---|")
            two = {K: agg("two_sided", c, delta, K, "threshold") for K in KS}
            one = {K: agg("one_sided", c, delta, K, "threshold") for K in KS_ONE}
            kb2 = max(KS, key=lambda K: two[K][0])
            kb1 = max(KS_ONE, key=lambda K: one[K][0])
            best.append((c, delta, kb2, two[kb2], kb1, one[kb1]))
            for K in KS:
                p = agg("two_sided", c, delta, K, "match_prob")[0]
                pt = agg("two_sided", c, delta, K, "periods_to_match")[0]
                dt = agg("two_sided", c, delta, K, "dates_to_match")[0]
                pu = agg("two_sided", c, delta, K, "partner_utility")[0]
                mark = " **←**" if K == kb2 else ""
                lines.append(f"| {K}{mark} | {two[K][0]:.3f} ± {two[K][1]:.3f} | {one[K][0]:.3f} | "
                             f"{p:.3f} | {pt:.2f} | {dt:.1f} | {pu:.3f} |")
    lines.append("\n## Best batch size K* (largest a*)\n")
    lines.append("| c | delta | K* two-sided | a* at K* | K* one-sided | a* at K* |")
    lines.append("|---|---|---|---|---|---|")
    for c, delta, kb2, v2, kb1, v1 in best:
        edge2 = " (edge of grid: true K* may be larger)" if kb2 == max(KS) else ""
        edge1 = " (edge of grid)" if kb1 == max(KS_ONE) else ""
        lines.append(f"| {c} | {delta} | {kb2}{edge2} | {v2[0]:.3f} | {kb1}{edge1} | {v1[0]:.3f} |")
    (RESULTS / "search_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-(len(best) + 4):]))


if __name__ == "__main__":
    main()
