# Prashna rebuild audit — 2026-09-19

## Production boundary

The mobile feature now implements one declared method: **Praśnatantra–Tājika**.
It does not combine Prashna Marga, KP, Parāśari aspect voting, Jaimini, numerology,
or an AI-generated astrological opinion. The removed legacy calculator must not be
restored as a fallback.

The public release accepts seven narrowly framed judgement modules, grouped into
six user-facing sections:

- a specific job, application, promotion, or employer outcome;
- receipt of a defined payment or gain;
- renewed contact, unblocking, return, or reconciliation with one specific romantic partner;
- marriage with one specific person or a specific marriage proposal;
- a specific planned journey;
- recovery of one missing possession;
- purchase or sale of one property.

Health, pregnancy/children, death, litigation winners, speculation, and broad life
readings are rejected before a chart is made. The same in-progress reading keeps
one fixed chart instant across retries. Cross-device repeat-question enforcement
requires durable user history and is not claimed by this release.

## What was replaced

| Previous path | Production path |
|---|---|
| Lahiri plus whole-sign houses | Hāyanaratna 1.9 textual precession plus quadrant cusps and junctions |
| Free-text question and chart cast together | Backend-owned guided question ID, followed directly by one chart cast |
| Optional KP 1–249 overlay | Rejected by the API; not part of this lineage |
| Partial yoga stack | All sixteen named configurations are emitted with source records |
| Generic support/obstruction `yes/no` | `favorable`, `unfavorable`, `mixed`, or `cannot_judge` |
| Silent defaults and fallback motion | Invalid or missing inputs stop the calculation |
| Technical jargon as the main result | Plain conclusion and decision meaning first; working is expandable |

The old `prashna_calculator.py`, Lahiri question-chart calculator, KP overlay,
perfection helper, and partial topic calculator were deleted so another caller
cannot silently reach the obsolete judgement.

## Calculation profile

`hayanaratna_textual_precession_quadrant_v1` freezes these choices:

- Swiss Ephemeris tropical longitudes and actual signed daily motion;
- the precession rule described at Hāyanaratna 1.9;
- ascendant and meridian from Swiss Ephemeris;
- quadrants trisected into twelve house cusps, with halfway junctions;
- house occupancy between junctions and 0–20 cusp strength;
- mean node only where an explicit topic rule calls for Rāhu;
- Hāyanaratna planetary orbs: Sun 15°, Moon 12°, Mars 8°, Mercury and
  Venus 7°, Jupiter and Saturn 9°;
- exact angular application/separation using actual signed motion, including
  impending contact over a sign boundary;
- domicile, exaltation/fall, haddā, decan, and ninth-part dignity;
- the explicitly selected Hāyanaratna 2.4.1 constant friend/enemy table;
- Hāyanaratna day/night planetary grouping and time-strength arc;
- disclosed solar-visibility limits used for setting and rays.

## Judgement policy

Each family has a closed list of verse records. Descriptive clauses, such as a
lost-item location clue, cannot affect the verdict. A supporting rule alone gives
`favorable`; an obstructing rule alone gives `unfavorable`; both give `mixed`;
no decisive rule gives `cannot_judge`. The engine never treats an absent match as
denial and never converts astronomical contact time into an event date.

Radda, khallāsara, and maṇaū qualify an otherwise relevant significator
connection. They do not create a free-standing negative prediction. Rare yoga
records retain the selected Hāyanaratna reading and its source URL.

## Verification completed

Focused tests cover:

- precession, cusp, junction, boundary, and house-strength arithmetic;
- exact, applying, separating, reverse-order, and cross-sign contact geometry;
- all sixteen named Tājika records and their source links;
- every enabled topic module and four-way verdict contract;
- guided-question catalogue ownership and immutable question IDs;
- rejection of high-stakes and unsupported topics;
- DST, timezone, coordinate, and malformed-clock failures;
- API separation between interpretation and chart casting;
- rejection/removal of the old KP field;
- Babel parsing of the rebuilt React Native screen.

These tests establish deterministic implementation behavior. They do not prove
astrology's predictive accuracy.

## Remaining release governance

Textual fidelity and predictive reliability are different claims. Before marketing
this as practitioner-reviewed, the source ledger and golden charts should be
signed off independently by a Sanskrit reader familiar with Tājika and by an
experienced practitioner. Before making any accuracy claim, freeze predictions,
collect consented outcomes prospectively, and publish sample size and unresolved
cases. Until then the UI correctly calls the result a traditional indication and
never a probability or guarantee.
