"""Render research figures from the saved world-level results only."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results", ROOT / "docs/figures"
PAPER, INK, MUTED = "#f8f6f0", "#173c35", "#536e59"
COLORS = {"random": "#8b9682", "score_greedy": "#b44d30", "coverage": "#236657"}
LABELS = {"random": "Random", "score_greedy": "Score greedy", "coverage": "Coverage"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "figure.facecolor": PAPER, "axes.facecolor": PAPER,
                     "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED})


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#bdc7bb")
    ax.grid(axis="y", color="#e4e5da", linewidth=.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6)


def main():
    data = json.loads((RES / "information_summary.json").read_text())
    manifest = json.loads((RES / "information_manifest.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6), gridspec_kw={"width_ratios": [1, 1.25]})
    fig.subplots_adjust(left=.065, right=.96, bottom=.25, top=.73, wspace=.75)
    a, b = axes
    for ax in axes:
        style(ax)
    for policy in COLORS:
        rows = sorted([r for r in data["summary"] if r["scenario"] == "baseline"
                       and r["proposer"] == "left" and r["policy"] == policy], key=lambda r: r["budget"])
        x = [r["budget"] for r in rows]
        m = [r["metrics"]["net_per_person"]["mean"] for r in rows]
        low = [r["metrics"]["net_per_person"]["low"] for r in rows]
        high = [r["metrics"]["net_per_person"]["high"] for r in rows]
        a.plot(x, m, marker={"random": "s", "score_greedy": "^", "coverage": "o"}[policy],
               color=COLORS[policy], label=LABELS[policy], linewidth=2)
        a.fill_between(x, low, high, color=COLORS[policy], alpha=.12, linewidth=0)
    a.set_xticks([24, 48, 96, 192])
    a.set_xlabel("Distinct pair inspections")
    a.set_ylabel("Net surplus per person (synthetic units)")
    a.set_ylim(0, .9)
    a.set_title("01 / Spending more can cost more than it adds", loc="left", fontsize=11, weight="bold", pad=18)
    a.legend(frameon=False, fontsize=9, loc="lower right")
    rows = [r for r in data["paired_contrasts"] if r["candidate"] == "coverage"
            and r["budget"] == 48 and r["proposer"] == "left"]
    names = {"baseline": "Baseline", "heterogeneous_outside": "Unequal outside options",
             "high_popularity_noisy": "High popularity / noisy",
             "high_popularity_precise": "High popularity / precise",
             "low_popularity_noisy": "Low popularity / noisy",
             "low_popularity_precise": "Low popularity / precise",
             "negative_reciprocity": "Negative reciprocity", "scarce_right": "Scarce right side"}
    for y, r in enumerate(rows):
        m = r["metrics"]["net_per_person"]
        b.errorbar(m["mean"], y, xerr=[[m["mean"]-m["low"]], [m["high"]-m["mean"]]],
                   fmt="o", color=COLORS["coverage"], capsize=3, markersize=6)
    b.set_yticks(range(len(rows)), [names[r["scenario"]] for r in rows], fontsize=9)
    b.invert_yaxis()
    b.axvline(0, color="#8b9682", linewidth=1, linestyle="--")
    b.set_xlim(-.015, .17)
    b.set_xlabel("Coverage − score greedy: net surplus / person")
    b.set_title("02 / Gains depend on the signal and market", loc="left", fontsize=11, weight="bold", pad=18)
    fig.text(.065, .93, "INFORMATION HAS A PRICE. SO DOES CONCENTRATION.", fontsize=12, color=MUTED, weight="bold")
    fig.text(.065, .84, "Equal budgets. Different opportunities.", fontsize=27, weight="bold")
    fig.text(.065, .13, f"{manifest['worlds']} worlds per scenario · left-proposing DA · pair cost {manifest['pair_cost']} · right panel: 48 inspections",
             fontsize=10, color=MUTED)
    fig.text(.065, .085, "Bands / whiskers: 95% world-bootstrap intervals; policy differences paired. Exploratory comparisons, no multiplicity correction.", fontsize=9, color=MUTED)
    fig.text(.065, .045, "Synthetic assumptions, not a calibrated platform effect. Source: results/information_summary.json", fontsize=9, color=MUTED)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "information_tradeoffs.png", dpi=180, facecolor=PAPER)
    plt.close(fig)

    rows = list(csv.DictReader((RES / "information_decomposition.csv").open()))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6))
    fig.subplots_adjust(left=.09, right=.96, top=.72, bottom=.25, wspace=.35)
    for ax, budget in zip(axes, (8, 16)):
        style(ax)
        losses = []
        for policy in COLORS:
            subset = [r for r in rows if r["policy"] == policy and int(r["budget"]) == budget and r["proposer"] == "left"]
            losses.append([np.mean([float(r[key]) for r in subset]) for key in ("information_loss", "da_allocation_loss")])
        x = np.arange(3)
        a, b = np.array(losses).T
        ax.bar(x, a, color="#c9d2c2", width=.5, label="Missing information")
        ax.bar(x, b, bottom=a, color="#b44d30", width=.5, label="DA vs revealed optimum")
        ax.set_xticks(x, list(LABELS.values()), fontsize=9)
        ax.set_ylim(0, 14)
        ax.set_title(f"{budget} distinct inspections", loc="left", fontsize=12, weight="bold")
    axes[0].set_ylabel("Lost gross surplus vs full planner optimum")
    axes[1].legend(frameon=False, loc="upper right", fontsize=9)
    fig.text(.09, .91, "DECOMPOSE THE GAP", fontsize=11, color=MUTED, weight="bold")
    fig.text(.09, .81, "Information loss and allocation loss are different.", fontsize=23, weight="bold")
    fig.text(.09, .13, f"8 × 8 markets · {manifest['small_worlds']} worlds · left-proposing DA · means, descriptive only · no inspection costs in this decomposition", fontsize=9, color=MUTED)
    fig.text(.09, .075, "Planner: maximum-surplus individually rational matching; may be unstable. Source: results/information_decomposition.csv", fontsize=9, color=MUTED)
    fig.savefig(OUT / "information_decomposition.png", dpi=180, facecolor=PAPER)
    plt.close(fig)


if __name__ == "__main__":
    main()
