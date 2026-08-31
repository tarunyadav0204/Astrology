# Longevity engine validation protocol

## What is being validated

The engine has two distinct validation targets:

1. **Classical implementation fidelity** — formulas, inputs, exceptions, boundaries, and disclosed interpretive profiles match the cited rule specification.
2. **Retrospective date discrimination** — event dates show more activation than ordinary person-time in an untouched cohort.

Passing the first target does not establish the second. Neither target turns astrology into medical advice or permits a death-date claim.

## Locked rule inventory

The machine-readable registry is `backend/longevity/classical_rule_registry.json`. A rule can be `source_locked`, `translation_profile`, `supporting_only`, `product_audit`, or `derived_proxy`. Product-audit rules must never be described as classical numerical formulas.

The registry also pins the working edition, Sanskrit transcription, and URLs used for audit. `source_locked` means that implementation and the pinned passage agree; it does not imply that all recensions or commentators agree. A disputed reading must remain `translation_profile`, be emitted in calculation evidence, and may not be changed without a new registry version and regression baseline.

The initial source audit corrected three defects before baseline measurement:

- Jaimini 2.1.9 Moon–Saturn precedence when Moon occupies Lagna or the seventh was missing.
- Under the selected Sanjay Rath reading, Jaimini 2.1.13 requires malefic influence for Saturn reduction; the previous condition was reversed.
- Jaimini 2.1.14 requires unaffiliated Jupiter in Lagna/seventh; benefic influence is not substituted for “unaffiliated.”

## Dataset rules

- Carry the original source URL and Rodden rating with every record.
- Use AA records for the primary cohort. Report A records separately.
- Never silently mix natural disease, accident, homicide, and uncertain/substance-related events.
- Do not use C, DD, X, or XX records for degree-, divisional-, or dasha-sensitive validation.
- A record used to change a rule becomes development data and cannot remain in the external-validation set.
- Keep a person wholly within one split; never split dates from one person across development and validation.

The checked-in `public_figures_v1` dataset is only a seed regression cohort. Five selected public figures cannot establish accuracy.

## Metrics

For a frozen convergence threshold, report:

- event capture rate;
- positive control person-time rate outside the event-exclusion band;
- event lift divided by positive control person-time;
- positive days per person-year;
- lifespan-compartment containment;
- birth-time stability at −15, −5, 0, +5, and +15 minutes;
- results separated by cause group and source quality.

Do not report “accuracy” from event capture alone. A method that captures 80% of events while activating on 90% of ordinary dates has no useful date discrimination.

## Running the benchmark

From `backend`:

```bash
PYTHONPATH=. .venv/bin/python -m longevity.validation \
  --dataset longevity/validation_data/public_figures_v1.json \
  --observation-years 5 \
  --event-exclusion-days 60 \
  --threshold 2
```

The benchmark output is descriptive JSON. It is intentionally not consumed by the user-facing calculator.

## Release gate

The screen may remain a licensed classical research workspace while the predictive gate is unmet. Predictive or medical-risk wording requires all of the following:

- a frozen rule registry;
- independent primitive-calculation parity;
- an untouched, adequately sized external cohort;
- event lift whose confidence interval excludes no improvement;
- acceptable predeclared false-alert person-time;
- birth-time robustness appropriate to the technique;
- independent classical and statistical review.

Until then, the supported claim is: “Classical Ayurdaya calculation and activation audit,” not mortality prediction.
