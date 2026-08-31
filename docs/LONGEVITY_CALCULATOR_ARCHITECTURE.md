# Longevity calculator architecture

## Boundary

`POST /api/longevity/calculate` is a free deterministic calculation endpoint. It owns chart mathematics and returns the versioned `longevity.v1` contract. Web and mobile render that contract; neither client recalculates astrology. The request's `subject` is `self`, `mother`, or `father`; every subject continues to use the selected native chart.

The calculator does not predict a death date. It emits traditional Ayurdaya compartments and relative vulnerability windows. A pre-Khanda three-system confirmation is labelled as a transformative/health-stress period, never as mortality.

## Source-locked safeguard convention

The engine deliberately does not translate classical statements into invented percentages.

- Jaimini Kakshya changes use only *Upadesha Sutras* 2.1.10–14. Saturn can cause one whole-compartment Hrasa only when the Moon–Saturn pair agrees with the selected three-pair result. Saturn in own/exaltation and the Sutra 13 exclusively-malefic-influence exception block the reduction. Jupiter in the derived H1/H7 must have benefic and no malefic Jaimini-rashi influence to cause one whole-compartment Vriddhi. The native result is bounded to the three represented compartments; no fractional hybrid band is manufactured.
- Hora Lagna follows BPHS Ch. 5.4–5: determine the preceding local astronomical sunrise, take the sidereal Sun longitude at that sunrise, and add one sign for every 2½ elapsed ghatis. `Sun + Moon − Ascendant` is not Hora Lagna and is not used.
- The parent screen is a derived-house proxy, so the native-only Jaimini Hrasa/Vriddhi rule is not transferred to it.
- Arishta-Bhanga evidence implements BPHS Ch. 10.2–5: Mercury/Jupiter/Venus in a Kendra; strong Jupiter in Lagna; a strong Lagna lord in a Kendra; and the exact Paksha/day-night/Lagna-aspect condition. Day/night uses astronomical local sunrise and sunset. "Strong" is satisfied by own/exaltation dignity or the planet meeting its classical required Shadbala rupas. These natal antidotes are not converted to 40–100% multipliers and are not treated as blanket cancellation of adult periods.
- Jaimini rashi drishti and Parashari graha drishti are separate functions. They are not substituted for each other.

## Window convergence policy

High vigilance is a product safety classification, not a fourth classical formula. It requires all three independent hits:

1. Vimshottari MD or AD is an explicitly derived maraka/badhaka/D3/D9 lord.
2. Shoola Dasha activates a Trishoola, A8, or Maheshwara sign.
3. Saturn supplies a sensitive/BAV/Shodhya-Pinda transit and Rahu–Ketu or the Sun supplies a separate confirmation.

The displayed 0/33/67/100 value is only the percentage of these three Boolean systems confirmed. It is not a probability, a medical score, or a weighted astrological sum. Parent high-vigilance output additionally requires D12 stress confirmation; otherwise it is capped at moderate and continues to require the parent's own horoscope for primary analysis.

## Result contract

- `verdict`: compartment, primary MPS threat, current vulnerability
- `subject`: selected view, derived native house/sign and natural karaka
- `pillars`: Jaimini three-pair vote, Parashari relative strength, Ashtakavarga baseline
- `maraka_dossier`: ranked planets and sensitive D3/D9/Jaimini points
- `safeguards`: traceable BPHS antidote rules and their scope
- `crisis_windows`: dated Vimshottari × Shoola × transit convergence, Khanda status, and parent corroboration
- `chat_context`: compact deterministic evidence for future chat injection
- `disclaimer`: product safety copy used by both clients

Mother rotates the native chart to H4; its derived 8th/3rd are native H11/H6 and its marakas are native H5/H10. Father rotates to H9; its derived 8th/3rd are native H4/H11 and its marakas are native H10/H3. Parent views add D12 confirmation, parent Shoola, Sun/Moon transit triggers and explicit native-house traceability. They are indicators from the native's chart, not substitutes for either parent's own chart or literal parent-age calculations.

`schema_version` must be checked before a chat adapter consumes the packet. Future calculator changes should add fields compatibly or increment the version.

## Future chat integration

All three chat modes enter through the chat-v2 request flow, but they branch after routing:

1. Standard: add a compact longevity evidence slice to the existing context builder when the intent is longevity, vitality, Maraka/Badhaka, or a crisis window.
2. Premium: use the same packet and allow the premium synthesis path to cite more of the `pillars`, `maraka_dossier`, and cross-window evidence. Do not run a different calculator.
3. Instant: add a longevity methodology/graph policy that consumes `chat_context`, following the existing Instant V2 packet pattern. Keep the deterministic packet authoritative and use the model only to explain it.

The chat adapter should calculate once per birth-chart hash, `subject`, and `as_of` date, cache `longevity.v1`, and pass the same evidence to every tier. Tier differences belong in explanation depth, not mathematical output.

## Guardrails for chat

- Never predict or imply a date of death.
- Say “relative astrological vulnerability” rather than medical risk.
- Three-system confirmations before the baseline compartment must use a transition/health-stress label.
- Recommend qualified medical help for actual symptoms; do not convert astrological factors into diagnoses.
- Preserve the source fields and scoring components so an answer can explain why a window was flagged.
