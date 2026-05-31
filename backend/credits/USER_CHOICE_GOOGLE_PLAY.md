# Google Play User Choice + Razorpay (India)

This app reports external (Razorpay) transactions to Google Play when the user picks **alternative billing** in the Play Billing user-choice flow.

## Backend

- **Credits:** `POST /api/credits/razorpay/create-order` accepts optional `google_play_external_transaction_token` (stored on the Razorpay order). After successful `POST /api/credits/razorpay/verify` (or `payment.captured` webhook), the server calls Google Play `externalTransactions.create` when that token is present.
- **Subscriptions:** same token on `POST /api/credits/razorpay/subscription/create` (subscription notes) and `POST /api/credits/razorpay/subscription/verify`.

Implementation: `credits/play_external_transactions.py`.

### Environment variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` or `GOOGLE_SERVICE_ACCOUNT_KEY` | Service account with Android Publisher API access (same as existing Play verify). |
| `PLAY_EXTERNAL_TX_REGION_CODE` | ISO region for `userTaxAddress` (default `IN`). |
| `PLAY_EXTERNAL_TX_IN_ADMIN_AREA` | For India, Google recommends a state/UT code (e.g. `KARNATAKA`, `DELHI`). Set when you know the user’s tax region, or set a conservative default for reporting. |
| `RAZORPAY_GST_RATE` | Decimal GST rate used to split inclusive INR amounts into pre-tax + tax for reporting (default `0.18`). |

## Mobile

- `react-native-iap` **14.x** with `alternativeBillingModeAndroid: 'user-choice'`, `userChoiceBillingListenerAndroid`, `fetchProducts`, and `requestPurchase` for both one-time and subscriptions.
- **User-choice UI at purchase time** only appears if `initConnection({ alternativeBillingModeAndroid: 'user-choice' })` succeeds (app enrolled in Play user-choice / alternative billing for that track). If init fails twice, the client may fall back to `initConnection()` without user-choice so IAP still works — in that case logcat will show `IAP user-choice init failed (attempt 2); using Play-managed billing without user-choice`. The Credit screen registers **purchase + user-choice listeners before `initConnection`**, matching the official `useIAP` hook order.
- `react-native-razorpay` for checkout after the user confirms the in-app disclosure.
- **Expo `plugins`:** include **`react-native-iap`** only. Do **not** list `react-native-nitro-modules` as an Expo config plugin: the published npm package does not ship a working `app.plugin.js` on disk, so Expo can resolve the package `react-native` entry (`src/index.ts`) and Node will fail with `SyntaxError: Unexpected token 'typeof'`. Nitro is still installed and **autolinked** as a dependency of `react-native-iap`.

Run `npx expo prebuild` after dependency changes so native projects pick up Nitro + IAP + Razorpay.

### Gradle / `NODE_ENV`

If `:expo-constants:createExpoConfig` warns that `NODE_ENV` is unset, set it when invoking Gradle, for example:

`NODE_ENV=production ./gradlew bundlePlayRelease`
