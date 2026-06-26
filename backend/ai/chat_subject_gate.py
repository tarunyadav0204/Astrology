import asyncio
import json
import logging
import os
from typing import Any, Dict

import google.generativeai as genai

logger = logging.getLogger(__name__)


GATE_INTENTS = {
    "none",
    "create_subject_chart",
    "complete_subject_birth_details",
    "relationship_setup",
    "partnership_offer",
}


def _compact_birth_details(birth_details: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(birth_details, dict):
        return {}
    return {
        "id": birth_details.get("id") or birth_details.get("birth_chart_id"),
        "name": birth_details.get("name"),
        "gender": birth_details.get("gender"),
        "relation": birth_details.get("relation") or birth_details.get("relationship"),
        "date": birth_details.get("date"),
        "time": birth_details.get("time"),
        "place": birth_details.get("place"),
    }


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = (text or "").replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _normalize_gate_result(raw: Dict[str, Any], question: str) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {"gate_required": False, "intent_gate": "none"}

    intent = str(raw.get("intent_gate") or "none").strip()
    if intent not in GATE_INTENTS:
        intent = "none"

    confidence = str(raw.get("confidence") or "low").strip().lower()
    gate_required = bool(raw.get("gate_required")) and intent != "none" and confidence in {"high", "medium"}
    if not gate_required:
        return {
            "gate_required": False,
            "intent_gate": "none",
            "confidence": confidence,
            "reason": raw.get("reason") or "",
        }

    other_person = raw.get("other_person") if isinstance(raw.get("other_person"), dict) else {}
    relationship_setup = raw.get("relationship_setup") if isinstance(raw.get("relationship_setup"), dict) else {}
    options = relationship_setup.get("options") if isinstance(relationship_setup.get("options"), list) else []
    normalized_options = []
    for item in options[:8]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        value = str(item.get("value") or label).strip()
        if label and value:
            normalized_options.append({"label": label[:80], "value": value[:120]})

    if intent == "relationship_setup" and not normalized_options:
        normalized_options = [
            {"label": "First / eldest", "value": "first or eldest relation"},
            {"label": "Second / younger", "value": "second or younger relation"},
            {"label": "Other", "value": "other relation order"},
        ]

    extracted_birth_hint = {
        "name": other_person.get("name") or "",
        "date": other_person.get("date") or None,
        "time": other_person.get("time") or None,
        "place": other_person.get("place") or "",
        "gender": other_person.get("gender") or "",
        "relation_to_user": other_person.get("relation_to_user") or "",
    }
    for key in ("latitude", "longitude"):
        if other_person.get(key) is not None:
            extracted_birth_hint[key] = other_person.get(key)

    return {
        "gate_required": True,
        "intent_gate": intent,
        "confidence": confidence,
        "reason": str(raw.get("reason") or "").strip(),
        "user_message": str(raw.get("user_message") or "").strip(),
        "question_about": raw.get("question_about") or "",
        "recommended_next": raw.get("recommended_next") or "",
        "original_question": question,
        "other_person": other_person,
        "extracted_birth_hint": extracted_birth_hint,
        "relationship_setup": {
            **relationship_setup,
            "options": normalized_options,
        },
    }


def build_subject_gate_message(gate: Dict[str, Any], selected_name: str | None = None) -> str:
    return str(gate.get("user_message") or "").strip()


class ChatSubjectGate:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        from utils.admin_settings import get_setting

        model_name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
        if "pro" in model_name.lower():
            model_name = "models/gemini-2.5-flash-lite"
        config = genai.GenerationConfig(temperature=0, top_p=0.95, top_k=40)
        try:
            self.model = genai.GenerativeModel(model_name, generation_config=config)
        except Exception:
            self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite-001", generation_config=config)

    async def classify(
        self,
        *,
        question: str,
        birth_details: Dict[str, Any] | None,
        language: str = "english",
        subject_gate_memory: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        compact_memory = []
        if isinstance(subject_gate_memory, list):
            for item in subject_gate_memory[-8:]:
                if not isinstance(item, dict):
                    continue
                compact_memory.append({
                    "decision": item.get("decision"),
                    "relation_to_user": item.get("relation_to_user"),
                    "relation_family": item.get("relation_family"),
                    "name": item.get("name"),
                    "question_about": item.get("question_about"),
                    "intent_gate": item.get("intent_gate"),
                    "original_question": item.get("original_question"),
                })
        prompt = f"""
You are a routing gate for an astrology chat app. Decide whether the user's question can be answered using the currently selected birth profile, or whether the app must first collect another person's chart or exact relationship setup.

STRICT RULES:
- Use semantic understanding across all languages. Do not use keyword heuristics.
- The examples below are non-exhaustive calibration examples only. Do not force-fit the user into these examples.
- Do not perform astrology. Only decide the safest next UX step.
- If uncertain, return gate_required=false so the normal chat can continue.
- Return a gate only when answering with the currently selected profile would likely be wrong or materially incomplete.
- Write ALL user-facing text in the same language/script as the user's question when you can infer it naturally. This includes user_message and option labels.
- When gate_required=true, user_message must explicitly tell the user to choose/tap one of the options shown below instead of typing a reply. Say this naturally in the same language/script as the user's question.
- If previous user choices show the user already chose selected-chart-only for the same referenced person or same exact relation in this chat, you may return gate_required=false only for a clear follow-up continuation of that same unresolved gate topic. Do not suppress a new gate for a fresh standalone question just because the relation is the same.
- In previous user choices, `relation_to_user` is the exact remembered relation/context; `relation_family` is broad metadata only. Never use `relation_family` alone to suppress a new gate. For example, a prior choice about "elder sister" or "sister" must not suppress a new gate for "brother"; a prior choice about "sibling" must not suppress sister/brother unless the new question explicitly references the same exact sibling context.
- For spouse / wife / husband / partner relationship questions, default to partnership_offer unless this is clearly just a direct continuation of the immediately prior selected-chart-only path for the same exact topic.

Currently selected birth profile:
{json.dumps(_compact_birth_details(birth_details), ensure_ascii=False)}

Previous user choices in this chat:
{json.dumps(compact_memory, ensure_ascii=False)}

User language preference: {language}
User question:
{question}

When to gate:
1. Other-person chart needed:
   If the user is mainly asking about another specific person's own life area, gate to create_subject_chart or complete_subject_birth_details.
   This applies even when the user has NOT provided that person's birth details yet. The UX must suggest creating/selecting that person's chart instead of answering from the selected native's chart.
   Life areas include health, career, marriage, relationship, mental state, education, money, timing, future, problems, remedies, and similar personal matters.
   user_message should explain: for blood relations, the selected chart can still be useful; for friends, colleagues, partners, or other independent people, their own chart is strongly recommended if accurate birth date, birth time, and birth place are available; then ask the user to choose how to continue by tapping one of the options below.
   Example: "my friend was born on 12 Jan 1994 at 4pm in Delhi, tell me about his career" -> create_subject_chart.
   Example: "How will my friend's health be?" -> create_subject_chart.
   Example: "Mere dost ki tabiyat kab thik hogi?" -> create_subject_chart.
2. Partnership analysis should be offered:
   If the question is about the relationship/compatibility/dynamics between the selected native and another specific person, offer partnership_offer.
   This is mandatory for relationship/dynamics wording such as "my relationship with...", "bond with...", "compatibility with...", "equation with...", "will we get along...", or equivalent phrasing in any language, including blood relations such as sister, brother, father, mother, child, spouse, and in-laws.
   Do NOT return gate_required=false merely because blood relations can be partially judged from the selected native's chart. For relationship/dynamics questions, the UX should still offer Partnership Analysis as the more complete option while allowing the user to continue from the selected chart.
   This applies even when the other person's birth details are not yet provided: the UX should offer combined-chart Partnership Analysis if the user knows those details, or let them continue with a general single-chart answer if they do not.
   user_message should explain that combined-chart Partnership Analysis is best when accurate birth details are available, while the user may continue with the selected chart if they do not have those details; and ask them to tap one of the options below.
   If the other person is a repeatable blood relation where house selection also needs ordinal/role context (for example sister/brother/child/spouse), still use partnership_offer for relationship/dynamics questions, but also fill relationship_setup.required=true with options like elder sister / younger sister or 1st child / 2nd child. This lets the UX offer both: quick single-chart context and optional combined-chart Partnership Analysis.
   For parent relationship/dynamics questions such as father or mother, use partnership_offer even though ordinal setup is usually not needed.
   Example: "will I marry this person, born..." -> partnership_offer.
   Example: "Tell me my relationship with my friend" -> partnership_offer, not relationship_setup.
   Example: "What is my relationship with my sister?" -> partnership_offer with relationship_setup options for elder sister / younger sister.
   Example: "What is my relationship with my brother?" -> partnership_offer with relationship_setup options for elder brother / younger brother.
   Example: "What is my relationship with my father?" -> partnership_offer.
3. Relationship setup needed without another chart:
   If the question can be answered from the selected native's chart but the relation can repeat and the exact relation order/role changes house selection, gate to relationship_setup.
   Use relationship_setup alone for questions about the other person's life area through the selected chart, not for relationship/compatibility/dynamics between the selected native and that person.
   Examples: daughter/son/child health or future may need first/second/third child; sibling questions may need elder/younger; spouse questions may need first/second marriage where relevant.
   Relationship setup must NEVER be used to ask the broad relation category. Do not offer options like "friend, sibling, partner, colleague". Only ask for ordinal/role context within a relation the user already stated, such as "1st daughter / 2nd daughter" or "elder brother / younger brother".
   user_message should ask for that exact ordinal/role context in the user's language and tell the user to tap one of the options below instead of typing.

When NOT to gate:
- The user asks about the selected native's own life, feelings, career, marriage, health, timing, or general distress.
- The user mentions another person only as background but the focus remains the selected native.
- The user explicitly says they do not know the other person's birth details or asks to answer from the selected chart only; continue normal chat.
- The message is casual, non-astrology, or asks what the app can do.

Return ONLY valid JSON:
{{
  "gate_required": true or false,
  "intent_gate": "none" or "create_subject_chart" or "complete_subject_birth_details" or "relationship_setup" or "partnership_offer",
  "confidence": "high" or "medium" or "low",
  "reason": "short internal reason",
  "user_message": "short user-facing message in the user's language; empty only when gate_required=false",
  "question_about": "selected_chart" or "other_person_only" or "relationship_between_selected_and_other" or "selected_chart_relation_requires_context" or "ambiguous",
  "recommended_next": "continue" or "create_chart" or "complete_birth_details" or "start_partnership" or "answer_after_relation_setup",
  "other_person": {{
    "name": "",
    "relation_to_user": "",
    "date": "",
    "time": "",
    "place": "",
    "latitude": null,
    "longitude": null,
    "gender": "",
    "birth_details_complete": false
  }},
  "relationship_setup": {{
    "required": true or false,
    "relation_family": "child" or "sibling" or "spouse" or "parent" or "in_law" or "other" or "",
    "question_to_user": "short question to ask the user",
    "options": [
      {{"label": "1st daughter", "value": "my 1st daughter"}},
      {{"label": "2nd daughter", "value": "my 2nd daughter"}}
    ]
  }}
}}
"""
        try:
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt, request_options={"timeout": 10}),
                timeout=12,
            )
            raw = _extract_json(getattr(response, "text", "") or "")
            return _normalize_gate_result(raw, question)
        except Exception as exc:
            logger.warning("chat subject gate failed; continuing normal chat: %s", exc)
            return {"gate_required": False, "intent_gate": "none", "reason": "gate_failed"}

    async def resolve_pending_gate_reply(
        self,
        *,
        pending_gate: Dict[str, Any],
        user_message: str,
        birth_details: Dict[str, Any] | None,
        partner_birth_details: Dict[str, Any] | None = None,
        language: str = "english",
    ) -> Dict[str, Any]:
        gate_intent = str((pending_gate or {}).get("intent_gate") or "none").strip()
        if gate_intent not in GATE_INTENTS:
            return {"action": "treat_as_new_question", "reason": "no_valid_pending_gate"}

        if isinstance(partner_birth_details, dict):
            partner_name = str(partner_birth_details.get("name") or "").strip()
            partner_date = str(partner_birth_details.get("date") or "").strip()
            partner_time = str(partner_birth_details.get("time") or "").strip()
            partner_place = str(partner_birth_details.get("place") or "").strip()
            if partner_name and partner_date and partner_time and partner_place:
                return {"action": "start_partnership", "reason": "partner_birth_details_already_present"}

        prompt = f"""
You are resolving a pending astrology chat gate reply.

Goal:
- The previous assistant turn was a gate, not a final answer.
- Decide what the user's latest free-text reply means in relation to that pending gate.
- This is session-state resolution, not astrology analysis.

STRICT RULES:
- Work semantically across languages.
- Do not depend on yes/no keywords.
- Do not ask a fresh astrology clarification here.
- Prefer treating the message as a gate reply when it is plausibly continuing that exact gate.
- Use `treat_as_new_question` only when the user clearly moved to a fresh unrelated question.
- Return only JSON.

Selected chart:
{json.dumps(_compact_birth_details(birth_details), ensure_ascii=False)}

Pending gate metadata:
{json.dumps(pending_gate, ensure_ascii=False)}

Partner birth details already supplied in request:
{json.dumps(partner_birth_details or {}, ensure_ascii=False)}

User language preference:
{language}

Latest user message:
{user_message}

Allowed actions:
- continue_selected_chart
- start_partnership
- need_relationship_context
- need_other_person_chart
- need_partner_birth_details
- repeat_gate
- treat_as_new_question

Use these meanings:
- continue_selected_chart:
  The user is continuing with the selected chart only, or is asking the same gate-bound question in a way that should proceed with the selected chart.
- start_partnership:
  The user wants the combined-chart / partnership path.
- need_relationship_context:
  The user is still in the gate path, but exact relation-order context is still missing.
- need_other_person_chart:
  The user still needs the other person's own chart/profile path.
- need_partner_birth_details:
  The user wants partnership analysis, but birth details are still missing.
- repeat_gate:
  The user is still replying to the gate, but the safest move is to restate the gate choices more clearly.
- treat_as_new_question:
  The latest message is clearly a fresh unrelated question and should bypass the old gate.

Return only JSON:
{{
  "action": "one_of_the_allowed_actions",
  "confidence": "high" or "medium" or "low",
  "reason": "short internal reason"
}}
"""
        try:
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt, request_options={"timeout": 10}),
                timeout=12,
            )
            raw = _extract_json(getattr(response, "text", "") or "")
            action = str(raw.get("action") or "").strip()
            if action not in {
                "continue_selected_chart",
                "start_partnership",
                "need_relationship_context",
                "need_other_person_chart",
                "need_partner_birth_details",
                "repeat_gate",
                "treat_as_new_question",
            }:
                action = "repeat_gate"
            return {
                "action": action,
                "confidence": str(raw.get("confidence") or "low").strip().lower(),
                "reason": str(raw.get("reason") or "").strip(),
            }
        except Exception as exc:
            logger.warning("pending native gate resolver failed; treating as new question: %s", exc)
            return {"action": "treat_as_new_question", "confidence": "low", "reason": "resolver_failed"}
