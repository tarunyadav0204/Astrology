import asyncio
import json
import pytest
from chat.verified_chat_pipeline import classify_verified_question
from chat_history.clarification_cards import build_clarification_next_action

class Router:
    def __init__(self, decision): self.decision = decision
    async def generate_text_from_prompt(self, prompt, **kwargs):
        assert 'Infer offer SEMANTICALLY' in prompt
        assert 'not a keyword list' in prompt
        assert 'select one of the displayed cards' in prompt
        assert 'The UI opens city selection AFTER' in prompt
        assert 'Do NOT ask them to type a choice, share a city' in prompt
        assert 'Having a saved birth chart does not rule out Prashna' in prompt
        return {'success': True, 'response': json.dumps({'prashna_intent': self.decision,
            'answer_mode':'event_prediction', 'category':'career', 'route_action':'answer',
            'user_message':'Choose your reading.'})}

@pytest.mark.parametrize('decision,ids', [('offer',['prashna','natal']),('explicit',['prashna'])])
def test_method_choice_preserves_question_and_durable_cards(decision, ids):
    question='Will I find my lost wallet?'
    intent=asyncio.run(classify_verified_question(Router(decision),question=question,history=[],language='english'))
    assert intent['status']=='CLARIFY'
    action=build_clarification_next_action(intent,question)
    assert action['choice_kind']=='prashna_method'
    assert [o['id'] for o in action['options']]==ids
    assert all(o['submit_text']==question for o in action['options'])
    assert action['options'][0]['query_context']['prashna_choice']=='prashna'

@pytest.mark.parametrize('context',[{'prashna_choice':'natal'},{'prashna_choice':'prashna'},{'prashna':{'submitted_at':'fixed'}}])
def test_confirmed_method_cannot_repeat_offer(context):
    intent=asyncio.run(classify_verified_question(Router('offer'),question='Will I get this job?',history=[],language='english',query_context=context))
    assert intent['status']=='READY'
    assert intent['prashna_intent']=='none'
    assert build_clarification_next_action(intent,'question') is None

def test_router_natal_decision_has_no_method_offer():
    intent=asyncio.run(classify_verified_question(Router('none'),question='Explain my overall career prospects.',history=[],language='english'))
    assert intent['status']=='READY'
    assert build_clarification_next_action(intent,'question') is None

@pytest.mark.parametrize('question', ['Where did I lose my pen, where can I fint it', 'Where can I find my missing wallet?', 'मेरा खोया पेन कहाँ मिलेगा?'])
def test_object_search_cannot_become_city_recommendation(question):
    class LocationRouter:
        async def generate_text_from_prompt(self,prompt,**kwargs):
            assert 'interpreting WHAT' in prompt
            assert 'NOT relocation or city advice' in prompt
            return {'success':True,'response':json.dumps({'location_intent':'object_search',
                'answer_mode':'location_recommendation','category':'career','route_action':'clarify',
                'user_message':'Would you like city suggestions in India, abroad, or both?'})}
    intent=asyncio.run(classify_verified_question(LocationRouter(),question=question,history=[],language='english'))
    assert intent['mode']=='PREDICT_EVENT_TIMING'
    assert intent['category']=='general'
    assert intent['prashna_intent']=='offer'
    assert 'India' not in intent['clarification_question']
    assert build_clarification_next_action(intent,question)['choice_kind']=='prashna_method'


def test_actual_relocation_still_uses_location_workflow():
    class LocationRouter:
        async def generate_text_from_prompt(self,prompt,**kwargs):
            return {'success':True,'response':json.dumps({'location_intent':'relocation',
                'answer_mode':'location_recommendation','route_action':'answer','prashna_intent':'none'})}
    intent=asyncio.run(classify_verified_question(LocationRouter(),question='Which city should I move to for my career?',history=[],language='english'))
    assert intent['mode']=='RECOMMEND_LOCATION'
    assert intent['prashna_intent']=='none'
