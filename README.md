# stable-matching-lab

Small experiments around the Gale–Shapley deferred acceptance (DA) algorithm,
motivated by Singapore's FirstDate government dating pilot, which uses DA to
match people from a questionnaire. Everything here is a toy: the numbers say
what happens in the models below, not what happens in any real service.

Two experiments:

1. **Manipulation explorer** – brute-force every possible misreport of one
   agent and check who can profit under men-proposing DA.
2. **Dating-market simulation** – compare one-shot DA, repeated DA cycles and
   "match people to events" in a stylised market with noisy questionnaires and
   outside options.

## Layout

```
stablematch/gs.py        DA with incomplete lists, blocking pairs, brute-force
                         stable matchings, many-to-one DA
stablematch/explore.py   misreport search
stablematch/market.py    market model and the mechanisms
experiments/             scripts that produce results/
results/                 saved outputs (JSON / Markdown / CSV)
tests/                   pytest
```

Reproduce (Python 3.10+, `numpy`, `pytest`):

```
pip install -r requirements.txt
python -m pytest
python experiments/run_manipulation.py 3            # all 46,656 profiles
python experiments/run_manipulation.py 4 20000 0    # 20,000 random profiles, seed 0
python experiments/run_market.py 200                # 200 random worlds per row
```

## 1. Who can profit from lying?

Setup: n men and n women, strict complete true preferences, men-proposing DA.
For each agent we try every ordered list built from any subset of the other
side (so truncations and permutations), and ask whether the true partner rank
improves. Being unmatched counts as worst.

| n | profiles | some man can gain | some woman can gain | gaining woman has a truncation that works | profiles with a unique stable matching | gaining woman while the stable matching is unique |
|---|---|---|---|---|---|---|
| 3 | 46,656 (all) | 0 | 12,576 (27.0%) | 12,576 | 34,080 (73.0%) | 0 |
| 4 | 20,000 (random sample) | 0 | 8,093 (40.5%) | 8,093 | 11,907 (59.5%) | 0 |

What this shows, for these sizes only:

* No proposer ever gained by misreporting (consistent with the Dubins–Freedman
  result), which is also a check on the implementation.
* Receivers sometimes can. In every profile where a receiver gains, a
  truncation of her true list is enough, and every profile with more than one
  stable matching had a gaining receiver. When the stable matching is unique
  nobody gained.
* Smallest example (m0: w0>w1, m1: w1>w0, w0: m1>m0, w1: m0>m1): truthful DA
  gives (m0,w0),(m1,w1); if w0 declares m0 unacceptable she ends up with m1,
  her true first choice. This is a unit test.

Full distributions (by number of stable matchings, by number of gaining
receivers) are in `results/manipulation_n*.json`.

## 2. Dating-market simulation

Model (all parameters in `stablematch/market.py`, `Params`): 60 men and 60
women with trait vectors and a common "appeal" score. True utility is trait
similarity + `lam` × appeal + idiosyncratic taste that is only revealed on a
date. The questionnaire sees the first two parts plus noise (`sigma_q`). Each
person only commits to someone above their outside option (the `outside_q`
quantile of their own utilities). There is no commitment: a pair that does not
both clear the bar stays single.

Mechanisms:

* `one_shot` – one run of DA on questionnaire scores, then dates.
* `cycles` – repeated DA among people still single, never repeating a pair.
* `events` – assign people to events by trait affinity (many-to-one DA); inside
  an event everyone meets everyone and pairs form by DA on true utility.
* `oracle` – DA on true utilities. Needs n² dates; only a reference.

Defaults (200 random worlds, mean ± standard error):

| mechanism | fraction coupled | dates / person | blocking pairs / person |
|---|---|---|---|
| one_shot | 0.736 ± 0.004 | 1.0 | 3.94 ± 0.05 |
| cycles | 0.902 ± 0.002 | 1.6 | 2.83 ± 0.03 |
| events (5 per event) | 0.782 ± 0.003 | 5.0 | 2.56 ± 0.04 |
| oracle | 0.916 ± 0.002 | 60 | 0 |

A "blocking pair" here is a man and woman, not together, who each have higher
true utility for the other than for their current partner (or their outside
option if single).

What the sweeps in `results/market_summary.md` show:

* Repeated cycles give the highest fraction coupled among the feasible
  mechanisms in every setting tried, and come close to the oracle at default
  parameters (0.902 vs 0.916) with about 1.6 dates per person.
* `events` improve as events get larger (fraction coupled 0.712 / 0.782 /
  0.826 / 0.863 for 2 / 5 / 10 / 20 dates per person) but stay below `cycles`
  (0.909 at 10 or 20) in this model.
* Blocking pairs per person are mixed. `events` have fewer than `cycles` at
  the defaults, with 5 or more dates per person, and at `sigma_q` ≥ 0.5, but
  more at `lam` 1 or 2, `outside_q` 0.7 or 0.85, `sigma_e` 2, `sigma_q` 0.25
  and 2 dates per person (see the tables for every row).
* One-shot DA leaves many people single, and gets worse as the questionnaire
  gets noisier (0.765 → 0.523 coupled as `sigma_q` goes 0.25 → 2.0). Higher
  outside options lower the fraction coupled for every mechanism, the oracle
  included (0.960 → 0.582 from `outside_q` 0.3 to 0.85), because fewer pairs
  are mutually acceptable at all.

Caveats that matter when reading these numbers:

* Event assignment uses true trait vectors with no questionnaire noise, and
  event themes are random, so this is not a tuned event-matching design.
* "Mean utility of coupled" in the output tables is not comparable across
  mechanisms: a mechanism that couples fewer people can look better on it
  because of selection.
* Every result depends on this model's functional forms and parameters. The
  sweeps vary one parameter at a time around the defaults.

## References

* D. Gale and L. S. Shapley, "College Admissions and the Stability of
  Marriages", *American Mathematical Monthly* 69(1), 1962, 9–15.
* L. E. Dubins and D. A. Freedman, "Machiavelli and the Gale–Shapley
  Algorithm", *American Mathematical Monthly* 88(7), 1981, 485–494.
* A. E. Roth, "The Economics of Matching: Stability and Incentives",
  *Mathematics of Operations Research* 7(4), 1982, 617–628.
* D. E. Knuth, *Mariages stables et leurs relations avec d'autres problèmes
  combinatoires*, 1976.
* The pilot that motivated this: "How Singapore's government-run dating
  service works" (Singapore Samizdat).
* Machine-checked DA in Lean 4: `hwatheod/galeshapley-lean` (not part of this
  repository).
