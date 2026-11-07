# Reel cost accounting

New runs record every paid operation before sending it to the provider, including storyboard planning, repair, presenter-line rewriting, images, TTS, and Omni opening/closing clips. Responses settle the same event; retries create separate events. Image usage is captured before decoding the asset. A timeout, process crash, missing usage, or unknown model rate remains **unknown**, never a confirmed zero. Successful parallel requests finish and settle even if another scene fails. Provider request IDs are retained where returned; prompts, audio and images are not copied into the ledger.

## Admin setup

Admin → Reel Generation Costs → Cost assumptions and additional charges:

- Set USD/INR to the billing conversion rate. The initial ₹95 value is a budget assumption.
- Set effective tax and payment/FX fee percentages from billing. Fees apply after tax. These are effective blended estimates, not a tax calculation by jurisdiction/provider.
- Set worker INR/second to the allocated server cost per active job, including idle provider wait, disks, queue overhead and shared capacity. Do not use the full machine price for each concurrent job.
- Set storage INR/GiB/month, storage write cost, upload transfer cost and the number of storage months to budget. Local intermediate assets are part of the worker/disk allocation; final output and GCS cover sizes are measured separately.
- Leave unknown rates blank. Enter zero only for an explicitly free/included category.

Settings are snapshotted when planning starts, so later changes do not silently reprice existing runs. Provider token rates and component quantities are saved on each cost event. Unknown/changed model IDs require a rate entry in `backend/reel_studio/costs.py` and are otherwise unpriced.

Image costs include text input, reference-image input and output tokens. Low quality does not make input tokens free. Direct Images API calls do not use cached-input pricing. OpenAI reasoning tokens are included in output tokens and are not charged twice. TTS uses the exact cleaned string sent to Google (Unicode characters including spaces), with the selected voice family's rate. SDK-level retries are disabled for text/TTS; explicit image transport retries have their own ledger entries.

## Meaning of totals

- **Known cost estimate**: usage multiplied by recorded rates and FX, plus configured compute, storage, tax and fees. Incomplete runs are visibly marked partial.
- **Complete estimate**: all recorded operations have usage and configured rates; this is still not an invoice.
- **Invoice confirmed**: an admin enters an allocated all-in INR total and invoice/allocation reference. This is append-only, retains usage evidence, and is invalidated if the usage ledger changes afterward.

Future playback/download traffic, account-wide free tiers, provider discounts/credits and shared cloud billing cannot be known from generation responses. Reconcile those from invoices; do not manufacture per-run actual costs. Storage is a fixed planning horizon, not ongoing metering. A configured zero is distinguishable from unknown.

Old runs retain their recorded estimates and are flagged incomplete because previously discarded input/planning usage cannot be reconstructed. No historical usage is invented. Failed/abandoned planning attempts now appear even without a render job. User credit debits/refunds remain independent of provider spend.

## Deployment and verification

The existing Reel Studio schema initializer creates three additive tables: `reel_cost_runs`, `reel_cost_settings`, `reel_cost_reconciliations`. Existing cost rows and media are preserved. Deploy backend and admin frontend together after testing. No API secrets are added to admin.

Tests: `backend/.venv/bin/python -m pytest` from backend with `tests/test_reel_costs.py`, planner, presenter, audio, billing and thumbnail tests. The accounting suite covers cached tokens, image inputs, exact TTS characters, Omni components, retries, partial failures, concurrency, rate snapshots, failed draft visibility and reconciliation.

Rate sources checked 2026-11-07:
- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://ai.google.dev/gemini-api/docs/pricing
- https://cloud.google.com/text-to-speech/pricing
