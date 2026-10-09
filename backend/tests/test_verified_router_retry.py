import asyncio
import json
import pytest
from chat.verified_chat_pipeline import classify_verified_question

VALID={'answer_mode':'topic_reading','category':'general','route_action':'answer','reading_type':'default'}
class Analyzer:
    def __init__(self, results): self.results=iter(results); self.calls=[]
    async def generate_text_from_prompt(self,prompt,**kwargs):
        self.calls.append(kwargs)
        return next(self.results)

@pytest.mark.parametrize('failure',[{'success':False,'error':'timeout'},{'success':True,'response':''},{'success':True,'response':'{}'}])
def test_transient_or_unusable_result_retries_same_model_and_accounts_usage(failure):
    analyzer=Analyzer([{**failure,'token_usage':{'input_tokens':4}}, {'success':True,'response':json.dumps(VALID),'token_usage':{'input_tokens':6}}])
    result=asyncio.run(classify_verified_question(analyzer,question='Explain my career',history=[],language='english'))
    assert result['status']=='READY'
    assert [call['request_timeout_s'] for call in analyzer.calls]==[60,30]
    assert analyzer.calls[0]['model_name_override']==analyzer.calls[1]['model_name_override']
    assert result['_llm_usage_stage']['token_usage']['input_tokens']==10

def test_retry_exhaustion_does_not_guess_workflow():
    analyzer=Analyzer([{'success':False,'error':'timeout'}]*2)
    with pytest.raises(RuntimeError,match='timeout'):
        asyncio.run(classify_verified_question(analyzer,question='Choose a wedding date',history=[],language='english'))
    assert len(analyzer.calls)==2

def test_configuration_error_is_not_retried():
    analyzer=Analyzer([{'success':False,'error':'OPENAI_API_KEY environment variable not set'}])
    with pytest.raises(RuntimeError,match='OPENAI_API_KEY'):
        asyncio.run(classify_verified_question(analyzer,question='Explain my career',history=[],language='english'))
    assert len(analyzer.calls)==1
