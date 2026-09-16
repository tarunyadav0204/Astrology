# Event Timeline V3.19 — Family Profiles

- [x] Add chart-specific structured profiles for spouse/partner, mother, father, child, and siblings.
- [x] Ask for living status, approximate age, daily work/life state, and location context.
- [x] Keep every field optional or allow an unknown answer.
- [x] Keep chat-extracted facts as a compatibility fallback.
- [x] Make the structured profile authoritative when both sources exist.
- [x] Exclude disabled or deceased profiles from future-event generation.
- [x] Evaluate a configured person astrologically before applying their Desh-Kaal-Patra wording.
- [x] Do not create an event merely because a person was configured.
- [x] Tailor work/status language for employed, business, homemaker, student, retired, and non-working relatives.
- [x] Retain the derived-house disclaimer when the relative's own chart is not linked.
- [x] Remove the two-person publication cap; retain one leading event per qualified person and keep that person's additional events in details.
- [x] Keep family events out of the yearly vibe/header because the monthly cards already contain them.
- [x] Include family profiles in the cache fingerprint so edits never reopen a stale timeline.
- [x] Add an environment rollback: `EVENT_TIMELINE_RELATIVE_PROFILES=false` restores chat-fact-only eligibility.
- [x] Add the database migration to the production runtime migration sequence.
- [x] Add English and Hindi mobile copy.
- [x] Add deterministic tests for eligibility, exclusion, fingerprint invalidation, and unlimited relatives.
- [x] V3.20 correction: treat each relative's reference house as the lagna used for rotation, not as a required activated house.
