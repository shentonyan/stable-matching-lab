"""Audit a locally obtained original Columbia CSV; write aggregates only.

python experiments/audit_speed_dating.py --input data/raw/speed-dating.csv
Obtain the original source with iid/pid/wave; cleaned OpenML drops graph IDs.
No raw records or participant identifiers are written to the output.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stablematch.empirical import audit_file

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "results/empirical_audit.json")
    p.add_argument("--source-accessed", type=date.fromisoformat, default=None,
                   help="Actual retrieval date YYYY-MM-DD, if known; not inferred from analysis date")
    args = p.parse_args()
    result = audit_file(args.input)
    result["source"] = "https://www.stat.columbia.edu/~gelman/arm/examples/speed.dating/Speed%20Dating%20Data.csv"
    result["source_accessed"] = args.source_accessed.isoformat() if args.source_accessed else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    sensitivity = {}
    for label, excluded in (("without_yes_budget_wave", [12]),
                             ("without_dictionary_flagged_variants", [5, 12, 13, 14, 18, 19, 20, 21])):
        filtered = audit_file(args.input, exclude_waves=excluded)
        sensitivity[label] = {k: v for k, v in filtered.items() if k != "per_wave"}
    sensitivity["interpretation"] = ("Descriptive sample-composition sensitivity only; not causal and not a reconstruction "
                                     "of the original paper's 14-session estimation sample.")
    args.output.with_name(args.output.stem+"_sensitivity.json").write_text(
        json.dumps(sensitivity, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "per_wave"}, indent=2))
