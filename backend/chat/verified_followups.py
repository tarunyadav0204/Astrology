"""Optional localized post-answer cards for Verified readings."""
import json
import logging

logger = logging.getLogger(__name__)


async def add_verified_followups(result, *, analyzer, question, intent, language,
                                 remedy_followup_active=False):
    if not result.get('success') or remedy_followup_active:
        return result
    if (intent or {}).get('route_action') in {'ack', 'clarify', 'handoff', 'out_of_scope'}:
        return result
    existing = result.get('next_action') or {}
    if existing.get('type') not in {None, '', 'none'}:
        return result  # Preserve workflow/refinement cards.
    prompt = f'''Create optional next-step cards for this completed Verified astrology reading.
Write every user-visible field in {language}. Treat the user as speaking directly to you.
Use only the question and answer below; do not add chart facts, predictions or remedies.
Suggest 2-3 concise, distinct follow-up QUESTIONS the user can send, specific to the reading.
Offer a remedy card when the reading identifies a meaningful challenge and remedies are useful;
otherwise use type none. Do not imply a remedy is mandatory or guarantees outcomes, and do not
replace medical, legal or financial care. For a remedy card, title is a short invitation, reason
explains relevance, and follow_up_questions contains one complete user request for remedies
for the identified issue. Respect the relationship and both people in partnership readings.
Return JSON only:
{{"follow_up_questions":["..."],"next_action":{{"type":"remedy|none","title":"...","reason":"...","confidence":"medium","follow_up_questions":["..."],"source":"verified"}}}}
QUESTION: {question}
READING: {str(result.get('response') or '')[:30000]}
'''
    try:
        output = await analyzer.generate_text_from_prompt(prompt, premium_analysis=False,
            provider_override='openai', model_name_override=result.get('chat_llm_model'),
            request_timeout_s=20, llm_log_tag='verified_followups')
        usage = output.get('token_usage') or {}
        total = result.setdefault('token_usage', {})
        for key in ('input_tokens', 'output_tokens', 'cached_tokens', 'non_cached_input_tokens', 'total_tokens'):
            if isinstance(usage.get(key), int):
                total[key] = total.get(key, 0) + usage[key]
        if not output.get('success'):
            return result
        from chat.verified_chat_pipeline import _json_object
        data = _json_object(str(output.get('response') or ''))
        questions = data.get('follow_up_questions') or []
        if isinstance(questions, list):
            result['follow_up_questions'] = list(dict.fromkeys(
                q.strip() for q in questions if isinstance(q, str) and q.strip()))[:3]
        action = data.get('next_action') or {}
        if isinstance(action, dict) and action.get('type') == 'remedy':
            requests = action.get('follow_up_questions') or []
            if (isinstance(action.get('title'), str) and action['title'].strip()
                    and isinstance(action.get('reason'), str) and action['reason'].strip()
                    and isinstance(requests, list) and requests
                    and isinstance(requests[0], str) and requests[0].strip()):
                result['next_action'] = {**action, 'source':'verified',
                    'follow_up_questions':[requests[0].strip()]}
    except Exception:
        logger.warning('Verified follow-up cards unavailable', exc_info=True)
    return result
