# Birth-time rectification blind benchmark

This benchmark measures whether the rectification engine recovers a verified
birth time from life events. It does not establish that astrology can prove an
exact birth minute, and its output is never consumed by the user-facing scorer.

## The blindness boundary

Each cohort has two separate files:

1. A blinded case file containing the birth date, coordinates, historical IANA
   timezone, candidate time window, preassigned split and dated life events.
   It must not contain the recorded or verified birth time anywhere.
2. A truth vault mapping anonymous case ids to verified local birth times and
   their documentary sources.

The runner validates the blinded file, completes every candidate scan, and only
then opens the truth vault. It rejects truth-like keys recursively in blinded
inputs and records SHA-256 hashes of both source files in the report.

For a genuine case, `window_strategy` is `pre_recorded_uncertainty`: the range
must have been recorded before scoring. Public AA charts do not provide an
uncertain range. Their research windows must therefore use
`blinded_uniform_truth_position`, placing the hidden time at varied positions
inside the window before the blinded file is exported. Never center every
public-chart window on the true time.

Do not commit a real truth vault. Files ending in `.private.json` under
`backend/rectification/benchmark_data/` are ignored. The checked-in example
files demonstrate structure only; their fictional values are not benchmark
evidence.

## Building the first cohort

Use 25–50 consented, deidentified charts with independently recorded birth
times and at least four dated events each. Prefer contemporaneous hospital,
municipal or family records over retrospective recollection.

Before looking at any engine result:

- assign each person wholly to `development` or `holdout`;
- keep approximately 70% for development and 30% for holdout;
- document the birth-time source and verification rating in the private vault;
- record event precision and source reliability honestly;
- exclude the founder/reference chart from aggregate recovery metrics; and
- freeze the case and vault hashes.

The development split can be used to identify bugs and propose a new versioned
rule profile. Once a holdout result has influenced a rule, that cohort is no
longer untouched holdout evidence and must be labelled accordingly.

### Freeze before holdout reveal

After independent event audit and before any holdout calculation, create a
private freeze manifest. It records the SHA-256 hashes of both files, exact
case IDs and split counts, and the engine/registry version. The runner will
not reveal a holdout unless that manifest matches the supplied files. Editing a
candidate window, event, hidden birth time or split invalidates the freeze.

```bash
PYTHONPATH=. .venv/bin/python -m rectification.cohort_freeze \
  --cases /private/path/audited.blinded.private.json \
  --truth /private/path/audited.truth.private.json \
  --output /private/path/cohort-v1.freeze.private.json
```

The default freeze threshold is 25 total audited cases with at least 10
preassigned holdout cases. Smaller thresholds exist only for isolated test
fixtures; they must never be used to claim readiness.

## Run the benchmark

From `backend`:

```bash
PYTHONPATH=. .venv/bin/python -m rectification.benchmark \
  --cases rectification/benchmark_data/cohort_v1.blinded.json \
  --truth rectification/benchmark_data/cohort_v1.private.json \
  --split holdout \
  --reveal-holdout \
  --frozen-manifest /private/path/cohort-v1.freeze.private.json \
  --robustness-controls \
  --output /tmp/rectification-holdout-v1.json \
  --markdown /tmp/rectification-holdout-v1.md
```

Use `--split development` without `--reveal-holdout` for all rule work. Omit
`--split` only with both `--reveal-holdout` and `--frozen-manifest`, to report
development, holdout and combined metrics. The default scan is one minute;
`--minute-step 2` through `5` is available for performance experiments but
should not be mixed into the same reported cohort.

## Reported metrics

For the selected winning minute and, separately, any exactly tied winning
minute, the report gives:

- absolute error in minutes;
- recovery within 5, 15, 30 and 60 minutes;
- Wilson 95% intervals for recovery rates;
- distance from the verified time to the leading supported cluster;
- development, holdout and combined summaries; and
- mean and median error.

The same report measures a no-astrology midpoint baseline. A rectification
method that cannot outperform the midpoint of its supplied range has not shown
useful time discrimination.

Tie-aware recovery is not the headline metric. It is shown to reveal broad,
indistinguishable scoring plateaus that could otherwise make the system look
more precise than it is.

The report also contains candidate-boundary diagnostics. For every pair of
adjacent candidate minutes it records changes in D1 and relevant divisional
ascendants, dasha chains, KP cusp sublords, transit contacts, layer scores and
the composite evidence fingerprint. Long identical plateaus are a warning that
the system cannot honestly distinguish the minutes inside them.

With `--robustness-controls`, every transformed cohort is also calculated
before the truth vault is opened. The controls rotate complete event histories
across charts, rotate dates across charts while preserving event types, and
jitter every event by ±7 and ±30 days. A method that fits another person's
events as well as—or better than—the actual history has not demonstrated
event-specific discrimination.

## Evidence-layer ablations

The same calculated candidates are rescored without each evidence layer:

- structural natal promise;
- dasha delivery;
- relevant divisional chart;
- transit confirmation; and
- KP confirmation.

The report also includes Parashari-only and KP-only views. Ablations are
post-calculation comparisons: they do not mutate production weights. A layer is
useful only if it improves untouched recovery or meaningfully narrows supported
clusters without damaging stability.

Engine v2 adds three anti-overfitting safeguards discovered through the public
development diagnostics:

- imprecise month/year events use the mean of sampled dates instead of letting
  each birth-time candidate cherry-pick its own highest-scoring date;
- static natal and KP cusp promise is occurrence-normalized, so four events of
  one type do not count the same natal promise four times; and
- dasha and divisional delivery require proportional MD–AD–PD chain support;
  one matching sub-period no longer receives full-chain credit.

## Release decision

Do not calibrate user-facing probabilities from a small cohort. Before enabling
“Use this rectified time,” require a larger untouched holdout, boundary fixtures,
event-date jitter tests, shuffled-event negative controls, performance testing,
and an explicit reversible chart-revision implementation.

The report enforces a blocked/limited-beta gate. Limited beta requires at least
25 total cases, at least 10 untouched holdout cases, better mean error than the
midpoint baseline, at least 50% recovery within 15 minutes, at least 70% within
30 minutes, and a worse type-preserving negative control for at least 75% of
cases. Passing this gate still does not enable applying a rectified time; that
remains a separate migration and safety decision.

The founder/reference chart may be run as a visible sanity check after the
harness passes, but it must remain labelled `reference_only` outside both
development and holdout aggregates.

## Public Astro-Databank development seed

Astro-Databank currently exposes an official `c_sample.xml` research subset.
The “C” describes surnames beginning with C; it is not a Rodden C rating. The
importer filters the sample to Rodden AA records only.

The XML notice restricts redistribution and product use of its research-data
section. Consequently, the importer:

- is a local deterministic research utility, not an API or training path;
- requires explicit acknowledgement of the research terms;
- writes only ignored `.private.json` files;
- removes names and identifying Astro-Databank entry links from the blinded file;
- does not export biographies, event notes or source notes; and
- labels extracted event dates as requiring independent verification.

From `backend`:

```bash
PYTHONPATH=. .venv/bin/python -m rectification.public_benchmark_seed \
  --xml /private/path/c_sample.xml \
  --dataset-id adb-public-aa-development-seed-v1 \
  --count 10 \
  --random-seed 819271 \
  --min-exact-events 2 \
  --blinded-output /private/path/adb-seed.blinded.private.json \
  --truth-output /private/path/adb-seed.truth.private.json \
  --acknowledge-adb-research-terms
```

Public AA seed cases stay in the development split. Their birth times are
source-rated, but Astro-Databank event rows are only candidate leads. Every
event needs a separate public citation before it can enter an audited
development cohort. A chart already inspected during development cannot later
be relabelled as untouched holdout evidence. The runner refuses to report an
unaudited public seed as holdout.

### Independently auditing public event rows

Use `rectification.event_audit` with a private overlay. Each overlay row records
one of `verified_exact`, `verified_precision`, `semantic_mismatch`,
`contradicted`, or `unsupported`. Verified rows require a public source URL,
publisher, audited event type, date and precision. This is a semantic check as
well as a date check: an election campaign, nomination or unofficial ceremony
must not silently become a promotion or legal marriage.

```bash
PYTHONPATH=. .venv/bin/python -m rectification.event_audit \
  --cases /private/path/seed.blinded.private.json \
  --truth /private/path/seed.truth.private.json \
  --audit /private/path/seed.event-audit.private.json \
  --blinded-output /private/path/audited.blinded.private.json \
  --truth-output /private/path/audited.truth.private.json \
  --report-output /private/path/audit-report.private.json
```

Events without a verified audit are excluded. Cases with fewer than four
verified events are excluded from the audited cohort. The output remains a
development cohort; source auditing does not turn a chart used during engine
development into untouched holdout evidence. Source URLs remain in the private
audit overlay and are not copied into the blinded scorer input.

The local September 2026 C-surname sample review yielded only 14 AA records
with four mapped events and two exact-day candidates before independent audit.
It therefore cannot supply the required 25-case / 10-holdout release cohort by
itself. Do not pad the cohort with weaker events or relabel development cases
as holdout. The remaining evidence must come from consented, deidentified
charts with documentary birth times and independently auditable events, or a
separately licensed broader research corpus.
