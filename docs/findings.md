# Findings and unresolved questions

These results are exploratory and conditional on the model in
[research-design.md](research-design.md). All estimates below use the saved
run with seed 20261021. Within each of eight scenarios, 100 independent world
draws are reused across four budgets, three policies and two proposer sides.
The resulting 19,200 treatment rows are **not 19,200 independent markets**.
The scenarios also reuse seeds. Intervals resample whole worlds within scenario;
they measure Monte Carlo uncertainty, not structural uncertainty or real-platform
policy effects. Multiple comparisons have no family-wise error correction.

## Targeting scores helps, but spreading opportunities can add value

The baseline has 24 participants per side, popularity variance share .5,
pair-shock reciprocity .5, signal-noise standard deviation 1, outside option 0
and per-pair inspection cost .05. At 48 distinct inspections with left-proposing
DA, mean net surplus per person is .2704 for random exposure, .6474 for score
greedy and .7189 for coverage discounting. Coverage-minus-greedy is **.0715**,
with paired bootstrap 95% interval **[.0572,.0862]**. The minimum side exposure
rate increases by **.205**, or 20.5 percentage points. Exposure here means at
least one inspection, not a match or a protected-group fairness guarantee.

| Baseline budget | Random net/person | Greedy net/person | Coverage net/person | Coverage fraction matched |
|---:|---:|---:|---:|---:|
| 24 | .1613 | .5292 | .6654 | .5738 |
| 48 | .2704 | .6474 | .7189 | .6254 |
| 96 | .3910 | .7153 | .7420 | .6683 |
| 192 | .4701 | .6776 | .6852 | .7208 |

Source: [summary](../results/information_summary.json), baseline, left proposer.
All participants, including singles, enter the welfare denominator. The common
cost cancels within a fixed-budget contrast; this comparison isolates allocation
under that budget, not an inspection-price effect.

## More inspections are not automatically better

In the baseline grid, coverage's average match fraction increases between
96 and 192 inspections, but average net surplus per person falls from .7420
to .6852. This is a descriptive budget comparison at the assumed cost, not a
proof that 96 is globally optimal. Only four budgets are evaluated. The exact
two-by-two witnesses in [theory.md](theory.md) separately show that even gross
DA surplus and match count need not increase when information expands.

Coverage's gains also depend on the structural scenario. At 48 inspections,
the high-popularity/noisy case gives coverage-minus-greedy **.0078**, with
interval **[-.0032,.0184]**. At 192 inspections in the scarce-right case, the
mean difference is **-.0034**, interval **[-.0123,.0052]**. Neither interval
supports a reliable positive gain in its stated comparison. Coverage is an
untuned heuristic, not a universally dominant policy or an optimal learning rule.
All scenarios, both proposer sides and secondary outcomes are retained in the
world-level CSV rather than filtered by favorable results.

## Missing information and the allocation objective create different losses

The 30 small-market worlds have eight participants per side and budgets 8,
16 and 32, with both proposer sides. An exact dynamic program computes
unconstrained maximum-surplus individually rational matchings on both the full
and revealed graphs. For each of 540 treatment rows,

    full planner surplus - DA surplus
      = missing-information loss + DA allocation loss.

The code checks both components are nonnegative. Allocation loss combines the
stability restriction with selection of a particular proposer-optimal stable
allocation; it cannot be interpreted as a pure causal cost of stability.
The planner can return an unstable matching, and its full-information upper
bound assumes free access to all utilities. It is a diagnostic benchmark,
not an implementable competitor spending the same information budget.

Source: [exact-reference rows](../results/information_decomposition.csv).

## The old scalar root survives one diagnostic, not an equilibrium proof

The legacy iid-reset search diagnostic fits its common cutoff on 2,000 training
events and evaluates the selected focal-agent deviation on 2,000 independent
test events. At K=4, c=.1, delta=.9, the common cutoff is **.690704**, with
training closure residual **-.0000291**. The 13-point deviation grid selects
the common cutoff for each side, so held-out deviation gains are zero.

This is a retained null diagnostic. There is no profitable grid deviation in
that experiment; there is also no certification against arbitrary deviations,
other K/c/delta values, type-dependent behavior or strategic reporting. Pooled
side utilities remain an accounting closure. Source:
[threshold audit](../results/threshold_audit.json).

## Observed encounters constrain interpretation

The original Columbia CSV contains 8,378 directed records. Ten unusable rows
are excluded; deduplication produces 4,184 encounters across 21 waves, all with
usable bilateral decisions. There are 690 mutual-yes edges, **16.49%** of those
encounters. Resampling the 21 heterogeneous waves gives a descriptive 95%
interval **[14.93%,18.27%]**. Every retained within-wave cross-side pair is
observed among participants represented in the CSV; all wave coverage ratios
are one on that represented population. This historical event design is
different from a modern recommendation platform with selectively observed pairs.

There are 551 participant-wave records in the cohort counts. Across the recorded
mutual-yes graphs, a maximum of 204 disjoint pairs can be selected under an
imposed one-to-one restriction. These are retrospective combinatorial outputs,
not actual relationships, strict stable matchings or welfare estimates. Participants
could express interest in multiple people, and one wave explicitly limited
the number of yes decisions. The all-wave audit is not a replication of the
paper's 14-session sample. Excluding the acceptance-budget wave yields 16.78%
mutual yes; removing all dictionary-flagged variants yields 16.76% across 13
waves. These are exploratory composition checks, not policy treatment effects
or a reproduction of the published estimation sample. See [data-protocol.md](data-protocol.md).

## What remains needed for a research contribution

The strongest completed claim is a reproducible conditional mechanism comparison,
supported by exact finite counterexamples and an observed-data audit. Costly
information acquisition and congestion already have close prior art; novelty
has not been established. A stronger next study needs a clearly differentiated
theoretical result or a credible empirical identification design.

Concrete extensions are individual inspection capacities, endogenous participation,
belief updating using inspected outcomes, policy tuning on separate training
worlds, a stable-optimum decomposition separating selection from stability,
and cohort-held-out prediction from genuinely pre-encounter features. Persistent
population dynamics, real meeting costs, long-term outcomes and externally
validated platform effects remain unimplemented.
