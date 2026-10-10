# Mundane calculator audit — 10 October 2026

Scope: existing Global/Mundane calculators and their legacy answer-generation consumers. This does not add the Verified mundane mode. Computational correctness, traditional rule fidelity and predictive calibration are separate concerns.

## Findings and fixes

| Component | Finding | Result |
|---|---|---|
| Solar ingress | Iterative search discarded seconds; Capricorn could fall in the next calendar year. | Bracketed angular crossing with sub-second convergence; all four ingresses occur within the requested UTC year. |
| Ingress/lunation charts | Tropical Placidus ascendant combined with sidereal planets. | Lahiri sidereal ascendant and whole-sign houses; supports polar latitudes. |
| Lunations | Searching/appending new moon first jumped over full moons; near-phase threshold could skip an imminent phase. | Select the earliest next new/full moon, retain both phases in a half-open range, and use the actual next syzygy for `valid_until`. |
| Eclipse visibility | Global-maximum magnitude/flags were treated as local visibility, without horizon coverage. | Separate global eclipse identity from local eclipse search covering all visible phases; penumbral magnitude handled. |
| Outer planets | Speed flag omitted; retrograde could always appear false. Naive local/event dates used at midnight. | Explicit speed flags, UTC conversion and full timestamp precision. Builder uses the same event instant; yoga outer positions match the base chart instant. |
| Event context | Offset calculated for today; negative/overflow UTC hour formatted without date rollover. | Resolve IANA timezone for actual wall time, reject ambiguous/nonexistent DST times, and carry normalized UTC date and time to every relocated chart. |
| Capital charts | Foundation coordinates mislabeled as capital coordinates (Philadelphia vs Washington, Tel Aviv vs Jerusalem). | Use capital coordinates from the existing country catalog. |
| Shared chart/dasha engines | Seconds ignored in civil birth time. | Include seconds without changing the signatures or output fields. Existing D1 calibration convention remains unchanged. |
| National foundations | Missing times silently became midnight; provenance omitted. | Reject incomplete records, preserve source/time/coordinates/offset and mark historical foundations as unverified conventions. Dasha snapshot identifies its focus instant and civil time basis. |
| Annual lords | Fabricated rotating nine-planet sequence; Aries ingress called King. | Partial result only: Aries-ingress local civil weekday gives Minister. King and other independent calendrical offices remain explicitly uncomputed. |
| Kurma mapping | Repeating single-star/direction pattern instead of three-star groups starting with Krittika. | Correct classical triplets. Modern regional lists explicitly labeled editorial analogies, especially outside Bharatavarsha. |
| Mundane yogas | Included Sun/Moon/nodes as generic planetary-war candidates; omitted valid five-planet pairs. Simplified configurations mislabeled Sanghatta, Durbhiksha, Mahargha and Parivartana. | All ten five-tara-graha proximity pairs, no invented victor. Other configurations labeled unvalidated heuristics, not verified named classical yogas. |
| Commodity links | Fixed `nakshatra + 14` claimed as Sarvatobhadra Vedha. | Remove unsupported Vedha; retain declared direct planetary-ruler/sector analogy. |
| Angular checks | Inflation/revolution checks failed at longitude wraparound; missing longitude became zero. | Shortest angular separation and explicit missing-data handling. |
| Sports | Host nation could replace competitors; hora called without required date/time; ties chose first input side; missing weekday became Sunday; friendship treated as symmetric; own-sign check omitted second owned sign. | Preserve the confirmed two sides, pass full hora inputs, report balanced ties, do not invent weekday, use directional friendship and both owned signs. Missing match time prevents scoring assumed noon. |
| Legacy writer | Required certainty, arbitrary percentages, full fabricated annual cabinet and unsupported precise event claims. | Updated mundane system and output contracts to use corrected evidence, acknowledge partial coverage and distinguish heuristic scores from probabilities. |
| Nakshatra shape | Builder supplied strings where two calculators assumed objects. | Accept both legacy string and object forms. |

## Compatibility

- Public `/mundane/session` and `/mundane/analyze` request/response models and polling behavior are unchanged. Web and mobile receive generated answer text, not the internal calculator payload.
- Existing top-level calculator containers and core keys remain: `ingresses`, `aries_ingress_chart`, lunation lists and their legacy fields, outer-planet name dictionaries, `entity_charts`, `national_dasha`, `locational_analysis`, `nav_nayak`, yoga/commodity lists, and sports `sides`/`edge`.
- Naive ingress/lunation datetime strings remain naive UTC for older consumers; additive `timezone` and `datetime_utc` identify their actual time basis. Aware datetime inputs normalize to UTC.
- `calculate_nav_nayak(ingress_datetime)` still works. Optional location kwargs are additive; uncomputed legacy office keys retain their shapes with null lords and availability reasons.
- Sports `confidence_percent` remains numeric for compatibility but is explicitly an unvalidated heuristic index. `balanced` is an internal result type; its only answer-template consumers were updated alongside the calculator.
- Corrected values necessarily differ from incorrect prior outputs. No mobile/web schema migration is required.

## Validation

`backend/.venv/bin/python -m pytest` with:

- `tests/test_mundane_calculator_audit.py`
- `tests/test_panchang_canonical.py`
- `tests/test_shadbala_parashara_light.py`
- `tests/test_vedic_graha_drishti.py`
- `tests/test_divisional_chart_parashara_light.py`
- `tests/test_parallel_chat_presentation_style.py`
- `tests/test_verified_chart_analysis.py`
- `tests/test_verified_chat_formatting.py`

Result: **86 passed**, two existing dependency/deprecated-facade warnings. No live LLM calls or deployed-device validation were involved.

All 25 new/full moons of 2026 match USNO published Universal Time to within 60 seconds. Additional tests cover ingress crossing brackets, sidereal ascendants, polar whole-sign charts, finite-difference retrograde checks, eclipse identity/local visibility, UTC rollover, date-specific DST, nonexistent wall times, national data validation, sports side/tie handling, full timestamp precision and actual legacy prompt generation.

## Remaining boundaries

The full annual cabinet requires a declared regional calendrical convention and independent anchors. It is deliberately partial, not silently approximated. Sanghatta and genuine Sarvatobhadra Chakra geometry are not implemented. Foundation records and modern geographic lists have not been historically/geographically authenticated; their limitations accompany the evidence. National dashas remain snapshots rather than full-horizon schedules. Sports scores are not empirically calibrated probabilities. These are explicit limitations for the subsequent Verified integration, not verified forecasting capabilities.

## Reference material

- [Swiss Ephemeris programmer documentation](https://www.astro.com/swisseph/swephprg.htm): sidereal house flags, speed flags, UTC dates and local/global eclipse APIs.
- [USNO 2026 primary Moon phases](https://aa.usno.navy.mil/calculated/moon/phases?year=2026): independent phase-time regression fixtures.
- [Brihat Samhita, Kurma Vibhaga 14.1](https://www.siva.sh/brihat-samhita/14/1): three-star groups beginning with Krittika.
- [Brihat Samhita, chapter 17](https://sanskritdocuments.org/doc_z_misc_sociology_astrology/bRRihatsaMhitA.html): planetary conflict is not equivalent to an automatic catastrophe or fabricated victor.
- [Mantri Mandala calculation anchors](https://www.drikpanchang.com/festivals/samvat-newyear/info/about-new-samvata-mantri-mandala.html): published Narada Samhita verses and separate King/Minister anchors; used to remove the unsupported rotation, not to claim a complete calendrical implementation.
