# Deva Keralam reviewed batch B v1 — source audit

## Scope

- Private source: *Deva Keralam, Book I (Chandra Kala Nadi)* scan.
- Reviewed range: PDF pages 111–185, corresponding to printed pages 87–161 and verses 938–1879.
- Manifest: `reviewed_batch_b_v1.json`.
- Result: 40 reviewed candidates, of which 31 compile as isolated pilot rules and 9 remain explicitly rejected.
- Registration: none. Loading or compiling this manifest does not add rules to the global registry or change an existing chart/chat contract.

## Review method

OCR was used only to locate candidate passages. The premise, outcome, verse number, page number, section heading, inherited Ascendant/Nadiamsa context, and editorial note were checked against rendered source-page images. Long narrative sequences, timing passages, corrupt readings, and rules whose essential premise cannot be represented by the canonical fact ontology were excluded.

Each approved expression was checked for:

- a complete source-bounded Ascendant and Nadiamsa premise when the passage depends on it;
- canonical fact keys only;
- possible Rashi, house, Navamsa, Nadiamsa, conjunction, and classical Parashari aspect geometry;
- removal of age, dasha, transit, longevity, and event-date material;
- a short outcome paraphrase rather than a long source quotation;
- the birth-time precision requirement for exact Nadiamsa rules.

The admitted rules cover appearance/constitution, health tendencies, wealth/status, learning, parents and siblings, progeny, marriage, and limited sensory or urinary vulnerability. They remain source-specific natal judgments and are not standalone conclusions.

## Context decisions

- **Guha / Dhruva:** verses 1313 onward are admitted under canonical Dhruvaa ordinal 22 only where the editor explicitly resolves that local section to Dhruva. The earlier unresolved Guha block at verses 1219–1225 remains rejected.
- **Trailokya-mohankari:** the Capricorn/Trailokya context is retained for later verses in its uninterrupted section even when a verse does not restate it. These cases are marked as qualified rather than silently treated as self-contained.
- **Half-verses:** the schema stores integer verse bounds; the exact half-verse range remains in `reference_label` and the source numbering note.
- **Aspect direction:** when the translation names a relation but does not establish direction, the rule admits either classical directional aspect instead of inventing one.

## Rejected candidates

| Candidate | Source | Machine blocker | Reason |
| --- | --- | --- | --- |
| `DK.B.1096_PISCES_SEETHALA_SATURN_VENUS` | PDF 123, vv.1096–1097 | `blocked_missing_shashtiamsa_facts` | Sudha Shashtiamsa is an essential premise and cannot be dropped. |
| `DK.B.R0969_AROODHA_VENUS` | PDF 113, vv.969–970.5 | `blocked_missing_aroodha_fact_ontology` | The premise depends on Aroodha Lagna/house contact facts. |
| `DK.B.R0972_LAGNA_LORD_NAVAMSA` | PDF 113, v.972 | `blocked_dynamic_lord_binding` | The expression must bind the current Ascendant lord to that planet's Navamsa. |
| `DK.B.R1020_SWATI_MOON` | PDF 117, vv.1020–1025 | `blocked_missing_nakshatra_facts` | The editor resolves the premise to Moon in Swati pada 2; those planetary facts are unavailable. |
| `DK.B.R1057_MARS_SATURN_MORTALITY` | PDF 120, v.1057 | `rejected_direct_mortality_claim` | A deterministic death claim is not executable or user-facing. |
| `DK.B.R1219_GUHA_UNRESOLVED` | PDF 134, vv.1219–1225 | `blocked_unresolved_nadi_name` | The source itself reports the local Guha name as unresolved. |
| `DK.B.R1338_KANTHAA_VENUS_TRIMSAMSA` | PDF 145, vv.1338–1342 | `rejected_impossible_subdivision_context` | Capricorn Kanthaa at 6°00′–6°12′ cannot also fall in the stated Venus Trimsamsa at 0°–5°. |
| `DK.B.R1782_PANKAJA_PROGENY` | PDF 179, vv.1782–1783.5 | `rejected_impossible_aspect_geometry` | From Capricorn, Mars in H7 and Jupiter in H5 cannot classically aspect each other in either direction. |
| `DK.B.R1818_JUPITER_DEBILITATED_CANCER_NAVAMSA` | PDF 180, v.1818 | `rejected_impossible_rashi_navamsa_geometry` | Jupiter debilitated in Capricorn cannot occupy Cancer Navamsa. |

## Limitations and next gates

This batch does not operationalize source timing, dasha order, transit timing, age-specific results, Arudha, planetary Nakshatra/pada, Shashtiamsa, or dynamic lord binding. Those passages should be reconsidered only after the relevant canonical facts exist. No rejected passage should be approximated with a broader surrogate condition.

Before any rule is registered for chart use, it still needs product-level review for interpretation wording, contradiction handling, confidence display, and comparison against known charts. The manifest deliberately supports private compilation and testing without exposing source text or changing existing clients.
