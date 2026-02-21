# Testing Nudge + Push Before Production

## 1. Backend only (no device)

**Goal:** Confirm the nudge engine runs and writes to the DB.

1. **Start backend locally** (from repo root):
   ```bash
   cd backend
   python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Trigger a scan** (use a date when a planet changes sign, or any date to see “0 events”):
   ```bash
   # Today
   curl -X POST "http://localhost:8001/api/nudge/scan"

   # Specific date (e.g. one that has a transit)
   curl -X POST "http://localhost:8001/api/nudge/scan?scan_date=2025-03-15"
   ```

3. **Check response**  
   Example: `{"date":"2025-03-15","events_found":1,"users_targeted":5,"delivered":5,"error":null}`

4. **Check DB** (optional):
   ```bash
   cd backend
   sqlite3 astrology.db "SELECT id, userid, trigger_id, title, sent_at, channel FROM nudge_deliveries ORDER BY id DESC LIMIT 5;"
   ```

If you see rows and no `error`, the engine and delivery (DB write) work. Push is only sent when the user has a row in `device_tokens` (next step).

---

## 2. Point the app at your local backend

**Goal:** App talks to your machine so login and device-token registration hit local backend.

- **Simulator / emulator**
  - iOS Simulator: `http://localhost:8001`
  - Android Emulator: `http://10.0.2.2:8001`
- **Physical device (same Wi‑Fi)**  
  Use your machine’s LAN IP, e.g. `http://192.168.1.10:8001` (replace with your IP).
- **Physical device (any network)**  
  Use a tunnel, e.g. `ngrok http 8001` → use the `https://xxxx.ngrok.io` URL.

In **`astroroshni_mobile/src/utils/constants.js`**, temporarily set the API base URL:

```javascript
const getApiUrl = () => {
  // Local / dev testing
  if (__DEV__) {
    if (Platform.OS === 'ios') return 'http://localhost:8001';
    if (Platform.OS === 'android') return 'http://10.0.2.2:8001';
    // Physical device on same WiFi (replace with your machine IP):
    // return 'http://192.168.1.10:8001';
  }
  return 'https://astroroshni.com';
};
```

Or use an env / build flag so you don’t commit local URLs. Restart the app after changing this.

---

## 3. Get a push token and register it (local backend)

**Goal:** Your device gets an Expo push token and sends it to your local backend.

1. **Backend running** on 8001 (and app pointing to it as above).
2. **Run the app** on a **physical device** (push does not work in iOS Simulator / Android Emulator).
   - Development build: `npx expo run:ios` or `npx expo run:android`
   - Or Expo Go (iOS only for receiving push in many setups)
3. **Log in** with a user that exists in your local `astrology.db` (same DB the backend uses).
4. **Allow notifications** when the app asks.
5. **Confirm token was sent** to your backend:
   ```bash
   sqlite3 backend/astrology.db "SELECT userid, platform, substr(token,1,40) FROM device_tokens;"
   ```
   You should see one row per user/platform with an `ExponentPushToken[...]` prefix.

If you don’t see a row, check:
- App is really using the local API URL (login works against local backend).
- No 401/5xx in network tab for `POST /api/nudge/device-token`.
- Backend logs for that request.

---

## 4. End-to-end: trigger scan and see a push

**Goal:** Backend sends a nudge; device receives a push.

1. Backend running locally.
2. App on **physical device**, pointed at local backend, **logged in**, token already registered (step 3).
3. **Trigger the scan** for a date that has at least one transit (so there is an event):
   ```bash
   curl -X POST "http://localhost:8001/api/nudge/scan?scan_date=2025-03-15"
   ```
   Or use today if you know a planet changes sign today.

4. **Check**:
   - Response: `delivered` ≥ 1.
   - Device: a notification appears (title/body like “Mars enters Gemini…”).
   - DB: `nudge_deliveries` has a row for that user with `channel = 'push'`.

If no notification:
- Confirm that user has a row in `device_tokens` and the token looks like `ExponentPushToken[...]`.
- Backend must be able to reach `https://exp.host` (no firewall blocking).
- App in foreground: you should still see the notification (we set `shouldShowAlert: true`).

---

## 5. Test notification tap (open Chat)

1. Send a nudge (step 4) so a notification is on the device.
2. **Background or kill the app** (so the notification is in the tray).
3. **Tap the notification.**  
   App should open and navigate to **Home** (Chat screen).

If it doesn’t navigate, check that `setupNotificationResponseListener(navigationRef)` is running (App.js) and that the notification payload includes `data.cta` (backend sends `cta: "astroroshni://chat"`).

---

## 6. Staging (optional)

- Deploy backend to a **staging** host (e.g. `https://staging.astroroshni.com`).
- In the app, use a build or env that sets `API_BASE_URL` to that staging URL.
- Run the same flow: login → register token → trigger scan (e.g. `curl -X POST "https://staging.astroroshni.com/api/nudge/scan"`) → verify push and tap.

No change to Expo Push: tokens work the same against staging or prod; only the backend URL in the app changes.

---

## Quick checklist

| Step | What to verify |
|------|----------------|
| Backend scan | `POST /api/nudge/scan` returns no `error`, optional `events_found` ≥ 1 |
| DB deliveries | `nudge_deliveries` has rows after scan |
| App → local API | Login works with local/staging URL |
| Token registration | `device_tokens` has row for test user after login |
| Push received | Notification appears on device after scan |
| Tap → Chat | Tapping notification opens app and Home (Chat) |

---

## Finding a date with a transit (optional)

To get `events_found ≥ 1` when testing:

```bash
# Backend: list transits for a month
curl "http://localhost:8001/api/transits/monthly/2025/3"
```

Pick a `date` from the response and use it in `?scan_date=...`.
