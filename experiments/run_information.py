"""Paired, equal-budget information allocation study (synthetic, exploratory).

python experiments/run_information.py --worlds 100 --small-worlds 30
Outputs individual world rows, aggregate contrasts, exact small-market bounds
and a reproducibility manifest. Never overwrites the historical experiment files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stablematch.information import generate_world, run_policy, full_information_da, exact_maximum_surplus

POLICIES = ("random", "score_greedy", "coverage")
BASE = dict(n_left=24, n_right=24, common_appeal=.5, reciprocity=.5, noise=1.,
            outside_left=0., outside_right=0.)
SCENARIOS = {
    "baseline": {},
    "low_popularity_precise": dict(common_appeal=.1, noise=.25),
    "low_popularity_noisy": dict(common_appeal=.1, noise=2.),
    "high_popularity_precise": dict(common_appeal=.85, noise=.25),
    "high_popularity_noisy": dict(common_appeal=.85, noise=2.),
    "negative_reciprocity": dict(reciprocity=-.5),
    "scarce_right": dict(n_right=12),
    "heterogeneous_outside": dict(outside_left=[0.]*12+[.75]*12,
                                  outside_right=[0.]*12+[.75]*12),
}
METRICS = ("net_per_person", "match_fraction", "left_mean_surplus", "right_mean_surplus",
           "min_side_exposure", "gini", "hidden_blocking_fraction")


def outcome_row(world, outcome):
    nl, nr = world.true_left.shape
    assert outcome.revealed_blocking_pairs == 0, "DA must be revealed-graph stable"
    return dict(net_per_person=outcome.net_surplus/(nl+nr),
                match_fraction=outcome.match_fraction,
                left_mean_surplus=float(outcome.utility_left.mean()),
                right_mean_surplus=float(outcome.utility_right.mean()),
                min_side_exposure=outcome.min_side_exposure, gini=outcome.utility_gini,
                hidden_blocking_fraction=outcome.global_blocking_pairs/(nl*nr),
                inspections=int(outcome.discovered.sum()))


def interval(values, seed, draws=2000):
    """World-level mean and percentile bootstrap; no agent pseudo-replication."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    samples = values[rng.integers(len(values), size=(draws, len(values)))].mean(axis=1)
    return dict(mean=float(values.mean()), low=float(np.quantile(samples, .025)),
                high=float(np.quantile(samples, .975)), n_worlds=len(values))


def summarize(rows, seed):
    summary, contrasts = [], []
    groups = sorted(set((r["scenario"], r["budget"], r["proposer"]) for r in rows))
    for scenario, budget, proposer in groups:
        block = [r for r in rows if (r["scenario"], r["budget"], r["proposer"]) == (scenario, budget, proposer)]
        index = {(r["world"], r["policy"]): r for r in block}
        worlds = sorted({r["world"] for r in block})
        for policy in POLICIES:
            summary.append(dict(scenario=scenario, budget=budget, proposer=proposer,
                                policy=policy, metrics={metric: interval(
                                    [index[(w, policy)][metric] for w in worlds], seed)
                                    for metric in METRICS}))
        for candidate, reference in (("coverage", "score_greedy"), ("score_greedy", "random")):
            contrasts.append(dict(scenario=scenario, budget=budget, proposer=proposer,
                                  candidate=candidate, reference=reference,
                                  metrics={metric: interval([index[(w, candidate)][metric]
                                      - index[(w, reference)][metric] for w in worlds], seed)
                                      for metric in METRICS}))
    return dict(summary=summary, paired_contrasts=contrasts,
                interval="95% percentile bootstrap, worlds paired within scenario; exploratory, no multiplicity correction")


def small_market(worlds, seed, pair_cost):
    rows = []
    for rep in range(worlds):
        world = generate_world(8, 8, seed+rep, common_appeal=.5, noise=1., reciprocity=.5)
        full = exact_maximum_surplus(world).surplus
        cache = {}
        for budget in (8, 16, 32):
            for policy in POLICIES:
                for proposer in ("left", "right"):
                    out = run_policy(world, budget, policy, seed+rep*1000+budget,
                                     pair_cost=pair_cost, proposer=proposer)
                    key = out.discovered.tobytes()
                    if key not in cache:
                        cache[key] = exact_maximum_surplus(world, out.discovered).surplus
                    revealed = cache[key]
                    assert full+1e-9 >= revealed >= out.gross_surplus-1e-9
                    rows.append(dict(world=rep, budget=budget, policy=policy, proposer=proposer,
                                     full_planner_surplus=full, revealed_planner_surplus=revealed,
                                     da_gross_surplus=out.gross_surplus,
                                     information_loss=full-revealed,
                                     da_allocation_loss=revealed-out.gross_surplus))
    return rows


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(worlds, small_worlds, seed, pair_cost, output):
    if worlds < 2 or small_worlds < 1 or not np.isfinite(pair_cost) or pair_cost < 0:
        raise ValueError("need >=2 main worlds, >=1 small world, nonnegative finite cost")
    output.mkdir(parents=True, exist_ok=True)
    rows, references = [], []
    for name, overrides in SCENARIOS.items():
        params = dict(BASE, **overrides)
        for rep in range(worlds):
            world = generate_world(**params, seed=seed+rep)
            for proposer in ("left", "right"):
                reference = full_information_da(world, proposer)
                references.append(dict(scenario=name, world=rep, proposer=proposer,
                                       **outcome_row(world, reference)))
            for multiple in (1, 2, 4, 8):
                budget = params["n_left"]*multiple
                for policy in POLICIES:
                    for proposer in ("left", "right"):
                        out = run_policy(world, budget, policy, seed+rep*1000+budget,
                                         pair_cost=pair_cost, proposer=proposer)
                        assert int(out.discovered.sum()) == min(budget, params["n_left"]*params["n_right"])
                        rows.append(dict(scenario=name, world=rep, budget=budget,
                                         policy=policy, proposer=proposer, **outcome_row(world, out)))
        print(f"completed {name}: {worlds} worlds", flush=True)
    write_csv(output / "information_worlds.csv", rows)
    write_csv(output / "information_full_da.csv", references)
    write_csv(output / "information_decomposition.csv", small_market(small_worlds, seed+100000, pair_cost))
    report = summarize(rows, seed)
    (output / "information_summary.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    paths = [ROOT / "stablematch/information.py", Path(__file__), ROOT / "docs/research-design.md"]
    manifest = dict(seed=seed, worlds=worlds, small_worlds=small_worlds, pair_cost=pair_cost,
                    scenarios={name: dict(BASE, **overrides) for name, overrides in SCENARIOS.items()},
                    budgets_per_left=[1, 2, 4, 8], policies=list(POLICIES), proposer_sides=["left", "right"],
                    python=platform.python_version(), numpy=np.__version__, base_commit=commit,
                    hash_convention="SHA256 of bytes after CRLF-to-LF normalization (Git checkout independent)",
                    source_sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest() for p in paths},
                    output_sha256={p.name: hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                                   for p in sorted(output.glob("information_*.csv"))},
                    status="exploratory synthetic study; no empirical calibration or equilibrium claim")
    (output / "information_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worlds", type=int, default=100)
    parser.add_argument("--small-worlds", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20261021)
    parser.add_argument("--pair-cost", type=float, default=.05)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    run(args.worlds, args.small_worlds, args.seed, args.pair_cost, args.output)
