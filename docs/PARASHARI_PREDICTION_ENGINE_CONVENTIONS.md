# Parashari Prediction Engine — Declared Conventions

The deterministic engine is correct only within a declared rule profile. It
must not silently mix conventions from different Jyotisha schools.

## `parashari_fomo_v1` / profile 2.0.0

- Zodiac: sidereal.
- Ayanamsha: Lahiri through Swiss Ephemeris `SIDM_LAHIRI`.
- Natal and transit houses: whole-sign houses from the natal ascendant.
- Nodes: mean Rahu; Ketu is exactly opposite.
- Graha drishti: Sun, Moon, Mercury and Venus use the seventh; Mars uses
  fourth, seventh and eighth; Jupiter uses fifth, seventh and ninth; Saturn
  uses third, seventh and tenth.
- Node aspect convention: Rahu and Ketu use fifth, seventh and ninth aspects.
  This is profile-owned because node aspects differ by school.
- Dasha: strict Vimshottari MD–AD–PD with actual calculated boundaries. No
  fabricated dasha fallback is permitted.
- Transit sample: 12:00 UT for each calendar date. Windows split when a
  material sign, retrograde, combustion, or dasha signature changes.
- The Sun is a monthly timing trigger. It can reinforce a house already
  connected to the active dasha, but cannot create natal promise.
- A non-dasha Moon never creates or promotes a 90-day event. It records short
  peak bands only when it contacts both an already activated house and a natal
  delivery carrier. If the Moon is an MD/AD/PD lord, it operates normally as a
  dasha carrier in addition to those peak contacts.
- Transit reference currently validated for natal Lagna/whole-sign houses.
  Moon-reference transit judgment is not promoted into prediction evidence
  until its policy has golden-chart validation.
- Relative anchors: mother fourth, father ninth, spouse seventh. A derived
  frame is emitted only when the activation also connects to the relative's
  anchor or primary natural karaka. It describes a theme involving the
  relative, not an independent prediction from the relative's unseen chart.

## Reasoning hierarchy

1. Build all twelve natal-house connections independently of event names.
2. Find direct MD/AD/PD lordship, occupation, and graha-drishti connections.
3. Build MD–AD–PD sambandha through natal conjunction, aspects, dispositors,
   sign exchange, or repetition of the same planet in the dasha chain.
4. Preserve transit-only activation as background; it cannot create an event.
5. Promote a house only when natal/dasha delivery and a relevant transit
   trigger coexist. Natal contact by the trigger produces the strongest band.
6. Derive bounded house manifestations only after activation is established.

## D1 natal promise and strength policy

Without Shadbala, vargas, or Ashtakavarga, the engine judges directional D1
promise from the house lord's dignity/combustion/cancellation, classical
occupants and aspects, final dispositors, relevant natural karakas, and a
small validated yoga registry. Waxing/waning condition is applied to the
Moon; Mercury's natural tendency is conditioned by whole-sign association.

The validated yoga subset is Kendra-Trikona sambandha, 2–11 Dhana sambandha,
9–10 Dharma-Karma sambandha, Panch Mahapurusha, and conservative D1 Neecha
Bhanga conditions. A yoga contributes to an event only while one of its
forming planets is in the active delivery chain. Neecha Bhanga removes the
automatic debilitation penalty; it is not automatically promoted to a
beneficial Raja Yoga.

## Fail-closed boundaries

The following calculators may exist elsewhere in the repository but are not
allowed to change a prediction until independently validated against classical
worked examples and manually verified golden charts:

- Shadbala and Ishta/Kashta strength.
- Ashtakavarga productivity thresholds.
- Yogas outside the validated D1 subset and more expansive cancellation rules.
- All divisional-chart event specificity; divisional charts are not calculated
  by this profile for now.
- Neecha-bhanga and other cancellation rules.
- Moon-reference transit weighting and exact angular trigger orbs.

Their absence must appear as an unimplemented validation boundary, never as a
fabricated neutral value or fallback calculation.
