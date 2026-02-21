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

- **planet_transit_sign** — Planet enters a new sign (Sun, Mars, Mercury, Jupiter, Venus, Saturn). Uses Swiss Ephemeris, Lahiri ayanamsa; same logic as `transits/routes.get_monthly_transits`.

## Adding triggers

1. Implement a class in `triggers/` that extends `TriggerBase` and implements `get_events(date) -> List[NudgeEvent]`.
2. Register it in `trigger_registry.py`.

## API

- `POST /api/nudge/scan` — Run the scan for today (or `?scan_date=YYYY-MM-DD`). Returns `{ date, events_found, users_targeted, delivered, error? }`.
- `POST /api/nudge/device-token` — Register push token (body: `{ token, platform }`). Requires auth.
- `POST /api/nudge/admin/send` — **Admin only.** Send an arbitrary notification to a user. Body: `{ "user_id": int, "title": str, "body": str }`. Returns `{ ok, sent, tokens_found, message }`. Use from admin UI: select user (by user_id), enter title and body.

## DB

- **device_tokens** — userid, token, platform (ios/android). One row per user per platform.
- **nudge_deliveries** — userid, trigger_id, title, body, sent_at, channel (push | stored).

Tables are created on first scan or first device-token call if missing.
