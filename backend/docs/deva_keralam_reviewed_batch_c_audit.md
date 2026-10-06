# Deva Keralam reviewed batch C audit

## Scope

Batch C reviews the supplied *Deva Keralam, Volume 1 (Chandrakala Nadi)* scan from PDF pages 186–260 (printed pages 168–242). It is a deliberately selective source stream: it captures high-value natal statements whose local sign, Nadiamsa and half context can be resolved, rather than treating every translated line as executable doctrine.

The existing Capricorn Kaalaa pilot for verses 2497–2498 is recorded as excluded prior work and is not included in the batch counts.

## Review result

- Reviewed candidate units: **40**
- Approved executable candidates: **29**
- Rejected candidates: **11**
- Runtime publication: **disabled** (`globally_registered: false`)

The approved rules cover appearance and temperament, learning and writing, parents and siblings, marriage and spouse indications, prosperity and livelihood, status, conveyances and spiritual inclination. The reviewed contexts include Aquarius Nirmalaa, Capricorn Jagathi, fixed-sign and Aquarius Kundaa, Aries Mangala, Gemini Dhruvaa and Capricorn Dhruvaa.

## Review method

Each unit was checked against the local passage, adjoining verses and editorial notes so that inherited context did not silently cross a section boundary. Approved candidates contain:

- exact PDF page, printed page and verse provenance;
- the canonical Nadiamsa name and ordinal where Nadiamsa is a condition;
- explicit sign, house, Navamsa, conjunction or aspect facts required by the passage;
- a declared ascendant precision requirement whenever an exact Nadiamsa or half is used;
- concise outcomes that stay within the translated passage;
- no unresolved blockers.

Rules were compiled only through the reviewed-manifest compiler. They are not added to the global classical-rule registry by this file.

## Astronomical feasibility checks

Canonical names and ordinals were checked against the pinned Nadiamsa table: Nirmalaa 68, Kundaa 133, Jagathi 20, Mangala 92 and Dhruvaa 22. Sign, Navamsa and house combinations in approved rules were also checked for geometric compatibility.

One passage, verse 1905, was rejected specifically because its conditions cannot coexist under the canonical table: Aquarius Nirmalaa falls in the Aquarius Navamsa interval, while the verse requires a Venus-owned Navamsa. Other accepted combinations, including the Aries Mangala rules, were retained only where the sign interval permits the stated Navamsa.

Synthetic positive fact contracts were evaluated for all 29 approved candidates, and each matched its compiled rule. Negative and missing-precision behavior remains governed by the shared fail-closed matcher.

## Rejection audit

The 11 rejected units retain machine-readable blockers in the manifest. The main reasons are:

- unresolved inherited or abruptly changing Nadiamsa context;
- age, dasha, longevity or death timing outside this natal-only batch;
- alternative readings that cannot be expressed as one deterministic condition set;
- corrupt or editorially disputed translation;
- an astronomically impossible condition combination;
- unsupported one-third Nadiamsa subdivisions;
- unsupported facts such as Moon extremis or the required Arudha relationship.

Rejected units are source records only. They do not compile into rules.

## Limits

This is not an exhaustive encoding of PDF pages 186–260. Repetition, unclear translation and passages needing unsupported timing or derived concepts were left out rather than approximated. The source is a scanned English edition whose own notes flag misplaced, interpolated or defective readings in places.

The batch does not infer missing context, normalize fuzzy Nadiamsa aliases, calculate Nadiamsa positions, or introduce dasha, transit, age-event, death, Nadi-quarter or Nadi-third prediction. Exact Nadiamsa rules require reliable ascendant precision and fail closed when that fact is unavailable.

## Validation

The manifest was loaded with `load_reviewed_manifest()` and compiled with `compile_reviewed_manifest()` using the backend environment. The validated summary is:

```text
schema_version: deva-keralam-reviewed-manifest/1.0.0
batch_key: deva_keralam.reviewed_batch_c.v1
reviewed_candidates: 40
compiled_rules: 29
rejected_candidates: 11
globally_registered: false
```
