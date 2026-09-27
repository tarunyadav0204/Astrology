# Classical Yogas and Doshas implementation checklist

This checklist covers the astrologer feedback for combustion, Neecha Bhanga,
Mangal Dosha, Pitra Dosha, and Kaal Sarp. A result is not complete until the
calculation, API compatibility, mobile presentation, translations, and regression
tests are all complete.

## Non-negotiable rules

- [ ] Every implemented rule identifies its classical work, chapter, and verse.
- [ ] Textual or translation variants are exposed; the calculator must not silently merge them.
- [ ] No rule is added merely because it is common on websites or in modern software.
- [ ] No invented weighted score, probability, or strength grade is presented as classical.
- [ ] Calculation evidence is returned as structured data, not only prose.
- [ ] Existing response keys remain available until all clients have migrated.
- [ ] Chat, reports, chart overview, health, and prediction clients use the same canonical result.
- [ ] Regular users receive a plain-language result; astrologers can expand the exact rule evidence.
- [ ] All visible labels use theme tokens and are localized in every supported language.

## Combust planets

- [x] Mark combust planets with `(C)` in North Indian charts.
- [x] Mark combust planets with `(C)` in South Indian charts.
- [x] Show combustion in planetary-position tables and relevant chart tables.
- [x] Explain `(C)` in the chart legend.
- [x] Audit the canonical combustion thresholds, retrograde variants, and node exclusion against the chosen classical source.
- [x] Display angular distance, threshold used, and motion state in the planet detail.
- [x] Make every Parashari client consume the same combustion service; keep
  method-specific Tajika/Prashna solar conditions separate and labelled.

## Neecha Bhanga Raja Yoga

- [x] Select a named primary classical rule set: *Phaladeepika*, Chapter 7, verses 26–30.
- [x] Build one canonical calculator from those verses only.
- [x] Preserve the `Uchchanatha` interpretation variants stated by the translator/commentator.
- [x] Remove duplicate and contradictory calculation paths.
- [x] Preserve legacy `/yogas/`, chat, report, health, and prediction response fields.
- [x] Return the debilitated planet, sign, matched rule IDs, evidence, references, and unmatched rules.
- [x] Do not add Navamsha, retrogression, exchange, conjunction, or strength scoring unless separately sourced to a named classical text.
- [x] Add focused tests for every verse condition and for false positives.
- [x] Show the classical basis and reference on the Yoga card.
- [x] Add a compact `NB` planet condition indicator and deep-link to the explanation.
- [x] Show the houses ruled, occupied, and classically aspected by a debilitated
  or retrograde planet without treating retrogression as automatic positivity.
- [x] Reuse the same structured delivery channels in Planetary Positions and
  the Neecha Bhanga Yoga card.
- [x] Validate chat, reports, Health Blueprint, Event Timeline, and the Yoga screen after migration.

## Mangal Dosha

- [x] Choose and document the classical source and supported reference points.
- [x] Consolidate the current Yoga and marriage-matching calculators.
- [x] Replace the current High/Low shortcut with a source-backed classification.
- [x] Return placements, applicable exceptions, and pair-level balancing separately.
- [x] Add a Doshas-tab card with concise and expanded astrologer views.
- [x] Keep standalone chart assessment separate from partner compatibility.
- [x] Add calculation, API, chat, report, and UI regression tests.

## Kaal Sarp

- [x] Decide whether the feature can be supported by a named classical source; do not present a modern convention as ancient scripture.
- [x] Replace house-number containment with exact longitude arc calculation.
- [x] Define boundary handling for planets conjunct Rahu or Ketu.
- [x] Keep complete and partial configurations distinct.
- [x] Return the nodal direction, contained planets, outside planets, type rule, and reference.
- [x] Add a Doshas-tab card only after calculation validation.
- [x] Add boundary and false-positive tests.

## Pitra Dosha

- [x] Select a named textual tradition and document its exact combinations.
- [x] Replace the current broad any-affliction detector with explicit rule matches.
- [x] Keep ninth-house strain, solar affliction, and a named Pitra Dosha rule distinct.
- [x] Return corroborating and protective factors without erasing the base combination.
- [x] Add a Doshas-tab card with evidence and reference.
- [x] Add false-positive, corroboration, API, chat, report, and UI tests.

## Information architecture

- [x] Rename the chart entry from `Yogas` to `Yogas & Doshas`.
- [x] Add separate `Yogas` and `Doshas` tabs.
- [x] Keep per-planet states in Planetary Positions.
- [x] Cross-link affected planets and Yoga/Dosha details.
- [x] Render backend objects such as `major_doshas`; do not silently discard non-array categories.
- [x] Preserve the native selector, tablet layout, dark themes, and accessibility behavior.
