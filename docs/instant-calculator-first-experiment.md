# Calculator-first Instant experiment

The earlier path is active in the local backend `.env`: `INSTANT_CHAT_PATH=baseline`. The calculator-first experiment remains available through `instant_path: "calculator_first"` on an Instant request, or by setting `INSTANT_CHAT_PATH=calculator_first` and restarting the backend. An unset flag defaults to `baseline`, preserving the existing flow in other environments. It runs alongside the previous routed/calculated flow, selected with `instant_path: "baseline"` in an Instant `/ask` request or its `query_context`. The selected path is captured when the request is accepted and travels with the queued job.

## What runs

1. Retain authentication, chart/session ownership, billing, birth-input normalization and conversation history.
2. Skip the worker intent classifier, secondary answer-mode classifier, context-builder initialization, eager Instant evidence packet and deterministic knowledge graph. Do not merge the latest question into an abandoned clarification concern.
3. Send Luna the latest question, chart-owner birth inputs, user clock, recent conversation, and 49 registered calculators with typed input requirements. No calculated baseline is sent. Previously generated prediction anchors are excluded from confirmed user facts.
4. Execute only requested calculators. The three core adapters calculate natal foundation, strict Vimshottari periods and strict transit snapshots on demand. Other tools reuse the existing individual calculator adapters. Successful identical requests are cached within the turn; failures can be retried with corrected inputs.
5. Accept brief public progress findings only for successful calculations. Luna can request more tools, ask the user a focused clarification, or answer. There is **no calculator-round ceiling**. The request has a configurable wall-clock deadline of 360 seconds to fit the durable relay; timeout fails the turn rather than inventing an answer.
6. Deliver Luna's answer from the decision that actually answered. There is no additional final-writer model call. Progress arrives live while tools run; completed answer text is delivered when that model decision finishes.

Speech and Verified retain their existing paths. The existing routed Instant path remains available through the per-request override. `INSTANT_CHAT_CONVERSATION_ENABLED` still controls whether that baseline uses the calculator review agent or the older composer.

## Controls and measurements

- `INSTANT_CHAT_PATH=calculator_first|baseline` chooses the default for new Instant requests. Changing backend `.env` requires restarting the local backend; a per-request override is immediate.
- `INSTANT_CALCULATOR_FIRST_TIMEOUT_SECONDS=360` is a wall-clock deadline, not a tool-count limit.
- `INSTANT_CHAT_AGENT_MODEL` overrides the shared configured Verified model. Both benchmark paths use the same model.
- `/ask` returns `instant_path`. Completed `gate_metadata` contains the selected path and `experiment_metrics`; status timing stages include tool rounds, requested calculators, cache hits, calculation time, provider time, first-progress time and total agent time. Actual provider token usage includes every round.
- A clarification ends its persisted turn without an Instant per-answer charge; elapsed consultation billing remains unchanged. A completed experimental answer clears the pending clarification count.

## Live sample

`artifacts/instant-calculator-first-comparison.json` records a real-provider comparison on a fictional birth chart, with the question: “Which sign and house is my Moon in, and what is my current Mahadasha?”

| Path | Total wall time | First public finding | First answer text |
| --- | ---: | ---: | ---: |
| Calculator first | 12.002 s | 7.497 s | 12.001 s |
| Existing baseline | 13.706 s | 7.550 s | 12.888 s |

The experimental reading requested two calculators over three tool rounds. Calculator execution took 5.9 ms; most latency was the model. Both answers identified Aquarius Moon in house 12 and Saturn Mahadasha. The experimental date wording matched the direct shared-calculator result (9 February 2024–9 February 2043); the baseline answer displayed the end date one day earlier. This boundary-label discrepancy warrants review rather than an overall accuracy claim.

This is one factual question on one fictional chart, not an astrological accuracy score or a general latency benchmark. Provider caches, request order and model variation affect the measurements. Broader career, relationship, event-timing and clarification samples are still needed.

To repeat locally from `backend`:

```sh
.venv/bin/python scripts/compare_instant_paths.py --path both --question "YOUR QUESTION" --output /tmp/instant-comparison.json
```

The script uses fictional birth inputs, avoids user-history writes and billing, saves both complete answers and reference facts, and reports provider failures by exception type without printing credentials.
