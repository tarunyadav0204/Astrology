# Release Tracker

## Version 209

- Status: In progress
- App version: 1.2.4
- Android version code: 209
- Started: 2026-07-21

### Included changes

- [x] Fix the message copy button in the Android app by using the supported `expo-clipboard` native module.
- [x] Fix the message copy button in the PWA by adding a fallback for browsers that reject or do not expose the Clipboard API.
- [x] Show a visible error when copying fails instead of silently ignoring the failure.
- [x] Hide the Instant/Standard/Premium mode picker while the first free question is available and always send that question as Standard.
- [x] Restore the normal chat-mode picker after the free question is consumed.
- [x] Add a server-backed “Push enabled only” filter to Audience Builder user selection.
- [x] Add a PN-only campaign policy with no WhatsApp or email fallback.
- [x] Replace rolling-count guesses in Audience Builder with exact IST today/yesterday and paid-question facts.
- [x] Add a governed Data Explorer for cross-table business questions using live approved schemas, read-only SQL, sensitive-field blocking, timeouts, and 500-row limits.
- [x] Add the ₹100/month Astrologer License as a separate entitlement that can coexist with VIP.
- [x] Restrict Activation Explorer to licensed astrologers, with automatic access for admins.
- [x] Add Google Play, Android alternative-billing, Razorpay web/PWA purchase flows and family-specific subscription management.
- [x] Route unlicensed chart users to the focused Astrologer License purchase section and return them to Activation Explorer after activation.

### Validation

- [x] Android Expo production bundle completed successfully.
- [x] PWA production build and SEO post-build completed successfully.
- [x] Astrologer entitlement and subscription-family backend regression tests passed.
- [ ] Physical Android device smoke test.
- [ ] Installed PWA smoke test.
- [ ] Release build uploaded to Play Console.
