"""Approved event-focused timing contract for Verified chat."""

EVENT_TIMING_MODES = {'PREDICT_EVENT_TIMING', 'LIFESPAN_EVENT_TIMING'}

EVENT_TECHNICAL_TEMPLATE = '''
## The promise and what shapes its timing
Open by speaking to the person and give the judgment in natural language. For example: "I would not read this as
denial; the chart shows why the path asks for patience before it becomes easier." Do not copy that sentence as a
template, but preserve its human, decisive movement. Explain the two or three factors that matter most as connected
paragraphs: the event house/lord, a supporting or delaying factor, and the relevant divisional chart when it changes
the result. Translate each technical term when it first appears. Do not merely recite placements or every system that
happens to agree.

## When this becomes most likely
Show every deterministic candidate window in its exact calculated rank order. Keep `Rank 1`, `Rank 2`, and so on so
the ordering is unambiguous, but make each rank read like a reasoned paragraph, not a row in a report. State its date
range, the one most likely event stage, and why that period carries its particular weight. Rank 1 is the strongest
calculated window; never promote an attractive lower-ranked sub-period above it. A viable Rank 2+ window is not merely
"preparation". Use an exact day only when the calculation explicitly supports exact-day precision; otherwise use the
calculated month or date band. Do not manufacture alternate windows.

## How to hold the present period
Give one concrete interpretation of the current or nearest period and, when guidance was requested, one proportionate
action. Write it as counsel from an astrologer who has weighed the chart—not as an instruction sheet. Do not give
medical, legal, financial, or lifestyle checklists unless specifically requested. End with a direct closing sentence,
not a separate "Bottom line" or a repetition of the opening verdict.
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
Start with the straight answer, then write a clear, satisfying consultation rather than a fragmented all-systems report.
Use the three sections below; do not add method headings, an executive-summary duplicate, a final-verdict duplicate,
or a boilerplate disclaimer.
Use Markdown headings on separate lines with blank lines and meaningful bold emphasis. Sentiment spans are the only
allowed HTML. Do not emit cards, internal answer IDs or evidence-transport language.
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
conclusion, but give the person the lived meaning of each fact in the same paragraph. No compulsory unrelated methods.
''') + template
