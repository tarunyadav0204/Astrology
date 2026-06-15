# Observability Hardening Plan

This document is the working plan for making AstroRoshni backend incidents understandable within minutes instead of through manual detective work.

It is intentionally practical and updateable. We can keep adding findings, status notes, and follow-up tasks here over time.

## Goals

1. When a VM restarts or is recreated, know why.
2. Keep logs after VMs are replaced.
3. Distinguish startup failure, runtime slowness, and infra autohealing.
4. Reduce noisy logging so real incidents are visible.
5. Make backend health regressions alertable.

## Current Problems

- Backend logs are primarily local to VM disk and are not a durable source of truth.
- Many production code paths still use `print(...)` instead of structured logging.
- Request logging is verbose and high-volume, which makes real incident clues hard to find.
- Sentry is present, but it is not a full logging system and does not replace centralized logs.
- VM replacement in MIG can erase the easiest place we currently look for incident context.
- We do not yet have a single reliable lifecycle trail for:
  - startup begin
  - startup step progress
  - startup complete
  - slow request spikes
  - shutdown reason
  - restart/recreate reason

## Working Theory From Recent Incidents

- The recent outages did not look like clean Python crashes.
- Both VMs showed periods of slowness around credits / Google Play endpoints.
- Health checks were often still arriving, which suggests intermittent slowness or wedging rather than obvious process death.
- We also found at least one startup fragility issue:
  - eager import-time construction in `muhurat_routes.py`

## Decision

Use both:

- `Cloud Logging` as the durable operational log store
- `Sentry` as the exception and grouped error tracker

Do not rely on local VM files as the primary incident source.

## Checklist

### Phase 1: Durable Logging

- [x] Switch backend logging to stdout-first so VM/runtime collectors can forward a durable stream
- [x] Include deploy commit SHA in backend process env (`APP_COMMIT_SHA`)
- [x] Make backend startup output unbuffered (`PYTHONUNBUFFERED=1`) during deploy/restart scripts
- [ ] Confirm backend stdout/stderr is being captured into GCP Cloud Logging
- [ ] Confirm VM startup-script logs are captured into Cloud Logging
- [ ] Confirm system/service logs relevant to process death and restart are visible in Cloud Logging
- [x] Stop treating local `server_shutdown.log` as the primary incident record

### Phase 2: Lifecycle Signals

- [x] Add structured `startup_begin` log
- [x] Add structured per-step startup logs for major initialization blocks
- [x] Add structured `startup_complete` log
- [x] Add structured `shutdown_begin` log
- [x] Add structured shutdown reason log for signal/manual termination
- [x] Include instance identity and commit/version metadata in lifecycle logs

### Phase 3: Slow Request Observability

- [x] Replace noisy all-request logging with threshold-based slow request logging
- [x] Log requests slower than 2s as warning
- [x] Log requests slower than 5s as error
- [x] Include path, method, latency, instance, and request category
- [x] Add special logging around credits / Google Play endpoints

### Phase 4: Sentry Hardening

- [x] Tag Sentry events with instance name
- [x] Tag Sentry events with environment
- [x] Tag Sentry events with backend version / commit SHA if available
- [ ] Capture startup failures explicitly
- [ ] Capture shutdown reasons explicitly
- [x] Capture degraded health / repeated slowness messages as Sentry events where useful

### Phase 5: Logging Cleanup

- [x] Audit `print(...)` usage in production backend code
- [~] Convert important lifecycle and failure prints to `logger.*`
- [ ] Gate deep debug logs behind a feature flag or debug mode
- [x] Reduce noisy request-level chatter
- [ ] Remove or tame especially verbose astrology calculation debug output in production paths

Recent progress:
- login/auth failure prints converted to structured lifecycle logs in `backend/main.py`
- chat routing/context/delete hot-path prints converted to structured logger events in `backend/chat_history/routes.py`
- deep astrology diagnostics in dasha/jaimini/context-builder are still pending and should likely be gated behind a debug flag instead of staying always-on in prod

### Phase 6: Alerting

- [ ] Add alert for public `/api/health` failing
- [ ] Add alert for repeated MIG recreate activity
- [ ] Add alert for repeated startup failures
- [ ] Add alert for slow credits / Google Play endpoint spikes
- [ ] Add alert for repeated backend process restarts on same instance

## Suggested Logging Model

### Cloud Logging should store

- application stdout/stderr
- structured backend logs
- startup script logs
- system logs
- VM/instance lifecycle logs

### Sentry should track

- uncaught exceptions
- grouped app errors
- explicit startup/shutdown error events
- high-signal degradation events

## Suggested Structured Events

Examples of event names to standardize:

- `startup_begin`
- `startup_step_begin`
- `startup_step_ok`
- `startup_step_failed`
- `startup_complete`
- `shutdown_begin`
- `shutdown_signal`
- `slow_request`
- `health_degraded`
- `credits_play_latency_spike`
- `manual_restart`
- `instance_recovery`

## Questions To Resolve

- Are backend stdout/stderr already reaching Cloud Logging, or do we need Ops Agent setup?
- What is the best source for instance identity inside the app process?
- Do we want JSON logs immediately, or first migrate the highest-value prints to logger calls?
- Should we emit commit SHA from deploy-time env or from a generated version file?

## Notes

### 2026-06-15

- Recent evidence suggests the credits / Google Play screen path can cause multi-second stalls.
- Google Play metadata caching and bonus/status-path optimizations have already been started separately.
- Admin settings caching with invalidation and version polling has also been introduced separately.
- Observability work is still needed even if those fixes reduce outage frequency.
- Backend now emits structured lifecycle events to stdout with:
  - `event`
  - `instance`
  - `version`
  - `pid`
- Deploy/restart scripts now export `APP_COMMIT_SHA` and `PYTHONUNBUFFERED=1`.
- Remaining Phase 1 work is GCP-side verification:
  - confirm stdout/stderr arrives in Cloud Logging
  - confirm startup-script/system logs are visible centrally
- Live verification on `astroroshni-mig-zmc9` showed:
  - startup-script logs exist in `google-startup-scripts.service` journal
  - no `google-cloud-ops-agent` unit was installed
  - Cloud Logging queries for backend/startup markers returned no results
- Because backend is still launched with `nohup ... >> logs/backend.log`, centralized logging needs an agent that tails files unless process launch is later moved under a journal-aware supervisor.
- Added repo-side Ops Agent assets:
  - `/ops-agent/config.yaml`
  - `/scripts/install_ops_agent.sh`
- Replaced noisy all-request middleware logging with threshold-based `slow_request` events.
- Default thresholds:
  - warning at `2.0s` via `SLOW_REQUEST_WARN_SECONDS`
  - error at `5.0s` via `SLOW_REQUEST_ERROR_SECONDS`
- Slow `credits` and `health` requests now also emit a Sentry message at error threshold.
- Sentry now tags events with:
  - `instance`
  - `version`
  - `environment_name`

## Next Recommended Implementation Steps

1. Wire backend logs durably into Cloud Logging.
2. Add structured startup/shutdown logs in `backend/main.py`.
3. Replace all-request timing prints with slow-request threshold logs.
4. Add instance/version metadata to logs and Sentry.
5. Begin a controlled cleanup of noisy `print(...)`s.
