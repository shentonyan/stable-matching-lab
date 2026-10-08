"""Compare mechanisms in the simulated dating market.

usage: python experiments/run_market.py [SEEDS]
Writes results/market_*.csv and results/market_summary.md
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stablematch.market import MECHANISMS, Params, evaluate, make_world  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
METRICS = ["fraction_coupled", "dates_per_person", "mean_utility_of_coupled",
           "blocking_pairs_per_person"]


def run_config(p: Params, seeds: int) -> dict:
    acc = {name: {m: [] for m in METRICS} for name in MECHANISMS}
    for s in range(seeds):
        w = make_world(p, np.random.default_rng(1000 + s))
        for name, fn in MECHANISMS.items():
            couples, dates = fn(w)
            res = evaluate(w, couples, dates)
            for m in METRICS:
                acc[name][m].append(res[m])
    out = {}
    for name in MECHANISMS:
        out[name] = {}
        for m in METRICS:
            v = np.array(acc[name][m], dtype=float)
            v = v[~np.isnan(v)]
            out[name][m] = (v.mean(), v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else 0.0)
    return out


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    base = Params()
    rows = []
    sweeps = {
        "default": [("default", base)],
        "sigma_q": [(f"sigma_q={v}", replace(base, sigma_q=v)) for v in (0.25, 0.5, 1.0, 2.0)],
        "outside_q": [(f"outside_q={v}", replace(base, outside_q=v)) for v in (0.3, 0.5, 0.7, 0.85)],
        "lam": [(f"lam={v}", replace(base, lam=v)) for v in (0.0, 0.5, 1.0, 2.0)],
        "sigma_e": [(f"sigma_e={v}", replace(base, sigma_e=v)) for v in (0.25, 0.5, 1.0, 2.0)],
        "dates": [(f"dates={v}", replace(base, dates=v)) for v in (2, 5, 10, 20)],
    }
    lines = [f"# Market simulation results\n\nn={base.n} per side, {seeds} random worlds per row, "
             f"mean ± standard error. Other parameters at their defaults: {base}.\n"]
    for group, cfgs in sweeps.items():
        lines.append(f"\n## {group}\n")
        lines.append("| setting | mechanism | fraction coupled | dates / person | "
                     "mean utility of coupled | blocking pairs / person |")
        lines.append("|---|---|---|---|---|---|")
        for label, p in cfgs:
            res = run_config(p, seeds)
            for name, vals in res.items():
                fmt = [f"{vals[m][0]:.3f} ± {vals[m][1]:.3f}" for m in METRICS]
                lines.append(f"| {label} | {name} | " + " | ".join(fmt) + " |")
                rows.append({"group": group, "setting": label, "mechanism": name,
                             **{f"{m}_mean": vals[m][0] for m in METRICS},
                             **{f"{m}_se": vals[m][1] for m in METRICS}})
    (RESULTS / "market_summary.md").write_text("\n".join(lines) + "\n")
    with open(RESULTS / "market_all.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print("\n".join(lines[:14]))


if __name__ == "__main__":
    main()
