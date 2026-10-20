# Protocol for the observed encounter audit

The empirical layer is descriptive. It does not fit the synthetic utility model or evaluate a causal scheduling policy. Its implementation is [stablematch/empirical.py](../stablematch/empirical.py), and the saved aggregate output is [results/empirical_audit.json](../results/empirical_audit.json).

## Source and scope

Use the original Columbia [Speed Dating Data.csv](https://www.stat.columbia.edu/~gelman/arm/examples/speed.dating/Speed%20Dating%20Data.csv). The accompanying [Word dictionary](https://www.stat.columbia.edu/~gelman/arm/examples/speed.dating/Speed%20Dating%20Data%20Key.doc) was downloaded and text-extracted locally for checking. It defines `iid` as the unique subject number, `pid` as the partner's `iid`, `gender` as female=0/male=1, `match` as yes=1/no=0, and `dec_o` as the partner's decision on the event night. The parser requires these fields plus `wave` and `dec`; numerical side labels orient each pair. The scorecard instruction explicitly says it is filled out after each date and elicits yes/no interest and attribute ratings, confirming that date ratings are not pre-encounter signals.

The [original 2006 paper](https://business.columbia.edu/sites/default/files-efs/pubfiles/867/fisman%20iyengar.pdf) analyzes 14 sessions and explains why seven others were excluded. This repository reports all 21 waves present in the file. It is **not a replication of the paper's 14-session estimates**. The dictionary flags wave 5 as undergraduates, wave 12 as a budget condition allowing yes decisions for only 50% of people met, waves 13–14 as using a different master of ceremonies, and waves 18–21 as involving a magazine or book. Wave 12 constrains acceptance decisions, not the number of encounters; it must not be described as an inspection-cap experiment or as clean identification of this repository's exposure policy. These design differences require explicit exclusion/sensitivity analyses before behavioral pooling. Public access does not establish an explicit redistribution license. Raw participant records should remain local and excluded from version control; the repository publishes aggregate results and retrieval instructions.

## Parsing and denominator

`audit_file` reads the CSV using CP1252 encoding and records the source file's SHA-256. `audit_rows` accepts only finite integer IDs, wave values and 0/1 side labels. It raises an error if one participant has conflicting side labels within a wave. A directed row is excluded if its identifiers or side are unusable, or its partner cannot be linked to an opposite-side participant in that wave.

Encounter identity is `(wave, side-0 participant ID, side-1 participant ID)`. Each encounter counts once even if both participants supplied directed records. The parser counts duplicate directed rows and flags conflicting duplicates, disagreements between a recorded partner decision and that partner's own decision, and recorded match values that contradict available bilateral decisions. Flagged encounters remain in observed coverage but are excluded from behavioral denominators. Identical duplicate records do not create additional encounters.

An encounter enters `complete_decision_pairs` only when both participants' own decisions are observed and consistent with available counterpart reports. It becomes `mutual_yes_pairs` only if both own decisions equal one. Missing decisions are never imputed as zero. A single-sided encounter can contribute to observed coverage but cannot enter the complete-decision denominator. Coverage divides observed encounter count by the product of the two within-wave participant counts; it is not a claim that missing cross-wave edges represent rejection.

## Saved results and uncertainty

The source accessed on 21 October 2026 yielded 8,378 directed rows, of which 10 were excluded before constructing pairs. The result contains 4,184 observed encounters; all 4,184 had usable bilateral decisions, with 690 mutual-yes encounters across 21 waves. The resulting descriptive mutual-yes rate is **16.49%**. The audit reports zero conflicting or duplicate directed encounter records in its retained per-wave groups.

The saved 95% percentile interval is **14.93%–18.27%**, calculated from 2,000 resamples of whole waves with seed 20261021. Each draw recomputes the encounter-weighted ratio from resampled wave totals. This preserves within-wave dependence in resampling, but assumes exchangeable waves for an inferential interpretation. With only 21 heterogeneous waves, including intervention waves, it is best read as descriptive sensitivity rather than a population or treatment-effect interval.

All retained within-wave coverage ratios are one, relative to participants
represented and linked in the CSV. This does not establish that every recruited
participant was recorded. The historical event design is substantially more
complete than a selective modern platform exposure log.

The runner also writes [sample-composition sensitivity](../results/empirical_audit_sensitivity.json).
Excluding wave 12 alone gives 669 mutual-yes pairs among 3,988 encounters
(16.78%, 20 waves). Excluding all dictionary-flagged variants—waves 5, 12,
13, 14 and 18–21—gives 446 among 2,661 (16.76%, 13 waves). These exclusion
sets were prompted by reading the dictionary during this exploratory audit;
they are not a reconstruction of the paper's 14-wave sample or a causal test
of the budget condition.

Each wave also reports the maximum cardinality of a one-to-one matching restricted to observed mutual-yes edges. This is an offline combinatorial feasibility bound. It is not the actual number of relationships, a stable matching, a welfare bound or a policy-effect estimate. Binary yes/no choices do not identify strict rankings, utility magnitudes or lifetime compatibility; the one-to-one restriction is imposed by the analysis.

## Requirements for further empirical work

An ex-ante prediction exercise must separate questionnaire information available before the encounter from post-date ratings, liking, partner decisions and later follow-up. Using post-date information to choose first encounters leaks the outcome-generating information. Split validation by wave rather than random directed rows so mirrored pairs and participants do not cross folds within a session. Report label completeness, calibration, discrimination and sensitivity to session exclusions before connecting prediction to synthetic experiments.

Observed-edge prediction does not identify unobserved-pair outcomes, search costs, equilibrium outside values or the effect of changing exposure. Off-policy or causal claims require a documented exposure mechanism and appropriate randomized or identifiable observational design. Any fitted binary-choice layer must remain distinct from uncalibrated synthetic cardinal welfare.
