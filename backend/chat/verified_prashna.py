"""Question-chart-only evidence and presentation for Verified Prashna."""
from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from chat.calculator_menu import CalculatorParameters, compact_result

PRASHNA_CAPABILITIES = {
    'prashna.parashari': 'Fixed question chart: sidereal whole-sign placements, house lords, Moon, dignity and planetary relationships. No natal dashas.',
    'prashna.kp': 'Time-based KP question chart with cusp/star/sub-lords and significators for the fixed clock/location. Not number-based KP horary; no invented horary number.',
    'prashna.tajika': 'Independent classical Hayanaratna Prashna chart/profile and Tajika configurations. Requires exactly two distinct planets and one matter house in parameters. No annual solar-return substitution.',
}


def freeze_prashna(location, submitted_at):
    from pydantic import BaseModel, Field, ConfigDict
    from utils.timezone_service import get_iana_timezone
    class Coordinates(BaseModel):
        model_config = ConfigDict(extra='ignore')
        name: str = Field(min_length=1, max_length=200)
        latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
        longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    place = Coordinates.model_validate(location)
    # Resolve timezone from coordinates, never from birth profile or caller clock.
    try:
        zone = get_iana_timezone(place.latitude, place.longitude)
        ZoneInfo(zone)
    except Exception as exc:
        raise ValueError('Unable to resolve question location timezone') from exc
    now = submitted_at.astimezone(timezone.utc)
    return {'version': 1, 'submitted_at': now.isoformat(), 'location': {**place.model_dump(), 'timezone': zone},
            'clock_source': 'server_question_received', 'primary_method': 'parashari'}


def question_birth(context):
    place = context['location']
    stamp = datetime.fromisoformat(context['submitted_at'])
    if stamp.tzinfo is None: raise ValueError('Question timestamp requires timezone')
    local = stamp.astimezone(ZoneInfo(place['timezone']))
    return {'name': 'Prashna', 'date': local.date().isoformat(), 'time': local.strftime('%H:%M:%S'),
            'place': place['name'], 'latitude': place['latitude'], 'longitude': place['longitude'],
            'timezone': place['timezone'], 'gender': '', 'relation': 'prashna'}


def calculate_prashna(capability, context, parameters=None):
    if capability not in PRASHNA_CAPABILITIES: raise ValueError('Not a question-chart calculator')
    data = question_birth(context)
    if capability == 'prashna.parashari':
        from calculators.chart_calculator import ChartCalculator
        from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
        chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**data))
        rulers = ['Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']
        asc_sign = int(chart['ascendant'] // 30)
        offsets = {'Sun':[7],'Moon':[7],'Mars':[4,7,8],'Mercury':[7],'Jupiter':[5,7,9],'Venus':[7],'Saturn':[3,7,10]}
        aspects = {planet: [((int(chart['planets'][planet]['longitude']//30)-asc_sign+offset-1)%12)+1 for offset in distances] for planet,distances in offsets.items()}
        facts = {'chart': chart, 'house_lords': {str(h): rulers[(asc_sign+h-1)%12] for h in range(1,13)},
                 'dignities': PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities(),
                 'graha_drishti_houses': aspects, 'aspect_convention':'Whole-sign Parashari graha drishti; node aspects excluded'}
        profile = 'lahiri_whole_sign_question_chart'
    elif capability == 'prashna.kp':
        from chat.instant_chat_pipeline import _instant_real_kp_evidence
        facts = _instant_real_kp_evidence(data)
        if not facts: raise ValueError('KP question calculation unavailable')
        profile = 'kp_time_based_question_chart'
    else:
        p = CalculatorParameters.model_validate(parameters or {})
        if not p.planets or len(set(p.planets)) != 2 or not p.houses or len(p.houses) != 1:
            raise ValueError('Tajika requires two distinct planets and one matter house')
        from prashna.service import _question_clock
        from calculators.prashna_classical_chart import ClassicalPrashnaChartCalculator
        from calculators.tajika_classical_engine import TajikaClassicalEngine
        clock = _question_clock(**{k:v for k,v in data.items() if k not in {'gender','relation'}})
        chart = ClassicalPrashnaChartCalculator().calculate_chart(clock)
        engine = TajikaClassicalEngine(chart)
        facts = {'chart': chart, 'significators': p.planets, 'matter_house': p.houses[0],
                 'configurations': engine.all_configurations(*p.planets, matter_house=p.houses[0])}
        profile = chart['calculation']['profile_id']
    return {'calculator': capability, 'chart_basis': 'question_chart', 'clock': context,
            'profile': profile, 'facts': compact_result(facts)}


def prashna_contract(style):
    return '''VERIFIED PRASHNA CONTRACT
This is explicitly a question-chart reading, not natal analysis. The clock and location are immutable across tool rounds
and clarification replies. Start with Parashari question-chart evidence. Request KP/Tajika only when they help resolve
the matter. These have separate calculation profiles; label them and resolve differences instead of blending placements.
Never apply natal Vimshottari/Yogini/Chara schedules, natal promise, annual Varshphal or number-based KP horary to this
question chart. No fabricated horary number, aspects, applications, perfection dates or guaranteed outcomes. Exact timing
requires calculated support under the stated method; otherwise state that a reliable narrow window cannot be established.
Recent natal answers and facts are conversational context only, not Prashna evidence. Do not silently add natal comparison.
CURRENT READING, NOT A RECAP: Write a self-contained answer to the current question. Start directly with
what this question chart indicates. Do not frame it as confirming, retaining or revising an earlier
conclusion unless the user's CURRENT question explicitly asks to revisit or compare an earlier answer.
Recent assistant answers are not verified evidence and must not establish the current verdict.
Calculator rounds and intermediate model analysis within this request are internal preparation for
ONE answer, never earlier user-visible readings. A repeated original question after selecting a method
or city is the current question, not a request to reaffirm a past conclusion. Clarification replies
continue this reading; do not imply that an answer has already been delivered.
Avoid openings such as "The earlier conclusion remains", "The earlier Prashna reading", "as previously
assessed", or "the calculated evidence already available". Say directly "You are more likely to..."
or "This question chart suggests...", expressing qualifications naturally.
Describe KP/Tajika only if successfully calculated IN THIS REQUEST. Explain them as additional
perspectives in this reading, never "previously considered" profiles. A historical answer mentioning
KP/Tajika is not proof that either method was calculated for this question chart.
Use only this calculator menu and its requirements:
''' + str(PRASHNA_CAPABILITIES) + '''
Use Markdown headings on separate lines, blank lines and meaningful bold. Sentiment spans are the only HTML.
## Your Answer
Lead with the supported favorable/unfavorable/conditional/delayed/unresolved conclusion, separate outcome from timing.
## Your Prashna Chart
Show original question, fixed local date/time, timezone, city and method; these define this reading.
## You and the Matter Asked About
Explain question ascendant/lord, relevant matter house/lord, condition and connections and practical meaning.
## The Moon and the Question’s Development
Explain calculated Moon placement/condition and relevant relationships; no invented future contacts.
## What Supports the Outcome—and What Opposes It
Weigh specific relationships and strength under the chosen method. Explain which factors carry most weight.
## Additional Perspectives
Include KP and/or Tajika only when requested and successfully calculated. Explain their independent conclusions and
agreement/disagreement with Parashari. Do not call number-based KP horary calculated or assume one profile's placements
apply to another. Omit this section when not used.
## Timing—If Supported
Provide a supported window and basis, otherwise explain the timing uncertainty without making up a date.
## Conditions and Practical Guidance
Explain dependencies and delays and useful actions. No invented personal facts or guaranteed remedies.
## Final Judgment
Bold outcome, main reasons, supported timing if any, and principal qualification.
''' + ('SIMPLE: Explain the same reasoning naturally; translate technical labels without losing relevant conclusions.\n' if style == 'simple' else 'TECHNICAL: Explain the actual calculated houses, lords, conditions and method-specific factors.\n')


async def generate_prashna_response(*, question, intent, history, language, response_style, model_name, stream_callback, calculation_callback):
    from chat.verified_chat_pipeline import run_verified_calculator_agent
    context = (intent.get('query_context') or {}).get('prashna')
    import asyncio
    baseline = await asyncio.to_thread(calculate_prashna, 'prashna.parashari', context)
    result = await run_verified_calculator_agent(question=question, language=language,
        birth_data=question_birth(context), instant_context={'intent_summary': {'mode':'PRASHNA', 'category': intent.get('category'),
        'period_window': intent.get('period_window')}, 'query_context': intent.get('query_context') or {},
        'prashna_baseline': baseline}, history=history, model_name=model_name, timeout_s=180,
        response_style=response_style, stream_callback=stream_callback, calculation_callback=calculation_callback)
    return {**result, 'response': result['response'], 'response_style':response_style,
        'information_rounds':result['information_rounds'], 'terms':[], 'glossary':{}, 'follow_up_questions':[],
        'llm_prompt_chars': result.get('prompt_chars'), 'llm_response_chars': len(result['response']),
        'next_action': {'type':'none'}, 'prashna_context':context}
