# Working paper: information, stability, and exposure

[Read the PDF](manuscript.pdf) · [Chinese reading guide](reading-guide.zh-CN.md) ·
[LaTeX source](manuscript.tex) · [Evidence and submission audit](submission_audit.md)

The organizing question is why an additional acceptable encounter can worsen
stable welfare when newly revealed blocking pairs cannot be ignored. The paper
separates this possibility result from its average synthetic comparisons and
from descriptive observed-encounter evidence.

The package includes three propositions with proofs, a matched-participant
invariance lemma explaining the exact stable solver, four source-backed figures,
two generated result tables, eleven research references and inspectable provenance.
It does not claim theoretical priority, an optimal acquisition policy, strategic
equilibrium, calibrated human utility or readiness for submission.

## Additional analysis

- Exact best-stable benchmarks split the prior allocation gap into stability
  constraint and DA-selection gaps on the same 540 treatment rows.
- Six contrasts are evaluated on 500 new worlds per selected scenario,
  retaining both proposer directions and adjusted percentile intervals.
- Cost-dependent budgets are selected on original training worlds and frozen
  before held-out evaluation.
- A separate post hoc complete-market diagnostic checks stable outcome
  selection; its population and scale differ from the Gaussian study.

The independent validation resolves a small positive noisy-scenario effect
that was imprecisely estimated in the original exploration. That update is
explicit in the manuscript rather than silently preserving the earlier interval.

## Reproduce

From the repository root:

```bash
python -m pytest -q
python experiments/validate_research.py
python paper/run_analysis.py --worlds 500 --bootstrap 20000
python paper/make_artifacts.py
python paper/record_provenance.py
python paper/validate.py
python paper/build.py
```

Analysis uses the existing NumPy/Matplotlib dependencies. Building the PDF
requires a local LaTeX distribution with standard packages; package installation
is disabled by the builder. Optional PyMuPDF renders local preview pages.
Generated preview and build files stay under ignored `paper/build/`.

`paper/results/manifest.json` binds analysis sources and inputs. The separate
`paper/generated/manifest.json` binds numerical, empirical, bibliography and
figure sources. Binary figures are hashed as binary, and text hashes normalize
CRLF to LF. Tables and headline numbers are generated directly from saved results.
The claim registry records draft-block hashes; hashes do not establish truth or
replace source verification. All external references retain an explicit pending
human-verification state.
