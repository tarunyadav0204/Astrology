# Classical combustion calculation

## Selected method

AstroRoshni uses the Parashari loss-of-rays method described in *Brihat
Parashara Hora Shastra*, chapter 7, verses 28–29. Those verses describe full
strength opposite the Sun, loss at identical longitude, and proportional loss
between those positions.

Operational combustion limits come from the explanatory table immediately
following those verses in R. Santhanam, *Brihat Parashara Hora Sastra*, Vol. I
(1984), printed pages 99–100. The table is an edition note and is not presented
as Sanskrit verse text.

| Planet | Direct | Retrograde |
| --- | ---: | ---: |
| Moon | 12° | not applicable |
| Mars | 17° | 8° |
| Mercury | 14° | 12° |
| Jupiter | 11° | 11° |
| Venus | 10° | 8° |
| Saturn | 16° | 16° |

Rahu and Ketu are excluded as mathematical points, as the edition note states.
The Sun is the source of the condition. Gulika, Mandi, Indu Lagna and other
calculated points have no limit in this table.

## Calculation contract

- Use the shortest zodiacal longitude separation, including contacts across
  0° Aries.
- The boundary is inclusive: separation equal to the applicable limit is
  combust.
- Select the retrograde column from the planet's actual motion flag.
- Return the angular distance, selected threshold, direct and retrograde
  thresholds, motion state, applicability, exclusion reason and source.
- Do not create a cazimi exception. Exact conjunction remains combust.
- Do not convert combustion into an invented probability or numeric strength
  multiplier.

The canonical implementation is
`backend/calculators/classical_combustion.py`. Chart calculation attaches the
structured block at `chart.combustion.planets[planet]` and mirrors the legacy
`combustion_status` and `combust` keys for existing clients.

## Method boundary

This contract is used by Parashari natal, transit, dignity, health, prediction,
chat and chart-display consumers. Tajika/Prashna solar conditions remain inside
the Tajika engine because that tradition grades proximity to the Sun under its
own rules. A Tajika condition must not be presented as the Parashari combustion
marker, and the Parashari limits above must not silently replace Tajika rules.
