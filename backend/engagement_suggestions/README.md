# Engagement suggestions

This package stores one evidence-backed question opportunity and prepares
channel-specific copy for Chat, push, WhatsApp, SMS, email, and the in-app
inbox. It does not send notifications and is not connected to ChatScreen yet.

## Sources

- `chat_followup`: copies the follow-up questions already returned with a
  completed chat answer. It never makes another LLM request.
- `monthly_manifestation`: takes activated houses from the Prediction Engine
  or qualified Event Timeline candidates and resolves them through the same
  shared Manifestation KG used by Event Timeline.
- `kp_daily`: sends KP houses giving results through that same Manifestation
  KG. KP is always called with `synthesize=False` by the refresh worker.

## When work runs

Use event-driven writes for normal traffic:

1. A completed chat answer stores its follow-ups immediately and queues that
   chart for monthly and KP refresh.
2. A newly saved Parashari activation snapshot resolves its house combinations
   through the shared Manifestation KG and stores those deterministic questions.
3. `/api/kp/fructification` stores daily questions when `birth_chart_id` is
   supplied and belongs to the caller.
4. A completed Event Timeline stores only candidates carrying explicit
   `manifestation_kg` identity and deterministic evidence-gate metadata.

Use cron as bounded preparation and repair rather than an all-user calculation:

- Every 15 minutes: `POST /api/engagement-suggestions/cron/repair` imports any
  stored chat/FOMO rows missed by event-driven hooks and expires stale rows.
- Daily before notification delivery:
  `POST /api/engagement-suggestions/cron/schedule-notification-refreshes`
  queues charts for users who explicitly enabled astrology alerts and at least
  one channel.
- Every 5 minutes on the worker service:
  `POST /api/engagement-suggestions/cron/process-due?limit=2` processes a small
  batch. The low bound protects the notification worker from chart-calculation
  bursts.

All cron endpoints require `X-Cron-Secret: NUDGE_CRON_SECRET`. Multiple workers
are safe because queue claims use `FOR UPDATE SKIP LOCKED` and a lease.

## API prepared for later clients

- `GET /api/engagement-suggestions`
- `POST /api/engagement-suggestions/interactions`
- `POST /api/engagement-suggestions/refresh`
- `GET|PUT /api/engagement-suggestions/preferences`

The mobile app deliberately does not call these endpoints yet.
