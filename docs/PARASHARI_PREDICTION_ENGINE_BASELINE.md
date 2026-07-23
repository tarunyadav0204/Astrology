# Parashari Prediction Engine Calibration Baseline

> Historical note: this document describes the superseded family-first v6
> baseline. Schema v7/profile 2.0.0 replaced its same-carrier gate with the
> house-first ledger documented in `PARASHARI_PREDICTION_ENGINE_CONVENTIONS.md`.

Schema v8/profile 2.1.0 adds the D1 natal-promise ledger, validated D1 yoga and
cancellation subset, Sun reinforcement bands, and non-creating Moon peak bands.

| V8 case | 90-day calculation | Windows | Eligible activation windows | Final candidates |
|---|---:|---:|---:|---:|
| Delhi 1990 | 777.4 ms | 12 | 25 | 8 |
| Mumbai 1985 | 640.4 ms | 49 | 34 | 8 |
| London 2000 | 493.1 ms | 20 | 14 | 8 |
| Total | 1911.0 ms | — | — | 24 |

## Schema v7 / profile 2.0.0 local baseline

Recorded on 2026-07-22 after full classical-planet transit calculation,
house-window merging, and house-first combination resolution.

| Case | 90-day calculation | Raw windows | Eligible activation windows | Final candidates |
|---|---:|---:|---:|---:|
| Delhi 1990 | 1199.3 ms | 12 | 27 | 8 |
| Mumbai 1985 | 734.0 ms | 49 | 132 | 8 |
| London 2000 | 502.3 ms | 20 | 38 | 8 |
| Total | 2435.7 ms | — | — | 24 |

An eligible activation window is a source-aware house/timing segment before
one best timing segment per house or house combination is selected. It is not
an event count. V7 calculates the full classical transit field, but only
dasha planets, the Sun, Jupiter, Saturn and the nodes split material windows.

Recorded on 2026-07-21 using the repository's Python virtual environment and the fixed, synthetic calibration charts in `backend/tests/fixtures/parashari_prediction_calibration.json`.

Command:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/dev_prediction_engine_benchmark.py
```

## Current local baseline

| Case | 90-day calculation | Deterministic windows | Eligible consolidated themes | Final diverse candidates |
|---|---:|---:|---:|---:|
| Delhi 1990 | 734.5 ms | 9 | 5 | 2 |
| Mumbai 1985 | 1094.7 ms | 47 | 3 | 2 |
| London 2000 | 1331.6 ms | 19 | 7 | 3 |
| Total | 3160.9 ms | — | — | 7 |

This baseline includes event resolution through D1 house-combination promise, MD–AD–PD delivery, and a same-carrier transit trigger. Divisional charts and supporting houses distinguish a `corroborated_event` from a `core_event`; absence of divisional confirmation does not veto an otherwise delivered event. “Eligible consolidated themes” means signatures that passed core resolution before final diversity limits.

Candidates sharing the same native house, carrier, dasha chain, and time window are consolidated into one ambiguity cluster when they represent different self/relative house frames. Candidate counts therefore measure displayable themes, not the number of possible derived-house interpretations stored inside those themes.

From schema `prediction_engine.v5`, ambiguity clusters are house-first. Every activated native house is rotated into each requested subject frame and expanded through the complete house-signification registry. Named combinations such as 2+11 income accumulation or 10+11 career recognition appear only when all constituent houses are active under the same delivery chain.

From schema `prediction_engine.v6`, neutral house topics are separate from predicted expression. Every interpretation alternative carries the shared carrier-based outcome tone, de-duplicated supportive/challenging factor counts, rule provenance, and an explicit tone-conditioned reading. Derived-house rotation changes the life area but cannot reverse the underlying activation polarity.

These timings are a development-machine baseline, not a production SLA. The fixtures verify deterministic stability and policy invariants; their predicted life events have not yet received manual astrologer sign-off and must not be described as accuracy gold standards until that review is completed.
