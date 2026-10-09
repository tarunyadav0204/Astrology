"""Approved daily presentation and mandatory day-specific foundations."""
from datetime import date
from chat.calculator_menu import Location

DAILY_TECHNICAL_TEMPLATE = '''
## Your Day: [Weekday, Date]
Give the direct answer immediately: overall character, strongest opportunity, main pressure and best approach.
Distinguish a routine day from stronger event potential. Bold the key conclusion. Explicitly name the requested date.

## The Main Themes of the Day
Explain the strongest areas of activation in order of relevance. For each: what may become noticeable, its calculated
basis, whether it is opportunity/pressure/preparation/completion/an event, and how it appears in ordinary life.
Do not assume career dominates because previous questions concerned promotion.

## Your Planetary Periods: What Is Active Now?
Explain the periods operating on the REQUESTED date. Start with relevant available shorter periods; then connect
Mahadasha/Antardasha and the shorter periods to natal house ownership, placement, relationships and delivery quality.
Separate the long-running background from this day's triggers. Explain any calculated within-day period change.
A period boundary is not a guaranteed external event. Never invent unavailable finer periods.

## Moon, Nakshatra and Navatara: The Day’s Immediate Tone
Explain the requested-day Moon sign, activated natal house, nakshatra, Navatara relationship to birth nakshatra,
and relevant calculated natal contacts. Explain attention, emotional responses, communication, cooperation and momentum.
Name and explain the Tara category. Weigh it alongside the other evidence; difficult Tara does not make the entire day bad.
Discuss Moon/nakshatra changes only when the transition is actually calculated.

## Panchang: The Quality of the Day
Explain Vara and ruler, Tithi, Nakshatra, Nitya Yoga and Karana for the selected location. Explain their combined
practical significance and activities they support or complicate. Nitya Yoga is a Panchang element, not a natal yoga.
Discuss local boundaries, sunrise or transitions only when calculated. Do not mechanically label the entire day good/bad.

## Opportunities and Cautions Across Your Day
### Work, Study and Responsibilities
Explain concentration, execution, cooperation, meetings, visibility and decisions with their astrological basis.
Separate completing work from receiving recognition.
### Money, Purchases and Practical Decisions
Explain routine transactions, spending, paperwork and discussions. Do not infer major gain/loss from a minor daily factor.
### Relationships and Communication
Explain cooperation, sensitivity, conversation and conflict. Do not claim to know another person's intentions.
### Energy, Focus and Emotional Balance
Explain day-level stamina, restlessness, mental load and patience; do not turn these into diagnoses.
### Travel, Movement and Everyday Tasks
Discuss when relevant or supported: errands, appointments, short journeys, coordination and schedule changes.
Explain each relevant area substantially. If an area has no distinct daily signal, say so briefly; never manufacture predictions.

## Important Transit Influences
Prioritize day-sensitive fast transits and relevant natal connections. Slow transits are the background.
For each important influence explain its natal connection, practical significance and whether it supports or moderates
this day's outlook. Distinguish a months-long influence from something distinctive about this date.

## Where the Astrological Factors Agree—or Differ
Explain reinforcing factors, mixed indications, which deserve the most weight for this day, and why.
Additional Jaimini/Nadi/KP/divisional/strength systems belong here when they contribute a distinct finding.
Do not give every school equal weight or repeat earlier sections. Do not create compulsory school-by-school reports.

## Timing Through the Day
Explain calculated changes and useful local intervals with their actual basis: Moon/nakshatra/Panchang transitions,
short-period changes or activity-specific Muhurat. Identify location and timezone when giving clock times.
If intraday timing is not established, give a day-wide assessment; never invent a productive afternoon or work-hour window.

## How to Make the Most of the Day
Connect priorities, patience, checking and handling opportunities to the specific reading. Address any named interview,
exam, meeting or purchase. Do not add remedies unless requested.

## Final Judgment
Summarize the overall outlook, strongest opportunity, most relevant caution and best approach.
State material uncertainty briefly; do not introduce new predictions or a list of disclaimers.
'''

SIMPLE_HEADINGS = {
 'The Main Themes of the Day':'What Stands Out Today',
 'Your Planetary Periods: What Is Active Now?':'What Is Shaping Your Day',
 'Moon, Nakshatra and Navatara: The Day’s Immediate Tone':'Your Mood and Momentum',
 'Panchang: The Quality of the Day':'Which Activities Fit the Day',
 'Important Transit Influences':'What Supports You—and What Adds Pressure',
 'Where the Astrological Factors Agree—or Differ':'Why This Is the Overall Outlook',
}

def daily_contract(style='technical'):
    template=DAILY_TECHNICAL_TEMPLATE
    if style=='simple':
        for old,new in SIMPLE_HEADINGS.items(): template=template.replace('## '+old,'## '+new)
        template+='\nSIMPLE PRESENTATION: Preserve this breadth and explanation in everyday language. Translate technical instructions into practical meanings; do not expose chart codes, house numbers, dasha abbreviations, or compulsory school headings. Use level-2 headings; render domain labels as bold sublabels.\n'
    return '''APPROVED DAILY READING CONTRACT (takes precedence over generic Deep Dive):
Write a substantial, rounded reading of the requested day. No fixed word count. Direct answer first, then the sections
below. Translate all headings naturally into the requested response language. Use readable paragraphs, blank lines,
selective bold and supported sentiment highlighting. Sections must contain useful explanations, not one-line placeholders.
Omit irrelevant specialist subsections; never pad the reading with unsupported claims. Do not use lifespan/event-arc,
ranked multi-year windows, promotion layers or compulsory Parashari/Nadi/Jaimini sections.

MANDATORY DAILY EVIDENCE:
Inspect requested-date Vimshottari and available shorter periods, requested-day planetary positions and natal links,
election.navatara and election.panchang. The baseline's daily_required_calculations supplies these two mandatory
calculators when date/location are available; inspect their returned facts. If missing, request them with explicit
parameters.start_date and, for Panchang, parameters.location (coordinates and timezone). Never substitute today.
Use the daily prediction spine when calculated. Additional calculators are optional and unlimited in selection:
Yogini, relevant divisions, strengths/delivery, Ashtakavarga, Jaimini/Nadi/KP, annual/Tajika, Muhurat or double transit
when they answer the actual question. Supply every required input. Do not infer an event from a natal combination alone.
If required date/location is unresolved, ask a focused question instead of giving fabricated day-specific results.
If a calculator fails, explain the practical limit briefly and use the remaining evidence without inventing missing facts.
Location basis must be explicit: use a known current location; otherwise identify the saved birth location being used.
Clock times must use that location's timezone. Relative-day dates come from the structured user-local query context.
''' + template

def daily_inputs(birth, context):
    intent=context.get('intent_summary') or {}
    window=intent.get('period_window') or {}
    extracted=intent.get('extracted_context') or {}
    target=window.get('start') or window.get('date') or window.get('target_date') or extracted.get('specific_date')
    if not target: raise ValueError('Requested daily date is unresolved')
    target=date.fromisoformat(str(target)[:10]).isoformat()
    query=context.get('query_context') or {}
    current=query.get('current_location')
    if isinstance(current,dict) and current.get('latitude') is not None and current.get('longitude') is not None and (current.get('timezone') or current.get('timezone_name')):
        location=Location.model_validate({
            'name':current.get('name') or current.get('place') or 'Current location',
            'latitude':current['latitude'],'longitude':current['longitude'],
            'timezone':str(current.get('timezone') or current.get('timezone_name'))})
        basis='current_location'
    else:
        if birth.get('latitude') is None or birth.get('longitude') is None or birth.get('timezone') in (None,''):
            raise ValueError('Daily location and timezone are unresolved')
        location=Location(name=birth.get('place') or 'Saved birth location',latitude=birth['latitude'],longitude=birth['longitude'],timezone=str(birth['timezone']))
        basis='saved_birth_location'
    return {'start_date':target,'time':'12:00:00','location':location.model_dump()}, basis
