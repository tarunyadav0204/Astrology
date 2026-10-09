# Verified Muhurat calculator audit — 9 October 2026

## Scope and result

Reviewed the rich planners, simple Panchang elections, canonical Panchang, Navatara,
chat adapters, public routes and mobile/web consumers. Added an **opt-in** Verified
interval engine and conversational workflow. Existing public planner request/response
contracts and hourly sampling shapes remain unchanged. Shared Choghadiya sequencing and Yamaganda/Gulika weekday-index corrections intentionally change calculated values, without changing client fields or signatures. Their accuracy limitations
below still apply; passing compatibility tests does not certify their predictions.

## Inventory and findings

| Existing component | Clients / capability | Finding and disposition |
| --- | --- | --- |
| `calculators/muhurat_calculator.py` | Mobile planners; public vehicle route; chat calculator adapter | Vehicle, Griha Pravesh, gold, business, childbirth. Tropical ascendant was mixed with sidereal planets; hourly samples were not complete valid intervals. Verified now uses a separate sidereal interval engine. |
| `panchang/muhurat_calculator.py` | Marriage/property and simple Panchang elections | Fixed daytime segments are not a complete activity-specific election, wedding analysis or personalized matching. These remain available to existing clients; Verified explicitly reports unsupported coverage. |
| `panchang/panchang_calculator.py` | Canonical Panchang and legacy facade | Reused for local sunrise/sunset and Choghadiya; supports actual limbs and transition evidence. Retains its existing public contract. |
| `calculators/navatara_calculator.py` | Daily / calculator menu | Uses zero-based natal nakshatra. Rich Muhurat expects one-based: corrected only the chat Muhurat adapter, preserving Navatara’s convention. |
| `chat/calculator_menu.py` | Verified and conflict tool menu | Compaction dropped `recommendations` entirely. Added `candidate_samples` before compaction, with explicit legacy hourly-sample coverage. These are not advertised as validated intervals. |
| `panchang/muhurat_routes.py` | Public rich vehicle wrapper / web | Wrapper presents hourly samples as 60-minute slots. Left unchanged for compatibility; Verified does not use this wrapper. |

Additional rich-planner issues: solar-day anchoring could mix dates; sunrise-only
Panchang filtering ignored later limb changes; rikta filtering omitted Krishna
19/24/29; generic daily combustion warnings could name Venus for another karaka;
shared business scoring inherited a vehicle/home fourth-house rule; numeric offsets
were unreliable for future daylight-saving changes. Searches silently capped at 60
days. Legacy natal context could default a missing birth time to noon and did not
include birth seconds. A D16 comment is not an actual D16 calculation.

Shared corrections: Choghadiya day/night planetary sequences were incorrect; corrected both while retaining all existing output keys. Yamaganda/Gulika used shifted weekday segment indexes; corrected those in the rich planner and Verified engine. Verified tests actual timestamp boundaries rather than rounded clock labels.

References: [Drik Panchang Choghadiya weekday tables](https://www.drikpanchang.com/tutorials/muhurat/daily/choghadiya-muhurat.html?lang=en), [published Yamaganda table](https://chilakamarthi.com/files/documents/2015-CHILAKAMARTHI-ENGLISH-PANCHANGAM.pdf).

## New Verified engine

`calculators/verified_muhurat_calculator.py` reuses existing activity policies and
scorers, but computes Lahiri sidereal ascendants, full birth timestamps, coordinate-
resolved event-city IANA timezones and local solar days. It rejects both pakshas’
rikta tithis, Vishti and the existing app’s Panchak/yoga/activity policies. It checks
Rahu Kaal, Yamaganda, Gulika, Choghadiya, Lagna, Panchang and applicable natal factors
at each minute’s start, midpoint and end; only contiguous acceptable cells form a
window. Window score is the lowest sampled score, not a success probability.
Business does not inherit the generic fourth-house rule. Rule completeness remains
limited: this is not independent certification of all classical doctrine.

Searches are inclusive **1–60 days**, daylight only; no hidden date truncation,
availability relaxation or substitution of activities. Incomplete solar/calculation
coverage is `partial`, not proof that no good times exist. Top eight candidates are
returned with an explicit total/count limit. Solar-day exclusions are retained for
audit. Missing natal birth time does not create an invented noon chart.

Supported activity rule sets: vehicle purchase, Griha Pravesh, gold purchase and
business opening. Personalized vehicle scoring uses natal vehicle context and Tara
Bala; other supported activities currently add Tara Bala only. A general election
must not be called fully personalized. Marriage, property, travel, medical and
other unimplemented activities return an explicit unsupported limitation.

## Workflow and compatibility

Luna distinguishes choosing/checking when to begin an action from predicting when
an event occurs. The themed chat form confirms activity, event city, dates/hours and
personal scope. Confirmed form values override model guesses. Follow-up questions
can continue the same constraints; new topics exit the workflow. No-match results
offer explicit next-30-days/change-details/all-weekdays choices. No widening occurs
without a user choice. The writer streams through the existing Verified model
selection and cost path; Muhurat gets its own detailed contract. Admin history shows
`ELECT_MUHURAT` and initial/additional calculator request/result rounds.

No database migration or public planner contract change is required. Existing chat
history and prior-answer context are retained. Existing planners retain their hourly sampling and other documented limitations; only the shared weekday/Choghadiya corrections apply to them. Migrate their clients to the interval engine separately if desired.

## What still needs a new rules engine

- Full marriage election: activity-specific doshas, both profiles, matching and
  relevant personalized evidence; fixed daytime segments are insufficient.
- Property signing versus purchase versus Griha Pravesh must have distinct policies.
- Complete business election should evaluate activity-specific houses, karakas and
  user constraints beyond the inherited generic scorer.
- Travel/other activity policies and night elections require dedicated rules.
- Exact transition solving would improve precision beyond the conservative grid.
- Clinical scheduling is not an astrology election engine.

Swiss Ephemeris documents the distinction between tropical houses and sidereal
`houses_ex` flags: [programming reference](https://www.astro.com/swisseph/swephprg.htm).
Astronomical correctness and agreement with implemented policies do not establish
predictive certainty or exhaustive classical coverage.
