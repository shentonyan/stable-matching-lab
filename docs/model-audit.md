# Scientific audit and research boundaries

This repository is a synthetic computational research environment. None of its
parameter sweeps identifies a causal effect in a human population. The table
records limitations of the original modules and what a defensible research
comparison must disclose. Mathematical claims are developed in [theory.md](theory.md).

| Issue | Consequence | Required interpretation or check |
|---|---|---|
| `search.py` pools both sides' matched utilities under proposer DA | Equal match counts do not imply equal continuation values | Label the historical scalar solution a pooled reservation-value fixed point; inspect side-specific utilities and deviations |
| A scalar numerical root is presented as equilibrium | Existence, uniqueness and optimal response are separate questions | Report timing, residuals, brackets, search grid and holdout diagnostics; no Nash claim without proof |
| Matched people are replaced | Constant head count alone does not prove stationarity with persistent heterogeneity | Treat iid refreshed opportunities as an explicit assumption; use demographic dynamics before making population predictions |
| Original outside options are quantiles of each agent's full true utility row | The modeler uses utilities unavailable before inspections; thresholds move when pool composition changes | Treat these as oracle-defined exogenous reservation rules, not estimated individual behavior; compare with independently specified thresholds |
| `one_shot`, `cycles` and `events` share a nominal `dates` argument but spend different realized numbers of inspections | Outcome differences confound allocation, information and expenditure | Enforce the same budget definition; report realized inspections and person-level burdens as well as caps |
| Event assignment sees noiseless traits while individual matching uses noisy scores | Mechanisms have unequal access to covariates | Hold their observable information sets fixed or name the information advantage as a treatment |
| Utility of coupled agents excludes singles | Selection can improve the conditional mean while reducing population welfare | Include outside utilities, all participants, costs and side-specific distributions |
| Full-information DA is called an oracle | It is neither a surplus nor cardinality upper bound across arbitrary policies | Call it a full-information DA reference; use maximum-surplus IR matching for a planner bound |
| Stability is evaluated on different opportunity graphs | A local stable outcome can have global hidden blocking pairs | Distinguish revealed, full-information and commitment stability and name each denominator |
| Search batch size is an exogenous common choice | The welfare-best grid point is not necessarily an individual's privately optimal choice | Separate platform choice of K from individual participation or deviation incentives |
| Sweeps vary one parameter around a baseline | Interactions and tail behavior can be missed | Use crossed stress scenarios, independent worlds, paired contrasts and uncertainty intervals |
| Utilities are synthetic cardinal scores | Numerical welfare and fairness depend on scaling and outside options | Disclose normalization; compare side means, lower tails and participation alongside aggregate surplus |
| There are no fitted real participant data | No calibration, empirical validation or welfare policy recommendation follows | Treat real data as an explicitly unfinished validation layer |

## A research question the model can answer

Under a fixed bilateral inspection budget and a shared signal model, when does
information targeted at predicted compatibility improve cost-adjusted population
surplus, and when do congestion and stable reassignment reverse that gain?
This specifies a mechanism, an intervention, constraints and an estimand. It
requires comparisons on identical latent worlds and separate reporting of
coverage, surplus, inequality and hidden blocking. A model can test this question
without claiming a universally superior social platform.

## What real-world relevance would require

For a dating interpretation, mutual interest observations could validate binary
acceptance or ranking predictions, subject to lawful data access and documented
definitions. Binary yes/no outcomes do not identify cardinal lifetime utilities,
discount factors, inspection costs or equilibrium outside values. Observational
recommendation logs also confound exposure with acceptance unless the exposure
process is modeled or randomized. No such empirical identification is completed
by the synthetic experiments.

For a hiring interpretation, capacities, job and applicant outside options,
offer timing and withdrawal rules must be specified; a one-to-one dating model
does not validate a hiring mechanism merely by renaming agents. The current
capacity DA helper alone does not supply those institutional assumptions.

These documents contain local derivations and implementation checks, rather
than a verified literature review or a submission-ready manuscript. Existing
README references retain their stated verification limits; no new external
evidence is asserted here.
