# Dasha Caching Phase Note

## Goal

Add dasha caching in a way that reduces repeated computation across app, web, and chat while keeping production risk low.

This note captures the agreed safety approach for the next phase.

## Core Safety Rule

For the next dasha caching phase:

- do not change callers
- do not change request shape
- do not change response shape
- do not change frontend parsing expectations
- change only the internals of what is already being called

In plain English:

- app code should keep calling the same endpoints
- web code should keep calling the same endpoints
- chat should keep using the same internal dasha paths
- each route or service should return the exact same payload structure it returns today
- caching should be an internal optimization, not a product behavior change

## Rollout Strategy

Prefer route-level internal caching first.

That means:

1. route receives the same input as today
2. route checks cache internally
3. on cache hit, return the same response payload structure
4. on cache miss, run the existing calculation path
5. store the result
6. return the same response payload structure

This limits damage because callers do not need to be modified or coordinated.

## Why This Is Safer

- no mobile rollout dependency
- no web rollout dependency
- no hidden contract drift
- easier rollback
- easier phased rollout
- easier to compare cached vs uncached behavior for the exact same route

## Important Constraint

Do not start by rewriting all dasha calculators into a new shared abstraction.

That may be a later improvement, but it increases blast radius.

First step should preserve existing route logic and insert cache at the edges.

## Dasha Routes Identified As Actually Used

These routes are actively used by app and/or web:

### Vimshottari

- `POST /api/calculate-cascading-dashas`

### Yogini

- `POST /api/yogini-dasha`

### Chara

- `POST /api/chara-dasha/calculate`
- `POST /api/chara-dasha/antardasha`

### Kalchakra

- `POST /api/calculate-kalchakra-dasha`
- `POST /api/calculate-kalchakra-antardasha`
- `GET /api/kalchakra-dasha-info` (info/metadata route, not the main compute path)

### Jaimini Kalchakra

- `POST /api/calculate-jaimini-kalchakra-dasha`
- `POST /api/calculate-jaimini-kalchakra-antardasha`
- `POST /api/jaimini-antardashas`

## Lower-Risk Initial Scope

Start with the smallest high-value set:

1. `POST /api/calculate-cascading-dashas`
2. `POST /api/chara-dasha/calculate`
3. `POST /api/chara-dasha/antardasha`

Reason:

- clearly used
- repeated user access
- simpler than kalchakra and jaimini variants

## Later Scope

After the first routes are stable:

1. `POST /api/yogini-dasha`
2. `POST /api/calculate-kalchakra-dasha`
3. `POST /api/calculate-kalchakra-antardasha`

Then later:

1. Jaimini Kalchakra routes
2. internal chat/shared service-level dasha caching so chat also benefits directly

## Chat Consideration

Chat often does not call the public HTTP dasha endpoints.

It also uses internal paths such as:

- `DashaCalculator.calculate_current_dashas(...)`
- `DashaCalculator.calculate_dashas_for_date(...)`
- context agents such as Vimshottari and Chara dasha agents

So route-level caching helps app/web first.

If we want chat benefit too, we should later add caching in shared internal dasha services or calculator entry points, but only after the route-level rollout is proven stable.

## Cache Design Principle

For the first phase, cache the final route response payload, not a newly invented intermediate model.

That keeps the optimization invisible to callers.

## Invalidation Principle

Invalidate by `birth_hash`, same as chart caching.

If dasha logic changes materially, bump cache version in the cache key rather than mutating caller contracts.

## Success Criteria

The dasha caching phase is successful if:

- same callers continue to work unchanged
- same response structures are returned
- same screens continue to render without code changes in callers
- repeated dasha views become faster
- rollback is simple because route contracts remain untouched
