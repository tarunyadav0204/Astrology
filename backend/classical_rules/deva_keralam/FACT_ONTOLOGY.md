# Deva Keralam canonical chart facts

`deva-keralam-facts/1.0.0` is the closed vocabulary used by reviewed Deva
Keralam rules. It is an opt-in Python contract. It does not change any chart,
chat, mobile or web response.

## Natal facts

The adapter calculates Ascendant and planet Rashi, whole-sign house, lordship,
Navamsha, named 150th Nadiamsa and its former/latter half. It also records
same-Rashi conjunctions and directional whole-sign Parashari graha drishti.
Both `true` and `false` relationship facts are emitted so absence is not
confused with unavailable data.

For Rahu and Ketu, the adapter follows the product's conservative classical
policy and emits only the seventh aspect. Their disputed fifth and ninth
aspects are not silently introduced into Deva Keralam matches.

House-lord placement is available as
`deva_keralam.house.<1..12>.lord_house`. Dignity is emitted only when the
existing `PlanetaryDignitiesCalculator` provides it; this adapter contains no
second dignity table.

## Timing facts

Dasha, transit and age facts live under `deva_keralam.timing`. They are
included only when a caller supplies an explicit timing context. Dasha levels
are typed (`mahadasha`, `antardasha`, `pratyantardasha`, `sookshma`, `prana`),
and transit house/aspect facts reuse the existing graha-drishti calculator.

Explicit age timing is kept separate from Dasha interpretation. When both
`birth_date` and `as_of` are supplied, the adapter emits completed age, running
year number, civil calendar year, and their ISO half-open interval boundaries.
The reviewed-rule grammar must explicitly choose `completed_age_equals`,
`completed_age_after` (strictly greater), `completed_age_at_or_after`
(inclusive), `completed_age_between`, `running_year_equals`,
`calendar_year_equals`, or `calendar_year_between`; it never decides that a
source phrase means one of these automatically. Missing dates leave such a
rule unavailable. For a 29 February birth, the declared civil anniversary in
a non-leap year is 28 February.

Named source periods use a separate `deva_keralam.timing.period.<1..5>`
contract. Each ordered level requires an explicit system, level, display name,
canonical planetary lord, start, exclusive end, and boolean active status.
The adapter validates active status against `as_of` and requires every child
interval to be contained within its parent. The grammar includes system and
boundary-presence premises, so missing system or dates fail closed. These
facts coexist with the older typed Vimshottari facts; they do not reinterpret
or replace them.

Every explicit source period also exposes deterministic elapsed days,
remaining days, progress, half, and third. Boundary proximity is emitted only
when that period row contains a `phase_window` with explicit non-negative
`start_proximity_days`, `end_proximity_days`, or `junction_tolerance_days`.
Rules must require the same numeric window as well as the resulting boolean;
there is no built-in definition of “near”, no inferred auspiciousness, and no
automatic conversion of source phrases such as “middle portion”. Overlapping
start/end windows are retained as an explicit `proximity_overlap` fact.

## Birth precision

Nadiamsa spans 12 arc minutes and its former/latter halves span 6 arc minutes.
Ascendant facts therefore carry boundary distance and a precision status. If
Ascendant longitude uncertainty is absent or reaches a division/half boundary,
precision-gated rules must return unavailable rather than guess.

## Extracted rule compilation

Extracted keys are accepted only when already canonical or present in the
reviewed alias table. Unknown keys fail closed. Values do not use fuzzy
matching. For the first reviewed slice, the section names `Abala` and `Prabha`
are explicit source aliases for Table 1's canonical `Prabhaa`, ordinal 16.
The compiler records that alias and its source note in the compiled premise.

This distinction allows Taurus-specific verses 61–75 and Aquarius-specific
verses 88 onward to retain their sign context while sharing the same stable
chart-fact vocabulary.
