"""Validate paper evidence hashes, exact gap accounting and numerical bindings."""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/"paper"
sys.path.insert(0,str(ROOT))
from paper.run_analysis import mean_interval


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n",b"\n")).hexdigest()


def validate():
    manifest=json.loads((HERE/"results/manifest.json").read_text())
    for group in ("source_hashes","input_hashes"):
        for path,value in manifest[group].items():
            assert digest(ROOT/path)==value, f"drifted {group}: {path}"
    for path,value in manifest["output_hashes"].items():
        assert digest(HERE/"results"/path)==value,f"drifted output: {path}"
    exact=list(csv.DictReader((HERE/"results/three_gaps.csv").open()))
    for r in exact:
        gaps=[float(r[k]) for k in ("information_gap","stability_gap","selection_gap")]
        assert min(gaps)>=-1e-9
        np.testing.assert_allclose(sum(gaps),float(r["full_planner"])-float(r["da_surplus"]),atol=1e-9)
    validation=json.loads((HERE/"results/validation_summary.json").read_text())
    rows=list(csv.DictReader((HERE/"results/validation_worlds.csv").open()))
    assert len(rows)==validation["worlds_per_scenario"]*20
    index={(r["scenario"],int(r["world"]),int(r["budget"]),r["policy"],r["proposer"]):r for r in rows}
    assert len(index)==len(rows)
    for r in validation["contrasts"]:
        a,b=r["candidate"],r["reference"]
        values=[float(index[(r["scenario"],w,a["budget"],a["policy"],r["proposer"])]["net_per_person"])
                -float(index[(r["scenario"],w,b["budget"],b["policy"],r["proposer"])]["net_per_person"])
                for w in range(validation["worlds_per_scenario"])]
        for label,family in (("ordinary95",1),("bonferroni_family6",6)):
            actual=mean_interval(values,validation["bootstrap_draws"],validation["seed"],family)
            for stat in ("mean","low","high"):
                np.testing.assert_allclose(actual[stat],r[label][stat],atol=1e-12,rtol=1e-12)
    refs=json.loads((HERE/"references.json").read_text())
    available={r["id"] for r in refs["references"]}
    tex=(HERE/"manuscript.tex").read_text(encoding="utf-8")
    cited=set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}",tex):
        cited.update(group.split(","))
    assert cited<=available, f"unknown citations: {cited-available}"
    assert not re.search(r"\[(?:CITE|NUM|ASK|TODO):|TBD|lorem ipsum",tex,re.I)
    numbers=json.loads((HERE/"generated/numbers.json").read_text())
    artifacts=json.loads((HERE/"generated/manifest.json").read_text())
    for path,value in artifacts["source_hashes"].items():
        assert digest(ROOT/path)==value, f"artifact source drift: {path}"
    for path,value in artifacts["text_output_hashes"].items():
        assert digest(HERE/"generated"/path)==value, f"artifact drift: {path}"
    for path,value in artifacts["binary_output_hashes"].items():
        assert hashlib.sha256((HERE/"generated"/path).read_bytes()).hexdigest()==value
    macros=(HERE/"generated/numbers.tex").read_text()
    for name,value in numbers.items():
        m=re.search(r"\\newcommand\{\\"+name+r"\}\{([^}]+)\}",macros)
        assert m is not None
        np.testing.assert_allclose(float(m.group(1)),value,atol=.005 if name=="EmpiricalPercent" else .000051)
    for r in validation["contrasts"]:
        prefix={"baseline_policy":"Base","noisy_policy":"Noise","baseline_budget":"Budget"}[r["id"]]+r["proposer"].title()
        for key,suffix in (("mean","Mean"),("low","Low"),("high","High")):
            assert numbers[prefix+suffix]==r["bonferroni_family6"][key]
    stress=list(csv.DictReader((HERE/"results/selection_stress.csv").open()))
    assert numbers["StressWorlds"]==len(stress)
    assert numbers["StressMultiple"]==sum(int(r["stable_extremes_differ"]) for r in stress)
    assert numbers["StressInterior"]==sum(int(r["best_strictly_exceeds_both"]) for r in stress)
    assert numbers["StressLeftLoss"]==sum(float(r["best_stable"])-float(r["left_da"])>1e-9 for r in stress)
    empirical=json.loads((ROOT/"results/empirical_audit.json").read_text())
    assert numbers["EmpiricalPairs"]==empirical["observed_pairs"]
    assert numbers["EmpiricalYes"]==empirical["mutual_yes_pairs"]
    assert numbers["EmpiricalPercent"]==100*empirical["mutual_yes_rate"]
    source_manifest=json.loads((HERE/"source_manifest.json").read_text())
    assert source_manifest["human_source_verification_complete"] is False
    source_ids={r["id"] for r in source_manifest["sources"]}
    for record in source_manifest["sources"]:
        if "sha256" in record:
            assert digest(ROOT/record["path"])==record["sha256"]
    lines=tex.splitlines()
    registry={r["claim_id"]:r for r in csv.DictReader((HERE/"claims.csv").open(encoding="utf-8"))}
    for idx,line in enumerate(lines):
        marker=re.fullmatch(r"% claim:(C\d+) evidence:([\w,]+)",line)
        if not marker:
            continue
        block=[]
        for following in lines[idx+1:]:
            if not following.strip():
                break
            if not following.lstrip().startswith("%"):
                block.append(following)
        assert set(marker[2].split(","))<=source_ids
        normalized=" ".join(" ".join(block).split())
        assert hashlib.sha256(normalized.encode()).hexdigest()==registry[marker[1]]["claim_hash"]
    print(f"Validated {len(exact)} exact rows, {len(rows):,} validation rows, six paired contrast intervals, citation keys, numerical macros and all analysis hashes.")


if __name__=="__main__":
    validate()
