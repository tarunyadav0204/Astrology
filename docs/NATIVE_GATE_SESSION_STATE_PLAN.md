# Native Gate Session-State Plan

## Problem

The chat subject gate currently returns a `native_gate` assistant message when a question should branch into one of these flows:

- continue with selected chart only
- start partnership analysis
- collect relationship context
- create/select another person's chart

That gate works correctly when the user taps the frontend buttons because the frontend sends hidden control fields such as:

- `subject_gate_override`
- `subject_gate_memory`

However, if the user responds in free text instead of tapping a button, the next message falls back into the normal intent-routing pipeline. At that point, the system no longer treats the user as replying to the gate. This can produce wrong behavior such as:

- generic clarification prompts
- stale-context answers from an earlier topic
- old Type A / Type B / Type C menu prompts
- failure to start partnership flow even after the user provides partner birth details


## Root Cause

This is not mainly a language problem. It is a session-state problem.

### Current behavior

1. `native_gate` is emitted before the main chat answer flow.
2. The frontend only records gate choice when the user clicks the rendered gate buttons.
3. If the user types a natural-language reply instead, no explicit gate override is stored.
4. The backend then routes that message through normal intent classification.
5. `native_gate` is not treated as a formal pending state in the session, so the router can mis-bind the message to earlier answer history.

### Why "just detect yes/no" is wrong

That approach is fragile because:

- users may answer in any language
- users may type a sentence, not yes/no
- users may paste the original question again
- users may provide partner details directly
- users may continue with the same topic but with different wording

So the fix must not depend on specific words.


## Agreed Direction

The correct solution is to make `native_gate` a proper **session-scoped pending state**, similar to how clarification already has state.

Important constraint:

- This must be scoped to the **chat session**, not the user globally.
- A new session must never inherit a pending native gate from an old one.
- We should not depend on time-gap heuristics.


## Target Behavior

If the latest assistant turn in a session is a `native_gate`, then the next user turn in that same session should be interpreted first as a **reply to the gate**, not as a fresh normal chat question.

The system should decide among these outcomes:

1. continue with selected chart
2. start partnership analysis
3. collect missing partner birth details
4. collect relationship context
5. create/select another chart
6. repeat the gate in clearer wording if the user response is still genuinely ambiguous

This logic must work for:

- free-text replies in any language
- repeated phrasing of the same question
- direct entry of partner birth details
- short replies
- corrections


## Proposed Backend Design

### 1. Persist pending gate state per session

Add session-local pending gate state, either in `conversation_state` or a dedicated session-state table.

Recommended fields:

- `session_id`
- `pending_gate_type`
- `pending_gate_metadata`
- `pending_gate_message_id`
- `pending_gate_created_at`

Optional:

- `pending_gate_question`
- `pending_gate_resolution_status`

### 2. Set pending gate when native gate is emitted

When the backend returns a `native_gate` assistant message:

- save the gate metadata into the session pending-gate state
- include the assistant message id that owns the gate

### 3. Resolve pending gate before normal intent routing

At the start of `/chat-v2/ask`:

- load pending gate state for the current `session_id`
- if a pending native gate exists, run a dedicated resolver first
- do not send the message into normal intent routing until the gate resolver has either:
  - resolved the branch, or
  - explicitly decided the user is asking a fresh unrelated question

### 4. Clear pending gate once resolved

Clear pending gate state when:

- user chooses selected-chart-only path
- partnership flow starts
- relationship setup is completed
- other chart flow is started
- backend intentionally abandons the gate because the user has clearly moved on inside the same session


## Proposed Resolver

Create a dedicated function, conceptually:

`resolve_native_gate_reply(session_id, user_message, pending_gate_metadata, request_payload) -> structured_action`

Expected outputs:

- `continue_selected_chart`
- `start_partnership`
- `need_relationship_context`
- `need_other_person_chart`
- `need_partner_birth_details`
- `repeat_gate`
- `treat_as_new_question`

This resolver should look at:

- pending gate intent
- current user message
- whether partner birth details are now present in request
- whether relationship context is now present
- whether the message is clearly on-topic for the pending gate

This resolver should be semantic and structured, not hardcoded around English words.


## Frontend Role

Frontend buttons should still exist and remain the cleanest path.

But backend must no longer assume button clicks are required.

Frontend can remain helpful by still sending:

- `subject_gate_override`
- `subject_gate_memory`

But those should become an optimization, not the only reliable branch control.


## Suggested Implementation Order

### Phase 1: backend hardening

1. add session-scoped pending native-gate state
2. write `resolve_native_gate_reply(...)`
3. hook it before normal intent routing
4. clear state on successful resolution

This phase alone should fix the core bug for typed replies.

### Phase 2: frontend polish

1. surface clearer gate UI text
2. keep button-driven overrides
3. optionally show remembered choice context inside the thread

### Phase 3: analytics / observability

Add event logging for:

- native gate shown
- native gate resolved
- native gate repeated
- native gate abandoned
- resolution path chosen

This will make production debugging much easier.


## Non-Goals

These are intentionally **not** the solution:

- detect only `yes` / `no`
- depend on time gap between messages
- store pending gate globally per user
- assume all users click buttons
- let normal intent routing guess what the gate reply meant


## Why This Design Is Safe

This approach avoids cross-session confusion because the pending state lives on `session_id`.

So:

- same session -> unfinished gate can continue correctly
- new session -> no pending gate unless a new one is created in that session

That gives deterministic behavior without any language-specific heuristics or time-based guesses.


## Files Likely Involved

Backend:

- `/Users/tarunydv/Desktop/Code/AstrologyApp/backend/chat_history/routes.py`
- `/Users/tarunydv/Desktop/Code/AstrologyApp/backend/ai/chat_subject_gate.py`
- possibly `/Users/tarunydv/Desktop/Code/AstrologyApp/backend/ai/intent_router.py`

Frontend:

- `/Users/tarunydv/Desktop/Code/AstrologyApp/frontend/src/components/Chat/ChatPage.js`
- `/Users/tarunydv/Desktop/Code/AstrologyApp/frontend/src/components/Chat/ChatModal.js`
- `/Users/tarunydv/Desktop/Code/AstrologyApp/frontend/src/components/Chat/MessageBubble.js`


## Short Summary

The bug exists because `native_gate` is currently a UI-assisted branch, not a first-class session state.

The fix is to:

- persist pending gate state per session
- resolve the next user turn against that gate before normal intent routing
- clear the gate when resolved

That gives a language-agnostic, session-safe solution and avoids stale routing bugs.
