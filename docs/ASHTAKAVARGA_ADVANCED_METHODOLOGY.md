# Advanced Ashtakavarga methodology

## Production convention

The engine follows the Parashara convention presented in P.V.R. Narasimha Rao's *Vedic Astrology: An Integrated Approach*. It uses the existing seven-graha Bhinna Ashtakavarga contribution tables, treats a benefic contribution as `1`, and excludes Rahu/Ketu from Ekadhipatya occupancy and Graha Pinda.

Primary calculation references:

- BPHS chapters 67–70: Trikona Shodhana, Ekadhipatya Shodhana, Pinda Sadhana and transit applications.
- P.V.R. Narasimha Rao, sections 12.6–12.7 and 25.5–25.6: Prastara/Kakshya, reductions, multipliers and worked examples.

## Prastara and Kakshya

For each target graha, Prastara Ashtakavarga is an 8 × 12 binary matrix. Its rows are Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon and Ascendant. Summing a sign's eight cells must reproduce that sign's BAV total.

Every sign is split into half-open Kakshya intervals:

| Number | Range | Ruler |
| --- | --- | --- |
| 1 | 0°00′ ≤ degree < 3°45′ | Saturn |
| 2 | 3°45′ ≤ degree < 7°30′ | Jupiter |
| 3 | 7°30′ ≤ degree < 11°15′ | Mars |
| 4 | 11°15′ ≤ degree < 15°00′ | Sun |
| 5 | 15°00′ ≤ degree < 18°45′ | Venus |
| 6 | 18°45′ ≤ degree < 22°30′ | Mercury |
| 7 | 22°30′ ≤ degree < 26°15′ | Moon |
| 8 | 26°15′ ≤ degree < 30°00′ | Ascendant |

A transit Kakshya is active only when the relevant ruler's Prastara cell is `1` for the target graha in the transit sign. A sign-level BAV count is not a Kakshya result.

## Shodhana and Pinda

For each planetary BAV:

1. Trikona Shodhana is applied independently to Aries/Leo/Sagittarius, Taurus/Virgo/Capricorn, Gemini/Libra/Aquarius and Cancer/Scorpio/Pisces. If any member is zero, the group is unchanged. Otherwise the smallest value is subtracted from all three.
2. Ekadhipatya Shodhana is applied to Aries/Scorpio, Taurus/Libra, Gemini/Virgo, Sagittarius/Pisces and Capricorn/Aquarius. The result depends on zero values and occupancy by the seven classical grahas; every rule decision is returned in the trace.
3. Rashi Pinda is the sum of each reduced sign value multiplied by `[7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]` from Aries through Pisces.
4. Graha Pinda sums the reduced value in each occupied sign multiplied by Sun `5`, Moon `5`, Mars `8`, Mercury `5`, Jupiter `10`, Venus `7` and Saturn `5`.
5. `Shodhya Pinda = Rashi Pinda + Graha Pinda`.

## Timing coordinates

The relevant raw BAV rekha count is multiplied by that graha's Shodhya Pinda. The remainder modulo 27 identifies the nakshatra; modulo 12 identifies the rashi. A zero remainder maps to 27 (Revati) or 12 (Pisces), not to an invalid zero index.

The API exposes the traditional reference set: Sun H9 for father, Moon H4 for mother, Mars H3 for siblings, Mercury H10 for profession, Jupiter H5 for children, Venus H7 for marriage and Saturn H8 for longevity.

## API and UI contract

`POST /api/calculate-ashtakavarga` returns `advanced_ashtakavarga` only for natal Lagna/D1 calculations. The object includes:

- `prastara`: all seven 8 × 12 contributor matrices;
- `natal_kakshya`: exact natal zone, ruler and active bindu status for every graha;
- `shodhya_pinda`: raw, both reductions, traces, products and final pindas;
- `classical_timing`: auditable multiplication and remainder coordinates.

Web and mobile render this same packet. They do not duplicate or reinterpret the mathematics.
