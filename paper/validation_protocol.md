# Additional analysis plan for the working paper

Written before executing `paper/run_analysis.py`. This is an internally recorded
computational validation plan, not a publicly preregistered human-subject study.
The original eight-scenario results were already observed and motivated these
contrasts. New worlds evaluate those selected claims independently; they do not
turn the original exploration into a preregistered study.

## Exact three-gap accounting

Reuse the 30 original 8-by-8 worlds and all 540 small-market treatment rows.
Compute the maximum-surplus stable matching on each distinct revealed graph,
under the same strict preferences as DA. Check against the saved outcomes and
split the previous DA allocation gap into stability and DA-selection components.
The exact solver enumerates at most k! assignments between invariant stable
matched-agent sets, where k<=8; independent brute-force tests check this reduction.

## Independent simulation validation

Use 500 worlds per scenario, seed 20271101 + world index, distinct from the
original seed range. Hold all original structural definitions fixed. Evaluate
the baseline at budgets 24, 48, 96 and 192 and the high-popularity/noisy scenario
at budget 48. Use score-greedy and coverage policies, both proposer directions,
and per-pair cost .05. Policy parameters remain fixed and untuned.

The six primary contrasts are the following three differences for each proposer:

1. Baseline coverage minus score greedy, budget 48.
2. High-popularity/noisy coverage minus score greedy, budget 48.
3. Baseline coverage budget 192 minus coverage budget 96.

The estimand is the mean paired difference in net surplus per person. Resample
whole independent worlds, keeping each contrast paired, with 20,000 bootstrap
draws. Report ordinary 95% percentile intervals and Bonferroni-adjusted intervals
with marginal coverage 1-.05/6 = 99.1667%. The adjustment uses asymptotic
bootstrap intervals; it is not an exact finite-sample family-wise guarantee.
All six contrasts are retained, irrespective of direction or interval.

## Cost comparative statics

At costs {0,.025,.05,.1,.2,.4}, choose a coverage-policy budget from
{0,24,48,96,192} using mean gross surplus in the original training worlds.
Break ties toward the smaller budget. Freeze these choices, then report their
mean net surplus in the new baseline worlds with ordinary world-bootstrap 95%
intervals. The zero-inspection option has zero incremental surplus. Choices
optimize only this finite candidate set, not all feasible acquisition policies.
No future outcome is allowed to change which budget was selected on training.

## Interpretation and provenance

The experiment tests reproducibility across independent synthetic draws.
No result identifies human preferences, an exposure-policy causal effect or
a globally optimal policy. Exact propositions are separated from Monte Carlo
estimates, and external novelty is not presumed. Store raw treatment rows,
summaries, source hashes, input hashes, seed, runtime versions and all null results.

## Post hoc exact-solver stress diagnostic

The first execution found no positive DA-selection gap in the 540 original
small-market rows. A separate diagnostic was consequently added: 500 complete
4-by-4 markets with independent U(.1,10) cardinal utilities, seed 20271101+100000.
This tests the exact stable benchmark in a population with more competing stable
allocations. Its utility scale and acceptability differ from the Gaussian study;
it is not an independent confirmation of the primary six contrasts, and its
results must not be pooled with them. Report all left/right DA and best-stable
values, including cases where the best stable outcome is neither DA extreme.
