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
- [x] Manage Razorpay Astrologer License cancellation inside the authenticated app/PWA instead of opening an unauthenticated web purchase page.
- [x] Separate the live backend/chat rollout from baked-image preparation so production becomes visibly ready for testing before future-VM artifacts finish.
- [x] Add deterministic English/Hindi FOMO teasers from resolved whole-chart manifestations without exposing houses, planets, dashas, dates, or the full outcome.
- [x] Persist versioned Parashari prediction snapshots and ownership-safe teaser/funnel records with expiry, invalidation, and a six-day display cooldown.
- [x] Present all non-overlapping resolved chart themes in the app/PWA homepage prompt arbiter, deduplicated by rendered copy and constituent life-area overlap per person, then grouped and labelled for Self, Spouse, Mother, or Father.
- [x] Replace per-card FOMO impression request fan-out with bounded batch persistence and server-side serialization for legacy clients, preventing analytics from exhausting the API database pool.
- [x] Replace generic “several connected areas” FOMO copy with explicit broad areas—finance, relationship, property, family, and so on—for Self and relatives while keeping the exact event concealed.
- [x] Add theme-aware accessible FOMO tone colors; challenging copy uses high-contrast coral on dark purple while retaining semantic red in light mode.
- [x] Build FOMO area labels from the actual derived houses for each subject instead of reusing generic event-domain copy; e.g. native H8 is Spouse H2 but Mother H5.
- [x] Make the homepage FOMO sheet direct: “Your chart shows what may happen next,” with concise English/Hindi copy inviting users to explore active areas for themselves and family.
- [x] Remove “Don’t show these again” from FOMO and stop historic accidental opt-outs from suppressing future eligible presentations; retain “Not now” and cooldown controls.
- [x] Add a permanent localized “What’s active in your chart?” homepage card below the ticker, with chart-derived area previews and access to every current FOMO theme.
- [x] Coordinate homepage prompts per account: show the free-question modal once, monthly events every 15 days, defer FOMO until the next session or 12 hours after the free prompt, repeat unchanged FOMO after 7 days, and allow changed sets after a 48-hour quiet period.
- [x] After a user dismisses the FOMO sheet, check Android notification permission and show a localized contextual opt-in explaining that AstroRoshni can alert them before important chart periods unfold; skip it after permission is granted and when they continue to chat.
- [x] Isolate homepage FOMO from critical API capacity with a dedicated two-thread executor, a two-request admission gate, and one serialized auxiliary DB slot per worker; cap the feature at three of four pooled connections and retain capacity until timed-out synchronous work actually finishes.
- [x] Prevent duplicate cross-worker FOMO calculations with database-backed expiring generation leases and a cache recheck after lease acquisition.
- [x] Throttle expired FOMO cleanup to once per hour per worker and bulk-insert teaser rows to minimize database connection hold time.
- [x] Hand clicked FOMO themes to a dedicated no-clarification chat mode using server-owned manifestation evidence, while preserving Premium/Standard selection and skipping the mode chooser.
- [x] Retain normal ChatContextBuilder guardrails in FOMO chat while preventing past dasha boundaries from being described as new transitions.
- [x] Keep FOMO temporal and evidence-scope enforcement language-neutral without post-processing generated prose.
- [x] Replace the general FOMO chat question with a current/upcoming manifestation-and-timing question and add a focused Parashari MD–AD–PD response schema without changing normal chat.
- [x] Upgrade FOMO chat to synthesize ranked human event scenarios across coherent active-house pairs, triples, and full clusters while deterministic evidence continues to control scope, timing, and tone.
- [x] Put both the homepage chart-theme card and automatic FOMO bottom sheet behind an admin feature flag with an optional user-ID allowlist; an empty allowlist enables all users only when the master switch is on.
- [x] Replace per-key admin-setting queries with a single-flight atomic snapshot cache, stale-on-database-error reads, transactional global versioning, and cross-worker invalidation.
- [x] Record remedy-card exposure only once per user/day instead of once per remedy-bearing answer, with persistent app/PWA deduplication and server normalization for older clients.
- [x] Move remedy-funnel table/index creation to runtime migration and backend startup, use signed JWT user IDs for best-effort analytics, and skip unavailable analytics without an ASGI error.
- [x] Add a bounded PostgreSQL pool-acquisition wait and pool-occupancy timeout logging so brief fifth-request spikes do not fail immediately.

### Validation

- [x] Android Expo production bundle completed successfully.
- [x] PWA production build and SEO post-build completed successfully.
- [x] Astrologer entitlement and subscription-family backend regression tests passed.
- [x] Production Astrologer subscription schema applied and entitlement/plan resolution verified.
- [x] Parashari FOMO migration applied and end-to-end local snapshot generation/reload verified.
- [x] FOMO/prediction regression suite passed and Android/PWA production bundles compiled.
- [x] Trusted FOMO-to-chat evidence, intent, and prompt-contract tests passed; PWA production export compiled.
- [x] Full backend test suite passed after the admin-settings cache and cross-worker invalidation change.
- [x] Remedy-funnel/pool regressions passed; full backend suite, PWA export, legacy frontend build, and SEO post-build completed.
- [ ] Physical Android device smoke test.
- [ ] Installed PWA smoke test.
- [ ] Release build uploaded to Play Console.
