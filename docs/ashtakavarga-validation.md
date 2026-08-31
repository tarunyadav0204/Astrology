# Ashtakavarga primitive validation

## Scope

This validation treats Bhinnashtakavarga, Prastara/Kakshya, Trikona Shodhana, Ekadhipatya Shodhana, Rashi Pinda, Graha Pinda, and Shodhya Pinda as separate primitives. Longevity outcomes are not used as expected values.

## Independent fixtures

### Parashara's Light Sample Report 5

- Birth: 11 November 2000, 09:01:20, Delhi.
- Source positions: report page 2; Lahiri ayanamsha.
- Published Ashtakavarga material: pages 14–18.
- Compared values: 84 raw BAV sign cells, 12 SAV sign totals, seven natal Kakshya ruler/bindu results, and 21 Pinda totals.
- Result under `parasharas_light_7`: exact match.

Source: <https://www.astrograha.com/Content/AstrologyReports/Circular-Astrology-Report.pdf>

### Parashara's Light AVKP1 sample

- Birth: 20 March 1980, 12:08:13, Delhi.
- Source positions: report page 2; Lahiri ayanamsha.
- Published Ashtakavarga material: pages 14–17.
- Compared values: 84 raw BAV sign cells, 12 SAV sign totals, and 21 Pinda totals.
- Result under `parasharas_light_7`: exact match.

Source: <https://himalayavedicworld.com/images/Reports%20sample/Sample_AVKP1en.pdf>

### P.V.R. Narasimha Rao Example 43

- Published reduced Mercury BAV: `3,1,3,0,0,0,0,0,0,0,2,0`.
- Published Rashi/Graha/Shodhya Pindas: `77 / 75 / 152`.
- Result under `pvr_narasimha_rao`: exact match.

Source: <https://lakshminarayanlenasia.com/articles/vedic-astrology-an-integrated-approach2.pdf>, sections 12.7.2–12.7.3.

## Convention divergence

The sources do not use identical Ekadhipatya rules:

- P.V.R. Narasimha Rao replaces a higher value in the empty sign with the occupied sign's lower value and does not treat Lagna as a graha occupant.
- Inference from the two Parashara's Light worked tables: reproducing every published Pinda requires subtracting the occupied sign's value from the higher empty sign and treating Lagna as occupancy. The reports expose the intermediate numbers but do not state this branch as prose.

For the first sample chart this changes Mercury Shodhya Pinda from `120` under P.V.R. to `108` under Parashara's Light, and Saturn from `125` to `133`. Both profiles are therefore implemented and named. The production default remains `pvr_narasimha_rao`; the response includes the profile, branch rule, occupancy set, citation, and URL. Profiles must never be blended silently.

## Kakshya finding

Kakshya geometry is invariant across the two reduction profiles: eight half-open 3°45′ divisions per sign, ruled in order by Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, and Lagna. The bindu is read from the matching contributor row of the target planet's Prastara. All seven natal Kakshyas in Sample Report 5 match the report's published Prastara rows.
