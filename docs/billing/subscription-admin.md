# Subscription billing visibility

Admin → Credits → Subscriptions combines Razorpay and Google Play subscriptions, including provider subscriptions without a linked membership. Plan configuration remains under Plan settings. Activity includes both providers, with a separate unresolved-event filter.

Billing status, auto-renew, next charge and access expiry are separate fields. Unknown provider state is explicitly unverified. Cancelled subscriptions have no next charge; existing paid membership access is preserved. Timestamps display in IST.

## Persistence and recovery

`subscription_billing_state` stores allowlisted provider snapshots. `subscription_lifecycle_events` durably records Razorpay webhook intake before entitlement handling. Provider event IDs deduplicate deliveries; per-subscription advisory locks serialize processing. Older conflicting snapshots do not overwrite current state. A provider refresh does not suppress a delayed charged webhook that describes the same billing period/state.

Application cancellation requests record the authenticated user before contacting Razorpay. A failed or uncertain request stays visible. External webhook/recovered cancellations use actor `unknown`: API creation source is not evidence of who cancelled.

Legacy membership links are repaired only for one exact user/plan/paid-period match, accepting the existing UTC or IST date convention. Other unverified provider subscriptions block automatic linking. Reconciliation does not grant access, cancel subscriptions, charge customers or change access dates. Ambiguous matches remain under Needs attention.

Google Play purchase tokens remain server-side; the admin uses hashed references. Existing Play lifecycle logs are included in Activity. Provider reads update Play billing state without granting membership access.

## Rollout

Deploy the backend and frontend together through the normal release process. Both ledger tables/indexes are created idempotently by the backend. No existing tables are dropped or rewritten.

The reconciliation task starts after 60 seconds, scans up to 20 overdue provider records per batch, and waits nine minutes between batches. Records are due for verification after six hours. A PostgreSQL transaction advisory lock limits batches to one process across instances. Failed reads remain visible and get retried. Set `SUBSCRIPTION_RECONCILIATION_ENABLED=false` to disable background checks; admin Check provider remains available. Provider records older than 24 hours are flagged.

After release, confirm Subscriptions and Activity load; search `sub_TZah63sNOKEk8h`; verify cancelled billing, no next charge, preserved access and a recovered cancellation at 2026-09-20 17:26:06 IST. Check Needs attention for unlinked or stale records. Provider API access is required for periodic verification.

## Production repair performed 2026-09-20

Verified Razorpay's three mapped subscriptions for user 435, plan 8. Two remained `created` with zero payments; `sub_TZah63sNOKEk8h` was cancelled with one paid period. Repaired membership 799's missing Razorpay linkage and cancellation flag. Membership remained active with its existing end date `2026-10-08 00:00:00`. Recorded the recovered cancellation with its provider timestamp and unknown actor. No provider mutations were made. This database repair does not deploy the new admin UI or webhook handlers.

## Verification

From `backend`, run:

```sh
RUN_SUBSCRIPTION_DB_TESTS=1 .venv/bin/python -m pytest tests/test_subscription_ledger.py tests/test_astrologer_subscription_entitlements.py tests/test_google_play_subscription_recovery.py -q --tb=short
```

The database tests require a local PostgreSQL DSN and create/drop only a disposable `test_billing_*` schema. They cover exact-period recovery, ambiguous links, cancellation deduplication, stale events, delayed payment webhooks, failed-event retry, resolved alerts, token redaction and admin authorization.

From `frontend`, build with `GENERATE_SOURCEMAP=false BUILD_PATH=/tmp/astroroshni-subscription-admin-build npx craco build`. No backend server is required for these checks.
