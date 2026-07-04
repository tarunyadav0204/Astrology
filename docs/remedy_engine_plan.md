# Remedy Engine Plan

## Goal
Keep the main chat answer focused on the user's question, then surface a single follow-up that can open a dedicated remedial flow when the user's next need is actually a remedy.

## Why this should exist
- Remedies are currently mixed into normal chat behavior.
- The codebase already has remedy calculators and a `remedy_action` answer mode.
- The chat UI already supports follow-up questions under the answer.
- A separate remedial engine will make the main answer cleaner and the remedy path more intentional.

## Target behavior
1. User asks a question.
2. Chat returns the main reading first.
3. Backend computes the most pressing next need.
4. If remedy is the strongest next need, the answer shows a follow-up card like:
   - "See a remedy plan"
   - "Check the blockage behind this"
   - "Show practical upay"
5. User taps that follow-up to enter a remedy-focused flow.

## Current code pieces we can reuse
- `backend/chat/instant_chat_pipeline.py`
  - already has `remedy_action`
  - already has question-mode detection helpers
- `backend/calculators/remedy_calculator.py`
- `backend/calculators/nakshatra_remedy_calculator.py`
- `backend/chat_context_builder.py`
  - already builds remedy context
- `backend/chat_history/routes.py`
  - already stores and returns `follow_up_questions`

## What to add

### 1. Next-need scorer
Add a small post-answer scorer that picks the most helpful follow-up:
- remedy
- deeper timing
- chart explanation
- relationship clarification
- comparison

Suggested name:
- `derive_next_best_need(...)`

Suggested output:
```json
{
  "next_best_need": "remedy",
  "confidence": "high",
  "follow_up_questions": ["See a remedy plan for this"]
}
```

### 2. Separate remedy mode
Keep `remedy_action` as a distinct mode, but make it reachable primarily through the follow-up path.

Suggested modes:
- `main_answer`
- `remedy_action`
- `remedy_plan`

### 3. Remedy payload
Use the existing calculators to build a structured remedy payload:
- target planet
- target house / nakshatra
- remedy tier 1..5
- rationale
- caution

This payload should be returned only when the user taps the remedy follow-up or directly asks for remedies.

### 4. Mobile UI hook
Show the remedy suggestion as a single follow-up chip/card under the answer.
Tap should open the remedy view in chat with the existing chart context.

### 5. Prompt cleanup
Reduce remedy leakage in ordinary answers:
- keep remedies out of generic explanations
- mention them only when the scorer says they are the next best need

## Suggested implementation order
1. Add the next-need scorer.
2. Attach it to chat response generation.
3. Return one remedy follow-up when appropriate.
4. Add the dedicated remedy path.
5. Clean the normal prompts so they do not over-push remedies.

## Acceptance criteria
- Main answer stays focused.
- Remedy appears as a follow-up, not as noise in every answer.
- Direct remedy questions still work.
- The existing chat UI can render the new follow-up without a redesign.
- No extra DB load beyond the existing chat write path.

## Notes
- Do not make this a separate top-level product yet.
- Make it a distinct mode inside the chat pipeline, surfaced as a follow-up action.
- If a question is clearly diagnosis-only or timing-only, do not force a remedy suggestion.
