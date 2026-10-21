"""Generate paper figures, numerical macros and bibliography from saved evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "generated"
INK, GREEN, ORANGE, MUTED, GRID = "#173c35", "#236657", "#b44d30", "#63736b", "#e0e5df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#a8b6ac", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=220, facecolor="white", bbox_inches="tight", pad_inches=.12)
    fig.savefig(OUT / f"{name}.pdf", facecolor="white", bbox_inches="tight", pad_inches=.12)
    plt.close(fig)


def revelation():
    fig, axes = plt.subplots(1, 3, figsize=(7, 3.2), gridspec_kw={"width_ratios": [1, 1, 1.3]})
    for ax, expanded in zip(axes[:2], (False, True)):
        ax.set(xlim=(-.5, 3.5), ylim=(-.55, 2.7))
        ax.axis("off")
        positions = [(0, 2), (0, 0), (3, 2), (3, 0)]
        edges = [(0, 2), (1, 3), (0, 3)] if expanded else [(0, 2), (1, 3)]
        for i, j in edges:
            active = (i, j) == (0, 3) if expanded else True
            a, b = positions[i], positions[j]
            ax.plot([a[0], b[0]], [a[1], b[1]], color=ORANGE if active and expanded else GREEN if active else "#bfc8c0",
                    lw=2.5 if active else 1.1, linestyle="-" if active else "--", zorder=1)
        for idx, (x, y) in enumerate(positions):
            ax.scatter([x],[y],s=320,facecolor="white",edgecolor=INK,linewidth=1.5,zorder=2)
            ax.text(x, y, ["a0", "a1", "b0", "b1"][idx], ha="center", va="center", fontsize=9)
        ax.text(1.5, 2.5, r"$(\varepsilon,1)$", ha="center", color=MUTED)
        ax.text(1.5, -.45, r"$(1,\varepsilon)$", ha="center", color=MUTED)
        if expanded:
            ax.text(1.4, 1.1, r"$(2\varepsilon,2\varepsilon)$", ha="center", color=ORANGE,
                    bbox=dict(fc="white", ec="none", pad=1))
        ax.set_title("B. After encounter" if expanded else "A. Before encounter", loc="left", fontsize=9, weight="bold")
        ax.text(1.5, -.9, r"Unique stable surplus: $4\varepsilon$" if expanded else r"Unique stable surplus: $2+2\varepsilon$",
                ha="center", fontsize=8, color=ORANGE if expanded else GREEN)
    ax = axes[2]
    eps = np.linspace(.001, .49, 400)
    ax.plot(eps, 2*eps/(1+eps), color=ORANGE, lw=2.5)
    ax.set(xlabel=r"$\varepsilon$", ylabel="Stable welfare retention ratio", xlim=(0,.5), ylim=(0,1))
    ax.grid(axis="y", color=GRID)
    ax.set_title("C. Welfare retained", loc="left", fontsize=9, weight="bold")
    ax.annotate(r"$2\varepsilon/(1+\varepsilon)\to0$", (.035,.068), (.08,.76),
                arrowprops=dict(arrowstyle="->", color=MUTED), color=INK)
    fig.subplots_adjust(wspace=.68, bottom=.2, top=.85)
    save(fig, "revelation")


def gaps(rows):
    fig, axes = plt.subplots(1,2,figsize=(7,3.5))
    colors = ["#c8d5c4", ORANGE, "#355a98"]
    for ax, budget in zip(axes, (8,16)):
        policies = ("random", "score_greedy", "coverage")
        values = np.array([[np.mean([float(r[k]) for r in rows if r["budget"]==str(budget)
                           and r["policy"]==p and r["proposer"]=="left"])
                            for k in ("information_gap", "stability_gap", "selection_gap")] for p in policies])
        bottom = np.zeros(3)
        for col, label, color in zip(values.T, ("Information", "Stability constraint", "DA selection"), colors):
            ax.bar(range(3), col, bottom=bottom, color=color, width=.55, label=label)
            bottom += col
        ax.set_xticks(range(3), ["Random", "Score greedy", "Coverage"], fontsize=9)
        ax.set_title(f"{budget} inspections", loc="left", fontsize=11, weight="bold")
        ax.set_ylim(0, 12)
        ax.grid(axis="y", color=GRID)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Lost gross surplus vs full planner")
    axes[1].legend(frameon=False, fontsize=9, loc="upper right")
    fig.text(.08,.015,"30 Gaussian 8-by-8 worlds; left DA. Selection gap is numerically zero.", fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=.19, wspace=.3)
    save(fig,"three_gaps")


def validation(summary):
    fig, ax = plt.subplots(figsize=(7,3.5))
    names={"baseline_policy":"Baseline: coverage − greedy, B=48",
           "noisy_policy":"Noisy/popular: coverage − greedy, B=48",
           "baseline_budget":"Coverage: B=192 − B=96"}
    for y, row in enumerate(summary["contrasts"]):
        m=row["bonferroni_family6"]
        color=GREEN if row["proposer"]=="left" else ORANGE
        ax.errorbar(m["mean"], y, xerr=[[m["mean"]-m["low"]],[m["high"]-m["mean"]]],
                    fmt="o" if row["proposer"]=="left" else "s", color=color, capsize=3)
    ax.set_yticks(range(6), [names[r["id"]]+f" ({r['proposer']})" for r in summary["contrasts"]],fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0,color=MUTED,lw=1,linestyle="--")
    ax.set_xlabel("Paired difference in net surplus per person")
    ax.set_xlim(-.085,.09)
    ax.set_xticks([-.08,-.04,0,.04,.08])
    ax.grid(axis="x",color=GRID)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=.49,bottom=.25,right=.98)
    fig.text(.04,.025,"500 worlds/scenario. Nominal 99.1667% percentile intervals, six contrasts.",fontsize=8,color=MUTED)
    save(fig,"validation")


def cost_frontier():
    original=list(csv.DictReader((ROOT/"results/information_worlds.csv").open()))
    fig,axes=plt.subplots(1,2,figsize=(7,3.4))
    costs=np.linspace(0,.5,301)
    budgets=[0,24,48,96,192]
    gross=[0.]+[np.mean([float(r["net_per_person"])+.05*b/48 for r in original
                        if r["scenario"]=="baseline" and r["policy"]=="coverage" and r["proposer"]=="left" and r["budget"]==str(b)]) for b in budgets[1:]]
    value=np.array([g-costs*b/48 for b,g in zip(budgets,gross)])
    for idx,b in enumerate(budgets[1:],1):
        axes[0].plot(costs,value[idx],color="#c1c9c2",lw=1)
    axes[0].plot(costs,value.max(axis=0),color=GREEN,lw=2.5)
    axes[0].set(xlabel="Per-pair inspection cost",ylabel="Optimized training net surplus/person",ylim=(0,1.05))
    axes[1].step(costs,np.array(budgets)[value.argmax(axis=0)],where="post",color=ORANGE,lw=2.5)
    axes[1].set(xlabel="Per-pair inspection cost",ylabel="Training-selected inspection budget",yticks=[0,24,48,96,192])
    for ax in axes:
        ax.grid(axis="y",color=GRID)
    fig.subplots_adjust(wspace=.35,bottom=.23)
    fig.text(.08,.015,"Coverage; finite schedules; original training means. Test evaluation: Table 2.",fontsize=8,color=MUTED)
    save(fig,"cost_envelope")


def tex_escape(s):
    table={"&":r"\&","%":r"\%","_":r"\_","#":r"\#","$":r"\$"}
    return "".join(table.get(c,c) for c in str(s))


def main():
    OUT.mkdir(exist_ok=True)
    summary=json.loads((HERE/"results/validation_summary.json").read_text())
    rows=list(csv.DictReader((HERE/"results/three_gaps.csv").open()))
    stress=list(csv.DictReader((HERE/"results/selection_stress.csv").open()))
    empirical=json.loads((ROOT/"results/empirical_audit.json").read_text())
    numbers={}
    for r in summary["contrasts"]:
        prefix={"baseline_policy":"Base","noisy_policy":"Noise","baseline_budget":"Budget"}[r["id"]]+r["proposer"].title()
        for key,suffix in (("mean","Mean"),("low","Low"),("high","High")):
            numbers[prefix+suffix]=r["bonferroni_family6"][key]
    numbers.update(ValidationWorlds=summary["worlds_per_scenario"], StressWorlds=len(stress),
                   StressMultiple=sum(int(r["stable_extremes_differ"]) for r in stress),
                   StressInterior=sum(int(r["best_strictly_exceeds_both"]) for r in stress),
                   StressLeftLoss=sum(float(r["best_stable"])-float(r["left_da"])>1e-9 for r in stress),
                   EmpiricalPairs=empirical["observed_pairs"],EmpiricalYes=empirical["mutual_yes_pairs"],
                   EmpiricalPercent=100*empirical["mutual_yes_rate"])
    macro=[]
    for key,value in numbers.items():
        rendered=str(value) if isinstance(value,int) else f"{value:.4f}"
        if key=="EmpiricalPercent":rendered=f"{value:.2f}"
        macro.append("\\newcommand{\\"+key+"}{"+rendered+"}")
    (OUT/"numbers.tex").write_text("\n".join(macro)+"\n",encoding="utf-8")
    (OUT/"numbers.json").write_text(json.dumps(numbers,indent=2)+"\n",encoding="utf-8")
    refs=json.loads((HERE/"references.json").read_text())
    bib=[r"\begin{thebibliography}{99}"]
    for r in sorted(refs["references"],key=lambda item:item["authors"][0].split()[-1].lower()):
        first=r["authors"][0].split()[-1]
        short=first+ (" et al." if len(r["authors"])>2 else " and "+r["authors"][1].split()[-1] if len(r["authors"])==2 else "")
        bib.append(r"\bibitem["+tex_escape(short)+"("+str(r["year"])+")]{"+r["id"]+"}")
        extra=(" "+str(r.get("volume",""))+("("+str(r["issue"])+")" if r.get("issue") else "")+(": "+str(r["pages"]) if r.get("pages") else "")).strip()
        bib.append(tex_escape(", ".join(r["authors"]))+". ("+str(r["year"])+"). "+tex_escape(r["title"])+". "+r"\textit{"+tex_escape(r["venue"])+"}"+(" "+tex_escape(extra) if extra else "")+". "+r"\href{"+r["url"]+"}{"+("doi:"+tex_escape(r["doi"]) if r.get("doi") else "Author manuscript")+"}.")
    bib.append(r"\end{thebibliography}")
    (OUT/"references.tex").write_text("\n".join(bib)+"\n",encoding="utf-8")
    # Tables bind directly to the same JSON that feeds figure annotations.
    table=[]
    for r in summary["contrasts"]:
        m=r["bonferroni_family6"]
        label={"baseline_policy":"Baseline policy","noisy_policy":"Noisy/popular policy","baseline_budget":"Budget 192 minus 96"}[r["id"]]
        table.append(f"{label} & {r['proposer'].title()} & {m['mean']:.4f} & [{m['low']:.4f}, {m['high']:.4f}] "+r"\\")
    (OUT/"validation_rows.tex").write_text("\n".join(table)+"\n",encoding="utf-8")
    header="\\begin{tabular}{llrr}\\toprule\nContrast & Proposer & Mean & Adjusted interval "+r"\\\midrule"+"\n"
    (OUT/"validation_table.tex").write_text(header+"\n".join(table)+"\n"+r"\bottomrule\end{tabular}"+"\n",encoding="utf-8")
    table=[]
    for r in summary["training_selected_budget_evaluation"]:
        if r["proposer"]=="left":
            m=r["heldout"]
            table.append(f"{r['cost']:.3f} & {r['selected_budget']} & {m['mean']:.4f} & [{m['low']:.4f}, {m['high']:.4f}] "+r"\\")
    (OUT/"cost_rows.tex").write_text("\n".join(table)+"\n",encoding="utf-8")
    header="\\begin{tabular}{rrrr}\\toprule\nCost per pair & Selected budget & Test net/person & 95\\% interval "+r"\\\midrule"+"\n"
    (OUT/"cost_table.tex").write_text(header+"\n".join(table)+"\n"+r"\bottomrule\end{tabular}"+"\n",encoding="utf-8")
    revelation();gaps(rows);validation(summary);cost_frontier()
    sources=[Path(__file__),HERE/"references.json",HERE/"results/validation_summary.json",
             HERE/"results/three_gaps.csv",HERE/"results/selection_stress.csv",
             ROOT/"results/empirical_audit.json",ROOT/"results/information_worlds.csv"]
    def hashed(path, binary=False):
        data=path.read_bytes()
        return hashlib.sha256(data if binary else data.replace(b"\r\n",b"\n")).hexdigest()
    manifest=dict(source_hashes={p.relative_to(ROOT).as_posix():hashed(p) for p in sources},
                  text_output_hashes={p.name:hashed(p) for p in OUT.iterdir() if p.suffix in (".tex",".json") and p.name!="manifest.json"},
                  binary_output_hashes={p.name:hashed(p,True) for p in OUT.iterdir() if p.suffix in (".pdf",".png")})
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
