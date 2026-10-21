# Theory notes: costly information under a stability requirement

These are self-contained finite-market results, not claims of priority over
existing theory. They explain which mechanisms the computational study can
separate. Outside utilities are zero unless stated otherwise. A pair is
individually rational (IR) only when both utilities are strictly positive.
Preferences over IR partners are strict. Welfare sums cardinal utility across
all agents; unmatched utility is zero. Comparisons therefore assume that these
cardinal units are comparable across people.

## 1. One additional encounter can destroy almost all stable welfare

**Proposition 1 (vanishing welfare ratio with bounded utilities).** For every
eta > 0 there exists a two-by-two market with all utilities in [0,1], and nested
information graphs E subset F differing in exactly one IR edge, such that each
graph has a unique stable matching and

    S(DA(F)) / S(DA(E)) < eta.

The number of matched pairs falls from two to one. The statement holds for
either proposing side because the stable outcome on each graph is unique.

**Construction and proof.** Choose 0 < eps < 1/2 with 2eps/(1+eps) < eta. Let
rows of U index left agents and rows of V index right agents:

    U = [[eps, 2eps], [0, 1]],
    V = [[1, 0], [2eps, eps]].

Let E={(0,0),(1,1)} and F=E union {(0,1)}. The omitted edge (1,0) is not IR,
so F reveals the complete IR graph. All entries lie in [0,1]. On E both
diagonal edges must be matched: otherwise the two unmatched endpoints of a
missing diagonal edge block. Thus the unique stable matching is the diagonal,
with welfare (eps+1)+(1+eps)=2+2eps.

On F, left0 strictly prefers right1 to right0, and right1 strictly prefers
left0 to left1. Therefore if they are not together they block, whatever the
other pairs do. Every stable matching must contain (0,1). The remaining agents
left1 and right0 have no IR edge, so the unique stable matching is {(0,1)},
with welfare 4eps. Its welfare ratio is 2eps/(1+eps), tending to zero. QED.

The full-graph IR planner retains the diagonal: it gives 2+2eps > 4eps.
Thus the same construction rules out a positive uniform multiplicative welfare
guarantee for stable outcomes relative to the IR planner, even with bounded
utilities and a unique stable matching. This does not establish a frequency or
average magnitude of loss under the study's Gaussian population model.

**Mechanism.** The newly encountered pair has mutually preferred but socially
small gains relative to its own previous partners. Its formation displaces two
agents who had large utilities for those partners. Nontransferability prevents
those displaced agents from buying preservation of the diagonal allocation.
The result concerns the requirement to respect all newly revealed blocking
pairs, rather than a computational failure of DA.

**Why this is not a negative value-of-information theorem for a planner.**
The constraint changes when more edges are revealed: an allocation formerly
stable may cease to be stable. A planner maximizing welfare over all IR
matchings can ignore the extra edge and retain its previous allocation, so its
value is monotone under graph inclusion. Similarly, an informed decision maker
who may ignore information retains the old decision rule. The counterexample
does not contradict that decision-theoretic argument. It applies when the
institution mandates stability on every revealed IR edge and allows rematching;
it need not apply to irrevocable commitment or a policy allowed to conceal or
exclude encountered pairs from the final matching stage.

## 2. Separate unavailable opportunities, stability, and DA selection

Let F be the full IR graph and E subset F the revealed graph. Define

    P(F) = max welfare among all IR matchings on F,
    P(E) = max welfare among all IR matchings on E,
    T(E) = max welfare among stable matchings on E,
    D(E) = welfare of the specified side-proposing DA outcome on E.

These maxima exist in a finite market, and DA supplies a stable matching on E.

**Proposition 2 (three-gap identity).**

    P(F) - D(E)
      = [P(F)-P(E)] + [P(E)-T(E)] + [T(E)-D(E)],

and all three terms are nonnegative.

**Proof.** Matchings on E are feasible on F. Stable matchings on E are a subset
of IR matchings on E. DA is one stable matching on E. Hence
P(F) >= P(E) >= T(E) >= D(E). Expanding the right side telescopes. QED.

The terms respectively measure unavailable feasible surplus, the stability
constraint, and selection of a particular stable outcome. The study's original
two-gap quantity P(E)-D(E), stored as `da_allocation_loss`, combines the last two;
it cannot identify the pure stability constraint without computing T(E).

In Proposition 1 with E replaced by the full revealed graph F, the entire loss
is the stability constraint; DA selection loss is zero by uniqueness. Conversely,
take complete two-by-two preferences induced by

    U = [[3,2],[2,3]],       V = [[1,100],[100,1]].

Left-proposing DA selects the diagonal, welfare 8. The off-diagonal matching
is also stable and has welfare 204. It attains the unrestricted IR planner
optimum, so P(E)-T(E)=0 and T(E)-D(E)=196. Thus selection loss need not vanish.
Exhaustive enumeration in the companion tests verifies both examples and all
subgraphs of the second example; it does not prove arbitrary-size identities.

**Costs.** With B distinct inspected pairs and per-pair cost c, net DA welfare
is D(E)-cB. Relative to the *gross, zero-inspection-cost* full planner benchmark,

    P(F) - [D(E)-cB] = the three gross gaps + cB.

At identical realized B the cost cancels in policy contrasts. This accounting
does not make the full planner a feasible zero-cost implementation. If two
policies have different realized budgets, their net contrast is
D(E1)-D(E2)-c(B1-B2). Costs paid separately by participants or nonconstant costs
require their own accounting. Divide all terms by population size when reporting
per-person quantities.

## 3. Cost comparative statics do not require monotone gross DA welfare

Fix a finite set of candidate schedules q, each producing expected gross welfare
G_q and expected inspection count B_q >= 0. Their distribution and final matching
rule are held fixed as cost c changes. Expectations may represent a specified
population or a fixed common set of simulation worlds. Include a zero-inspection,
zero-surplus candidate when abstention is allowed. Define

    W(c) = max_q [G_q - c B_q],       c >= 0.

**Proposition 3 (finite-schedule cost envelope).** W is continuous, convex,
piecewise linear and nonincreasing in c. Choose an optimizer with the smallest
budget when there is a tie. Its budget is weakly decreasing in c.

**Proof.** Each candidate is an affine, nonincreasing function of c. A finite
maximum is continuous and piecewise linear; maxima preserve convexity and
nonincrease. At costs c1<c2, let optimal schedules have budgets B1,B2 and gross
values G1,G2. Optimality gives

    G1-c1 B1 >= G2-c1 B2,
    G2-c2 B2 >= G1-c2 B1.

Adding yields (c2-c1)(B1-B2)>=0, hence B1>=B2. The minimum-budget tie rule makes
selection unambiguous in budget at a breakpoint. No monotonicity assumption on
G_q in B_q is needed. QED.

For candidates a,b with B_b>B_a, b is weakly better exactly when
c <= (G_b-G_a)/(B_b-B_a). These are pairwise switching thresholds, not necessarily
breakpoints of the optimized envelope: a third candidate may dominate both.
The envelope describes optimization over the stated candidate set, not a proved
globally optimal acquisition policy. Selecting and evaluating candidates on the
same noisy simulation sample adds selection bias; the algebra remains valid for
that sample but does not remove the need for independent policy evaluation.

The graph-to-DA-welfare objective in Proposition 1 is nonmonotone. Accordingly
the standard guarantee for greedy maximization of a *monotone submodular*
objective cannot be invoked for it. Nonmonotonicity alone does not establish
failure of submodularity or rule out other approximation guarantees; neither is
claimed here.

## Verification boundary

`tests/test_paper_theory.py` checks the parameterized witness using exact rational
arithmetic, enumerates stable and IR matching sets on tiny graphs, checks the
implemented DP against exact planner values, and exhausts a finite collection
of gross-welfare schedules for the cost comparative statics. The proofs above
establish the stated general claims; the tests guard their correspondence to
the examples and implementation. External novelty and empirical relevance
require separate literature review and validation.
