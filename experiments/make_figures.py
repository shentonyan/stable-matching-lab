"""Draw the README figures from the saved results (no experiment is re-run).

usage: python experiments/make_figures.py        (needs matplotlib)
Writes docs/figures/*.png
"""

from __future__ import annotations

import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, Patch  # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "docs" / "figures"

# Palette: categorical slots 1-3, the blue ordinal ramp and neutral chrome.
# Every set was run through the dataviz palette validator (light mode,
# surface #fcfcfb) before use.
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, NEUTRAL_FILL = "#e1e0d9", "#c3c2b7", "#c8c7bf"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
ORDINAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # light -> dark

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9.5,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def style(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(0.8)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.7, linestyle="-")
    ax.set_axisbelow(True)
    ax.tick_params(length=0, labelsize=9, labelcolor=INK2, pad=5)


def headline(fig, text, sub=None, y=0.975):
    fig.text(0.012, y, text, fontsize=12.5, fontweight="semibold", color=INK, va="top")
    if sub:
        fig.text(0.012, y - 0.06, sub, fontsize=9.5, color=INK2, va="top")


def footnote(fig, text, y=0.012):
    fig.text(0.012, y, text, fontsize=8.2, color=MUTED, va="bottom")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("wrote", OUT / name)


# ---------------------------------------------------------------- figure 1
def fig_example():
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0))
    men = {"m0": (2.2, 4.2), "m1": (2.2, 1.6)}
    women = {"w0": (7.8, 4.2), "w1": (7.8, 1.6)}
    men_lists = {"m0": "w0 > w1", "m1": "w1 > w0"}
    women_true = {"w0": "m1 > m0", "w1": "m0 > m1"}
    panels = [
        ("A. Everyone reports truthfully",
         [("m0", "w0"), ("m1", "w1")], {"w0": "m1 > m0", "w1": "m0 > m1"},
         "w0 ends up with m0, her 2nd choice"),
        ("B. w0 declares m0 unacceptable",
         [("m0", "w1"), ("m1", "w0")], {"w0": "m1 only", "w1": "m0 > m1"},
         "w0 ends up with m1, her 1st choice"),
    ]
    for ax, (title, edges, reported, note) in zip(axes, panels):
        ax.set_xlim(-1.7, 11.7)
        ax.set_ylim(-0.4, 5.8)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.text(-1.7, 5.6, title, fontsize=10.5, fontweight="semibold", va="top")
        for a, b in edges:
            xa, ya = men[a]
            xb, yb = women[b]
            mine = b == "w0"
            ax.plot([xa, xb], [ya, yb], color=BLUE if mine else MUTED,
                    lw=2.6 if mine else 1.8, solid_capstyle="round", zorder=1)
        for name, (x, y) in men.items():
            ax.add_patch(Circle((x, y), 0.62, fc=SURFACE, ec=BLUE, lw=2.2, zorder=3))
            ax.text(x, y, name, ha="center", va="center", fontsize=10.5, zorder=4)
            ax.text(x - 0.95, y, men_lists[name], ha="right", va="center", fontsize=9.2, color=INK2)
        for name, (x, y) in women.items():
            ax.add_patch(Circle((x, y), 0.62, fc=SURFACE, ec=ORANGE, lw=2.2, zorder=3))
            ax.text(x, y, name, ha="center", va="center", fontsize=10.5, zorder=4)
            txt = ("reports: " if reported[name] != women_true[name] else "") + reported[name]
            ax.text(x + 0.95, y, txt, ha="left", va="center", fontsize=9.2, color=INK2)
        ax.text(5.0, -0.25, note, ha="center", va="center", fontsize=9.6, color=INK)
    headline(fig, "A receiver can gain by shortening her list",
             "Men propose. Each person's true ranking is shown next to the name; the blue line is w0's partner.",
             y=1.03)
    footnote(fig, "Circles: blue = proposing side (men), orange = receiving side (women). "
                  "Unit test: tests/test_gs.py::test_truncation_example_helps_the_receiver", y=-0.03)
    save(fig, "fig1_truncation_example.png")


# ---------------------------------------------------------------- figure 2
def fig_manipulation():
    data = {n: json.loads((RES / f"manipulation_n{n}.json").read_text()) for n in (3, 4)}
    rows = []
    for n, d in data.items():
        unique = d["unique_stable"] / d["profiles"]
        gain = d["women_gain"] / d["profiles"]
        assert abs(unique + gain - 1) < 1e-9, "every multi-stable profile had a gaining receiver"
        assert d["men_gain"] == 0
        label = f"n = {n}\n" + ("all " if n == 3 else "random sample of ") + f"{d['profiles']:,} profiles"
        rows.append((label, unique, gain))
    fig, ax = plt.subplots(figsize=(10.0, 3.3))
    style(ax, grid_axis="x")
    ys = [1, 0]
    for y, (label, unique, gain) in zip(ys, rows):
        ax.barh(y, unique, height=0.34, color=NEUTRAL_FILL, edgecolor=SURFACE, linewidth=1.5)
        ax.barh(y, gain, left=unique, height=0.34, color=BLUE, edgecolor=SURFACE, linewidth=1.5)
        ax.text(unique / 2, y, f"{unique:.1%}", ha="center", va="center", fontsize=10, color=INK)
        ax.text(unique + gain / 2, y, f"{gain:.1%}", ha="center", va="center", fontsize=10, color="white")
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.5, color=INK2)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.6, 1.6)
    ax.xaxis.set_major_locator(FixedLocator([0, 0.25, 0.5, 0.75, 1.0]))
    ax.xaxis.set_major_formatter(FixedFormatter(["0%", "25%", "50%", "75%", "100%"]))
    ax.set_xlabel("share of preference profiles")
    ax.legend(handles=[Patch(fc=NEUTRAL_FILL, label="unique stable matching: nobody can gain"),
                       Patch(fc=BLUE, label="2 or more stable matchings: some woman gains (a truncation works)")],
              loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, fontsize=9,
              handlelength=1.2, columnspacing=1.6)
    fig.subplots_adjust(top=0.78, left=0.2, right=0.985, bottom=0.2)
    headline(fig, "Who can profit from lying under men-proposing DA", y=1.02)
    footnote(fig, "Proposers (men): no profitable misreport in any of the "
                  f"{sum(d['profiles'] for d in data.values()):,} profiles checked. Source: results/manipulation_n*.json",
             y=-0.04)
    save(fig, "fig2_manipulation.png")


# ---------------------------------------------------------------- search data
def load_search():
    acc = defaultdict(lambda: defaultdict(list))
    with open(RES / "search_all.csv") as f:
        for r in csv.DictReader(f):
            if r["model"] != "two_sided":
                continue
            key = (float(r["c"]), float(r["delta"]), int(r["K"]))
            for fld in ("threshold", "match_prob", "partner_utility", "periods_to_match", "dates_to_match"):
                acc[key][fld].append(float(r[fld]))
    return {k: {f: st.mean(v) for f, v in fl.items()} for k, fl in acc.items()}


def log2_axis(ax, ticks):
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in ticks]))
    ax.xaxis.set_minor_locator(NullLocator())


# ---------------------------------------------------------------- figure 3
def fig_search_threshold(S):
    Ks = sorted({k[2] for k in S})
    cs = sorted({k[0] for k in S})
    ds = sorted({k[1] for k in S})
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.3), sharey=True)
    for ax, delta in zip(axes, ds):
        style(ax)
        for c, col in zip(cs, ORDINAL):
            ax.plot(Ks, [S[(c, delta, K)]["threshold"] for K in Ks], color=col, lw=1.9,
                    solid_capstyle="round", solid_joinstyle="round")
            kb = max(Ks, key=lambda K: S[(c, delta, K)]["threshold"])
            ax.plot([kb], [S[(c, delta, kb)]["threshold"]], "o", ms=8.5, color=col,
                    mec=SURFACE, mew=2, zorder=5)
        log2_axis(ax, [1, 2, 4, 8, 16, 32, 48])
        ax.set_ylim(-1.05, 1.55)
        ax.set_title(f"δ = {delta}", loc="left", fontsize=10.5, fontweight="semibold", color=INK, pad=8)
        ax.set_xlabel("batch size K (people met per period)")
    axes[0].set_ylabel("equilibrium outside option a*\n(net of date costs)")
    axes[0].yaxis.set_major_locator(FixedLocator([-1, -0.5, 0, 0.5, 1, 1.5]))
    handles = [Line2D([0], [0], color=col, lw=2.6, label=f"c = {c}") for c, col in zip(cs, ORDINAL)]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.045, 0.885), ncol=4, frameon=False,
               fontsize=9.5, title="cost per date (light to dark: low to high)", title_fontsize=9,
               alignment="left", handlelength=1.8, columnspacing=1.8)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.72, bottom=0.16, wspace=0.07)
    headline(fig, "The best batch size grows with patience and shrinks with date cost", y=0.995)
    footnote(fig, "Dots mark the best K on the grid. For c = 0.02 (all δ) and for c = 0.05 with δ = 0.95 the best K "
                  "is at the grid edge (48), so the true optimum may be larger.\n"
                  "Lines: mean of 3 Monte Carlo replicates of 3,000 events. Source: results/search_all.csv",
             y=-0.07)
    save(fig, "fig3_search_batch_size.png")


# ---------------------------------------------------------------- figure 4
def fig_search_tradeoff(S, c=0.05, delta=0.9):
    Ks = sorted({k[2] for k in S})
    row = {K: S[(c, delta, K)] for K in Ks}
    kstar = max(Ks, key=lambda K: row[K]["threshold"])
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.8, 4.2))

    style(a, grid_axis="both")
    xs = [row[K]["dates_to_match"] for K in Ks]
    ys = [row[K]["periods_to_match"] for K in Ks]
    a.plot(xs, ys, color=BLUE, lw=1.9, solid_capstyle="round")
    a.plot(xs, ys, "o", ms=8, color=BLUE, mec=SURFACE, mew=2, zorder=4)
    for K in (1, 4, 12, 32, 48):
        dx, dy = (10, 9) if K != 1 else (8, 7)
        a.annotate(f"K = {K}", (row[K]["dates_to_match"], row[K]["periods_to_match"]),
                   xytext=(dx, dy), textcoords="offset points", fontsize=9, color=INK2)
    a.set_xlabel("expected dates until a match")
    a.set_ylabel("expected periods until a match")
    a.set_xlim(0, 90)
    a.set_ylim(0, 12)
    a.set_title("A. More dates, shorter wait", loc="left", fontsize=10.5, fontweight="semibold", pad=8)

    style(b)
    q = [row[K]["partner_utility"] for K in Ks]
    t = [row[K]["threshold"] for K in Ks]
    b.plot(Ks, q, color=BLUE, lw=1.9, solid_capstyle="round")
    b.plot(Ks, t, color=ORANGE, lw=1.9, solid_capstyle="round")
    b.plot([kstar], [row[kstar]["threshold"]], "o", ms=8.5, color=ORANGE, mec=SURFACE, mew=2, zorder=5)
    b.annotate(f"best K = {kstar}", (kstar, row[kstar]["threshold"]), xytext=(-6, -26),
               textcoords="offset points", fontsize=9, color=INK2, ha="center")
    log2_axis(b, [1, 2, 4, 8, 16, 32, 48])
    b.set_xlim(0.85, 70)
    b.set_ylim(0, 1.9)
    b.set_xlabel("batch size K (people met per period)")
    b.set_ylabel("utility units")
    b.text(49.5, q[-1], "match quality", color=INK2, fontsize=9, va="center")
    b.text(49.5, t[-1] - 0.07, "outside option a*", color=INK2, fontsize=9, va="center")
    b.set_title("B. Quality keeps rising; net welfare peaks", loc="left", fontsize=10.5,
                fontweight="semibold", pad=8)
    b.legend(handles=[Line2D([0], [0], color=BLUE, lw=2.6, label="mean utility of the partner you get"),
                      Line2D([0], [0], color=ORANGE, lw=2.6, label="outside option a* (net of date costs)")],
             loc="lower right", frameon=False, fontsize=9)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.80, bottom=0.17, wspace=0.26)
    headline(fig, f"What a bigger batch buys and costs (c = {c}, δ = {delta})", y=1.0)
    footnote(fig, "Two-sided model with mutual acceptance; mean of 3 Monte Carlo replicates. "
                  "Source: results/search_all.csv", y=-0.04)
    save(fig, "fig4_search_tradeoff.png")


# ---------------------------------------------------------------- figure 5
def fig_market():
    rows = list(csv.DictReader(open(RES / "market_all.csv")))

    def get(group, setting, mech, field):
        for r in rows:
            if r["group"] == group and r["setting"] == setting and r["mechanism"] == mech:
                return float(r[field])
        raise KeyError((group, setting, mech, field))

    names = {"one_shot": "one-shot DA", "cycles": "repeated DA cycles", "events": "event matching",
             "oracle": "full-information DA (reference)"}
    colors = {"one_shot": BLUE, "cycles": ORANGE, "events": AQUA, "oracle": MUTED}
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 4.2), gridspec_kw={"width_ratios": [1, 1.1]})

    style(a, grid_axis="x")
    order = ["one_shot", "cycles", "events", "oracle"]
    for i, m in enumerate(order):
        y = len(order) - 1 - i
        v = get("default", "default", m, "fraction_coupled_mean")
        se = get("default", "default", m, "fraction_coupled_se")
        d = get("default", "default", m, "dates_per_person_mean")
        a.barh(y, v, height=0.46, color=colors[m], edgecolor=SURFACE, linewidth=1.5)
        a.plot([v - se, v + se], [y, y], color=INK, lw=1.0)
        a.text(v + 0.02, y, f"{v:.3f}", va="center", fontsize=9.5, color=INK)
        a.text(0.012, y - 0.43, f"{d:.1f} dates per person" if m != "oracle" else "60 dates per person",
               va="center", fontsize=8.3, color=INK2)
    a.set_yticks(range(len(order)))
    a.set_yticklabels([names[m] for m in reversed(order)], fontsize=9.3, color=INK2)
    a.set_xlim(0, 1.08)
    a.set_ylim(-0.7, len(order) - 0.45)
    a.set_xlabel("fraction of people who end up coupled")
    a.set_title("A. Default setting", loc="left", fontsize=10.5, fontweight="semibold", pad=8)

    style(b)
    sizes = [2, 5, 10, 20]
    xpos = list(range(len(sizes)))
    for m in ("events", "cycles"):
        ys = [get("dates", f"dates={s}", m, "fraction_coupled_mean") for s in sizes]
        b.plot(xpos, ys, color=colors[m], lw=1.9, solid_capstyle="round")
        b.plot(xpos, ys, "o", ms=8, color=colors[m], mec=SURFACE, mew=2, zorder=4)
        b.text(xpos[-1] + 0.1, ys[-1], f"{names[m]}  {ys[-1]:.3f}", va="center", fontsize=9, color=INK2)
    one = get("dates", "dates=2", "one_shot", "fraction_coupled_mean")
    orc = get("dates", "dates=2", "oracle", "fraction_coupled_mean")
    b.plot([xpos[0], xpos[-1]], [one, one], color=colors["one_shot"], lw=1.9)
    b.text(xpos[-1] + 0.1, one, f"{names['one_shot']}  {one:.3f}", va="center", fontsize=9, color=INK2)
    b.plot([xpos[0], xpos[-1]], [orc, orc], color=colors["oracle"], lw=1.4)
    b.text(xpos[0], orc + 0.012, f"full-information DA  {orc:.3f}", va="bottom", fontsize=9, color=INK2)
    b.set_xticks(xpos)
    b.set_xticklabels([str(s) for s in sizes])
    b.set_xlim(-0.25, 3.0 + 1.55)
    b.set_ylim(0.68, 0.96)
    b.set_xlabel("event size = maximum number of cycles")
    b.set_ylabel("fraction coupled")
    b.set_title("B. Larger events narrow the gap but do not close it", loc="left", fontsize=10.5,
                fontweight="semibold", pad=8)
    handles = [Patch(fc=colors[m], label=names[m]) for m in order]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.06, 0.885), ncol=4, frameon=False,
               fontsize=9, handlelength=1.2, columnspacing=1.6)
    fig.subplots_adjust(left=0.2, right=0.985, top=0.74, bottom=0.16, wspace=0.62)
    headline(fig, "Exploratory market simulation: who ends up coupled", y=1.0)
    footnote(fig, "Uncalibrated model; 60 men and 60 women, 200 random worlds per setting; bars: mean ± standard error. "
                  "In B, cycles use fewer\nthan the maximum number of dates (about 1.3 to 1.9 per person); one-shot "
                  "and the reference do not depend on event size. Source: results/market_all.csv", y=-0.07)
    save(fig, "fig5_market_simulation.png")


if __name__ == "__main__":
    S = load_search()
    fig_example()
    fig_manipulation()
    fig_search_threshold(S)
    fig_search_tradeoff(S)
    fig_market()
