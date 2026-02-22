# Nudge Engine

Daily notification engine: scans astrology triggers and sends nudges (stored + push) to drive chat/credit usage.

## Flow

1. **Scan** — Run all registered triggers for a date (e.g. today). Each trigger returns zero or more `NudgeEvent`s.
2. **Dedupe** — Global events (`user_ids=None`) are expanded to all users; each user gets at most one nudge per day (highest priority).
3. **Delivery** — For each user: if they have a registered device token, the nudge is sent via **Expo Push API**; it is always stored in `nudge_deliveries` (channel `push` or `stored`).

## How notifications are sent

- **Backend** uses the [Expo Push API](https://docs.expo.dev/push-notifications/sending-notifications/): `POST https://exp.host/--/api/v2/push/send` with `to` (Expo push token), `title`, `body`, `data`. No FCM/APNs keys needed on the server when using Expo.
- **Device tokens** are saved when the app calls `POST /api/nudge/device-token` with `{ "token": "ExponentPushToken[...]", "platform": "ios"|"android" }` (authenticated).
- When the daily scan runs, for each nudge we look up `device_tokens` by userid and send one push per token via Expo; we always insert a row in `nudge_deliveries` (channel `push` if any push was sent, else `stored`).

## What the app must do

1. **Install** `expo-notifications`.
2. **Request permissions** and get the Expo push token (e.g. `getExpoPushTokenAsync()`).
3. **After login**, call `POST /api/nudge/device-token` with the token and `platform: Platform.OS`.
4. (Optional) Handle notification tap (e.g. open chat via `data.cta` deep link).

## Triggers (current)

- **planet_transit_sign** — Planet enters a new sign (Sun, Mars, Mercury, Jupiter, Venus, Saturn). Uses Swiss Ephemeris, Lahiri ayanamsa.
- **lunar_phase** — Full Moon (Purnima) or New Moon (Amavasya) day. Sun–Moon elongation at noon UT; one nudge per phase.
- **planet_retrograde** — Planet turns retrograde or direct (station). Mercury, Venus, Mars, Jupiter, Saturn; compares daily motion vs previous day.
- **festival** — Hindu festivals on the date (amanta calendar, default India). One nudge per festival; major festivals have higher priority for dedupe.

## Adding triggers

1. Implement a class in `triggers/` that extends `TriggerBase` and implements `get_events(date) -> List[NudgeEvent]`.
2. Register it in `trigger_registry.py`.

## Scheduling the daily scan

`POST /api/nudge/scan` has **no auth** (so only expose it on a URL that only your scheduler can reach, or add a secret header).

**Option 1: System cron (server where the backend runs)**

Run once per day (e.g. 9:00 AM server time):

```bash
0 9 * * * curl -s -X POST "https://astroroshni.com/api/nudge/scan" > /dev/null 2>&1
```

Add to crontab: `crontab -e` and paste the line. Use your real backend URL.

**Option 2: External cron service**

Use [cron-job.org](https://cron-job.org), [EasyCron](https://www.easycron.com), or similar:

- **URL:** `https://astroroshni.com/api/nudge/scan`
- **Method:** POST
- **Schedule:** Daily at the desired time (e.g. 9:00 AM in your timezone)

**Option 3: GitHub Actions (if you host elsewhere)**

Add a workflow that runs on schedule and calls your API (use a secret for the URL or an API key if you add one):

```yaml
# .github/workflows/nudge-scan.yml
name: Nudge scan
on:
  schedule:
    - cron: '0 4 * * *'   # 4 AM UTC daily
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -s -X POST "https://astroroshni.com/api/nudge/scan"
```

**Optional: protect the endpoint**

To avoid random hits triggering the scan, add a secret header (e.g. `X-Cron-Secret: your-secret`) in the route and in your cron request, and reject requests without it.

## API

- `POST /api/nudge/scan` — Run the scan for today (or `?scan_date=YYYY-MM-DD`). Returns `{ date, events_found, users_targeted, delivered, error? }`. No auth; intended for cron.
- `POST /api/nudge/device-token` — Register push token (body: `{ token, platform }`). Requires auth.
- `POST /api/nudge/admin/send` — **Admin only.** Send an arbitrary notification to a user. Body: `{ "user_id": int, "title": str, "body": str }`. Returns `{ ok, sent, tokens_found, message }`. Use from admin UI: select user (by user_id), enter title and body.

## DB

- **device_tokens** — userid, token, platform (ios/android). One row per user per platform.
- **nudge_deliveries** — userid, trigger_id, title, body, sent_at, channel (push | stored).

Tables are created on first scan or first device-token call if missing.
