import asyncio
import json

from chat.verified_chat_pipeline import classify_verified_question


def test_natal_fertility_question_preserves_router_decision_and_card_workflow():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'use your understanding of\nPrashna' in prompt
            assert 'continue with the birth chart\nunless clarification is necessary' in prompt
            assert 'something unresolved, missing, pending' not in prompt
            # The regression question belongs in the request, not teaching examples.
            assert prompt.count('Why am I not having kids?') == 1
            assert 'choose Use Prashna or Continue with my birth chart' in prompt
            assert 'UI opens city selection AFTER the Use Prashna card' in prompt
            assert 'Keep its chart clock' in prompt
            assert 'Use a fresh question timestamp' in prompt
            assert 'do not offer Prashna again for that\nsame question' in prompt
            assert 'Set requires_new_location true only' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'topic_reading', 'category': 'children',
                'route_action': 'answer', 'prashna_intent': 'none',
                'reading_transition': 'natal', 'reading_type': 'default',
            })}

    result = asyncio.run(classify_verified_question(
        Router(), question='Why am I not having kids?', history=[], language='english',
    ))
    assert result['status'] == 'READY'
    assert result['prashna_intent'] == 'none'
