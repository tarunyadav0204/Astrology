import asyncio
import json
from chat.verified_followups import add_verified_followups


def test_verified_cards_are_localized_structured_and_usage_counted():
    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'in hindi' in prompt and 'partner' in prompt
            assert kwargs['provider_override'] == 'openai'
            return {'success':True,'token_usage':{'input_tokens':10,'output_tokens':5},'response':json.dumps({
                'follow_up_questions':['हम संवाद कैसे सुधारें?','हमारा अच्छा समय कब है?'],
                'next_action':{'type':'remedy','title':'उपाय जानें','reason':'तनाव कम करने के लिए',
                    'follow_up_questions':['हमारे संबंधों के तनाव के लिए उपाय बताएं।']}})}
    result = asyncio.run(add_verified_followups({'success':True,'response':'You and your partner face tension.',
        'chat_llm_model':'gpt-5.6-luna','token_usage':{'input_tokens':20}}, analyzer=Analyzer(),
        question='Compare us',intent={},language='hindi'))
    assert len(result['follow_up_questions']) == 2
    assert result['next_action']['type'] == 'remedy'
    assert result['next_action']['source'] == 'verified'
    assert result['token_usage']['input_tokens'] == 30


def test_remedy_followup_and_workflow_cards_do_not_repeat_offers():
    class Analyzer:
        async def generate_text_from_prompt(self, *args, **kwargs):
            raise AssertionError('must not generate cards')
    for active, action in [(True,{}),(False,{'type':'clarification_choice'})]:
        result={'success':True,'response':'Reading','next_action':action}
        assert asyncio.run(add_verified_followups(result, analyzer=Analyzer(), question='Q',intent={},
            language='english',remedy_followup_active=active)) is result


def test_optional_metadata_failure_keeps_completed_answer():
    class Analyzer:
        async def generate_text_from_prompt(self, *args, **kwargs):
            return {'success':True,'response':'invalid JSON'}
    result={'success':True,'response':'Completed answer'}
    output=asyncio.run(add_verified_followups(result,analyzer=Analyzer(),question='Q',intent={},language='english'))
    assert output['response'] == 'Completed answer'
    assert not output.get('next_action')
