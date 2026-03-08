# Testing credits & subscriptions locally with Android emulator

You can run the app in the **Android emulator** against your **local backend** to test balance, subscription plans (with Google Play prices), refresh subscription status, and—with a Play Store image—in-app purchases.

## 1. Point the app to your machine

In **`astroroshni_mobile/src/utils/constants.js`** set:

```js
const USE_DEV_API = true;   // was false
```

Leave `DEV_API_HOST` empty. In dev, the app will use:

- **Android emulator**: `http://10.0.2.2:8001` (emulator’s alias for your host)
- **iOS simulator**: `http://localhost:8001`

Remember to set `USE_DEV_API = false` again before building for production.

## 2. Run the backend locally

From the **backend** directory:

```bash
cd backend
export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=/path/to/your/service-account.json
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

- `--host 0.0.0.0` lets the emulator (and other devices on your LAN) reach the server.
- Port **8001** must match what the app uses (see above).
- For **subscription plans with correct prices**, the backend needs access to Google Play (same service account used in production). If the env var is missing or invalid, plans still load but `formatted_price` may be null and the app falls back to DB/iap price.

Optional: use a local DB so you don’t touch production data (e.g. point to a copy of `astrology.db` or set the path your app expects).

## 3. Run the app on the emulator

```bash
cd astroroshni_mobile
npx react-native run-android
```

Use an AVD that has the **Google Play** system image if you want to test real in-app purchases; for balance, subscription list, and “Refresh subscription status” any Android emulator is enough.

## 4. What you can test

| Feature | Works on any emulator | Needs Play Store image + license tester |
|--------|------------------------|------------------------------------------|
| Login / register | ✅ | - |
| Balance, history, subscription details | ✅ | - |
| Subscription plans list (with prices from Play when backend has credentials) | ✅ | - |
| “Refresh subscription status” button | ✅ | - |
| Actual subscription / IAP purchase | - | ✅ |

For **real purchases** in the emulator: add your test Google account as a **license tester** in Play Console (Setup → License testing), use an AVD with **Google Play** (not “Google APIs” only), and sign in on the emulator with that account. Test purchases will not be charged.

## 5. Troubleshooting

- **App can’t reach backend**: Ensure backend is bound to `0.0.0.0:8001` and firewall allows it. On Android emulator the app uses `10.0.2.2`, not your machine’s IP.
- **Subscription prices missing**: Backend needs a valid `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` with access to the app’s subscription products in Play Console.
- **CORS**: If you hit CORS from a browser or another origin, the FastAPI app may need to allow that origin; the mobile app typically does not send a browser Origin.
