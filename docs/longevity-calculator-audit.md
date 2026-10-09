# Longevity calculator audit — 9 October 2026

This change repairs calculator arithmetic and evidence contracts. It does not introduce a new Verified vulnerability mode, certify an astrology-based prediction of medical danger, or change the death-query unlock policy.

## Corrections

| Area | Change | Compatibility |
| --- | --- | --- |
| Shoola | Distinguishes standard Shoola from Niryana Shoola; corrects standard forward order; adds twelve ADs, exact instants, explicit focus date and year convention. Excludes outer/derived bodies from the declared strength comparison. | Retains existing period/date/current fields; additional metadata and AD rows. |
| Yogini | Invalid birth dates fail instead of becoming today. Exact MD transitions select the next period. Timezones remain tied to birth, not the query timezone. Reconstructs the full MD origin before clipping birth-balance ADs. | Keeps existing current/timeline fields; adds ISO instants. Yogini API uses those instants for subperiods and progress. |
| Verified Yogini | Returns bounded MD/AD facts rather than an undifferentiated 120-year MD list. | Tool returns a structured method/periods object; existing public timeline API remains unchanged. |
| Divisional charts | Replaces generic D5/D6/D8/D11 mappings with named formulas. Rejects unsupported divisions. Removes premature boundary epsilon; prevents floating-point longitude rollover. D30 degrees use the actual unequal-part width. | Existing chart/planet/house shape retained. Corrected values propagate to existing clients. |
| Chara | Retains birth time, scopes requested MD/AD range, exposes ISO instants, excludes nonclassical bodies from association counts, and rejects missing planetary signs. | Identified as the existing K.N. Rao variant; existing date fields retained. |
| Sensitive points | Uses **22nd Drekkana**. Separates mapped D3/D9 signs from physical D1 sectors. Adds Lagna-based 64th Navamsa alongside Moon-based calculation. Missing source placements no longer become Aries. | Existing names/keys retained; added coordinates/reference fields. Compact context retains coordinate frame. |
| Verified natal points | Does not invoke or supply the legacy Bhrigu Bindu future-transit search. A natal-point calculation supplies no date prediction. | `upcoming_transits` reports `not_requested`; clients retain the field. |
| Profile consistency | Verified supplemental charts, historical Vimshottari, double transit, Navatara and longevity transit snapshots respect selected ayanamsha/node convention. Yogini API resolves timezone for the birth date. | Default convention remains unchanged. |
| Legacy longevity timeline | Fixes overlapping Shoola date boundaries; distinguishes unavailable layers from no activation; labels daily sampling and product linkages. Solar linkages use the physical D1 sector instead of a D3 mapped sign. | Existing v2 fields/aliases retained; availability metadata added. |
| Legacy relative Maraka | Replaces “Double Maraka/Critical Danger” and remedy/threat assertions with the actual lordship/occupation relation. | Existing string fields remain; no claim that this is an MD/AD confluence. |
| Legacy prompt score | Removes the invented 0–10 risk rubric whose maxima added to 10.5 and double-counted related factors. Uses descriptive evidence instead. | Writer template updated consistently across instructions, branch prompt and output template. |

## Methods that must remain qualified

- The starting-sign strength selection in the existing Shoola calculator is still a **simplified declared profile**, not a fully certified Ayur rashi-strength engine. The corrected forward period schedule does not certify this selection.
- **Niryana Shoola is not implemented by this calculator** and must not be substituted with standard Shoola. The menu and both Verified/conflict instructions say this explicitly.
- Existing Rudra and Maheshwara outputs are now explicitly labelled **simplified**. They must not be represented as complete classical identities.
- Chara is one named Jaimini dasha variant, not an independent second system beside “Jaimini”. Different dasha systems and repeated sensitive factors are not statistically independent proof.
- Current transit snapshots cannot establish arbitrary future contacts. The legacy Bhrigu Bindu forecast search is excluded from Verified evidence; a separately audited bounded contact service is still required for such requests.
- The bounded Yogini menu supplies MD/AD, not PD/SK/PR. Do not claim deeper periods were calculated.
- The dedicated longevity module remains a legacy interpretive product. Its daily activation timeline is not an exact contact-time engine. A future Luna workflow should request raw calculators, not inherit its verdict or ranking.

## Sources and validation

Named divisional formulas and standard Shoola scheduling were checked against [P.V.R. Narasimha Rao’s author-hosted textbook](https://vedicastrologer.org/articles/vedic_astro_textbook.pdf), sections 6.2.5, 6.2.6, 6.2.8, 6.2.11 and 23.2. These are method references, not clinical validation. The D8 worked example contains an inconsistent final Mercury sentence; the stated formula and intermediate counting agree on Libra, which the regression test checks.

Tests cover synthetic boundary cases, every D3/D9 sector mapping, UTC equivalence, birth-balance clipping, independent published divisional fixtures, public API shape, and existing longitude/health/chat clients. Historical public-chart fixtures are deterministic regressions only. JFK’s Shoola boolean changed from true to false with the corrected forward sequence; no rule was adjusted to fit a known death outcome.

Deployment/restart is required to load these changes and clear process-local static context caches. Existing saved messages are historical outputs and are not rewritten.
