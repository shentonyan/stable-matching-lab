# What is proved, and what is only a model assumption

These finite-market arguments are derived here. Their executable witnesses are
in `tests/test_research_theory.py`. They are not claims of novel matching theory,
and tests do not replace proofs for arbitrary market sizes.

## Environment and accounting

Let sides A and B have sizes n and m. A bilateral inspection reveals both
utilities on one pair. Let E be the set of distinct inspected pairs. Agent i has
outside utility r_i. An edge is acceptable only if both utilities strictly exceed
their respective outside utilities. Preferences on acceptable edges are strict
(or ties are resolved by a fixed rule). Unmatched agents receive r_i.

Gross welfare is the sum of matched utilities plus unmatched outside utilities.
Equivalently, relative to the fixed outside-option baseline it is

    S(M) = sum_(i,j in M) [(u_ij - r_i) + (v_ji - r_j)].

This is an analyst's cardinal objective. Summing nontransferable utilities assumes
a common cardinal scale; it does not mean agents can compensate one another.
Report side means and distributional outcomes as well as this sum.

If c is a **per-participant** inspection cost, total inspection cost is 2c|E|,
so per-person net surplus is [S(M) - 2c|E|]/(n+m). If c is a **per-pair** cost,
replace 2c|E| by c|E|. Repeated inspections, event overhead, delay and screening
costs require additional explicit terms; they are not included in this identity.

## Proposition 1: revealed stability has a restricted domain

DA on the mutually acceptable edges of E terminates at an individually rational
matching with no blocking pair in E. It need not eliminate blocking pairs outside E.

**Proof.** Each proposer advances down a finite list, so at most |E| proposals
occur. A receiver's held partner only improves. If an acceptable revealed pair
blocked the final outcome, the proposer must have proposed to that receiver
before settling for a worse partner or exhausting the list. Rejection means the
receiver held someone preferred at that time and hence also at termination, a
contradiction. Nothing in this argument concerns an edge absent from E. The
first witness below has exactly such a hidden blocking edge. QED.

An irrevocable sequence of matches is not generally DA on the union of all
inspected edges. Proposition 1 applies only if DA is rerun with every agent free
to rematch on that union; report stability of commitment mechanisms separately.

## Proposition 2: the planner bound is not the full-information DA outcome

Let F be the full set of individually rational edges, and let S* maximize S over
all one-to-one matchings using F, including the empty matching. For any feasible
policy producing M on the acceptable inspected edges E intersect F, S(M) <= S*. With nonnegative inspection cost,
its net surplus is also at most S*. This is a gross, zero-information-cost bound.

**Proof.** M belongs to the planner's feasible set, so its objective cannot exceed
the maximum. Subtracting a nonnegative cost preserves the inequality. QED.

The planner does not impose stability. A stability-constrained planner gives a
bound only for matchings stable on the same full graph. Full-information DA is
one stable allocation, not a maximum-surplus or maximum-cardinality benchmark
over arbitrary restricted-graph policies.

**Witness A (more information lowers DA welfare and match count).** Outside
utilities are zero. Rows of U are A agents; rows of V are B agents:

    U = [[4, 5], [0, 100]]     V = [[100, 0], [5, 4]].

With revealed edges {(0,0),(1,1)}, DA returns both diagonal pairs, total utility
208. Reveal (0,1) as well, completing the individually rational graph. A0 prefers
B1 and B1 prefers A0; DA returns only (0,1), total utility 10. Both outcomes are
stable on their own revealed graph. The diagonal outcome is blocked by (0,1) on
the full graph. Thus full-information DA has fewer matches and lower welfare
than this restricted-information allocation. Exhaustive enumeration of every
feasible full-graph matching confirms planner surplus 208.

**Witness B (a higher stable match count need not mean higher welfare).**

    U = [[100, 4], [4, 0]]     V = [[4, 5], [4, 0]].

On revealed graph {(0,0)}, DA matches (0,0), total utility 104. After adding
(0,1) and (1,0), B0 prefers A1 to A0. DA returns (0,1),(1,0), total utility 17.
The match count rises from one to two while welfare falls. These comparisons
change the graph. They do not assert different cardinalities among stable
matchings of the same fixed graph.

These are counterexamples to universal monotonicity, not predictions of average
effects in random markets. Inspection costs would further change net welfare.

## Proposition 3: inspection budgets saturate in finite markets

Suppose each pair can be inspected at most once and each agent on both sides has
degree cap k. Then

    |E| <= min(nm, nk, mk),       sum_i degree(i) = 2|E|.

**Proof.** There are nm possible edges. Summing degree caps separately over A
and B gives nk and mk. Each edge contributes once to each side's degree sum,
yielding the identity. QED.

In a balanced n-by-n market, k >= n cannot reveal additional distinct pairs.
Unused capacity is not an incurred inspection cost. A nominal round cap, an
event-size parameter, a total inspection cap and a per-person cap are different
constraints; equal nominal values need not define equal-budget experiments.

## The reservation-value fixed point is a closure, not a proved Nash equilibrium

Under the original timing, a single agent pays cK now; a match pays u starting
next period. With fresh independent opportunities after failure and constant
per-period match probability p_s and unconditional matched utility g_s on side s,

    V_s = -cK + delta [g_s/(1-delta) + (1-p_s)V_s],
    V_s = [-cK + delta g_s/(1-delta)]/[1-delta(1-p_s)].

Comparing accepting u to continuing at the *same next-period decision point*
gives u/(1-delta) >= V_s, hence a_s=(1-delta)V_s. Both continuation alternatives
share the factor delta; mixing current-period and next-period payoffs would
produce an inconsistent cutoff.

In balanced events the number matched is equal on both sides, so p_A=p_B.
However proposer-proposing DA can give g_A != g_B even under exchangeable utility
draws. Averaging utilities across the sides yields a pooled value, not evidence
that each side has this same continuation value. A common scalar cutoff is a
reservation-value accounting closure. A two-cutoff closure would still require
an existence argument, numerical residual checks, and a best-response analysis
before being called an equilibrium of strategic reporting and acceptance.

Replacing matched agents maintains pool size. It does not alone establish the
stationary distribution of survivors: if persistent latent types or utilities
affect exits, survivor composition can change. The iid redraw model avoids that
selection channel by assumption, not by an estimated demographic process.

Common random numbers reduce comparison noise but make finite Monte Carlo
statistics step functions, not smooth population functions. Bisection and a
small bracket alone do not prove a small fixed-point residual or uniqueness.
Holdout cutoff audits can find profitable deviations within a specified grid;
failure to find one on that grid does not prove Nash equilibrium.
