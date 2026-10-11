# Instant conversation review

The `baseline` path described here is the local default. The newer [calculator-first experiment](instant-calculator-first-experiment.md) remains available as an optional path.

Instant previously supplied topic-specific deterministic evidence to a constrained, single-generation composer. Its WebSocket only observed an HTTP-submitted turn. The web UI ignored live deltas, then replayed the completed answer; mobile displayed rotating canned loading lines. Verified already provided a registered calculator menu, a bounded Responses tool loop, and model-written calculation findings.

## Implemented behavior

- `/api/chat-v2/conversation` accepts authenticated `ask` commands containing the same request body as `/ask`, plus a stable `client_request_id`. It returns `queued`, then relays durable `progress`, `content_delta`, and terminal events. The socket stays open for subsequent questions and replies. Existing `/ask`, `/status`, and `/stream` recovery paths remain available.
- Both web and mobile submit Instant turns over that connection and subscribe to their updates. A connection failure before submission falls back to HTTP. A lost acknowledgement after submission reports an uncertain outcome without automatically submitting another turn. Server-side work continues after disconnect.
- Instant retains its existing question routing, medical triage, and calculated topic baseline. The shared calculator agent inspects raw calculated evidence, chooses additional registered calculators with typed inputs, and can revise interpretations. It bypasses the legacy composer and verdict rewriting.
- Calculator IDs, input requirements, result limitations, and failed calculations are exposed to the model. Model knowledge can interpret results but cannot invent or silently replace calculated facts.
- `ask_user` ends the current turn with one focused clarification. Its message and pending clarification count are persisted, so the next reply has the original question and recent conversation context. It does not incur an Instant per-answer credit charge; existing elapsed-session billing still applies.
- Loading displays use short model-written findings from inspected calculations. They are public evidence summaries, not private chain-of-thought. Until a finding arrives, the UI displays a neutral waiting indicator. The final answer streams directly, without a second artificial reveal.
- Existing chart ownership, credit/session gates, token accounting, glossary lookup, and calculation audits are retained through the shared request/worker pipeline.

## Runtime configuration

`INSTANT_CHAT_CONVERSATION_ENABLED=true` enables the agent in production workers by default. Set it to `false` to use the legacy Instant composer. The socket transport can still relay that legacy result.

The agent requires `OPENAI_API_KEY` and uses OpenAI Responses tools. `INSTANT_CHAT_AGENT_MODEL` selects its model; when unset it uses the configured Verified model. This is a provider change from an Instant installation configured for Gemini or DeepSeek; those settings continue to control the legacy path. Speech chat retains its existing generation flow.

`INSTANT_CHAT_MAX_CALCULATOR_ROUNDS` defaults to 4, bounded to 1–16. `INSTANT_CHAT_AGENT_TIMEOUT_SECONDS` defaults to 120, bounded to 15–180 seconds. Each tool round adds provider latency and token cost. No arbitrary code or model-named unregistered calculator is executed.

## Practical limits and follow-up work

The conversation handles one reading at a time. Clarification replies start a fresh persisted turn rather than keeping a provider request suspended. Cancellation/interrupting an active reading and restoring an uncertain submission automatically are useful next additions. Lost acknowledgements currently require history/status recovery; blindly starting a new request can duplicate a question.

Deployment smoke testing should verify reverse-proxy WebSocket upgrades, a real provider calculator call, a clarification/reply, progress in web and mobile, reconnect recovery, and elapsed-session billing. Unit and regression tests use simulated provider responses; they cannot establish live model quality or astrological accuracy.
