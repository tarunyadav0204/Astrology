"""Approved event-focused timing contract for Verified chat."""

EVENT_TIMING_MODES = {'PREDICT_EVENT_TIMING', 'LIFESPAN_EVENT_TIMING'}

EVENT_TECHNICAL_TEMPLATE = '''
## Your Answer: Most Likely Outcome and Timing
Answer what is likely to happen and when before presenting analysis. Bold the strongest conclusion and window.
Distinguish precursors from the event: interview versus offer, offer versus joining, responsibilities versus promotion,
meeting versus marriage. If the event is not supported within the requested horizon, say so and describe the closest
supported development. Never invent an outcome or date to satisfy the question.

## Does the Chart Support This Event?
Establish natal promise using relevant houses, lords, occupants, aspects, connections, significators and their condition.
Explain appropriate divisional confirmation, relevant yogas, strengths and obstacles. Conclude whether the event,
a conditional opportunity, partial outcome or weaker possibility is supported; interpret rather than list placements.

## Your Current Stage: What Happens Before the Event?
Explain the likely event-specific sequence and current stage using known circumstances without inventing milestones.
For example: responsibility, results, management discussion, approval; or relationship, commitment, arrangements, marriage.
Previous answers explain conversational references but are not verified astrological evidence.

## Dasha Analysis: When the Event Becomes Active
Explain Mahadasha's broader chapter, Antardasha's event activation, Pratyantardasha's stronger periods and finer levels
only when calculated and useful. Connect active planets to event houses, lordship, placements, aspects, significators,
and divisional confirmation. Separate a period beginning from the event occurring; a boundary is not an announcement.

## Transit and Double-Transit Confirmation
Explain Jupiter and Saturn influences on relevant houses, lords and significators; inspect event-house double-transit
confirmation over candidate windows. Include other relevant transits, nodes, shorter triggers and calculated retrograde
or repeated activation. Distinguish full confirmation from partial or aspect-only support.

## Dive Deep: Independent Confirmation
Use relevant subsections, not compulsory school reports. Explain what each adds, including disagreement:
Divisional confirmation: event-specific chart and timing implications.
Jaimini: relevant karakas, Chara dasha, Argala and rashi strength; inspect Chara dasha before Jaimini timing claims.
KP: relevant house significations and event support.
Nadi: calculated planetary connections and their meaning.
Additional dashas: Yogini or Shoola when useful; never claim deterministic death predictions.
Annual analysis: Varshphal, Tajika and annual nakshatra for candidate years.
Strength and yogas: planetary delivery, house strength, Ashtakavarga and event-specific yogas.
Do not repeat one finding under many systems. Omit unrelated systems instead of manufacturing confirmation.

## Ranked Event Windows
Rank genuinely distinct candidate windows strongest first. For each show date range, most likely development
(preparation/opportunity/commitment/execution/completion), specific dasha and transit reasons, what strengthens it,
what delays or weakens it, and relative high/medium/low confidence with a reason. No numerical probabilities without
an established basis. Show one window when only one is supported; never manufacture alternatives or arbitrary exact dates.
Narrow to days only when actual calculations justify that precision.

## Where the Evidence Agrees—and Where It Differs
Combine the methods into one prioritized judgment. Explain why support plus delay may imply responsibility first and
recognition later. Resolve contradictions; do not leave equally weighted conflicting possibilities without a conclusion.

## What Could Change the Timing?
Separate astrological conditions from practical dependencies such as approvals, recruitment, relationship readiness,
documents or financing. Ask material missing personal facts during information rounds when the tools support clarification.
Otherwise state relevant uncertainty plainly; do not fabricate user facts or claim to have asked a question.

## Preparation and Action
Give useful actions now, before the strongest window, and signs of progress to watch for. Remedies only when requested
or directly relevant, without guaranteeing an event.

## Final Verdict
Clearly state and bold: most likely outcome, strongest window, earlier development, main astrological reason and main
condition or uncertainty. Maintain a decisive evidence-based conclusion without guaranteeing external events.
'''


def event_timing_contract(style):
    template = EVENT_TECHNICAL_TEMPLATE
    if style == 'simple':
        replacements = {
            'Does the Chart Support This Event?': 'How Strong Is the Possibility?',
            'Dasha Analysis: When the Event Becomes Active': 'When the Opportunity Becomes Stronger',
            'Transit and Double-Transit Confirmation': 'What Supports or Slows the Timing',
            'Dive Deep: Independent Confirmation': 'A Closer Look at the Overall Picture',
        }
        for old, new in replacements.items():
            template = template.replace('## ' + old, '## ' + new)
    return '''VERIFIED EVENT TIMING OUTPUT CONTRACT — overrides generic lifespan and Standard Simple layouts.
Start with the straight answer, then provide a detailed 360-degree event analysis. No fixed word count or fixed number
of reasons/windows. Use Markdown headings on separate lines with blank lines and meaningful bold emphasis. Sentiment
spans are the only allowed HTML. Do not emit cards, internal answer IDs or evidence-transport language.
SCOPE: Assess the requested event and timeframe. For "this November", assess November first. For open "when" questions,
explore future candidate windows. Never automatically expand a bounded event question into a lifespan timeline.
EVIDENCE CHECKLIST: Inspect event promise, relevant divisional confirmation, dasha coverage, transits and event-house
double transit. Request additional calculators freely when they strengthen or challenge the conclusion, rather than
letting deterministic topic selection restrict analysis. Supply required dates, houses and other parameters explicitly.
For parashari.double_transit, always specify houses (1–12), start_date and end_date covering the candidate window;
respect the calculator's date boundary semantics. Annual tools require the candidate year and their other menu inputs.
Never interpret a calculator failure as negative event evidence. State the practical uncertainty without internal details.
''' + ('''SIMPLE: Preserve the same analytical breadth, reasoning, dates and cautions, but translate all technical
instructions below into everyday explanations. Do not expose house numbers, chart codes, dasha abbreviations, dignity
labels, counts or method-by-method reports. Explain why the outcome is likely through understandable real-life effects.
''' if style == 'simple' else '''TECHNICAL: Explain the concrete calculated astrological factors and how they lead to each
conclusion. Relevant Dive Deep subsections can use Markdown level-3 headings. No compulsory unrelated methods.
''') + template
