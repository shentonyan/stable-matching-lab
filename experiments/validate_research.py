"""Check saved study hashes, budgets, summaries and exact reference identities.

No new simulations or network requests. Run after regenerating saved results.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.run_information import summarize, METRICS


def validate(root=ROOT):
    res = root / "results"
    manifest = json.loads((res / "information_manifest.json").read_text())
    for path, digest in manifest["source_sha256"].items():
        assert hashlib.sha256((root / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest, f"source drift: {path}"
    for path, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((res / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest, f"output drift: {path}"
    raw = list(csv.DictReader((res / "information_worlds.csv").open(encoding="utf-8")))
    expected = len(manifest["scenarios"])*manifest["worlds"]*len(manifest["budgets_per_left"])*len(manifest["policies"])*len(manifest["proposer_sides"])
    assert len(raw) == expected
    keys, rows = set(), []
    for row in raw:
        r = dict(row)
        for key in ("world", "budget", "inspections"):
            r[key] = int(row[key])
        for metric in METRICS:
            r[metric] = float(row[metric])
            assert np.isfinite(r[metric])
        key = tuple(r[k] for k in ("scenario", "world", "budget", "policy", "proposer"))
        assert key not in keys, f"duplicate treatment row {key}"
        keys.add(key)
        scenario = manifest["scenarios"][r["scenario"]]
        assert r["inspections"] == min(r["budget"], scenario["n_left"]*scenario["n_right"])
        rows.append(r)
    original = json.loads((res / "information_summary.json").read_text())
    rebuilt = summarize(rows, manifest["seed"])
    for section in ("summary", "paired_contrasts"):
        assert len(original[section]) == len(rebuilt[section])
        for old, new in zip(original[section], rebuilt[section]):
            for metric in METRICS:
                for stat in ("mean", "low", "high", "n_worlds"):
                    np.testing.assert_allclose(old["metrics"][metric][stat], new["metrics"][metric][stat], atol=1e-12, rtol=1e-12)
    with (res / "information_decomposition.csv").open(encoding="utf-8") as stream:
        bounds = list(csv.DictReader(stream))
    assert len(bounds) == manifest["small_worlds"]*3*3*2
    for r in bounds:
        missing, allocation = float(r["information_loss"]), float(r["da_allocation_loss"])
        assert missing >= -1e-9 and allocation >= -1e-9
        assert abs(float(r["full_planner_surplus"])-float(r["da_gross_surplus"])-missing-allocation) < 1e-9
    empirical = json.loads((res / "empirical_audit.json").read_text())
    assert empirical["observed_pairs"] == sum(r["observed_pairs"] for r in empirical["per_wave"])
    assert empirical["mutual_yes_pairs"] == sum(r["mutual_yes_pairs"] for r in empirical["per_wave"])
    assert empirical["complete_decision_pairs"] == sum(r["complete_decision_pairs"] for r in empirical["per_wave"])
    assert empirical["mutual_yes_rate"] == empirical["mutual_yes_pairs"]/empirical["complete_decision_pairs"]
    # No raw participant records should appear in any published aggregate JSON.
    assert not ({"iid", "pid", "dec", "dec_o"} & empirical.keys())
    print(f"Validated {len(rows):,} treatment rows, {len(bounds)} exact-reference rows, all summary intervals and source/output hashes.")


if __name__ == "__main__":
    validate()
