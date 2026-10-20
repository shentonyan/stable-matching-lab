"""Additional exact accounting and independent-world validation for the paper.

python paper/run_analysis.py [--worlds 500 --bootstrap 20000]
Never changes the original results/ experiment files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stablematch.information import World, generate_world, run_policy, full_information_da, exact_maximum_surplus
from stablematch.stable_optimum import exact_stable_surplus

OUT = ROOT / "paper/results"
SEED = 20271101
BASE = dict(n_left=24, n_right=24, common_appeal=.5, reciprocity=.5, noise=1., outside_left=0., outside_right=0.)


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mean_interval(values, draws, seed, family=1):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    # Batch resampling bounds memory for larger validation samples.
    samples = []
    for start in range(0, draws, 500):
        idx = rng.integers(len(values), size=(min(500, draws-start), len(values)))
        samples.extend(values[idx].mean(axis=1))
    lo, hi = np.quantile(samples, [.025/family, 1-.025/family])
    return dict(mean=float(values.mean()), low=float(lo), high=float(hi), n=len(values))


def exact_accounting(output):
    legacy = json.loads((ROOT / "results/information_manifest.json").read_text())
    original = list(csv.DictReader((ROOT / "results/information_decomposition.csv").open()))
    lookup = {(int(r["world"]), int(r["budget"]), r["policy"], r["proposer"]): r for r in original}
    rows = []
    for rep in range(legacy["small_worlds"]):
        world = generate_world(8, 8, legacy["seed"]+100000+rep,
                               common_appeal=.5, reciprocity=.5, noise=1.)
        full = exact_maximum_surplus(world).surplus
        cache = {}
        for budget in (8, 16, 32):
            for policy in ("random", "score_greedy", "coverage"):
                for proposer in ("left", "right"):
                    out = run_policy(world, budget, policy, legacy["seed"]+100000+rep*1000+budget,
                                     pair_cost=.05, proposer=proposer)
                    key = out.discovered.tobytes()
                    if key not in cache:
                        cache[key] = (exact_maximum_surplus(world, out.discovered).surplus,
                                      exact_stable_surplus(world, out.discovered).surplus)
                    planner, stable = cache[key]
                    prior = lookup[(rep, budget, policy, proposer)]
                    np.testing.assert_allclose(out.gross_surplus, float(prior["da_gross_surplus"]), atol=1e-10)
                    assert full+1e-9 >= planner >= stable-1e-9 >= out.gross_surplus-2e-9
                    rows.append(dict(world=rep, budget=budget, policy=policy, proposer=proposer,
                                     full_planner=full, revealed_planner=planner, best_stable=stable,
                                     da_surplus=out.gross_surplus, information_gap=full-planner,
                                     stability_gap=planner-stable, selection_gap=stable-out.gross_surplus))
        print(f"exact stable accounting {rep+1}/{legacy['small_worlds']}", flush=True)
    write_rows(output / "three_gaps.csv", rows)
    return rows


def independent_validation(worlds, draws, output):
    rows = []
    for scenario in ("baseline", "high_popularity_noisy"):
        params = BASE if scenario == "baseline" else dict(BASE, common_appeal=.85, noise=2.)
        budgets = (24, 48, 96, 192) if scenario == "baseline" else (48,)
        for rep in range(worlds):
            world = generate_world(**params, seed=SEED+rep)
            for budget in budgets:
                for policy in ("score_greedy", "coverage"):
                    for proposer in ("left", "right"):
                        out = run_policy(world, budget, policy, pair_cost=.05, proposer=proposer)
                        rows.append(dict(scenario=scenario, world=rep, budget=budget, policy=policy,
                                         proposer=proposer, gross_per_person=out.gross_surplus/48,
                                         net_per_person=out.net_surplus/48, match_fraction=out.match_fraction,
                                         min_side_exposure=out.min_side_exposure))
        print(f"independent validation {scenario}: {worlds} worlds", flush=True)
    write_rows(output / "validation_worlds.csv", rows)
    index = {(r["scenario"], r["world"], r["budget"], r["policy"], r["proposer"]): r for r in rows}
    contrasts = []
    for proposer in ("left", "right"):
        definitions = [("baseline_policy", "baseline", 48, "coverage", 48, "score_greedy"),
                       ("noisy_policy", "high_popularity_noisy", 48, "coverage", 48, "score_greedy"),
                       ("baseline_budget", "baseline", 192, "coverage", 96, "coverage")]
        for label, scenario, ba, pa, bb, pb in definitions:
            values = [index[(scenario, w, ba, pa, proposer)]["net_per_person"]
                      -index[(scenario, w, bb, pb, proposer)]["net_per_person"] for w in range(worlds)]
            contrasts.append(dict(id=label, proposer=proposer, scenario=scenario,
                                  candidate=dict(budget=ba, policy=pa), reference=dict(budget=bb, policy=pb),
                                  ordinary95=mean_interval(values, draws, SEED),
                                  bonferroni_family6=mean_interval(values, draws, SEED, family=6)))
    original = list(csv.DictReader((ROOT / "results/information_worlds.csv").open()))
    decisions = []
    for proposer in ("left", "right"):
        for cost in (0., .025, .05, .1, .2, .4):
            values = {0: 0.}
            for budget in (24, 48, 96, 192):
                training = [float(r["net_per_person"])+(.05-cost)*budget/48 for r in original
                            if r["scenario"] == "baseline" and r["policy"] == "coverage"
                            and r["proposer"] == proposer and int(r["budget"]) == budget]
                values[budget] = float(np.mean(training))
            budget = max(sorted(values), key=lambda b: values[b])
            heldout = ([index[("baseline", w, budget, "coverage", proposer)]["gross_per_person"]-cost*budget/48
                        for w in range(worlds)] if budget else [0.]*worlds)
            decisions.append(dict(cost=cost, proposer=proposer, selected_budget=budget,
                                  training_mean=values[budget], heldout=mean_interval(heldout, draws, SEED)))
    return dict(seed=SEED, worlds_per_scenario=worlds, bootstrap_draws=draws,
                family_size=6, adjusted_marginal_coverage=1-.05/6,
                contrasts=contrasts, training_selected_budget_evaluation=decisions,
                interpretation="Independent synthetic-world validation; adjusted bootstrap coverage is approximate, not an empirical or exact finite-sample guarantee.")


def selection_stress(output):
    """Post hoc separate reference population, not a pooled primary experiment."""
    rng = np.random.default_rng(SEED+100000)
    rows = []
    for rep in range(500):
        left, right = rng.uniform(.1, 10, (4, 4)), rng.uniform(.1, 10, (4, 4))
        world = World(left, right, left, right, np.zeros(4), np.zeros(4))
        dl = full_information_da(world, "left")
        dr = full_information_da(world, "right")
        stable = exact_stable_surplus(world)
        planner = exact_maximum_surplus(world)
        assert planner.surplus+1e-9 >= stable.surplus >= max(dl.gross_surplus, dr.gross_surplus)-1e-9
        rows.append(dict(world=rep, left_da=dl.gross_surplus, right_da=dr.gross_surplus,
                         best_stable=stable.surplus, planner=planner.surplus,
                         stable_extremes_differ=int(not np.array_equal(dl.matching, dr.matching)),
                         best_strictly_exceeds_both=int(stable.surplus>max(dl.gross_surplus, dr.gross_surplus)+1e-9)))
    write_rows(output / "selection_stress.csv", rows)


def main(worlds=500, draws=20000, output=OUT):
    if worlds < 2 or draws < 100:
        raise ValueError("require at least two worlds and 100 bootstrap draws")
    output.mkdir(parents=True, exist_ok=True)
    exact_accounting(output)
    summary = independent_validation(worlds, draws, output)
    selection_stress(output)
    (output / "validation_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    sources = [Path(__file__), ROOT / "stablematch/stable_optimum.py", ROOT / "stablematch/information.py",
               ROOT / "stablematch/gs.py", ROOT / "paper/validation_protocol.md"]
    inputs = [ROOT / "results/information_worlds.csv", ROOT / "results/information_decomposition.csv",
              ROOT / "results/information_manifest.json"]
    manifest = dict(python=platform.python_version(), numpy=np.__version__,
                    source_hashes={p.relative_to(ROOT).as_posix(): digest(p) for p in sources},
                    input_hashes={p.relative_to(ROOT).as_posix(): digest(p) for p in inputs},
                    output_hashes={p.name: digest(p) for p in output.iterdir() if p.suffix in (".csv", ".json") and p.name != "manifest.json"},
                    hash_convention="SHA256 after CRLF-to-LF normalization")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worlds", type=int, default=500)
    parser.add_argument("--bootstrap", type=int, default=20000)
    args = parser.parse_args()
    main(args.worlds, args.bootstrap)
