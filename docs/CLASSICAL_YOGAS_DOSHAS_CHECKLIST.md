# Classical Yogas and Doshas implementation checklist

The remaining source-audited backlog is maintained in
[`MISSING_CLASSICAL_YOGAS_DOSHAS_CHECKLIST.md`](MISSING_CLASSICAL_YOGAS_DOSHAS_CHECKLIST.md).

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

## Matru Dosha

- [x] Use the thirteen Mātṛ-śāpa combinations in BPHS 83.34–46.
- [x] Keep the stated progeny scope and reject broad Moon/fourth-house shortcuts.
- [x] Return every matched and unmatched clause with source references.
- [x] Add the Doshas card, complete-rule popup, chat compaction and report output.
- [x] Add verse coverage, false-positive and contract tests.

## Information architecture

- [x] Rename the chart entry from `Yogas` to `Yogas & Doshas`.
- [x] Add separate `Yogas` and `Doshas` tabs.
- [x] Keep per-planet states in Planetary Positions.
- [x] Cross-link affected planets and Yoga/Dosha details.
- [x] Render backend objects such as `major_doshas`; do not silently discard non-array categories.
- [x] Preserve the native selector, tablet layout, dark themes, and accessibility behavior.

## Existing Yoga audit

- [x] Replace the permissive Gaja Kesari house-pair shortcut with BPHS 36.3–4,
  including benefic support and the debilitation, combustion, and enemy-sign exclusions.
- [x] Enforce BPHS 36.5–6 exclusive-benefic occupancy for Amala Yoga.
- [x] Rebuild Sunapha, Anapha, Durudhura, Kemadruma and Adhi from BPHS 37.5–13;
  document the selected Kemadruma cancellation reading instead of merging variants.
- [x] Rebuild Vesi, Vasi and Ubhayachari from BPHS 38.1–4 and expose the
  benefic, malefic, or mixed composition without inventing a strength grade.
- [x] Rebuild Pancha Mahapurusha from Phaladeepika 6.1.
- [x] Rebuild Saraswati from Phaladeepika 6.26–27; remove the former
  conjunction/mutual-aspect shortcut.
- [x] Rebuild Kendra–Trikona Raja Yoga from BPHS 34.11–15, including the
  single-planet Yogakaraka rule and stated dusthana-lord exclusion.
- [x] Replace the generic 2nd/11th Dhana shortcut with the special combinations
  explicitly stated in BPHS 41.2–15.
- [x] Rebuild Dharma–Karma, Harsha, Sarala, Vimala and the 66 Parivartana
  classification from their named Phaladeepika rules.
- [x] Rebuild all four Nabhasa families from BPHS 35.1–17: add Mala and Sarpa,
  correct Nala, require complete Akriti patterns, and treat Sankhya as residual.
- [x] Preserve legacy response keys while omitting unsourced product-created
  labels from the classical Yoga screen.
- [x] Add false-positive and response-contract regression tests.
- [x] Record the executable reading and variant policy in
  'docs/CLASSICAL_CORE_YOGA_READINGS.md'.
- [x] Correct Phaladeepika 6.57 to support both difficult-house placement and
  malefic conjunction/aspect branches for Harsha, Sarala and Vimala.
- [x] Resolve 'mahita-bhava' in Phaladeepika 6.37 through the text's own 1.17
  good/difficult-house classification; do not silently substitute
  Kendra/Trikona.
- [x] Keep a single 9th/10th lord under BPHS 34.13 Yogakaraka rather than
  relabelling it as Phaladeepika's two-lord conjunction.
- [x] Make Amala exclusivity reject nodal malefic occupation while preserving
  the seven-visible-planet domain for Nabhasa.
- [x] Return BPHS and Phaladeepika Kemadruma readings separately.
- [x] Attach BPHS 41.16 delivery and 41.17 qualification instructions to the
  enumerated Dhana combinations.
