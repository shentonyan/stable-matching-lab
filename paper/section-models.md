# Section models and manuscript design

This planning document records AI-assisted inspection of original full texts on 21 October 2026. It is not human verification or a claim that the draft matches these papers' scholarly contribution. Source IDs refer to `references.json`. Abstract lengths are approximate visual/text estimates, not journal requirements. Descriptions below paraphrase structure rather than copy prose.

## Three close benchmarks

### E01: interviews as a computational problem

Rastegari, Goldberg and Manlove (2016), [full 17-page arXiv version](https://arxiv.org/pdf/1602.04792), [HTML](https://arxiv.org/html/1602.04792v3). The separate [two-page AAMAS extended abstract](https://www.cs.ox.ac.uk/people/paul.goldberg/papers/rgm-aamas16.pdf) must not be mistaken for the full paper.

The full version proceeds through introduction and related work; preliminary definitions and stability levels; interviews as preference refinements and interview-minimization problems; NP-completeness; polynomially solvable variants; conclusion and future work. Its abstract is approximately 260 words: identify incomplete knowledge, specify interviews, challenge a naive benchmark, state computational hardness, then delimit tractable cases. Definitions make each theorem's object explicit before results. There is no empirical validation layer. For our draft, borrow the problem-definition discipline and benchmark separation; do not imitate the hardness contribution or present synthetic runs as evidence for it.

### E04: recommendations as a protocol with guarantees

Ashlagi, Braverman, Kanoria and Shi, [author-hosted published PDF](https://www.columbia.edu/~yk2577/mnsc.2018.3265.pdf), online 2019, journal issue 2020. Full text inspected through browser and in-memory PDF extraction.

Its roughly 180-word abstract specifies congestion, an information metric, assumptions, a protocol result, incentives and intuition. Section 1 presents the problem, results, managerial interpretation and related literature. Section 2 establishes the model and admissible protocols; Section 3 gives the main protocol and lower bound; Section 4 develops a simultaneous two-round alternative; Section 5 treats incentives; Section 6 discusses implications. Appendices carry technical proofs. This is a theory paper, not a field validation. Our draft should likewise state the information available to a scheduler before comparing policies. Its mandatory-DA graph-expansion argument concerns realized cardinal welfare, whereas this benchmark prioritizes communication efficiency while attaining stability; these are different objectives, not contradictory findings.

### E03: theory predictions precede a behavioral test

Hakimov, Kübler and Pan (2023), [publisher full text](https://onlinelibrary.wiley.com/doi/full/10.3982/QE1955); [opened author manuscript dated 19 July 2021](https://www.hakimov.info/_files/ugd/bbb8ad_8bde4763f1de41428284c1e0f60d6a53.pdf). The author manuscript is a prior version, not the 2023 version of record; exact section numbering below describes that inspected version.

The approximately 200-word abstract moves from costly search to institutional comparison, welfare mechanism, behavioral evidence and a cheaper informational intervention. Introduction motivates search mistakes; the theoretical framework derives mechanism and search predictions; experimental design specifies treatments, costs and priors; experimental results compare welfare and behavior; discussion addresses implications; appendices contain proofs and additional results. Its experiment tests predictions with incentivized participants. Our synthetic comparison is not an equivalent experiment, and the Columbia audit is observational description of a separate sample. Borrow their separation of theoretical prediction from behavioral evidence without implying that our project has completed the latter.

## Draft structure selected for this project

Use an approximately 180–220-word abstract organized as question, environment, precise analytical result, measured computational finding, empirical scope and limitation. Place no unsupported novelty or platform-effect claim in it. The introduction should explain why mandatory stable reassignment changes the feasible outcome after learning, then identify the restricted contribution. Related work must confront both information acquisition and cardinal stability costs. The model should define inspection graphs, outside options, acceptability, information access, mandatory reuse of revealed edges and welfare accounting. Analytical results should separate the constructed graph-expansion loss from the optional-discard benchmark. Computational design should precede results and state paired worlds, actual budgets and uncertainty. The empirical audit should occupy a short, explicitly descriptive section. Discussion should explain institutional applicability and what remains unidentified. Full assumptions, reproducibility instructions and supplementary stress results belong in appendices or linked artifacts.

The organizing argument is a conditional mechanism effect, not a general claim that knowledge hurts. This draft should not add author, affiliation, funding, ethics-approval or human-verification placeholders. Provenance and outstanding checks belong in the submission audit rather than invented declarations.
