"""Build README cover and performance figure from checked-in evidence.

Run: python experiments/make_identity.py. No simulations are run.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path as Curve

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
PAPER, FOREST, GREEN, ORANGE = "#f8f6f0", "#173c35", "#b9d5aa", "#eaa884"
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})


def text(ax, x, y, s, size=12, color=PAPER, **kw):
    return ax.text(x, y, s, fontsize=size, color=color, va="top", **kw)


def cover():
    d = json.loads((ROOT / "results/manipulation_n3.json").read_text())
    fig = plt.figure(figsize=(14, 7.4), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 140), ylim=(0, 74))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 25), 140, 49, boxstyle="square,pad=0", fc=FOREST, ec="none"))
    text(ax, 6, 68, "S / M     RESEARCH NOTEBOOK", 11, GREEN, weight="bold")
    text(ax, 6, 59, "Stable matching,", 37, weight="bold")
    text(ax, 6, 51, "under the surface.", 37, weight="bold")
    text(ax, 6, 40, "Who can gain by lying? How many people should you meet?", 12)
    text(ax, 6, 36, "Algorithms, incentives and costly search — made inspectable.", 12, "#c2d0c4")
    text(ax, 6, 29.5, "PYTHON  /  GALE–SHAPLEY  /  REPRODUCIBLE EXPERIMENTS", 9, GREEN)
    # A schematic bipartite graph, deliberately without empirical meaning.
    for i in range(4):
        for j in range(4):
            ax.plot([101, 129], [61-i*8, 61-j*8], color="#34574a", lw=0.7, zorder=1)
    for i, j in enumerate([2, 0, 3, 1]):
        y1, y2 = 61-i*8, 61-j*8
        path = Curve([(101, y1), (111, y1), (119, y2), (129, y2)],
                     [Curve.MOVETO, Curve.CURVE4, Curve.CURVE4, Curve.CURVE4])
        ax.add_patch(PathPatch(path, ec=GREEN if i % 2 == 0 else ORANGE, lw=2.5, fc="none", zorder=2))
    for side, x in enumerate([101, 129]):
        for i in range(4):
            ax.add_patch(Circle((x, 61-i*8), 1.8, fc=FOREST, ec=GREEN if side == 0 else ORANGE, lw=1.8, zorder=3))
    text(ax, 101, 65, "PROPOSE", 8, GREEN, ha="center")
    text(ax, 129, 65, "CHOOSE", 8, ORANGE, ha="center")
    text(ax, 115, 29.5, "MATCHING SCHEMATIC", 8, "#c2d0c4", ha="center")
    cards = [("01 / INCENTIVES", f"{d['profiles']:,}", "complete profiles, n = 3",
              "Every single-agent misreport checked."),
             ("02 / SEARCH", "Meet. Pay. Match.", "an endogenous outside option",
              "Batch size trades time against date cost."),
             ("03 / MARKETS", "Three mechanisms.", "one common simulated market",
              "One-shot DA, repeated cycles, events.")]
    for i, (label, title, sub, note) in enumerate(cards):
        x = 6 + i*44
        if i:
            ax.plot([x-3, x-3], [6, 21], color="#d7dccf", lw=1)
        text(ax, x, 21, label, 9, "#536e59", weight="bold")
        text(ax, x, 16.8, title, 23 if i == 0 else 18, FOREST, weight="bold")
        text(ax, x, 11.5, sub, 10, FOREST)
        text(ax, x, 8, note, 8.5, "#536e59")
    text(ax, 6, 2.8, "A MODEL, NOT A CLAIM ABOUT REAL DATING SERVICES.", 8, "#536e59")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "cover.png", dpi=160, facecolor=PAPER)
    plt.close(fig)


def benchmark():
    data = json.loads((ROOT / "results/benchmark_search.json").read_text(encoding="utf-8-sig"))
    eq = data["equilibrium"]
    fig = plt.figure(figsize=(13, 5.6), facecolor=PAPER)
    fig.text(.055, .91, "COMPUTATION / SAME MODEL, FASTER SEARCH", fontsize=10, color="#536e59", weight="bold")
    fig.text(.055, .80, "Spend time on the question.", fontsize=28, color=FOREST, weight="bold")
    fig.text(.055, .735, "Batch deferred acceptance across independent events.", fontsize=12, color="#405b54")
    fig.text(.055, .51, f"{eq['speedup']:.1f}×", fontsize=68, color=FOREST, weight="bold")
    fig.text(.06, .40, "faster equilibrium solve", fontsize=14, color=FOREST)
    fig.text(.06, .335, f"K = {eq['K']} · {eq['events']:,} events · one local run", fontsize=10, color="#536e59")
    ax = fig.add_axes([.51, .32, .43, .32], facecolor=PAPER)
    vals = [eq["scalar_seconds"], eq["batch_seconds"]]
    ax.barh([1, 0], vals, height=.38, color=["#c9d2c2", "#236657"])
    for y, v in zip([1, 0], vals):
        ax.text(v+.025, y, f"{v:.3f} s", va="center", fontsize=12, color=FOREST)
    ax.set_yticks([1, 0], ["Scalar DA", "Batch DA"], fontsize=11, color=FOREST)
    ax.set_xlim(0, max(vals)*1.28)
    ax.set_xticks([0, .5, 1.0], ["0", "0.5", "1.0 s"], fontsize=10, color="#536e59")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#bdc7bb")
    ax.tick_params(length=0, pad=8)
    fig.text(.055, .17, "Every partner checked against scalar DA. All equilibrium fields agree within 1e−12 tolerance.",
             fontsize=11, color=FOREST)
    fig.text(.055, .105, f"Python {data['python']} · NumPy {data['numpy']} · construction excluded · hardware-dependent timings",
             fontsize=9, color="#536e59")
    fig.text(.055, .06, "Source: results/benchmark_search.json  |  Reproduce: python experiments/benchmark_search.py",
             fontsize=9, color="#536e59")
    fig.savefig(OUT / "benchmark.png", dpi=160, facecolor=PAPER)
    plt.close(fig)


if __name__ == "__main__":
    cover()
    benchmark()
