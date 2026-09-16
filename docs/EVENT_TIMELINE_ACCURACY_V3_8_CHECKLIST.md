# Event Timeline Accuracy V3.8 — Integrated Calculators Checklist

This checklist turns the accuracy recommendations into reversible, testable implementation work. `integrated_v2` is the new default; V3.7 (`delivery_v1`) and V3.6 remain comparison and rollback paths.

## Rollback and evidence contract

- [x] Add `EVENT_TIMELINE_V3_ACCURACY_LAYER=integrated_v2` as the default.
- [x] Support `EVENT_TIMELINE_V3_ACCURACY_LAYER=delivery_v1` to reproduce the prior V3.7 judgment layer without the new supporting modifiers.
- [x] Support `EVENT_TIMELINE_V3_ACCURACY_LAYER=legacy_v3_6` for immediate rollback.
- [x] Include the accuracy-layer version and language in the result/cache fingerprint.
- [x] Preserve the existing mobile response contract and deterministic English/Hindi templates.
- [x] Record every gate, score contribution, limitation, and evidence source in the candidate model.
- [x] Never present an astrological support score as an empirical probability.

## P0 — natal promise gate

- [x] Evaluate the event anchor house and its lord in D1.
- [x] Evaluate transition and outcome house/lord connections without treating outcome as mandatory.
- [x] Evaluate event-specific natural karakas.
- [x] Detect direct lord/house/karaka sambandha by conjunction, aspect, exchange, and dispositor linkage.
- [x] Repeat the event-signature check from the Moon where reliable Moon data is available.
- [x] Classify natal promise as `strong`, `available`, `weak`, or `unavailable`.
- [x] Require at least `weak` natal promise for narrow concrete claims; downgrade broad themes safely when data is incomplete.
- [x] Keep a trace explaining why the natal gate passed, weakened, or could not be evaluated.

## P0 — active planet delivery

- [x] Evaluate each MD/AD/PD carrier's natal house, lordships, sign and dignity.
- [x] Include combustion, retrogression, and conjunction/affliction data when available.
- [x] Evaluate the carrier's dispositor and whether the dispositor connects to the event signature.
- [x] Distinguish direct lordship/occupation from aspect-only delivery.
- [x] Measure cooperation or conflict among MD/AD/PD carriers.
- [x] Produce `supportive`, `mixed`, `obstructed`, or `unavailable` delivery verdicts.
- [x] Use delivery to rank and qualify manifestation; never let missing optional strength data fabricate denial.

## P0 — event outcome and obstruction

- [x] Define event-specific obstruction/denial houses separately from event houses.
- [x] Score initiation, ease/obstruction, outcome, permanence, and completion as separate dimensions.
- [x] Do not equate event activation with a favourable outcome.
- [x] Express preparatory, developing, result-window, and obstructed phases distinctly.
- [x] Prevent narrow positive wording when outcome support is absent or obstruction dominates.

## P1 — Rahu/Ketu and dispositor chain

- [x] Preserve the doctrine that nodes have no direct classical house lordship.
- [x] Evaluate node occupation and seventh aspect.
- [x] Resolve sign dispositor from natal longitude/sign.
- [x] Resolve nakshatra lord when longitude is available.
- [x] Include conjunctions within a documented orb.
- [x] Trace whether the node's dispositor/nakshatra lord participates in MD/AD/PD or the event signature.
- [x] Expose unavailable links instead of inventing them.

## P1 — KP event confirmation

- [x] Evaluate cusp sub-lord permission for every event anchor.
- [x] Resolve planet → star lord → sub-lord significator chains when supplied by KP data.
- [x] Separate positive event houses from obstructing houses.
- [x] Require the active dasha hierarchy to signify the event combination for strong KP support.
- [x] Evaluate transit contact to KP anchor cusps when degrees are available.
- [x] Return `supported`, `qualified`, `pressured`, `blocked`, or `unavailable` with a complete trace.
- [x] Keep KP Placidus coordinates independent of the Parashari whole-sign graph.

## P1 — relevant divisional-chart judgement

- [x] Evaluate the selected varga ascendant and ascendant lord when present.
- [x] Evaluate the relevant varga house, its lord, and the event karaka.
- [x] Evaluate active dasha carriers by placement, lordship, dignity, conjunction, and aspect in that varga.
- [x] Require D1–varga repetition for the strongest confirmation.
- [x] Distinguish `confirmed`, `mixed`, `not_confirmed`, and `unavailable`.
- [x] Never use one divisional chart for unrelated life departments.

## P1 — transit geometry and temporal windows

- [x] Preserve exact ingress/change dates already present in the transit ledger.
- [x] Split a month when MD/AD/PD/Sookshma or a relevant transit segment changes.
- [x] Classify daily-sampled transit contacts as applying, exact, separating, or boundary/stationary when degrees permit.
- [x] Account for retrograde repeat passes and direction-change stations exposed by the daily ephemeris.
- [x] Evaluate contacts to natal event lords/karakas, not houses alone.
- [x] Evaluate contacts to Lagna and Moon as reference evidence without adding the same contact twice to the score.
- [x] Mark day-level or sign-level timing limitations explicitly when exact degrees are unavailable.
- [x] Cap the exact-contact ranking contribution; do not convert daily samples into false intraday precision.

## P2 — conditional supporting systems

- [x] Add the repository's planet-specific Prastara Bhinnashtakavarga and Kakshya bindu data as an ease/timing modifier only.
- [x] Add the verified Varshaphal subset already calculated in the repository: solar return chart, Muntha, current year-lord field, and Mudda Dasha.
- [ ] Add full Varshaphal/Tajika judgment only when Panchavargiya Bala, independently selected Varshesha, Sahams, and Tajika aspects exist. The current calculator does not implement these, so the product must label the subset honestly.
- [x] Add Chara, Yogini, Kalachakra, and Sudarshana as independently grouped, capped comparators with explicit applicability rules.
- [x] Prevent confidence multiplication when multiple techniques reuse the same underlying signal; each independence group contributes at most once and the total adjustment is capped.

## Desh-Kaal-Patra and birth-time reliability

- [x] Continue using explicit user facts as manifestation constraints, never astrological evidence.
- [x] Apply employment, relationship, parenthood, age, and life-stage gates to new layers.
- [x] Record birth-time source/verification/uncertainty when available.
- [x] Downgrade KP cusp and sensitive-varga claims when birth-time uncertainty crosses a relevant boundary.
- [x] Run birth-time sensitivity at the supplied bounds for Lagna, Moon nakshatra, D4/D7/D9/D10/D24/D30 ascendants, KP cusp sub-lords, and the MD/AD/PD stack.

## Product and calibration

- [x] Preserve all qualified candidates and distinguish primary from background display.
- [x] Store immutable pre-period forecasts, including background candidates, with engine/method/evidence/layer versions and a content hash.
- [x] Collect occurred, partly occurred, did-not-occur, actual date, severity, notes, and material unpredicted events.
- [x] Measure observed precision, strict precision, precision@3, reported-event recall, timing error, grade/domain false positives, and engine/layer breakdowns without treating support scores as probabilities.
- [ ] Run a prospective comparison of V3.8, V3.7, V3.6, V2, and a non-astrological age/life-stage baseline. Storage and engine/layer metrics now support the comparison; credible results require future outcome data and a separately specified baseline.
- [ ] Promote or remove rules based on blinded prospective results rather than anecdotal matches.

## Verification

- [x] Unit-test natal promise, delivery, node chains, obstruction, KP, varga, and language parity.
- [x] Regression-test the Saturn–Rahu–Jupiter multi-house example.
- [x] Confirm monthly and yearly use the same accuracy layer.
- [x] Confirm V3.6 rollback reproduces its candidate selection.
- [x] Confirm V3.7 rollback excludes the new exact-contact, Ashtakavarga, alternate-dasha, and birth-sensitivity modifiers.
- [x] Run backend, mobile JSX, localization, and whitespace checks.
- [x] Run at least one real yearly deterministic comparison and inspect event volume and explanations.

## V3.9 — subject-relative events and complete monthly evidence

- [x] Preserve every fast-planet transit segment in integrated V3, including segments after the former eight-segment cutoff.
- [x] Keep the historical cutoff in V2/legacy rollback paths.
- [x] Add reusable relative-house rotation for spouse, child, mother, father, younger sibling, and elder sibling.
- [x] Create relative-health candidates only for people established by current user facts.
- [x] Require the person's anchor, at least two of their derived H6/H8/H12, a dasha connection, and a transit trigger inside those medical houses.
- [x] Treat D30, KP, medical karakas, and exact transits as confirmation rather than diagnosis.
- [x] Allow procedure wording only when derived H8, a treatment/rest house, and Mars coincide; never assert surgery or a body-part diagnosis.
- [x] Prefer the newest explicit user fact while retaining conflicting older facts in the audit basis.
- [x] Carry birth-time rectification metadata into background timeline generation.
- [x] Cover relative-house mapping, user-fact eligibility, stale-fact resolution, and late-month evidence with regression tests.

## V3.10 — all applicable events for people around the native

- [x] Rotate every Instant event definition into each fact-established relative's house frame.
- [x] Superseded in V3.20: use the relative's reference house as the rotated lagna, not as an activation gate; require the rotated event houses to pass their own gates.
- [x] Reuse each source event's karakas, KP rules, obstruction houses, varga, and exact-transit logic after house rotation.
- [x] Add subject-aware English and Hindi copy for work, recognition, health, property, relocation, relationships, travel, children/caregiving, education, and income.
- [x] Suppress spouse-relative marriage and children duplicates because those describe shared native events and could be misleading as separate spouse events.
- [x] Keep native events in the primary focus list and return relative events through separate `people_candidates` fields.
- [x] Initially expose at most two Grade A/B relative events, with at most one per person; retain every remaining result under `people_background_candidates`.
- [x] Add a collapsed “People around you” section on yearly and monthly-deep screens, then a separate nested accordion for every person with an event count and top-theme preview.
- [x] Count people—not events—in the month header badge, while keeping every event accessible inside that person's accordion.
- [x] Keep every relative-event Why collapsed by default.
- [x] Add at most one recurring family-context line to the annual vibe without displacing native themes.
- [x] Verify backend selection/API behavior, mobile JSX, and localization.

## V3.11 — persistent permission and bounded event timing

- [x] Apply the rule generically to H1-H12 rather than adding an H9/travel exception.
- [x] Let direct transit occupation by an active MD/AD/PD lord open a required event anchor when natal dasha channels do not open it.
- [x] Classify that occupation as persistent background permission instead of allowing it to time its own event.
- [x] Require a separate PD/Sookshma or faster-transit channel in the event's transition/outcome houses.
- [x] Evaluate date overlap at ledger segment boundaries; reject a month when permission and the independent trigger do not coexist.
- [x] Apply the same subject-anchor and event-anchor rule after relative-house rotation for every eligible person and event family.
- [x] Keep long-running qualified themes in background while reserving primary cards for their strongest one- or two-month corridor.
- [x] Merge adjacent monthly instances under an auditable cross-month event-window ID.
- [x] Explain the persistent permission and independent timing trigger separately in English and Hindi.
- [x] Keep `delivery_v1` and `legacy_v3_6` as cache-separated rollback paths with their earlier natal-only anchor semantics.
- [x] Add native, relative-person, repetition-control, timing-window, and rollback regression tests.

## V3.12 — bhava-to-life-channel disambiguation

- [x] Make `EVENT_TIMELINE_V3_PUBLICATION_MODE=exhaustive` bypass every primary-card and persistent-peak display limit.
- [x] Keep prioritized mode as the default without deleting qualified/background evidence.
- [x] Add an H1-H12 thread catalogue so an activated house is treated as a department rather than a concrete event.
- [x] Require property purchase to combine H4, H11, and a funding/outlay channel through H2 or H8.
- [x] Add vehicle acquisition as a separate event definition requiring H4, H2, and H11.
- [x] Add D3, D12, and D16 to the optimized natal context for sibling, parent-line, and vehicle/comfort discrimination.
- [x] Judge each event channel through companion houses, natural karakas, and its topic varga.
- [x] Return `channel_distinguished`, `channel_supported_but_ranked`, or `bhava_level_ranked` with every native and relative candidate.
- [x] Downgrade exact-channel wording when karaka/varga evidence does not isolate the selected manifestation.
- [x] Keep property, vehicle, residence, mother/family-line, education, and emotional-security meanings distinct rather than treating every H4 activation as property.
- [x] Confirm relative identity separately through D3 for siblings, D7 for children, D9 for spouse, and D12 for parents, without replacing the event-specific varga.
- [x] Add exhaustive-mode, H4-only rejection, H11 acquisition, vehicle separation, and all-house audit regression coverage.

## V3.13 — plain-language event cards

- [x] Separate visible event-card language from the technical astrology explanation.
- [x] Use short sentences, common words, and direct descriptions in every English deterministic event template.
- [x] Simplify Hindi event labels, predictions, phase language, and relative-person wording.
- [x] Remove planet names, dasha/transit terminology, KP, varga names, and scoring language from visible predictions.
- [x] Keep the complete technical evidence in the collapsed Why and audit payload.
- [x] Express developing, result, preparatory, obstructed, and uncertain phases in everyday language.
- [x] Apply the same plain-language contract to self and People Around You events.
- [x] Reject optional LLM prediction text containing astrology jargon and restore the deterministic plain-language sentence.
- [x] Add regression coverage proving predictions contain no astrology terminology while Why retains the evidence.

## V3.14 — clear prediction-strength presentation

- [x] Stop mixing credible alternatives, long-running themes, and weak signals under “Other qualified events.”
- [x] Show only Grade A/B candidates as main possibilities in prioritized integrated V3; retain the legacy and exhaustive rollback behavior.
- [x] Split omitted native candidates into `also_possible_candidates`, `ongoing_background_candidates`, and `weak_signal_candidates`.
- [x] Apply the same classification to relative events without mixing them into the native's sections.
- [x] Add deterministic `display_tier`, `display_reason`, `display_explanation`, and non-technical `support_label` fields.
- [x] Explain that main possibilities are not guarantees, alternatives are credible but less clear, ongoing themes lack a sharp monthly peak, and weak signals are not predictions.
- [x] Replace user-facing Grade A/B/C badges with Strong, Moderate, Background, and Weak indication labels.
- [x] Provide the complete presentation contract in both English and Hindi.
- [x] Preserve `background_candidates` and `people_background_candidates` as compatibility unions for rollback and older clients.
- [x] Keep every technical Why collapsed by default in all four tiers.
- [x] Add regression coverage for tier separation, reason codes, Hindi labels, legacy rollback, and compatibility fields.

## Deterministic delivery progress

- [x] Replace the fixed 100-second percentage with backend-reported pipeline stages for deterministic generation.
- [x] Report 5% while preparing the chart, 78% after astrology calculations, 88% while resolving events, 96% while finalizing, and 100% on completion.
- [x] Keep separate interpretation-stage progress for LLM narration mode.
- [x] Return `generation_mode`, `progress_percent`, and `progress_stage` from job start/status responses.
- [x] Start polling immediately because deterministic runs may finish before the first three-second interval.
- [x] Apply the same progress contract to yearly timelines and monthly deep dives.
- [x] Persist generation mode with resumable mobile jobs and stop simulated progress as soon as server progress is available.
- [x] Keep showing the numerical percentage through finalization rather than replacing it with an indefinite “Almost there” label.

## V3.15 — monthly timing lift and recurrence control

- [x] Treat natal promise, MD/AD permission, KP, and varga support as an annual baseline rather than twelve separate monthly events.
- [x] Compute `monthly_timing_score` from event-specific PD/Sookshma channels, fast-planet exact contacts, corridor length, and manifestation phase.
- [x] Require a distinctive Sun/Moon/Mars/Mercury/Venus contact to an event lord, karaka, or relevant target before promoting a monthly peak.
- [x] Cap contact corroboration so a noisy count of broad contacts cannot overwhelm contact quality.
- [x] Select at most two separated peaks per subject/event family, and require the second peak to have a different fine-timing signature.
- [x] Mark adjacent months as continuation rather than predicting the event again.
- [x] Keep non-adjacent annual permission in `annual_context_candidates` for audit/yearly synthesis, but do not show it as a monthly event or background chip.
- [x] Remove the forced minimum of three monthly events and permit genuinely quiet months.
- [x] Limit a peak month to four distinct native life domains and two relative-person peaks without deleting alternatives.
- [x] Narrow primary-card dates to the strongest retained event-specific contact window.
- [x] Apply the same peak/continuation/background policy to all event families and all fact-established relatives.
- [x] Preserve exhaustive and earlier accuracy layers as rollback modes.
- [x] Verify the policy against Deepika Yadav's real 2026 local chart and add a twelve-month repetition regression.
