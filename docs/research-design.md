# Information, congestion and stable matching: computational study protocol

## Question and scope

When bilateral compatibility must be learned through costly encounters, how
should a platform allocate a fixed number of encounters? We compare random,
score-targeted and coverage-discounted exposure, holding both the latent market
and the realized number of inspected pairs fixed. The project studies a
finite-market allocation problem; it does not claim a new equilibrium theory,
optimal acquisition policy or calibrated prediction for dating services.

The study is exploratory. This protocol was written before the new experiment
runner's first execution, but it is not an externally registered analysis plan.
All scenario contrasts, negative results and proposer directions are retained.
After the first run, terminology was tightened to call the second planner gap
an allocation loss rather than a pure stability cost, and to distinguish
saturation unit tests from unsaturated experiment budgets. Parameters, policies
and reported scenarios were retained. Artifact hashes normalize CRLF to LF so
Git checkouts on different operating systems can validate the same text.

## Structural model

For left agent i and right agent j, draw independent standard-normal popularity
terms A_i,B_j and pair shocks X_ij,Z_ij. Set

    u_ij = sqrt(alpha) B_j + sqrt(1-alpha) X_ij
    v_ij = sqrt(alpha) A_i + sqrt(1-alpha)
           [rho X_ij + sqrt(1-rho^2) Z_ij].

Each marginal utility has variance one. Popularity induces dependence between
the evaluations of a shared partner. Reciprocal utility correlation on a pair
is (1-alpha)rho, so changing alpha also changes total bilateral correlation.
That is a structural interaction, not an isolated causal congestion treatment.
Both positive and negative reciprocal compatibility can be tested.

Observable scores equal true utility plus independent N(0,sigma²) noise.
They are noisy signals, not posterior expected utilities. The platform sees
the entire score matrix before inspections; screening has no modeled cost.
An inspection reveals both true utilities on a pair. Reveal decisions do not
use latent utilities, and no uninspected pair can match. Outside utilities
are absolute inputs, rather than oracle quantiles of unknown alternatives.

All revealed mutually acceptable pairs are ranked by true utility and matched
with deferred acceptance. All participants can rematch at this final stage;
there is no irrevocable early commitment. Left- and right-proposing versions
are separate treatments. Index order breaks utility ties. Inspections are a
total market budget, not individual degree caps or sequential arrival slots.

## Policies and costs

- Random: sample B distinct pairs uniformly, independent of true utility.
- Score greedy: rank the sum of positive bilateral predicted surplus, giving
  zero priority when either endpoint's score does not beat its outside option.
- Coverage: discount that priority by [(1+d_i)(1+d_j)]^gamma, where d counts
  inspections allocated so far. Gamma=1 is the declared baseline, not a tuned
  optimum. A 1e-6 priority floor resolves zero-score coverage; ties use index
  order. The schedule is coverage-aware but does not update beliefs from the
  newly revealed utilities. It is not adaptive Bayesian learning.

Use exactly min(B,nm) distinct pairs. Gross surplus S sums utility above
individual outside options over **all** people, with unmatched surplus zero.
Pair cost c is paid once per inspected pair; net population surplus per person
is (S-c min(B,nm))/(n+m). Costs are a platform aggregate; we do not assign the burden to
individual sides or use it in the gross-surplus Gini. Equal budgets cancel
the cost term in within-budget policy contrasts; cost matters across budgets.

## Scenarios and comparisons

The baseline has 24 agents on each side, alpha=.5, rho=.5, sigma=1, outside
option zero, pair cost .05, and B/n_left in {1,2,4,8}. Crossed stress cases
vary popularity and noise together; further cases use negative reciprocity,
scarce right-side participants, and heterogeneous outside options. Settings
are declared in the runner and saved in the output manifest.

Each scenario has 100 independent worlds by default. All policies, budgets
and proposer directions share a world's latent draws and signal noise.
Random-policy allocations use independent reproducible seeds per world and
budget. They are **not** required to be nested as budget increases, so
individual random-policy paths must not be interpreted as deterministic
marginal-information experiments. Scenario worlds reuse seeds for variance
reduction, but primary policy comparisons condition on scenario.

Primary metric: net surplus per person. Secondary metrics: fraction of all
people matched, each side's mean gross surplus, minimum side exposure rate,
gross surplus Gini (zero if all surpluses are zero), and hidden blocking pairs
per possible pair. Revealed blocking must be zero in every run.

Report means and paired bootstrap 95% intervals for coverage-minus-greedy and
greedy-minus-random within a scenario, budget and proposer direction. Resample
worlds, not agents or edges. Intervals express simulation uncertainty conditional
on chosen structural assumptions; exploratory multiple comparisons have no
family-wise error control. No policy is selected on the evaluation sample.

## Small-market decomposition and theory

For 8-by-8 markets, independently compute maximum-surplus individually rational
matchings by exact dynamic programming, both on the revealed graph and on the
full graph. The planner need not be stable. Then decompose

    S*_full - S_DA = (S*_full - S*_revealed) + (S*_revealed - S_DA).

The first term is lost feasible surplus due to incomplete information. The
second is the loss from using a particular stable DA outcome instead of the
revealed-graph surplus optimum. This allocation gap includes both the stability
constraint and selection of the proposer-optimal stable outcome; it is not an
identified pure cost of stability. Both terms are nonnegative; the decomposition is gross and excludes
inspection costs. Full-information DA is reported separately, never as an
upper bound. Exact tiny counterexamples in [theory.md](theory.md) disprove
universal monotonic gains from revealing more edges.

## Falsification, robustness and real-data boundary

Implementation tests cover hidden-information isolation, exact budgets, both
proposer directions, revealed stability, strict cutoff boundaries and exact
planner comparisons against brute force. Crossing popularity with noise can
falsify a universal claim that coverage always improves matching or welfare.
Unit tests verify finite-market saturation. The experimental budgets remain
below full revelation and test diminishing returns and excessive inspection costs.

The old iid-reset search model receives a separate training/holdout cutoff
audit. The common pooled cutoff and best grid deviations are selected using
training events; held-out paired bootstrap intervals evaluate the selected
deviation. A null diagnostic is retained and is not an equilibrium certificate.

The Columbia data audit uses only observed encounters and recorded yes/no
decisions. It checks reciprocal records and graph feasibility, not latent
cardinal utility, counterfactual unseen-pair outcomes or causal policy effects.
Its cohort composition differs from the original paper's analyzed sample.
See [data-protocol.md](data-protocol.md) and [evidence.md](evidence.md).

Next identifiable study: obtain prospectively randomized exposure assignments,
pre-encounter signals, mutual-interest decisions, time/cost burdens and later
retention outcomes. Use participant-disjoint or whole-cohort holdouts and prevent
post-encounter rating leakage. A real platform experiment needs an independently
reviewed protocol and participant protections; no such experiment is conducted
by this repository.
