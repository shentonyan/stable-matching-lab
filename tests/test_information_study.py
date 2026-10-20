import csv
import hashlib
import json

import pytest

from experiments import run_information as study


def test_paired_contrast_uses_world_differences_not_unpaired_intervals():
    rows = []
    for w in range(4):
        for policy, shift in (("random", 0), ("score_greedy", .2), ("coverage", .5)):
            rows.append(dict(world=w, scenario="test", budget=2, proposer="left", policy=policy,
                             **{key: float(w)+shift for key in study.METRICS}))
    report = study.summarize(rows[::-1], 0)
    contrast = report["paired_contrasts"][0]["metrics"]["net_per_person"]
    assert contrast["n_worlds"] == 4
    for key in ("mean", "low", "high"):
        assert contrast[key] == pytest.approx(.3)


def test_small_end_to_end_study_has_replayable_manifest_and_planner_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "BASE", dict(study.BASE, n_left=4, n_right=4))
    monkeypatch.setattr(study, "SCENARIOS", {"tiny": {}})
    study.run(3, 2, 1234, .05, tmp_path)
    manifest = json.loads((tmp_path/"information_manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((tmp_path/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest
    rows = list(csv.DictReader((tmp_path/"information_worlds.csv").open()))
    assert len(rows) == 3*4*3*2
    for row in rows:
        assert int(row["inspections"]) == min(int(row["budget"]), 16)
        assert 0 <= float(row["match_fraction"]) <= 1
    bounds = list(csv.DictReader((tmp_path/"information_decomposition.csv").open()))
    for r in bounds:
        assert float(r["information_loss"]) >= -1e-10
        assert float(r["da_allocation_loss"]) >= -1e-10
        assert float(r["full_planner_surplus"])-float(r["da_gross_surplus"]) == pytest.approx(
            float(r["information_loss"])+float(r["da_allocation_loss"]))


def test_interval_rejects_invalid_study_size(tmp_path):
    with pytest.raises(ValueError):
        study.run(1, 1, 1, .05, tmp_path)
