# Event Timeline Accuracy V2 — Implementation and Rollback Checklist

This checklist converts the September 2026 astrology/code audit into a reversible rollout. The legacy engine remains available as `legacy_v1`; the new path is `accuracy_v2`.

> Superseded as the default by `accuracy_v3`. V2 remains available as a rollback comparator. See `EVENT_TIMELINE_ACCURACY_V3_METHODOLOGY.md`.

## Rollback contract

- [x] Gate all changed prediction behaviour behind `EVENT_TIMELINE_ENGINE_VERSION`.
- [x] Accept `legacy_v1` and `accuracy_v2`; use `accuracy_v2` by default.
- [x] Attach `engine_version`, `methodology_version`, and `evidence_version` to every successful result.
- [x] Persist the engine version on jobs so caches from different methodologies are not silently mixed.
- [x] Allow an immediate rollback by setting `EVENT_TIMELINE_ENGINE_VERSION=legacy_v1` and restarting the backend.
- [x] Preserve the existing mobile JSON fields (`macro_trends`, `monthly_predictions`, events).
- [ ] Add an admin UI switch after the backend comparison period.
- [ ] Keep a cohort-based rollout percentage once sufficient production samples exist.

## P0 — target-period correctness

- [x] Build annual context for the selected year, not server “now”.
- [x] Replace misleading `current_dashas` in V2 context with a target-year anchor.
- [x] Include start/middle/end Vimshottari stacks and every detected MD/AD/PD/Sookshma change in the selected year.
- [x] Generate slow-planet transits for the exact selected calendar year, including past and far-future supported years.
- [x] Calculate Nadi age from the selected year.
- [x] Add target-month daily change detection instead of only start/middle/end change booleans.
- [x] Fail closed when target-period dasha or transit evidence cannot be calculated.
- [ ] Add exact sub-day ingress/aspect root solving; V2 currently resolves to calendar day.

## P0 — precision over volume

- [x] Remove legacy minimum-six-events-per-month and minimum-twenty-events-per-month requirements in V2.
- [x] Permit quiet months and an explicit `insufficient_evidence` state.
- [x] Limit normal yearly output to the strongest 0–3 event families per month.
- [x] Limit monthly deep output to the strongest 1–6 event families.
- [x] Remove “guaranteed”, “supreme override”, “on fire”, “million dollar”, and sales-conviction language from V2 prompts.
- [x] Require ranked alternatives beneath one event family instead of combinatorial event multiplication.

## P1 — deterministic evidence and validation

- [x] Build a machine-readable monthly evidence ledger before asking the LLM for prose.
- [x] Record the target dasha stack, dasha lord natal house/lordships, transit segments, whole-sign aspects, double-transit houses, and SAV values available for each month.
- [x] Give every evidence row a stable ID and require V2 events to cite evidence IDs.
- [x] Validate calendar month/year, date ordering, intensity values, event count, evidence IDs, and prohibited certainty language.
- [x] Downgrade unsupported High claims and drop events with no valid evidence.
- [x] Retain validation warnings in the result for audit/debugging.
- [ ] Add a full claim parser for every planet/sign/house/degree statement in generated prose.
- [ ] Replace day-level whole-sign conjunctions with configurable degree-orb entry/peak/exit windows.

## P1 — astrology layer repairs

- [x] Retain D2 in the timeline divisional-chart context for wealth checks.
- [x] Recompute Navatara evidence per selected transit segment in the deterministic ledger instead of relying on the first future macro segment.
- [x] Treat Nadi age, double transit, nakshatra return, Sudarshana, and Ashtakavarga as weighted evidence rather than guarantees in V2.
- [ ] Implement full Tajika annual chart judgement: Panchavargiya Bala, defensible Varshesha selection, Tajika aspects/yogas, Sahams, Muntha-lord condition, and annual house lords.
- [ ] Correct and independently verify Mudda Dasha against reference charts before giving it scoring authority.
- [ ] Add planet-specific Bhinnashtakavarga/Kakshya evidence; V2 currently exposes SAV as supporting evidence only.
- [ ] Independently score Parashari, Jaimini, Nadi, and Tajika before ensemble confirmation.

## P2 — birth-time and personal-context calibration

- [ ] Require/display birth-time source and uncertainty.
- [ ] Run sensitivity analysis for Lagna, Moon nakshatra boundary, divisional ascendants, and subdasha boundaries.
- [ ] Connect the dedicated rectification workbench to explicitly confirmed historical events.
- [ ] Capture current marital, employment, education, parenthood, and country/cultural context to suppress impossible manifestations.
- [ ] Never label a chart “rectified” from a single generic event confirmation.

## P2 — prospective outcome validation

- [ ] Store immutable pre-period forecasts with event family, window, probability, engine version, and evidence IDs.
- [ ] Add “occurred / did not occur / partly occurred”, actual date, and severity feedback to timeline cards.
- [ ] Measure precision, recall, precision@3, timing error, and Brier score by event domain.
- [ ] Compare V2 against `legacy_v1` and non-astrological age/life-stage baselines.
- [ ] Calibrate displayed probabilities only on an untouched holdout cohort.
- [ ] Promote V2 beyond provisional confidence labels only after the benchmark gate passes.

## Verification completed in this implementation

- [x] Existing timeline summary tests continue to pass.
- [x] New tests cover version selection, target-year context replacement, evidence construction, conservative validation, and cache-version separation.
- [ ] Run a blinded historical cohort comparison before making product accuracy claims.
