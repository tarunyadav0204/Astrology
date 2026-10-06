# Deva Keralam Book 1 completion audit — stream D

## Scope

Stream D owns catalogue ordinals **1–293** from the frozen 878-passage Book 1
snapshot. In canonical page/passage order, this is PDF pages 26–117, ending at
verses 1018–1019. The completion ledger contains every ordinal exactly once.

This stream does not publish or globally register rules. It changes no API,
chat, mobile, or web contract.

## Disposition result

| Disposition | Passages |
|---|---:|
| Already reviewed | 46 |
| Newly executable | 1 |
| Timing pending | 72 |
| Mortality excluded | 69 |
| Ambiguous context | 53 |
| Unsupported fact | 38 |
| Corrupt or disputed | 8 |
| Commentary only | 5 |
| Duplicate | 1 |
| Impossible geometry | 0 |
| **Total** | **293** |

“Already reviewed” means that the catalogue passage overlaps a source range in
the Abala/Prabhaa pilot or reviewed batches A–C. This includes both approved
rules and earlier explicit rejections; it does not imply that every such row is
executable.

## New reviewed manifest

Six units received direct page-image review:

- **1 approved:** verses 101–102, Jupiter in Scorpio and Virgo Navamsha. The
  translated passage is self-contained and its two conditions are represented
  by canonical chart facts.
- **5 rejected:** verses 99, 100, 103, 212–213, and 219. These retain explicit
  blockers for Ascendant scope, kinship terminology, blended clauses, a source
  premise the edition says is missing, or the unresolved “Varuna” section
  identity.

The approved rule deliberately does not inherit Aquarius Ascendant or a named
Nadiamsa from its neighbours. The translated heading independently supplies
Jupiter's Scorpio Rashi and Virgo Navamsha positions. A following editorial
Aquarius example is explanatory and is not made a hidden premise.

## Method and limits

The ledger is a **complete disposition**, not a claim that all 293 passages are
fully operationalized. Existing reviewed mappings and the six newly reviewed
units use page-image context. Remaining rows use the retained two-column OCR,
the source extraction assessment, its uncertainties, prediction kind, and
condition families to place work in a conservative queue:

- death and lifespan statements are excluded from consumer execution;
- Dasha, transit, age, and period-junction statements remain timing work;
- passages with unresolved inherited sign/Nadiamsa or relative-chart context
  remain ambiguous;
- clear-looking drafts that require unbound yoga, Avastha, relative, or alias
  facts remain unsupported rather than being approximated;
- missing or contradictory source clauses remain disputed.

No OCR-only row was promoted to executable status.

## Validation

- `completion_ledger_d_v1.json` validates with `load_completion_ledger()` and
  covers ordinals 1–293 in order.
- `reviewed_batch_d_v1.json` validates with `load_reviewed_manifest()`.
- The guarded compiler produces exactly one rule and rejects all five blocked
  units.
- A raw chart with Jupiter at 216.8° (Scorpio Rashi, Virgo Navamsha) matches the
  new rule; moving Jupiter to 220.1° removes the match.
- The manifest/compiler/fact-ontology test group passes: 22 tests.

## Artifacts

- `backend/classical_rules/deva_keralam/data/completion_ledger_d_v1.json`
- `backend/classical_rules/deva_keralam/data/reviewed_batch_d_v1.json`

