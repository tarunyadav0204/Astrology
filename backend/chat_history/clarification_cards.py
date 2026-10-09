from __future__ import annotations

def is_compound_choice_followup(
    query_context: dict | None = None,
    extracted_context: dict | None = None,
) -> bool:
    """True when the user is answering a pick-one compound-question card."""
    qc = query_context if isinstance(query_context, dict) else {}
    follow_up = str(qc.get("follow_up_type") or qc.get("followUpType") or "").strip().lower()
    if follow_up == "clarification_choice":
        return True
    ctx = extracted_context if isinstance(extracted_context, dict) else {}
    if str(ctx.get("answer_mode") or "").strip().lower() == "compound_plan":
        return True
    dialogue = ctx.get("instant_dialogue") if isinstance(ctx.get("instant_dialogue"), dict) else {}
    return str(dialogue.get("pending_choice_kind") or "").strip() == "compound_plan"


def compound_choice_option(raw, index: int) -> dict | None:
    if not isinstance(raw, dict):
        return None
    label = str(raw.get("label") or raw.get("theme") or raw.get("life_domain") or "").strip()
    submit_text = str(
        raw.get("submit_text") or raw.get("question") or raw.get("exact_question") or raw.get("text") or ""
    ).strip()
    if not submit_text:
        return None
    if not label:
        label = submit_text[:80]
    option_id = str(raw.get("id") or raw.get("part_id") or f"q{index}").strip() or f"q{index}"
    return {
        "id": option_id[:40],
        "label": label[:80],
        "submit_text": submit_text[:500],
    }


def fallback_compound_choices_from_parts(intent: dict) -> list[dict]:
    plan = intent.get("evidence_plan") if isinstance(intent.get("evidence_plan"), dict) else {}
    raw_parts = plan.get("question_parts") if isinstance(plan, dict) else None
    if not isinstance(raw_parts, list):
        raw_parts = intent.get("question_parts")
    if not isinstance(raw_parts, list):
        return []
    options = []
    seen = set()
    for raw in raw_parts:
        option = compound_choice_option(raw, len(options) + 1)
        if not option:
            continue
        dedupe_key = " ".join(option["submit_text"].casefold().split())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        options.append(option)
        if len(options) >= 5:
            break
    return options if len(options) >= 2 else []


def build_clarification_next_action(
    intent: dict | None,
    original_question: str | None = None,
) -> dict | None:
    """Build a durable card payload for compound-question clarification."""
    if not isinstance(intent, dict):
        return None
    if str(intent.get("status") or "").upper() != "CLARIFY":
        return None
    if intent.get('muhurat_setup'):
        return intent['muhurat_setup']
    if intent.get('workflow_choice'):
        question = str(original_question or '').strip()
        return {'type': 'clarification_choice', 'choice_kind': 'prashna_scope',
                'original_question': question, 'source': 'verified_intent_router',
                'options': [
                    {'id': 'continue', 'label': 'Continue this question', 'submit_text': question,
                     'query_context': {'prashna_workflow_choice': 'continue'}},
                    {'id': 'new', 'label': 'Start a new reading', 'submit_text': question,
                     'query_context': {'prashna_workflow_choice': 'new'}}]}
    if intent.get('prashna_intent') in {'offer', 'explicit'}:
        question = str(original_question or '').strip()
        options = [{'id': 'prashna', 'label': 'Use Prashna', 'submit_text': question,
                    'query_context': {'prashna_choice': 'prashna'}}]
        if intent['prashna_intent'] == 'offer':
            options.append({'id': 'natal', 'label': 'Continue with my birth chart', 'submit_text': question,
                            'query_context': {'prashna_choice': 'natal'}})
        return {'type': 'clarification_choice', 'choice_kind': 'prashna_method',
                'options': options, 'original_question': question, 'source': 'verified_intent_router'}
    if str(intent.get("answer_mode") or "").lower() != "compound_plan":
        return None

    options = []
    seen = set()
    for raw in intent.get("clarification_choices") or []:
        option = compound_choice_option(raw, len(options) + 1)
        if not option:
            continue
        dedupe_key = " ".join(option["submit_text"].casefold().split())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        options.append(option)
        if len(options) >= 5:
            break
    if len(options) < 2:
        options = fallback_compound_choices_from_parts(intent)
    if len(options) < 2:
        return None

    payload = {
        "type": "clarification_choice",
        "options": options,
        "source": "intent_router",
    }
    original = str(original_question or "").strip()
    if original:
        payload["original_question"] = original[:2000]
    return payload
