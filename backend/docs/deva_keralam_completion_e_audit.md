# Deva Keralam Book 1 completion audit — stream E

## Scope

Stream E is the exact middle third of the canonical 878-passage catalogue:

- catalogue ordinals **294–586**, inclusive
- **293 passages**
- PDF pages **117–197**
- first passage: `DK1.OCR.P0117.V1026-1028`
- last passage: `DK1.OCR.P0197.V1999-2001`

The ledger is [completion_ledger_e_v1.json](../classical_rules/deva_keralam/data/completion_ledger_e_v1.json). It is an audit artefact only. It neither publishes rules nor registers them with chart, chat or API clients.

## Method

The catalogue was frozen in canonical PDF-page, verse and passage-key order before review. Existing reviewed manifests were compared by source page and overlapping verse range, because earlier review streams use reviewer-assigned passage keys rather than the OCR catalogue key. Those passages are recorded as `already_reviewed`, with the prior candidate keys retained.

For the remaining passages, the OCR translation and extraction draft were used as navigation aids. They were not treated as source authority. A passage was admitted as executable only when:

1. the rendered page and local section context were checked;
2. every inherited premise was retained;
3. the astronomical combination was feasible;
4. every premise could be supplied by the canonical fact adapter; and
5. the guarded manifest compiler accepted the candidate.

## Disposition totals

| Disposition | Count |
|---|---:|
| Timing pending | 77 |
| Ambiguous context | 59 |
| Mortality excluded | 51 |
| Unsupported fact | 45 |
| Already reviewed | 25 |
| Corrupt or disputed | 24 |
| Commentary only | 10 |
| Impossible geometry | 1 |
| Newly executable | 1 |
| **Total** | **293** |

`timing_pending` includes Dasha, transit, age, year and source-specific sequence rules that should be implemented through a dedicated timing layer, not flattened into natal promises. `unsupported_fact` records readable clauses whose complete premises need a calculator that the current fact ontology does not yet provide. `mortality_excluded` keeps death, lifespan and infant-mortality statements out of deterministic consumer prediction. These are complete dispositions, not silent omissions.

## Newly executable source unit

Verse 1889 on PDF page 186 was checked against the rendered scan. It occurs in the continuing Aquarius/Nirmalaa section and says that Mercury joined Ketu in Aries, with Mercury in Leo Navamsa, produces the stated faith and sibling indications. The rule therefore retains:

- Aquarius Ascendant;
- Nirmalaa Nadiamsa, ordinal 68;
- Mercury and Ketu together in Aries; and
- Mercury in Leo Navamsa.

The Nadiamsa half is not restricted by verse 1889. Ascendant precision is required. The executable record is `DK.E.1889.AQUARIUS_NIRMALAA_MERCURY_KETU` in [reviewed_batch_e_v1.json](../classical_rules/deva_keralam/data/reviewed_batch_e_v1.json).

The source geometry is feasible: Aquarius contains Nirmalaa ordinal 68 under the pinned 150-Nadi table, while Mercury can occupy the Leo Navamsa portion of Aries and remain conjunct Ketu in Aries.

## Validation

- The ledger validates through `load_completion_ledger()` and covers ordinals 294–586 exactly once and in order.
- The reviewed manifest validates through `load_reviewed_manifest()`.
- The guarded compiler compiles the one approved candidate and rejects none.
- No global registration, publication, API route, UI path or chat contract was changed by this stream.

## Remaining work exposed by this stream

The largest concrete backlog is the 77 timing units. They require explicit modelling of the book's numbered Dasha sequences, Janma/Kshema/Sampat terminology, period junctions and transit qualifiers. The 45 unsupported-fact units identify the next fact-ontology work, including Aroodha-derived placements, named yogas used as premises, finer Vargas and relational quantifiers such as “a benefic occupying a house and associated with Saturn.” The 59 ambiguous-context units need adjoining-page reconstruction or a second textual witness before any rule is admitted.
