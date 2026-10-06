# Deva Keralam Book 1 timing backlog

## Result

The three completion ledgers contain **220 timing-pending passages**. Every one
appears exactly once in `timing_backlog_v1.json`; the backlog has no entries
outside that ledger disposition.

| Timing family | Passages | What must be resolved or calculated |
|---|---:|---|
| Dasha phase or junction | 45 | Dasha system, period interval, former/middle/latter fractions, thirds, and period-boundary rules |
| Ordinal, Tara, or Rashi Dasha | 36 | Source-specific sequence for first/second/etc. periods, Janma/Sampat/Vipat/Kshema labels, and Rashi periods |
| Named planet or lord period | 34 | Typed Dasha system, planet/sign/house-lord period resolver, and main/sub-period intervals |
| Explicit age or year | 24 | Exact age interval from birth date and an `as_of` date |
| Dasha plus transit | 24 | A valid Dasha permission window plus a separately calculated transit trigger |
| Transit activation | 21 | Sidereal transit positions and targets derived from natal Rashi, Navamsha, lords, or transit cycle count |
| Unclear timing method | 14 | Source reconstruction and preferably a second witness |
| Life stage or relative event | 10 | Defined life-stage boundaries or an external event anchor, neither of which should be guessed |
| Unclear Dasha method | 10 | Identification of the Dasha system and how the named period maps to it |
| Calendar trigger | 2 | Panchanga weekday, Tithi, or ruling Nakshatra/day facts |
| **Total** | **220** | |

The taxonomy uses one primary family per passage. A passage requiring both a
Dasha and transit is therefore counted under the combined family rather than
being duplicated in the two component families.

## Important Dasha distinction

The text does not use one timing vocabulary consistently. It contains named
planetary periods, house-lord periods, numbered periods, Rashi periods, and
Tara labels such as Janma, Sampat, Vipat, and Kshema. These must not all be
silently interpreted as Vimshottari Dasha.

Before a Dasha rule can run, its source review must declare:

1. the Dasha system;
2. whether a number identifies sequence order, a Rashi period, or another
   source-specific period;
3. the period and sub-period rulers;
4. the exact start and end instants;
5. how halves, thirds, middle portions, and junctions are measured.

The existing typed Vimshottari facts can support passages explicitly confirmed
as Vimshottari. They are not a fallback for unidentified Nadi timing.

## Transit requirements

The transit passages go beyond a planet merely occupying a house. They include
contacts with:

- a natal planet or Rashi;
- the Rashi containing a planet's Navamsha position;
- the Navamsha dispositor of a house lord;
- a target Rashi or its trines;
- a planet's first, second, or third circuit after birth;
- a Dasha window that must already be open.

The later transit layer therefore needs typed target provenance. A rule should
be able to say that Saturn reached a Rashi derived from the natal Sun's
Navamsha, rather than reducing that statement to an unexplained sign match.

## Recommended first implementation slice

The safest high-frequency first slice is the **24 explicit age-or-year
passages**. This does not approve their predictions. It adds deterministic
timing plumbing that a source-reviewed rule can use later.

This slice is preferable because:

- age is independent of the unresolved Nadi Dasha system;
- the fact engine already accepts birth date and `as_of` date;
- exact ages and “after age N” conditions can be tested without inferred
  planetary periods;
- matching can fail closed when birth date, timezone, or calendar boundaries
  are unavailable;
- the same interval calculator is reusable outside Deva Keralam.

The implementation should support three explicit predicates:

1. **during completed age N** — from the Nth birthday until the next birthday;
2. **at or after completed age N** — beginning at the Nth birthday;
3. **strictly after completed age N** — beginning at the next birthday;
4. **between completed ages N and M** — a bounded birthday-to-birthday
   interval.

“Childhood”, “youth”, “middle age”, “old age”, and phrases tied to marriage,
puberty, or another person's event are excluded from this first slice because
the source does not give universal date boundaries for them.

Before any of the 24 passages becomes a rule, source review must still confirm
its natal premises, exact age wording, alternatives, and outcome policy.
`implementable_now` in the JSON therefore describes calculator readiness, not
permission to publish the passage.

## Subsequent order

After age intervals, the recommended order is:

1. identify and encode the ordinal/Tara/Rashi Dasha systems;
2. bind named planet and house-lord periods to an explicitly declared system;
3. implement period fractions and junctions;
4. add transit targets derived from natal and Navamsha facts;
5. combine Dasha permission with transit triggers;
6. add Panchanga calendar triggers;
7. retain vague life-stage and unresolved timing statements for source review
   or a second witness.

This order unlocks the 45 largest phase/junction family only after its period
boundaries are trustworthy.

## Validation

`timing_backlog_v1.json` validates with `load_completion_backlog()`. Its 220
entries pass `audit_backlog_against_ledger()` against the combined D, E, and F
completion ledgers with no missing or extra passage.
