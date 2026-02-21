# Notification (Nudge) Engine — Architecture

**Goal:** A daily-running engine that scans for astrology-based triggers and sends nudges to users to encourage chat (and credit usage). Triggers are extensible: transits, Bhrigu Bindu, Pushkara Navamsa, Moon Tara Bala, etc.

---

## 1. High-level flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHEDULER (e.g. daily 06:00 UTC or per-timezone windows)                │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIGGER SCAN                                                            │
│  For each registered trigger type:                                       │
│    → Compute "events" for today (global and/or per-user)                 │
│    → Output: list of (trigger_id, user_id?, event_params, message)     │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DEDUPE & CAP                                                            │
│  Per user: max N nudges per day, prefer "best" trigger (e.g. personal)   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DELIVERY                                                                │
│  Push (FCM/APNs) and/or in-app inbox / badge                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core concepts

### 2.1 Trigger type (extensible)

A **trigger type** is a pluggable unit that:

1. **Decides what “event” means** for a given date (and optionally for a given user).
2. **Determines which users** are eligible (e.g. “all with birth data”, “users whose Mars is in X”).
3. **Produces a nudge payload**: title, body, optional deep-link (e.g. open Chat).

**Examples:**

| Trigger ID | Description | Scope | Needs birth chart? |
|------------|-------------|--------|--------------------|
| `planet_transit_sign` | Planet X enters sign Y today | Global or per-user (e.g. “Mars enters your 7th house”) | Optional (personalized) |
| `bhrigu_bindu_transit` | A planet transits over native’s Bhrigu Bindu | Per-user | Yes |
| `pushkara_navamsa_entry` | Planet enters Pushkara Navamsa | Per-user | Yes (D9) |
| `moon_tara_bala` | Moon Tara Bala strong / significant today | Per-user | Yes |
| `sade_sati_phase_change` | Saturn moves to next phase of Sade Sati | Per-user | Yes |
| `dasha_change` | User enters new Antar/Maha dasha | Per-user | Yes |
| `retrograde_station` | Mercury/Mars/Jupiter etc. turns retrograde/direct | Global | No |
| `eclipse` | Solar/Lunar eclipse | Global | Optional (personalized by chart) |

New triggers = new handler in the registry; no change to scheduler or delivery.

### 2.2 Event

An **event** is one concrete occurrence that can generate a nudge:

- **Global event:** e.g. “Mars entered Gemini on 2025-03-15”. All users (or a segment) can get the same message, or we personalize (“Mars in your 7th house”) for users with birth data.
- **Personal event:** e.g. “Saturn is transiting your Bhrigu Bindu this week”. Only that user gets it; message is inherently personal.

Output of the trigger scan: list of **events**, each with `trigger_id`, `user_id` (or null for “all”), `event_params` (planet, sign, house, dates, etc.), and **message** (title + body + optional CTA).

### 2.3 Nudge

A **nudge** is the decision to send one notification to one user on one day. After dedupe/cap, we have a list of nudges. Each nudge has: `user_id`, `title`, `body`, `cta_url` (e.g. `astroroshni://chat`), `trigger_id`, `event_params` (for analytics).

---

## 3. Data model (minimal)

### 3.1 Tables (backend)

- **users** (existing): id, email, etc.
- **birth_profiles** (existing): user_id, birth date/time/place, chart_id. Needed to evaluate per-user triggers.
- **device_tokens** (new): user_id, token, platform (ios|android), updated_at. For push delivery.
- **nudge_events** (new, optional): id, trigger_id, event_date, event_params (JSON), global vs per-user. Useful for idempotency and “already sent this event?”
- **nudge_deliveries** (new): id, user_id, trigger_id, event_id (optional), title, body, sent_at, channel (push|in_app). For cap (“max 1 per user per day”) and analytics.

### 3.2 Trigger registry (in code)

```python
# Pseudocode
TRIGGERS = {
    "planet_transit_sign": PlanetTransitSignTrigger(),
    "bhrigu_bindu_transit": BhriguBinduTransitTrigger(),
    "pushkara_navamsa_entry": PushkaraNavamsaTrigger(),
    "moon_tara_bala": MoonTaraBalaTrigger(),
    # ...
}
```

Each trigger implements an interface, e.g.:

```python
class TriggerBase:
    def get_events(self, date: date) -> List[Event]:
        """Return list of events for this date. Event = trigger_id, user_ids (or None for 'all'), params, message."""
        raise NotImplementedError
```

Some triggers need **global** computation first (e.g. “Mars enters Gemini today”), then optionally **personalize** for each user with a chart. Others are **per-user only** (e.g. Bhrigu Bindu: for each user with birth data, compute “is any planet on Bhrigu Bindu today?”).

---

## 4. Daily pipeline (detail)

### Step 1: Run scheduler

- **When:** e.g. once per day at 06:00 UTC, or split by timezone (e.g. 08:00 local) so users get the nudge in the morning.
- **How:** Cron calling an HTTP endpoint, or Cloud Scheduler → Cloud Function / backend job. Backend endpoint: `POST /internal/jobs/run-nudge-scan` (protected by API key or internal only).

### Step 2: Trigger scan

- For **today** (or “tomorrow” if we want to send “Mars enters Gemini tomorrow”):
  - For each trigger in the registry, call `trigger.get_events(today)`.
  - Each trigger uses existing backend logic where possible:
    - **Transit:** use `real_transit_calculator` or transit APIs to get “planet X enters sign Y on date D”.
    - **Bhrigu Bindu:** compute Bhrigu Bindu for each user’s chart; get transiting planets’ positions; see if any planet is conjunct (e.g. within 1°).
    - **Pushkara Navamsa:** use `pushkara_calculator` + D9 chart; check if any transiting planet enters a Pushkara navamsa today.
    - **Moon Tara Bala:** use existing Tara Bala logic; if Moon’s Tara Bala is high or crosses a threshold, emit event for affected users.
  - Collect all events: `[(trigger_id, user_id or None, params, title, body), ...]`.

### Step 3: Resolve “user_id or None”

- For events with `user_id = None` (global), optionally expand to a list of user_ids: e.g. “all users with push enabled” or “all users with birth data” for personalized message. If we don’t personalize, we can send the same message to everyone.

### Step 4: Dedupe and cap

- **Per user:** Keep at most **1 nudge per day** (or 2 if you want to test). If multiple events apply to the same user, choose one (e.g. prefer “personal” over “global”, or prefer a priority order by trigger_id).
- **Idempotency:** If we store `nudge_deliveries` by (user_id, date), we can skip users who already received a nudge today.

### Step 5: Delivery

- **Push:** For each nudge, look up `device_tokens` for that user, send via FCM (Android) / APNs (iOS). Use Expo Push if the app is Expo.
- **In-app:** Save to an `in_app_notifications` table or feed so the app can show “You have 1 new nudge” and open Chat when tapped.
- **Optional:** Only send push to users who have **push enabled** and **credits > 0** (or allow even with 0 to nudge them to buy).

---

## 5. Trigger interface (contract for “any number of events”)

So that new triggers don’t require changing the pipeline:

```python
# Optional: event schema for consistency
class NudgeEvent:
    trigger_id: str
    user_ids: Optional[List[int]]  # None = "all" or "expand later"
    params: Dict[str, Any]          # e.g. {"planet": "Mars", "sign": "Gemini", "house": 7}
    title: str
    body: str
    cta_deep_link: str = "astroroshni://chat"
    priority: int = 0               # higher = prefer when deduping

class TriggerBase(ABC):
    @abstractmethod
    def get_events(self, date: date) -> List[NudgeEvent]:
        pass
```

**Adding a new trigger:** Implement `TriggerBase`, register in `TRIGGERS`, and (if needed) add any new calculator or reuse existing ones (chart, transit, pushkara, etc.).

---

## 6. Example: “Planet transiting to a sign”

- **Global:** Ephemeris or transit API → “On 2025-03-15, Mars enters Gemini.”
- **Event:** trigger_id=`planet_transit_sign`, user_ids=`None`, params=`{planet: Mars, sign: Gemini}`, title=`Mars enters Gemini`, body=`See how this transit affects you. Ask in chat!`
- **Personalized variant:** For each user with birth data, compute “Mars transiting which house?” (e.g. 7th). Event: user_ids=`[u1,u2,...]`, body=`Mars is transiting your 7th house. Ask in chat what this means for you.`

---

## 7. Example: “Planet passing over Bhrigu Bindu”

- **Per-user:** Load users with birth charts. For each:
  - Compute Bhrigu Bindu (longitude) for the chart.
  - Get transiting planets’ longitudes for today.
  - If any planet within ~1° of Bhrigu Bindu → emit event for that user.
- **Event:** trigger_id=`bhrigu_bindu_transit`, user_ids=`[u1]`, params=`{planet: Saturn, orb: 0.5}`, title=`Saturn on your Bhrigu Bindu`, body=`A significant transit. Chat to explore its meaning.`

---

## 8. Example: “Planet entering Pushkara Navamsa”

- Use existing `pushkara_calculator` + D9. For each user with chart:
  - Get D9 positions; which navamsas are Pushkara.
  - Get transiting planet positions in D9 for today.
  - If a transiting planet enters a Pushkara navamsa today → event for that user.
- **Event:** trigger_id=`pushkara_navamsa_entry`, user_ids=`[u1]`, params=`{planet: Jupiter}`, title=`Jupiter enters Pushkara Navamsa`, body=`A favorable period. Ask in chat for details.`

---

## 9. Where to implement (in your repo)

- **Backend (Python):**
  - `backend/notifications/` or `backend/nudge_engine/`:
    - `trigger_base.py` — interface and `NudgeEvent`.
    - `triggers/planet_transit_sign.py`, `triggers/bhrigu_bindu.py`, `triggers/pushkara_navamsa.py`, `triggers/moon_tara_bala.py`, etc.
    - `trigger_registry.py` — `TRIGGERS` dict.
    - `scanner.py` — run all triggers for a date, return list of events.
    - `dedupe.py` — cap per user, choose one nudge.
    - `delivery.py` — push (FCM/Expo) and/or write to in-app feed.
  - `backend/main.py` or `backend/jobs/` — HTTP endpoint or cron target: `run_nudge_scan(date=today)`.
- **DB migrations:** Add `device_tokens`, `nudge_deliveries`, optionally `nudge_events`.
- **Mobile app:** Register for push (Expo Push or FCM), send token to backend; optional “Notifications” or “Nudges” screen reading from in-app feed.

---

## 10. Summary

| Piece | Purpose |
|-------|--------|
| **Scheduler** | Run once per day (or per timezone). |
| **Trigger registry** | Pluggable list of trigger types (transit, Bhrigu Bindu, Pushkara, Tara Bala, …). |
| **Trigger interface** | `get_events(date) → List[NudgeEvent]`; each event has user_ids, message, params. |
| **Scanner** | Runs all triggers, collects events. |
| **Dedupe/cap** | One nudge per user per day (or small N). |
| **Delivery** | Push + optional in-app feed; deep-link to Chat. |
| **Data** | device_tokens, nudge_deliveries (and optional nudge_events). |

This gives you an extensible notification engine: add new astrology triggers by implementing one class and registering it, without changing the daily scan or delivery pipeline.
