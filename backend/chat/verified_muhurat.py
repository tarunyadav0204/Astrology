"""Verified election intake, bounded calculations and interactive search refinements."""
from datetime import date, timedelta
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from chat.calculator_menu import Location

class MuhuratRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_type: str = Field(min_length=1,max_length=80)
    start_date: date
    end_date: date
    location: Location
    weekdays: list[int] = Field(default_factory=list)
    excluded_dates: list[date] = Field(default_factory=list)
    allowed_start: str = '00:00'
    allowed_end: str = '23:59'
    minimum_duration_minutes: int = Field(default=15,ge=5,le=120)
    personalized: bool = False
    retrospective: bool = False
    check_time: Optional[str] = None
    @model_validator(mode='after')
    def check(self):
        from datetime import time
        if self.end_date<self.start_date or (self.end_date-self.start_date).days>=60:
            raise ValueError('Select 1–60 days per search')
        if any(n not in range(7) for n in self.weekdays): raise ValueError('Invalid weekday')
        if time.fromisoformat(self.allowed_end)<=time.fromisoformat(self.allowed_start): raise ValueError('Available hours must end after they start')
        if self.check_time: time.fromisoformat(self.check_time)
        return self


def setup_action(question, request):
    return {'type':'clarification_choice','choice_kind':'muhurat_setup','original_question':question,
        'muhurat_request':request,'options':[{'id':'muhurat_setup','label':'Set Muhurat details','submit_text':question,
        'query_context':{'muhurat_setup_requested':True,'muhurat_request':request}}]}


def prepare_muhurat_intent(intent, question, context):
    qc=dict(context or {})
    if intent.get('reading_type')!='muhurat':
        qc.pop('muhurat_request',None)
        return {**intent,'query_context':qc}
    for key in ('prashna','prashna_requested','prashna_choice'):
        qc.pop(key,None)
    previous=qc.get('_muhurat_previous') or {}
    base=dict(previous) if intent.get('muhurat_transition')=='continue' else {}
    supplied=qc.get('muhurat_request') or {}
    extracted=intent.get('muhurat_request') or {}
    allowed = set(MuhuratRequest.model_fields)
    if isinstance(extracted,dict): base.update({k:v for k,v in extracted.items() if k in allowed and v is not None and k!='location'})
    # Structured, user-confirmed selections take precedence over model extraction.
    if isinstance(supplied,dict): base.update({k:v for k,v in supplied.items() if k in allowed})
    # Location must be explicitly selected, never invented by Luna or defaulted to birthplace.
    if isinstance(supplied,dict) and supplied.get('location'): base['location']=supplied['location']
    choice=qc.get('muhurat_choice')
    if choice=='next_30_days' and previous:
        start=date.fromisoformat(previous['end_date'])+timedelta(days=1)
        base.update(start_date=start.isoformat(),end_date=(start+timedelta(days=29)).isoformat(),check_time=None)
    elif choice=='all_weekdays': base['weekdays']=[]
    resolved=str(intent.get('resolved_question') or question)
    from calculators.verified_muhurat_calculator import SUPPORTED_EVENTS
    if base.get('event_type') and base['event_type'] not in SUPPORTED_EVENTS:
        return {**intent,'status':'READY','route_action':'answer','mode':'ELECT_MUHURAT','category':'muhurat',
            'prashna_intent':'none','query_context':{**qc,'muhurat_request':base},'resolved_question':resolved}
    try:
        # Sanitize and independently resolve the selected event location's timezone.
        if base.get('location'):
            from chat.verified_prashna import freeze_prashna
            from datetime import datetime,timezone
            base['location']=freeze_prashna(base['location'],datetime.now(timezone.utc))['location']
        parsed=MuhuratRequest.model_validate(base)
    except (ValueError,TypeError,KeyError):
        return {**intent,'status':'CLARIFY','route_action':'clarify','mode':'ELECT_MUHURAT','category':'muhurat',
            'prashna_intent':'none','query_context':{**qc,'muhurat_draft':base},
            'muhurat_setup':setup_action(resolved,base),'resolved_question':resolved,
            'clarification_question': intent.get('clarification_question') or 'Select the card below to set the activity, event city, dates and available hours.'}
    request=parsed.model_dump(mode='json')
    return {**intent,'status':'READY','route_action':'answer','mode':'ELECT_MUHURAT','category':'muhurat',
            'prashna_intent':'none','query_context':{**qc,'muhurat_request':request},'resolved_question':resolved}


def muhurat_contract(style):
    return '''VERIFIED MUHURAT ELECTION CONTRACT
CURRENT ANSWER, NOT A RECAP:
Give a fresh self-contained recommendation. Calculator rounds are internal preparation for THIS answer,
not previous answers received by the user. Never say "previously calculated", "remains", "earlier conclusion"
or imply an earlier reading unless the user explicitly asks to compare an actual earlier answer.
History supplies references and constraints, not verified candidates. Only this request's successful
calculations establish candidate windows. For planned actions, never recommend an elapsed window;
respect the server's not_before_utc cutoff. Retrospective results are historical assessments, not bookings.
This chooses/checks a time to BEGIN a specified action, not a prediction of when an event will happen,
not Prashna, and not a generic lifespan/deep-dive report. The confirmed event city, date range, activity,
availability and selected profile/general preference are binding. NEVER silently expand dates, relax
constraints, substitute activities or claim uncalculated methods. Ask useful questions if material facts
are missing. Unsupported activities require a clear limitation, not another activity's rules.
RESULT STATUS IS AUTHORITATIVE:
status=completed means the calculation ran successfully. If candidates is empty, explain that no window
met the selected criteria in this period; it does NOT mean the service is unavailable or that no search
ran. Do not say "cannot verify", "cannot run a fresh calculation" or "calculation access is unavailable"
for a completed result. Offer the refinement cards and discuss the actual rejection factors kindly.
status=partial means some dates failed; qualify coverage and retain any successfully calculated windows.
status=unsupported means the activity rule engine is incomplete, not a temporary service outage.
Failure of an optional supplementary tool does not invalidate a successful baseline search.
Lead with the strongest actually calculated window, or a clear no-match/insufficient-coverage conclusion.
An empty list is not "no good times exist" beyond the searched period and evaluated rules. Calculation
errors mean coverage is incomplete. Never display raw exception diagnostics to the user. Scores are rankings, not percentages of success. Show limitations.
VOICE AND USER EXPERIENCE:
Speak as Tara in a warm, calm, personal consultation. Address the user naturally as "you"; use their
name sparingly when known. Explain what each finding means for their actual activity and decision.
Do not narrate an algorithm, search pipeline, ranking inputs, calculated natal context or internal evidence
packet. Avoid phrases such as "the search included", "the calculation used", "these factors support the
ranking" and inventories of placements without interpretation. Do not invent personal facts or promise
results. Warmth must not disguise uncertainty, lack of personalization or missing calculations.
In Technical style retain the actual relevant houses, lords and conditions, connecting each to its
practical meaning in flowing prose. In Simple style lead with the meaning and explain technical terms
briefly when useful. Use clear sections and meaningful bold, not a software audit report.
## Direct Recommendation
Straight answer first, bold recommendation and critical qualifications. Tell the user what you recommend
and why it suits their plan, in conversational language.
## What We Checked
Activity/action that should begin, confirmed event city/timezone, searched inclusive dates and available
hours, exclusions and selected native/general scope. A city is not assumed from birth data.
## Best Windows and Alternatives
Only calculated candidates: local date, start/end, timezone, duration, score as ranking, Lagna and
Panchang factors, reasons, cautions, personalization actually calculated. Explain trade-offs and which
action should start within the window. Separate checking a fixed date/time from searching alternatives.
## Panchang and Activity Fit
Discuss Tithi, Nakshatra, Yoga, Karana, Choghadiya, Lagna and excluded periods only to the extent computed.
Do not invent marriage matching, wedding doshas, D16, dashas, exact transition times or complete doctrine.
## Personal Suitability
Give a personal explanation of what the successfully calculated natal factors mean for this purchase.
For example, when favorable Chandra Bala is actually present, explain its traditional support for feeling
more settled or approaching the purchase with confidence; Technical style may add the Moon relationship.
Connect the fourth house/lord and any relevant occupants to vehicle ownership and comfort, describing
only the conditions actually supplied and their supported implications. Do not treat a bare placement as
proof of a favorable result. Weigh mixed factors honestly and make the conclusion understandable.
Phrase qualifications naturally, for example: "This is a supportive time to move ahead, but still check
the car, paperwork and payment terms carefully." Use this only when support is actually established.
Do not append the same guarantee disclaimer mechanically to every section. Put proportionate uncertainty
where it affects the recommendation. If no natal comparison was calculated, explain kindly that these
windows reflect the activity and local Panchang, and are not a personal birth-chart assessment.
## Restrictions and Uncertainty
Explain coverage, daytime restriction, conservative minute-grid precision and incomplete activity rules.
No medical procedure or delivery timing may be prescribed by astrology; childbirth/surgery have no supported
engine in this workflow and clinical scheduling takes precedence. Do not substitute gold/business rules.
## Next Step
If no supported windows fit, explain major calculated rejection factors and invite selecting the refinement
cards. Suggest concrete options, never silently perform a wider search. Questions may continue across turns.
## Final Recommendation
Restate the useful window or honest limitation, practical dependencies and what remains unassessed.
''' + ('Use accessible explanations with the same coverage.\n' if style=='simple' else 'Explain the actually calculated technical factors and their relative weight.\n')

MUHURAT_CAPABILITIES={
    'election.muhurat':'Rerun the CONFIRMED bounded election search. Requires no new parameters; no expansion without a user refinement card.',
    'election.panchang':'Panchang for a candidate date/time INSIDE the confirmed period and event city. Requires start_date and time.',
    'election.navatara':'Natal Moon Tara relationships for a candidate date/time INSIDE the confirmed period and event city. Requires start_date and time; only in personalized mode.',
}


def calculate_muhurat_tool(capability, request, birth, parameters=None):
    if capability=='election.muhurat':
        if parameters and any(v is not None for v in parameters.values()): raise ValueError('Search parameters require user confirmation')
        from calculators.verified_muhurat_calculator import VerifiedMuhuratCalculator
        return VerifiedMuhuratCalculator().search(request,birth)
    if capability not in MUHURAT_CAPABILITIES: raise ValueError('Unsupported election calculator')
    p=dict(parameters or {})
    target=date.fromisoformat(str(p.get('start_date') or ''))
    if not date.fromisoformat(request['start_date'])<=target<=date.fromisoformat(request['end_date']): raise ValueError('Date outside confirmed search')
    if not p.get('time'): raise ValueError('Candidate local time required')
    from datetime import time
    local_time=time.fromisoformat(p['time'])
    if request.get('not_before_utc'):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        snapshot=datetime.combine(target,local_time,ZoneInfo(request['location']['timezone']))
        if snapshot<datetime.fromisoformat(request['not_before_utc']):
            raise ValueError('Elapsed snapshot outside planned election coverage')
    if capability=='election.navatara' and not request['personalized']: raise ValueError('Natal comparison not selected')
    from chat.calculator_menu import run_calculator
    return run_calculator(capability,birth,{'start_date':target.isoformat(),'time':p['time'],'location':request['location']})


async def generate_muhurat_response(*,question,intent,birth,history,language,response_style,model_name,stream_callback,calculation_callback):
    import asyncio
    from chat.verified_chat_pipeline import run_verified_calculator_agent
    request=intent['query_context']['muhurat_request']
    from datetime import datetime,timezone
    # The ask endpoint injects this trusted clock; never use the caller's local clock.
    received=intent['query_context'].get('_question_received_at')
    cutoff=datetime.fromisoformat(received) if received else datetime.now(timezone.utc)
    calculation_request={**request}
    if not request.get('retrospective'):
        calculation_request['not_before_utc']=cutoff.astimezone(timezone.utc).isoformat()
    baseline=await asyncio.to_thread(calculate_muhurat_tool,'election.muhurat',calculation_request,birth)
    result=await run_verified_calculator_agent(question=question,language=language,birth_data=birth,
        instant_context={'intent_summary':{'mode':'ELECT_MUHURAT','category':'muhurat'},'query_context':intent['query_context'],'muhurat_baseline':baseline},
        history=history,model_name=model_name,timeout_s=180,response_style=response_style,
        stream_callback=stream_callback,calculation_callback=calculation_callback)
    action={'type':'none'}
    if baseline.get('status')=='completed' and not baseline.get('candidates'):
        options=[{'id':'next_30_days','label':'Search the next 30 days','submit_text':question,'query_context':{'muhurat_choice':'next_30_days'}},
            {'id':'change_details','label':'Change dates or available hours','submit_text':question,'query_context':{'muhurat_setup_requested':True,'muhurat_request':request}}]
        if request['weekdays']:
            options.insert(1,{'id':'all_weekdays','label':'Include all weekdays','submit_text':question,'query_context':{'muhurat_choice':'all_weekdays'}})
        action={'type':'clarification_choice','choice_kind':'muhurat_refine','original_question':question,'options':options}
    return {**result,'response_style':response_style,'terms':[],'glossary':{},'follow_up_questions':[],
        'next_action':action,'muhurat_context':request,'llm_prompt_chars':result.get('prompt_chars'),'llm_response_chars':len(result['response'])}
