# Birth-time rectification architecture

Status: Phase 1 evidence workbench and blind benchmark harness implemented;
real holdout cohort collection and validation pending

Blind benchmark operation and dataset rules are documented in
`docs/BIRTH_TIME_RECTIFICATION_BENCHMARK.md`.

## Product boundary

Birth-time rectification is a dedicated, deterministic workflow. It is not an
Instant/Standard/Premium chat answer and it must never silently change a saved
chart. The engine ranks candidate birth-time **windows** against dated life
events and exposes the evidence and contradictions for every leading window.

The product must not claim that astrology independently recovered an exact
second. Until benchmark calibration exists, output is a `relative_fit` rather
than a statistical probability. A minute-level best candidate may be displayed
inside a wider supported interval, but the interval is the primary result.

The existing `birth_charts.is_rectified` / `calibration_year` fields and
`POST /verify-calibration` route are legacy calibration metadata. They are not
sufficient for, and must not be used as, the new rectification result.

## Architectural principles

1. Candidate generation and scoring are deterministic. An LLM may translate
   evidence or ask the next user-friendly question; it cannot alter scores.
2. Parashari and KP remain separate evidence streams. Agreement is explicit;
   rules are not blended into an opaque synthetic astrology method.
3. A known event is evaluated through static promise, event-specific varga,
   dasha delivery and transit confirmation. Timing coincidence alone is weak.
4. The same astrological fact is counted once. A dasha-house connection reused
   by two presenters is not two independent confirmations.
5. Exact, independently verifiable events receive more weight than subjective
   traits or approximate memories.
6. Candidate charts are clustered into equivalent or near-equivalent time
   intervals. Adjacent seconds are not presented as independent discoveries.
7. The original recorded time is immutable. Applying a result creates a
   versioned chart revision that can be reversed.

## Existing components to reuse

- `calculators.chart_calculator.ChartCalculator`: D1 and house calculation.
- `calculators.divisional_chart_calculator.DivisionalChartCalculator`: relevant
  vargas.
- `shared.dasha_calculator.DashaCalculator`: strict real MD/AD/PD boundaries.
- `calculators.real_transit_calculator.RealTransitCalculator`: event-date
  transits.
- `prediction_engine.primitives`: validated charts, classical Parashari
  connections and the corrected Rahu/Ketu aspect policy.
- `prediction_engine.event_windows.EVENT_DEFINITIONS`: initial vocabulary and
  auditable event-house definitions. Rectification definitions can extend them
  but must not mutate prediction behavior.
- `app.kp.services.chart_service.KPChartService`: Placidus cusps, cusp lords,
  four-step significators and KP ayanamsha calculations.

Rectification must call these Python services directly. It must not make a
network request to existing HTTP endpoints for every candidate.

The knowledge graph may expose rectification as a dedicated question/tool route
and describe which factors an event requires, but it is not the scoring engine.
The versioned rectification event registry and deterministic calculators remain
authoritative; graph or prompt wording cannot change a candidate score.

`build_calculation_context()` is optimized for continuous prediction windows.
Rectification needs a new sparse event-date context builder so 1,000 candidate
times are not each expanded into years of daily transit states.

## Supported event model

Every event contains:

- `event_type` and optional subtype;
- `subject` (`self`, spouse, child, mother or father when supported);
- `date_start` and `date_end`;
- `precision`: exact day, month, year or broad period;
- `source_reliability`: documented, confident memory or approximate memory;
- optional structured facts needed by the event definition; and
- a user-visible note, excluded from deterministic scoring.

Initial event types:

| Event | Primary frame | Confirming varga | Typical KP/event houses |
|---|---|---|---|
| Marriage / engagement | commitment and family formation | D9 | 2, 7, 11; 5 where relationship-led |
| Childbirth | child arrival and family gain | D7 | 2, 5, 11 |
| First job / job change | service, profession and transition | D10 | 2, 6, 10, 11 with 3/8/12 transition |
| Promotion | authority, status and gain | D10 | 2, 6, 10, 11 |
| Education milestone | study, admission or completion | D24 | event-specific 4/5/9/11 |
| Relocation / foreign move | home change and distance | D4 | 3, 4, 9, 12 |
| Property purchase | home/asset plus payment | D4 | 2, 4, 8, 11 |
| Surgery / serious accident | body, intervention and recovery | D30/D3 as defined | 1, 6, 8, 12 with recovery support |
| Major financial gain/loss | resources, gain, debt or loss | D2 | event-specific 2/6/8/11/12 |
| Parent milestone or loss | derived parent frame | D12 | derived houses plus event-specific houses |

Divorce, bereavement, pregnancy loss and severe illness require sensitive copy
and explicit user entry; the workflow must never solicit them as casual guesses.
Personality, appearance and body type may break a tie only after event scoring.

## Candidate search pipeline

### 1. Normalize the uncertainty window

Resolve the supplied local civil time with the historical IANA timezone and
coordinates. Store both local and UTC bounds. Reject impossible DST/local-time
combinations rather than silently shifting them.

Suggested limits:

- recorded time: user-selected `±5`, `±15`, `±30`, `±60` minutes;
- remembered part of day: explicit start/end window;
- completely unknown time: one local civil day, handled as a coarse search.

### 2. Coarse deterministic scan

Scan candidate minutes and calculate a lightweight fingerprint:

- D1 ascendant sign/degree and houses;
- Bhava/Placidus cusps;
- D9, D7, D10, D12, D24 and D4 ascendants only when events need them;
- KP ascendant/cusp star and sub lords;
- event-date MD/AD/PD lords.

For windows longer than six hours, begin at a wider step and refine only the
leading regions. Do not calculate every possible varga for every candidate.

### 3. Full event scoring

Retain the strongest coarse regions and calculate complete event evidence:

- Parashari natal/static promise;
- the event's relevant divisional chart;
- strict MD/AD/PD delivery at the event date/range;
- slow-planet and event-relevant transit confirmation;
- KP cusp promise and event-house significators; and
- explicit contradictions.

Transit ephemerides for an event date can be shared across candidates. Natal
house placement, cusps, dasha balance and varga placements remain
candidate-specific.

### 4. Fine refinement and clustering

Refine leading minute regions only where an astrological boundary can
distinguish candidates. Group adjacent candidates whose scores and decisive
evidence are materially identical. Stop at minute precision for the first
release. Second-level refinement is permitted only after separate validation
and must still return an uncertainty interval.

## Scoring contract

The engine returns component evidence, not only a total:

```json
{
  "candidate_local_time": "16:27:00",
  "candidate_window": {"start": "16:26:00", "end": "16:29:00"},
  "relative_fit": 84.2,
  "event_coverage": 0.91,
  "school_agreement": "parashari_kp_convergent",
  "events": [
    {
      "event_id": 101,
      "fit": "strong",
      "reliability_weight": 1.0,
      "parashari": {
        "static_promise": "supported",
        "varga_confirmation": "supported",
        "dasha_delivery": "strong",
        "transit_confirmation": "moderate"
      },
      "kp": {
        "cusp_promise": "supported",
        "timing_significators": "strong"
      },
      "contradictions": []
    }
  ]
}
```

The internal score should use source-locked, versioned component rules. Event
weights come only from date precision, source reliability and event
independence—not from whether the event makes a preferred candidate win.

KP denial is a KP-stream veto, not automatically a universal veto. A global
candidate rejection requires a versioned policy and tests showing that the
underlying calculation is reliable for that event category.

Confidence wording is based on separation and stability:

- score separation between the leading clusters;
- number of independent, high-reliability events;
- leave-one-event-out stability;
- sensitivity to reasonable event-date uncertainty; and
- agreement or disagreement between schools.

Before empirical calibration, labels must be `clear relative leader`,
`moderate relative leader`, `multiple plausible windows`, or
`insufficient evidence`; never `84% likely`.

## Progressive narrowing

After each run, compare the leading candidate clusters and identify the event
category with the highest expected information gain. Ask one concrete question,
for example:

> The 4:27 PM and 4:35 PM windows both fit marriage and career. Do you know the
> month and year of your first major relocation?

The question selector is deterministic and may return a localized question key
plus structured choices. An LLM may phrase the question in the user's language,
but cannot choose which evidence would distinguish the candidates.

The user can add the event, mark it unknown or stop. Unknown answers are not
treated as negative evidence.

## Persistence

Phase 1 tables:

### `rectification_cases`

- `id`, `userid`, `birth_chart_id`
- saved chart reference plus an immutable chart-input hash
- uncertainty start/end and timezone
- status, active run id, created/updated timestamps

### `rectification_events`

- case id, event type/subtype, subject
- date start/end, precision, reliability
- structured metadata and optional encrypted user note
- active/deleted state and timestamps

### `rectification_runs`

- case id, status and progress
- engine, rule-registry and ephemeris versions
- immutable configuration and input hash
- best window, result summary, failure details and timestamps

### `rectification_result_clusters`

- run id, rank, local/UTC interval, best minute
- relative fit, stability and school-agreement fields
- event-by-event evidence JSONB

Store only top clusters and a compressed score landscape, not one database row
for every discarded minute. Full trace artifacts may use object storage with a
hash stored on the run.

### Chart revisions

Applying a result creates a `birth_chart_revisions` record containing original
and rectified values, source run id, user confirmation and calculation versions.
The existing chart may point to an active revision, but its recorded value must
remain recoverable. `is_rectified` can become a derived compatibility flag; it
must not be the source of truth.

## API surface

- `POST /api/rectification/cases`
- `GET /api/rectification/cases/{case_id}`
- `POST /api/rectification/cases/{case_id}/events`
- `PATCH /api/rectification/events/{event_id}`
- `DELETE /api/rectification/events/{event_id}`
- `POST /api/rectification/cases/{case_id}/runs`
- `GET /api/rectification/runs/{run_id}`
- `GET /api/rectification/runs/{run_id}/results`

Planned for Phase 2:

- `GET /api/rectification/runs/{run_id}/next-question`
- `POST /api/rectification/runs/{run_id}/apply`

All reads and mutations require ownership checks. Run creation is idempotent by
case/input/config hash. Applying requires explicit confirmation and cannot run
while the source run is incomplete.

## Execution model

Rectification is a durable background job. Production must dispatch a Cloud
Task (or a shared durable job abstraction) and persist progress; FastAPI
`BackgroundTasks` alone is not sufficient because a process restart would lose
the run. Development may use a local worker fallback.

Suggested stages reported to clients:

1. validating events;
2. scanning the birth-time window;
3. checking leading candidate charts;
4. testing result stability; and
5. preparing evidence.

Candidate batches must not hold database connections while calculating. Workers
read inputs once, release the connection, calculate, then acquire a connection
briefly to checkpoint progress/results.

## UI flow

1. Select a saved chart.
2. Describe time uncertainty with a range control and confidence explanation.
3. Add 4–8 important events through event-specific cards.
4. Review event dates and their precision before starting.
5. Show background progress; the user may safely leave the screen.
6. Present a score-landscape chart, best supported window and alternatives.
7. Expand any event to see supporting and contradicting evidence.
8. Offer one progressive question when it can materially separate candidates.
9. Apply the selected result as a reversible chart revision.

Web and mobile consume the same localized API contract. No astrology scoring is
implemented in either client.

## Validation gates

The feature is not production-ready until it has:

- calculator unit tests at ascendant, varga and KP sub-lord boundaries;
- deterministic score tests for every event type;
- timezone and historical DST fixtures;
- exact-day, month-only and year-only event tests;
- leave-one-event-out and event-date-jitter tests;
- negative controls using shuffled events;
- method-ablation reports showing what Parashari, KP and transit layers add;
- blind benchmark charts whose recorded times are hidden from the engine;
- measured recovery rates within 5, 15, 30 and 60 minutes; and
- performance/load tests for a full-day search.

The benchmark set must be separated into development and holdout sets. Rules
cannot be tuned against the same public or founder charts used to report final
accuracy.

## Delivery phases

### Phase 1 — evidence workbench

Support `±60 minutes`, minute candidates, marriage, childbirth, career,
education, relocation and property events. Return ranked windows and a full
audit trace. Do not yet apply results to saved charts.

### Phase 2 — progressive consumer flow

Add information-gain questions, localized UI, background notifications,
reversible chart revisions and mobile parity.

### Phase 3 — broad/unknown-time search

Add part-of-day/full-day coarse-to-fine scanning, additional sensitive event
types and practitioner controls.

### Phase 4 — calibrated confidence

After a sufficiently large blind benchmark, calibrate score separation into
empirical confidence bands. Only then consider narrower-than-minute output.
