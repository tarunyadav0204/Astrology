# Nudge Worker Deployment

This runbook separates nudge and notification background work from the public
API so large sends cannot take down the site or app.

## Goal

- Keep `https://astroroshni.com/api/*` on the main backend MIG
- Send Cloud Tasks nudge jobs to a **separate worker target**
- Keep the worker deployment backend-only and lighter-weight

## What changed in code

- Campaign dispatch now refuses to run when:
  - Cloud Tasks are enabled, and
  - `NUDGE_TASKS_TARGET_BASE_URL` still points at the public API host
- Daily scan, broadcast dispatch, chat-followup dispatch, admin bulk send, and
  campaign dispatch now queue onto the isolated worker instead of running inside
  the public API process
- Campaign queue defaults are now more conservative:
  - `NUDGE_CAMPAIGN_BATCH_SIZE=50`
  - campaign queue name defaults to `nudge-campaign-queue`

## Recommended topology

1. **Main API MIG**
   - serves app + web API traffic
   - existing load balancer target

2. **Nudge worker MIG**
   - not on the public load balancer
   - reachable only from Cloud Tasks / internal network / IAP
   - runs the same backend codebase
   - no local frontend

3. **Cloud Tasks queues**
   - standard queue for coordinator jobs and per-user chat follow-ups
   - campaign queue for campaign batches

## Worker VM startup

Use:

- [infra/gcp/astroroshni-nudge-worker-startup.sh](/Users/tarunydv/Desktop/Code/AstrologyApp/infra/gcp/astroroshni-nudge-worker-startup.sh)

This startup path:

- syncs repo + secrets
- skips frontend serving
- defers frontend build
- starts a smaller backend footprint:
  - `UVICORN_WORKERS=1`
  - `UVICORN_LIMIT_CONCURRENCY=100`

## Required env for safe campaign dispatch

Set these in production secrets/env:

```env
NUDGE_TASKS_ENABLED=true
NUDGE_CAMPAIGN_REQUIRE_TASKS=true
NUDGE_CAMPAIGN_REQUIRE_ISOLATED_WORKERS=true

NUDGE_TASKS_PROJECT=tradebest-465307
NUDGE_TASKS_LOCATION=asia-south1
NUDGE_TASKS_SECRET=...

NUDGE_TASKS_TARGET_BASE_URL=https://<worker-hostname-or-worker-lb>
NUDGE_TASKS_QUEUE=nudge-standard-queue
NUDGE_CAMPAIGN_TASKS_QUEUE=nudge-campaign-queue
NUDGE_CAMPAIGN_BATCH_SIZE=50
```

Important:

- `NUDGE_TASKS_TARGET_BASE_URL` must **not** be the public API host
- if it still points to `https://astroroshni.com`, campaign dispatch is blocked

## Queue settings

Create/update a dedicated campaign queue with conservative limits:

```bash
gcloud tasks queues create nudge-campaign-queue \
  --location=asia-south1 \
  --project=tradebest-465307
```

```bash
gcloud tasks queues update nudge-campaign-queue \
  --location=asia-south1 \
  --project=tradebest-465307 \
  --max-dispatches-per-second=1 \
  --max-concurrent-dispatches=5
```

Tune upward only after observing stable worker behavior.

Create/update the standard nudge queue as well:

```bash
gcloud tasks queues create nudge-standard-queue \
  --location=asia-south1 \
  --project=tradebest-465307
```

```bash
gcloud tasks queues update nudge-standard-queue \
  --location=asia-south1 \
  --project=tradebest-465307 \
  --max-dispatches-per-second=1 \
  --max-concurrent-dispatches=3
```

## Suggested rollout

1. Provision worker MIG / worker host
2. Deploy worker startup script
3. Point `NUDGE_TASKS_TARGET_BASE_URL` to worker host
4. Create `nudge-standard-queue`
5. Create `nudge-campaign-queue`
6. Set `NUDGE_TASKS_QUEUE=nudge-standard-queue`
7. Set `NUDGE_CAMPAIGN_TASKS_QUEUE=nudge-campaign-queue`
8. Create/update Cloud Scheduler jobs so they hit the public cron endpoints only
9. Verify one small campaign and one small chat-followup run
10. Resume queue(s)

## Validation

Before resuming:

```bash
curl -fsS https://astroroshni.com/api/health
curl -fsS https://<worker-hostname-or-worker-lb>/api/keepalive
```

Then send a tiny campaign to 1-5 users and verify:

- public API stays healthy
- public cron endpoints return quickly with `queued: true`
- worker handles `/api/nudge/internal/tasks/campaign-batch`
- worker handles `/api/nudge/internal/tasks/daily-scan`
- worker handles `/api/nudge/internal/tasks/chat-followup-dispatch`
- worker handles `/api/nudge/internal/tasks/broadcast-dispatch-due`
- admin campaign stats update normally

## Emergency rollback

If anything looks wrong:

1. Pause the campaign queue
2. Leave the main API queue/live site untouched
3. Fix worker target / concurrency before retrying
