# Parashari Desk Product Backlog

This is the working backlog for turning Parashari Desk from a collection of charts and calculators into a complete classical judgment workspace for practising astrologers.

The target is not to add the largest number of tabs. The target is to let an astrologer move from chart facts to a defensible conclusion without manually assembling evidence across multiple screens or using another application.

## Product outcome

Parashari Desk should answer four connected questions:

1. **What does the natal chart promise?**
2. **Which planets and combinations can deliver it?**
3. **What is active in the selected period?**
4. **Why did the application reach that conclusion?**

Every conclusion must be traceable to canonical chart facts, an identified interpretive rule, and—where a classical claim is made—a named source and reference.

## Non-negotiable principles

- [ ] Keep Parashari Desk method-pure. Do not silently mix KP, Nadi, Jaimini, Tajika, or product-created rules into a Parashari judgment.
- [ ] Use one canonical backend calculation for every astrological fact consumed by web, mobile, Ask Tara, reports, health, Event Timeline, and prediction clients.
- [ ] Preserve existing API fields until every client has migrated. Add structured fields rather than breaking contracts.
- [ ] Present the reading first. Put calculation traces, matched rules, textual variants, and references behind an intentional expansion.
- [ ] Preserve supporting, weakening, protective, and contradictory evidence. Do not cancel evidence before the astrologer can inspect it.
- [ ] Do not present an implementation score, weighted vote, or probability as a classical verdict.
- [ ] Declare the interpretive convention when classical traditions disagree.
- [ ] Keep natal promise separate from Dasha and transit activation.
- [ ] Make every layout usable on mobile, tablet, laptop, and large desktop without duplicating astrological logic.
- [ ] Localize all regular-user wording. Classical names and references may retain their standard transliteration where appropriate.
- [ ] A feature is incomplete until calculation tests, response-contract tests, client regression tests, responsive presentation, dark themes, and accessibility have been checked.

## Current strengths to preserve

- Multiple Ayanamsha standards and true/mean node selection.
- D1, divisional, Bhava Chalit, Karkamsa, Swamsa, and transit chart access.
- Shared time navigation for Dashas, transits, and activations.
- Vimshottari, Yogini, Kalachakra, and Chara Dasha tables.
- Clickable houses with natal condition, current activation, occupants, aspects, and Ashtakavarga evidence.
- Positions, Life, Yogas and Doshas, friendships, lordships, and aspects work areas.
- Shadbala, Ashtakavarga, dignity, Chara Karaka, Panchanga, special-point, special-Lagna, and planetary-condition summaries.
- Resizable desktop chart and analysis work areas.
- Mobile and tablet focused-chart presentation.

---

## P0 — Correctness and canonical-data consolidation

These items should be completed before new judgment features are trusted.

### P0.1 Fix house-selection data defects

- [x] In `frontend/src/components/BirthChart/ChartsDashasWorkspacePage.js`, make `buildHouseSelection()` use its `renderedChartData` argument instead of the undefined `chartData` variable.
- [x] In `frontend/src/components/BirthChart/ParashariDeskMobile.js`, make `buildHouseSelection()` use its `effectiveChartData` argument instead of the undefined `chartData` variable.
- [ ] Add tests covering house selection in D1, each selectable Varga, Bhava Chalit, Karkamsa, Swamsa, and transit charts.
- [ ] Confirm changing the native, chart standard, node mode, and selected Varga invalidates the selected-house state correctly.

**Exit gate:** The selected house always belongs to the chart currently visible, and no stale native or chart data appears in the insight panel.

### P0.2 Make planetary positions backend-canonical

- [ ] Remove local dignity calculation from `DeskPositionsTable.js`.
- [ ] Remove local Nakshatra and Pada calculation from `DeskPositionsTable.js`.
- [ ] Consume the same structured planetary-condition response used by the canonical Positions experience.
- [ ] Preserve dignity, sign relationship, Nakshatra-lord relationship, Vargottama, combustion, retrogression, avasthas, Yogi/Avayogi status, Dagdha/Tithi Shunya qualification, and other supported conditions without recomputation in React.
- [ ] Add boundary fixtures for sign, Nakshatra, Pada, combustion, and divisional transitions.

**Exit gate:** The same planet shows identical facts in Parashari Desk, Positions, chart bottom sheets, mobile, web, Ask Tara, and reports.

### P0.3 Make friendship and aspects backend-canonical

- [ ] Replace the hard-coded friendship calculation in `DeskFriendshipPanel.js` with the canonical backend friendship result.
- [ ] Render natural, temporal, and compound friendship as separate facts with the calculation basis.
- [ ] Replace frontend-owned aspect policy in `DeskAspectsPanel.js` with canonical structured aspects.
- [ ] Preserve the aspect type, source planet, target planet or house, direction, and convention used.
- [ ] Add contract tests proving existing chat, reports, predictions, and chart clients continue to receive compatible fields.

**Exit gate:** There is only one executable implementation for each Parashari friendship and aspect rule.

### P0.4 Declare debated traditions

- [ ] Add an **Interpretive tradition** setting to the Desk profile.
- [ ] Define and document the default strict Parashari profile.
- [ ] Keep Rahu and Ketu special aspects out of an unqualified universal legend.
- [ ] If node special aspects are supported, expose them as an explicit optional convention with a named basis.
- [ ] Store the convention/profile version with calculated evidence and saved results.
- [ ] Prevent a presentation-only setting from silently changing chat or prediction behavior.

**Exit gate:** An astrologer can tell which aspect convention produced every node-related conclusion.

### P0.5 Remove opaque verdict authority

- [ ] Audit visible support/challenge meters and weighted-strength labels.
- [ ] Keep raw contributing evidence available.
- [ ] Describe any product-created resolver as an implementation policy rather than a classical rule.
- [ ] Prefer classifications such as `promised`, `qualified`, `obstructed`, `activated`, and `not sufficiently established` only when their declared rule gates are satisfied.
- [ ] Keep overall house-strength labels explicitly directional; individual positive and negative factors remain the authoritative detail.

**Exit gate:** No unexplained score or colour is presented as if a classical text declared the verdict.

---

## P1 — Topic Lens and Classical Judgment Workspace

This is the primary product feature and the main professional-use moat.

**Current implementation:** Health is the first active topic. It uses the existing Health V2 natal and timing engines through a provider adapter, and reuses Event Windows for the optional broader search. Career, wealth, and the remaining topics stay unchecked until their own canonical providers and rule coverage are connected.

### P1.1 Topic registry

- [ ] Create a versioned topic registry for marriage, career, wealth, children, health, property and vehicles, education, foreign travel and settlement, litigation, parents, and spiritual life.
- [ ] For every topic, declare relevant D1 houses, natural Karakas, functional roles, special Lagnas, divisional charts, Yogas/Doshas, Dasha evidence, transit evidence, and applicable classical-rule families.
- [x] Keep topic configuration separate from UI components.
- [x] Support adding a topic through registry data and rule providers rather than adding a new set of screen-specific conditionals.

### P1.2 Topic-focused workspace

- [x] Add a visible topic selector to Parashari Desk.
- [ ] Reconfigure the chart area, pinned houses, relevant planets, divisionals, evidence panels, and period analysis for the selected topic.
- [x] Preserve a general chart-study mode without a topic selection.
- [ ] Make the selected topic and selected native part of the shareable/restorable workspace state.

### P1.3 Structured judgment contract

- [ ] Define a versioned backend response containing:
  - `natal_promise`
  - `primary_contributors`
  - `supporting_factors`
  - `obstructing_factors`
  - `protective_factors`
  - `active_period`
  - `timing_windows`
  - `possible_manifestations`
  - `alternative_manifestations`
  - `counter_evidence`
  - `rule_trace`
  - `source_references`
- [ ] Require every conclusion to reference normalized evidence IDs.
- [ ] Do not allow a Varga or transit to create an event that is absent from the declared natal-promise method.
- [ ] Explain why one manifestation was preferred when the same houses permit several meanings.

### P1.4 Judgment presentation

- [ ] Lead with a concise conclusion written for a practising astrologer.
- [ ] Show natal promise, current activation, timing, and alternatives as distinct sections.
- [ ] Add **Why this judgment?** with placements, relationships, matched rules, qualifications, and sources.
- [ ] Show counter-evidence and unresolved ambiguity instead of forcing a single conclusion.
- [ ] Provide focused mobile, split tablet, and workstation desktop layouts from the same response contract.

**P1 exit gate:** An astrologer can select a topic and reach a complete, inspectable judgment without manually searching unrelated tabs.

---

## P2 — Astrological Trace

### P2.1 Planet trace

- [ ] Selecting a planet highlights it across D1, relevant Vargas, Dashas, transits, Yogas/Doshas, strengths, aspects, and applicable rules.
- [ ] Present its lordships, occupation, conjunctions, aspects, dispositors, sign and Nakshatra relationships, dignity, avasthas, combustion, retrogression, Vargottama, Yogi/Avayogi, Dagdha/Tithi Shunya, Shadbala, Ashtakavarga, and functional role.
- [ ] Show how its role changes by topic and divisional context without changing natal astronomical facts.
- [ ] Produce a readable causal chain from natal role to current delivery.

### P2.2 House trace

- [ ] Selecting a house highlights its lord, occupants, aspecting planets, Karakas, Bhava strength inputs, Ashtakavarga, applicable rules, relevant Vargas, active Dasha carriers, and transit contacts.
- [ ] Separate house significations, sign-based body or thematic indications, and topic-specific interpretation.
- [ ] Preserve natal house condition while showing current activation separately.

### P2.3 Cross-panel selection model

- [ ] Define one shared selection state for planet, house, topic, Dasha period, transit date, and rule.
- [ ] Make every panel react to the same state without recalculating astrology independently.
- [ ] Support back/forward navigation and deep links to a trace.
- [ ] Provide **Clear focus** and visible breadcrumbs.

**P2 exit gate:** One selection produces a complete cross-chart evidence chain, and every displayed fact links back to its canonical record.

---

## P3 — Period Judgment

### P3.1 MD–AD–PD synthesis

- [ ] Clicking any MD–AD–PD combination opens a period judgment.
- [ ] Show houses activated by each lord and the exact mechanism: lordship, occupation, aspect, dispositor, Nakshatra link, Yoga, or other declared rule.
- [ ] Show cooperative delivery across the three lords rather than demanding that one planet carry every required house.
- [ ] Show matching natal promises and relevant divisional corroboration.
- [ ] Show supporting, obstructing, and protective transits separately.
- [ ] Keep Sookshma and Prana available as optional inspection data; do not make them the default basis of a long health or life-period conclusion.

### P3.2 Period comparison

- [ ] Add `Previous period`, `Selected period`, and `Next period` comparison.
- [ ] State which houses, planets, topics, and rules entered or left activation.
- [ ] Explain what materially changed instead of merely redrawing the chart for another date.
- [ ] Let the astrologer compare any two saved periods.

### P3.3 Timing layers

- [ ] Use slow transits to describe the broader operating climate.
- [ ] Use the Sun to identify shorter concentration windows.
- [ ] Use the Moon as a brief trigger only when a natal promise and an active period already exist.
- [ ] Group triggers into meaningful windows rather than producing repetitive daily lines.
- [ ] Display exact contacts and classical aspects in familiar astrological language.

**P3 exit gate:** The astrologer can explain what a period may deliver, why it differs from adjacent periods, and when its stronger windows occur.

---

## P4 — Varga Repetition Matrix

- [ ] Build a topic-aware matrix comparing D1 with only the relevant divisional charts.
- [ ] Show repeated planets, houses, signs, dispositors, dignity, relationships, Karakas, and rule themes.
- [ ] Distinguish repetition, reinforcement, qualification, and contradiction.
- [ ] Do not assign identical meanings to the same house number in every Varga.
- [ ] Explain why a particular Varga is relevant to the selected topic.
- [ ] Let a matrix cell open the Astrological Trace at that exact chart factor.

**Exit gate:** The astrologer can see genuine cross-Varga corroboration without opening and mentally comparing every chart.

---

## P5 — Classical Rule Coverage and Resolver

- [ ] Continue encoding classical rules chapter by chapter with source, verse, textual variant, prerequisites, matched clauses, unmatched clauses, and resulting interpretation.
- [ ] Keep catalogued doctrine separate from executable rules.
- [ ] Make the reading primary and expose the rule/reference on demand.
- [ ] Report how many applicable rules were evaluated, matched, qualified, contradicted, or lacked required data.
- [ ] Build a declared qualification resolver for dignity, affliction, cancellation, protection, lord strength, and repeated evidence.
- [ ] Never invent a resolver and describe it as a verse from the classics.
- [ ] Support new chapters through generic rule and reading renderers rather than chapter-specific screens.
- [ ] Connect rule matches to Topic Lens, Astrological Trace, and Period Judgment through stable evidence IDs.

**Exit gate:** A new supported chapter can contribute readings to the Desk without new bespoke frontend logic.

---

## P6 — Known-event validation

- [ ] Let the astrologer record dated or bounded known events such as marriage, childbirth, employment, promotion, property purchase, foreign move, surgery, and death of a parent.
- [ ] Evaluate the event against the same natal-promise, Dasha, and transit rules used prospectively.
- [ ] Show matched, missing, and contradictory evidence.
- [ ] Do not silently tune global rules or the native's chart from a recorded event.
- [ ] Offer an explicit handoff to rectification when the astrologer chooses to use the event for birth-time analysis.
- [ ] Store validation history with calculation, ephemeris, doctrine-profile, and rule versions.

**Exit gate:** The astrologer can assess how the declared method performed on known life events without contaminating future calculations.

---

## P7 — Professional research and comparison

- [ ] Compare two dates or transit skies with changed factors highlighted.
- [ ] Compare two Dasha periods with changed activation and manifestations highlighted.
- [ ] Compare supported calculation standards without silently combining them.
- [ ] Add search or command navigation for planet, house, Varga, Dasha, topic, Yoga/Dosha, special point, and classical rule.
- [ ] Allow named workspace presets after the core judgment workflow is stable.
- [ ] Add exportable judgment reports only after on-screen evidence and citations are complete.

---

## Calculations to audit for professional completeness

These may already exist elsewhere in the backend or mobile application. Audit before implementing another calculator.

- [ ] Bhava Bala and its component presentation.
- [ ] Vimshopaka or Shodashavarga strength, with a selected classical method.
- [ ] Ishta and Kashta Phala, if a source-grounded implementation can be established.
- [ ] Complete supported Avasthas and their interpretive limits.
- [ ] Argala and Virodhargala presentation in the appropriate Jaimini context rather than silent Parashari mixing.
- [ ] Arudha and Upapada links where relevant, with method labels.
- [ ] Divisional-chart-specific interpretive roles and limitations.
- [ ] Whether existing special points and Lagnas are calculated canonically and surfaced in the relevant traces.

Each audit must end in one of four states: `already canonical`, `canonical but not surfaced`, `duplicated/inconsistent`, or `not implemented`.

---

## Explicitly out of scope for the core Parashari judgment

- KP significator chains or cusp logic.
- Nadi combination logic.
- Jaimini Rashi Drishti, Argala, and Chara Dasha unless displayed as separately labelled supporting work areas.
- LLM-generated astrological facts or unsupported rules.
- Generic probability percentages for life events.
- CRM, appointment, billing, or astrologer-practice operations.
- More tabs whose information is not connected to a judgment workflow.

---

## Cross-client regression matrix

Every change to a shared calculator or response contract must test:

- [ ] Parashari Desk web desktop.
- [ ] Parashari Desk web mobile/tablet.
- [ ] Mobile native chart hub and detail screens.
- [ ] Standard/Premium Ask Tara path.
- [ ] Instant/live chat path.
- [ ] Chart house insight and planet detail.
- [ ] Positions, Life, Yogas/Doshas, Friends, Lords, and Aspects.
- [ ] Event Timeline monthly and yearly clients.
- [ ] Health Blueprint and health timing.
- [ ] Reports and saved/generated results.
- [ ] Existing cached payloads and older mobile builds.

## Recommended execution order

1. **P0 correctness and canonical consolidation**
2. **P1 Topic Lens and Classical Judgment Workspace**
3. **P2 Astrological Trace**
4. **P3 Period Judgment**
5. **P4 Varga Repetition Matrix**
6. **P5 Classical Rule Coverage and Resolver**
7. **P6 Known-event validation**
8. **P7 Professional research and comparison**

P5 rule authoring can continue in parallel with P1–P4, but new rules should enter the UI only through the shared contracts and generic renderers defined here.

## Definition of done for the overall backlog

- [ ] A professional astrologer can begin with a topic, inspect the natal promise, identify the delivering planets, select a period, see timing windows, and audit the conclusion without leaving Parashari Desk.
- [ ] The same astrological fact is identical across every client.
- [ ] Every classical claim has a traceable reference and every product policy is labelled as such.
- [ ] Contradictory and qualifying evidence remains visible.
- [ ] New topics, rules, and classical chapters do not require bespoke copies of calculation logic or one-off screen architecture.
- [ ] Mobile, tablet, and desktop provide purpose-built layouts over the same backend response.
