"""Train/holdout diagnostic for the legacy pooled threshold closure.

python experiments/run_threshold_audit.py --events 2000
No Nash certification: finite grid, iid reset opponents, one fixed K/c/delta.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stablematch.search import EventSimulator, solve_threshold
from stablematch.search_audit import focal_outcomes, renewal_value, paired_value_interval


def run(events=2000, K=4, c=.1, delta=.9, seed=20261021):
    train = EventSimulator(K, events, seed)
    test = EventSimulator(K, events, seed + 1)
    common = solve_threshold(train, K, c, delta).threshold
    from stablematch.search import _value
    pooled_p, pooled_g = train(common)
    residual = (1-delta)*_value(K, c, delta, pooled_p, pooled_g)-common
    grid = common + np.linspace(-.75, .75, 13)
    rows = []
    for side in ("left", "right"):
        values = [renewal_value(focal_outcomes(train, common, b, side), K, c, delta) for b in grid]
        b = float(grid[np.argmax(values)])
        base = focal_outcomes(test, common, common, side)
        dev = focal_outcomes(test, common, b, side)
        v0, v1 = renewal_value(base, K, c, delta), renewal_value(dev, K, c, delta)
        rows.append(dict(side=side, selected_cutoff=b, heldout_baseline_value=v0,
                         heldout_candidate_value=v1, heldout_gain=v1-v0,
                         paired_bootstrap_95=paired_value_interval(base, dev, K, c, delta, seed=seed),
                         train_values=values))
    return dict(K=K, c=c, delta=delta, events_per_split=events, seed=seed,
                common_cutoff=common, training_closure_residual=float(residual),
                deviation_grid=grid.tolist(), sides=rows,
                interpretation="Exploratory finite-grid deviation diagnostic, not an equilibrium certificate.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=2000)
    parser.add_argument("--output", type=Path, default=ROOT / "results/threshold_audit.json")
    args = parser.parse_args()
    result = run(args.events)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
