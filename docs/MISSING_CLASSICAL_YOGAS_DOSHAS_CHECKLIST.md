# Missing classical Yogas and Doshas checklist

This is the implementation backlog after the September 2026 classical audit.
It is intentionally scoped to the two works already selected for the product's
core Parashari catalogue:

- *Brihat Parashara Hora Shastra* (BPHS), with chapter and verse identity kept
  in every result.
- *Phaladeepika*, using the selected Sanskrit reading and recording textual
  variants rather than silently combining them.

It is **not** a claim to catalogue every yoga ever named in every Jyotisha
work. Additions from *Brihat Jataka*, *Saravali*, *Jataka Parijata*,
*Uttara Kalamrita*, or another work require a separately versioned source
audit. A checked family means all conditions in the cited passage are covered,
including alternatives, exclusions, cancellations, evidence, and false-positive
tests. One representative rule does not complete a family.

## Status legend

- `[ ]` missing
- `[~]` code or a product label exists, but it is not yet acceptable as a
  classical implementation
- `[x]` implemented and source-audited
- `Excluded` means it must not appear as a classical yoga/dosha unless a named
  primary passage is later established

## P0 — complete BPHS Chapter 83 before adding generic “doshas”

BPHS Chapter 83 is specifically about loss/obstruction of progeny. These rules
must retain that scope. They must not be generalized into predictions of a
family curse, bad luck, health trouble, or every life problem.

- [x] Pitri-shapa progeny combinations — BPHS 83.20–30.
- [x] Matri-shapa progeny combinations — BPHS 83.34–46.
- [ ] Sarpa-shapa progeny combinations — BPHS 83.9–16.
- [ ] Bhratri-shapa progeny combinations — BPHS 83.52–61.
- [ ] Matula-shapa progeny combinations — BPHS 83.65–68.
- [ ] Brahma/Brahmana-shapa progeny combinations — BPHS 83.72–78.
- [ ] Patni-shapa progeny combinations — BPHS 83.82–92.
- [ ] Preta-shapa progeny combinations — BPHS 83.97–105.
- [ ] Audit BPHS 83.7–8 general childlessness rules as a separate
  `progeny_obstruction` family; do not label them as a curse.
- [ ] Return the stated remedial verses only as a textual classical reference,
  with no commerce, guarantee, or claim of medical efficacy.
- [ ] Rename the UI family to “Classical progeny combinations” and show the
  original scope before any individual shapa result.

## P1 — finish BPHS Chapter 36 miscellaneous Yogas

Already complete in this chapter: Gaja Kesari (36.3–4) and Amala/Amalakirti
(36.5–6). The following named rules remain:

- [ ] Shubha and Ashubha Yogas — BPHS 36.1–2.
- [ ] Parvata Yoga — BPHS 36.7–8.
- [ ] Kahala Yoga — BPHS 36.9–10.
- [~] Chamara Yoga — BPHS 36.11–12. A legacy detector exists; rebuild it from
  the verse and remove the permissive shortcut.
- [ ] Shankha Yoga — BPHS 36.13–14.
- [ ] Bheri Yoga — BPHS 36.15–16.
- [ ] Mridanga/Mriganga Yoga — BPHS 36.17. Resolve the transmitted name before
  assigning the canonical ID or English display name.
- [ ] Srinatha Yoga — BPHS 36.18.
- [ ] Sharada Yoga — BPHS 36.19–20.
- [ ] Matsya Yoga — BPHS 36.21–22.
- [ ] Kurma Yoga — BPHS 36.23–24.
- [ ] Khadga Yoga — BPHS 36.25–26.
- [~] Lakshmi Yoga — BPHS 36.27–28. A legacy rule exists; replace it with the
  complete verse conditions.
- [ ] Kusuma Yoga — BPHS 36.29–30.
- [ ] Kalanidhi Yoga — BPHS 36.31–32.
- [ ] Kalpadruma/Parijata Yoga — BPHS 36.33–34, including the full dispositor
  chain and required strength states.
- [ ] Hari Yoga — BPHS 36.35–36.
- [ ] Hara Yoga — BPHS 36.35–36.
- [ ] Brahma Yoga — BPHS 36.35–36.
- [ ] Lagna Adhi Yoga — BPHS 36.37.
- [ ] Parijata-varga result ladder for the Lagna lord — BPHS 36.38–39. Keep it
  distinct from Kalpadruma/Parijata Yoga in 36.33–34.

## P1 — finish Phaladeepika Chapter 6 named Yogas

Already complete from this chapter: Pancha Mahapurusha, Saraswati,
Dharma–Karma, Harsha, Sarala, Vimala, and the Maha/Khala/Dainya exchange
classification.

- [~] Shubha Kartari and Papa Kartari — Phaladeepika 6.8. Existing house-card
  pressure/support logic is not a certified Yoga implementation.
- [ ] Sushubha Yoga — Phaladeepika 6.8.
- [ ] Mahabhagya Yoga — Phaladeepika 6.14.
- [~] Lunar Sakata Yoga — Phaladeepika 6.14. Do not confuse it with the already
  implemented Nabhasa Sakata Yoga.
- [ ] Adhama, Sama and Varishtha lunar-state Yogas — Phaladeepika 6.14.
- [ ] Vasumati Yoga — Phaladeepika 6.19.
- [ ] Phaladeepika Amala reading — Phaladeepika 6.19. Keep it separate from
  BPHS 36.5–6 if its executable conditions differ.
- [ ] Pushkala Yoga — Phaladeepika 6.19.
- [ ] Mala/Malika and Ashubha-Malika Yogas — Phaladeepika 6.21. Do not merge
  them with BPHS Nabhasa Dala Mala.
- [ ] Lakshmi Yoga — Phaladeepika 6.21. Preserve its source identity separately
  from BPHS 36.27–28.
- [ ] Gauri Yoga — Phaladeepika 6.21.
- [ ] Srikantha Yoga — Phaladeepika 6.28.
- [ ] Srinatha Yoga — Phaladeepika 6.28. Compare it explicitly with BPHS 36.18;
  share a display name only if the conditions truly agree.
- [ ] Vairinchi Yoga — Phaladeepika 6.28.
- [ ] Kahala and Parvata Yogas — Phaladeepika 6.35. Compare with BPHS 36.7–10
  before deciding whether these are equivalent readings or distinct variants.
- [ ] Shankha Yoga — Phaladeepika 6.37. Compare with BPHS 36.13–14.
- [ ] Twelve bhava Yogas — Phaladeepika 6.44: Chamara, Dhenu, Shaurya,
  Jaladhi, Chatra, Astra, Kama, Asura, Bhagya, Khyati, Suparijata and Musala.
  Namespace names that collide with Nabhasa or BPHS miscellaneous Yogas.
- [ ] The remaining nine bhava-lord condition Yogas in the 6.57 sequence:
  Avayoga (1), Nihsva (2), Mriti (3), Kuhu (4), Pamara (5), Dushkriti (7),
  Nirbhagya (9), Duryoga (10), and Daridra (11).
- [ ] Audit the inverse/cancellation instruction at Phaladeepika 6.70 across all
  twelve bhava-lord condition Yogas.

## P2 — complete the large rule families

These are not single named cards. They need a versioned rule catalogue and
deduplication policy.

- [ ] BPHS Chapter 39 Raja Yoga catalogue. Implement every stated Lagna,
  Karakamsha, Chara-karaka, aspect-strength, and varga condition; do not call
  the current Kendra–Trikona rule “all Raja Yogas.”
- [ ] BPHS Chapter 40 Raja-sambandha catalogue. Keep royal-service/authority
  combinations distinct from general Raja Yoga.
- [ ] Phaladeepika Chapter 7 Raja Yoga catalogue, excluding verses 26–30 that
  are already implemented as Neecha Bhanga Raja Yoga.
- [ ] BPHS Chapter 42 Daridra Yoga catalogue — 42.2–18, including the explicit
  bhanga/qualification clauses in 42.16–18.
- [ ] Compare overlapping Raja, Dhana, Daridra, Lakshmi, Srinatha, Shankha,
  Kahala and Parvata rules across selected texts. Return each matched textual
  reading; never inflate confidence because two labels share a name.

## P2 — classical but requires a separate, careful product surface

- [ ] Balarishta and Arishta-bhanga. Build only after fixing a source edition
  and UX policy. Do not show deterministic infant-death claims to consumers.
- [ ] Ayurdaya and Maraka rules. These belong in a restricted technical tool,
  not the ordinary Yogas & Doshas screen, and must not output a death date.
- [ ] Classical birth-shanti conditions such as Gandanta, Abhukta Mula,
  eclipse birth, Sankranti birth, and same-nakshatra birth. Place these under
  Panchanga/Birth Conditions after verifying the exact BPHS chapter/verses;
  do not call them natal doshas by default.

## P3 — audit legacy labels before they can re-enter the classical response

- [~] Legacy “career yogas” (Dashama-pati Lagna, Bhagya–Karma, Shani–Karma):
  product-created labels are currently excluded. Map each to a named primary
  passage or retire it permanently.
- [~] Legacy generic health and marriage “yogas”: keep excluded until each is
  tied to a named classical rule with its original scope.
- [~] Legacy Lakshmi, Chamara, lunar Sakata, and Kartari helpers: replace them
  with the P1 rules above; do not expose the old calculators in parallel.
- [ ] Audit every old private calculator still reachable from chat, reports,
  saved results, or admin tools. “Not shown in the Yoga screen” is not enough
  if another client still presents it as classical.

## Excluded or quarantined later conventions

The following names must not be branded as ancient/classical merely because
they are popular in contemporary software. For each one, either locate and
publish a primary textual rule with its true scope, or keep it visibly labelled
as a later convention.

- [x] Kaal Sarp: retained only as a later convention, never a classical rule.
- [ ] Guru Chandal Yoga/Dosha — quarantine pending a named primary passage.
- [ ] Grahan Yoga/Dosha — quarantine the modern generic label; classical
  eclipse/birth conditions must be sourced and named separately.
- [ ] Shrapit Dosha — quarantine pending a named primary passage.
- [ ] Angarak Yoga/Dosha — quarantine pending a named primary passage.
- [ ] Nadi Dosha — keep in compatibility matching only; it is not a standalone
  natal dosha card.
- [ ] Generic “Pitra Dosha” from Sun–Rahu or ninth-house affliction — excluded;
  do not mix it with BPHS Pitri-shapa progeny combinations.
- [ ] Generic “Matru Dosha” from Moon/fourth-house affliction — excluded; do
  not mix it with BPHS Matri-shapa progeny combinations.
- [ ] Partial Kaal Sarp names and severity scales — keep as later convention
  and separate from classical results.

## Canonical naming and collision checklist

- [ ] Every rule ID contains the work, chapter/verse, and family, for example
  `bphs.36.misc.shankha`, not only `shankha_yoga`.
- [ ] Distinguish Nabhasa Sakata from lunar Sakata.
- [ ] Distinguish Nabhasa Dala Mala from Phaladeepika Mala/Malika.
- [ ] Distinguish Nabhasa Musala from Phaladeepika's bhava Yoga named Musala.
- [ ] Distinguish every BPHS and Phaladeepika reading of Lakshmi, Srinatha,
  Shankha, Kahala, Parvata, Chamara, and any other shared name.
- [ ] Preserve Sanskrit/transliteration variants such as
  Mridanga/Mriganga in metadata without inventing silent equivalence.

## Definition of done for every new family

- [ ] Fix the exact edition, chapter, verse range, Sanskrit term, and selected
  translation before coding.
- [ ] Record alternate readings and ambiguous compounds explicitly.
- [ ] Encode conjunction, aspect, house, sign, lordship, dignity, combustion,
  strength, benefic/malefic, varga, and day/night requirements exactly as used
  by that passage. Do not borrow conditions from another text silently.
- [ ] Return structured matched and unmatched clauses, planets, houses,
  reference, source reading, and interpretation scope.
- [ ] Test every alternative branch, required conjunction, exclusion,
  cancellation, boundary, and a near-miss false positive.
- [ ] Preserve existing API fields while adding canonical versioned objects.
- [ ] Make Yoga screen, planet/house detail, chat, reports, saved results, and
  future prediction clients consume the same calculator.
- [ ] Write plain-language copy that states what the combination concerns and
  does not turn a classical indication into certainty, diagnosis, or fear.
- [ ] Add the information popup and reference; localize all supported languages.
- [ ] Verify phone, tablet, dark theme, accessibility, export, API-contract, and
  chat regression behavior.

## Source expansion after the selected canon is complete

- [ ] Create separate, edition-specific catalogues for *Brihat Jataka* and
  *Saravali*.
- [ ] Then audit *Jataka Parijata* and *Uttara Kalamrita* for genuinely new
  named formations and source variants.
- [ ] Never merge those catalogues into BPHS/Phaladeepika rules solely because
  later books or software use the same English name.
