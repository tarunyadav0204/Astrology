"""Approved bounded-period outlook contract for Verified chat."""

PERIOD_OUTLOOK_MODES = {'PREDICT_PERIOD_OUTLOOK'}

PERIOD_TECHNICAL_TEMPLATE = '''
## Your Answer: What This Period Is Most Likely to Bring
Start with the overall direction and strongest supported developments within the requested dates. Bold the leading
conclusion. Prioritize genuine activation; do not predict a major event in every area or dramatize ordinary pressure.

## The Main Chapters of Your Period
Divide the horizon into meaningful calculated dasha/transit phases, not arbitrary equal months or quarters.
For each give date range, dominant theme, likely developments, opportunity, caution and what changes from the prior phase.

## Your Planetary Periods: What Is Becoming Active?
Explain Mahadasha, Antardasha and relevant shorter periods within the horizon, connecting planets to houses, placements,
significations, condition and relevant divisional confirmation. Separate background from period-specific changes.
Mention outside-horizon boundaries only to explain what develops next. Never treat a boundary as a promised event.

## Major Transit Changes and Double-Transit Support
Explain relevant Jupiter/Saturn influences, house-specific double transit, nodes, calculated retrograde/repeated
activation and useful faster triggers. Do not scan houses mechanically or imply every overlap produces an event.

## Developments Across Your Life
Use substantive relevant subsections, with greatest depth for the strongest themes:
### Work, Career and Business
Responsibilities, recognition, job changes, projects, business progress or pressure; separate development from milestones.
### Money, Income and Assets
Earning, spending, savings, debt, investments or property where relevant; distinguish income from financial stability.
### Relationships, Marriage and Family
Cooperation, commitment, family responsibilities or tension; never assume marital or relationship status.
### Education, Skills and Personal Growth
Study, exams, qualifications, learning and direction where supported.
### Travel, Relocation and Life Arrangements
Movement, overseas opportunities, housing and routine; distinguish considering a move from completing it.
### Energy and Emotional Wellbeing
Workload, resilience, focus and recovery needs; no diagnosis or certain medical outcomes.
For each relevant area explain what is likely, when noticeable and why. Briefly acknowledge little distinctive activation
instead of inventing events. For a career-only period question, replace unrelated life-area subsections with relevant
career dimensions. Do not add marriage or property predictions outside the user's scope.

## Dive Deep: Why These Themes Stand Out
Select relevant independent methods and explain what each adds or challenges:
Divisional charts: confirmation for strongest themes.
Jaimini: Chara dasha and relevant karakas, Argala or rashi strength; inspect Chara dasha before Jaimini timing claims.
KP and Nadi: calculated event indications and connections.
Additional dashas: meaningful agreement/disagreement with Vimshottari; no deterministic death predictions.
Annual analysis: Varshphal, Tajika and annual nakshatra for relevant years. Give particular attention to annual evidence
for year-long readings; explain an annual-chart boundary when calculated. Use each tool's actual year/date semantics.
Strength and yogas: delivery capacity of activated planets and houses.
No repeated findings or compulsory irrelevant school reports. Never invent confirmation from unavailable calculations.

## Ranked Likely Developments
Rank the strongest supported developments, not the most dramatic. For each show likely development, best-supported
window, unfolding sequence, astrological reasons, support, possible delay/weakening and relative confidence with a reason.
No invented percentage probabilities. Sustained improvement can lead the ranking even without a major milestone.
Do not manufacture a fixed number of developments or unsupported exact dates.

## Opportunity Windows and Pressure Windows
Explain windows suited to applications, negotiations, preparation, commitments, consolidation or review, and why.
These are broad planning windows. Auspicious dates or exact appointment times require separate Muhurat calculations;
never infer them solely from a favorable month. Distinguish opportunity from guaranteed success.

## Where the Evidence Agrees—and Where It Differs
Resolve support and tension into a prioritized conclusion. Explain compatible sequences, such as a larger role first
and compensation later, instead of leaving equally weighted competing forecasts.

## How to Use This Period
Give phase-specific preparation, actions during stronger windows, care during pressure windows and observable signs
of progress. Practical actions do not guarantee predicted outcomes.

## Final Outlook
Bold the overall direction, strongest likely developments, best opportunity window, main pressure window and priority.
If no distinctive pressure or opportunity window is supported, say so instead of manufacturing one.
'''


def period_outlook_contract(style):
    template = PERIOD_TECHNICAL_TEMPLATE
    if style == 'simple':
        for old, new in {
            'Your Planetary Periods: What Is Becoming Active?': 'What Is Shaping This Period?',
            'Major Transit Changes and Double-Transit Support': 'What Supports Progress—and What Adds Pressure',
            'Dive Deep: Why These Themes Stand Out': 'A Closer Look: Why These Themes Stand Out',
        }.items():
            template = template.replace('## ' + old, '## ' + new)
    return '''VERIFIED EVENTS WITHIN A PERIOD OUTPUT CONTRACT — overrides generic lifespan and Standard Simple layouts.
Give a detailed 360-degree reading within the requested period and life areas, straight answer first. No fixed word
count, number of reasons or windows. Markdown headings must be on separate lines with blank lines and deliberate bold
emphasis. Sentiment spans are the only permitted HTML; no cards, answer IDs or internal evidence-transport language.
SCOPE: An overall period outlook identifies developments across the requested areas, not the timing of just one
milestone. Retain the user's exact horizon; never expand a bounded question into a lifespan timeline or add unrelated
life areas. Use structured dates and user-local query context to resolve relative periods, not natal dates or server time.
EVIDENCE CHECKLIST: Inspect dasha coverage and relevant transits across the ENTIRE requested horizon. A current snapshot
alone cannot establish future phases. Request relevant divisional, annual, strength, yoga and specialist calculators for
the themes identified; deterministic topic selection must not restrict the model's choice. Request as many relevant
calculators as needed, supplying required dates, houses, years, location and other menu parameters explicitly.
For parashari.double_transit specify houses (1–12), start_date and end_date covering the relevant window, and respect
its date-boundary semantics. Annual tools require relevant years and their other menu inputs. Verify horizon coverage
before conclusions; never invent future placements, transitions or calculator results. Failures create uncertainty,
not negative event evidence. Explain practical limits without exposing internal transport.
''' + ('''SIMPLE: Preserve the complete breadth, windows, reasons and cautions while translating all technical directions
below into everyday language. No house numbers, chart codes, dasha abbreviations, dignity labels, counts or
method-by-method reports. Explain the practical effects behind the conclusion.
''' if style == 'simple' else '''TECHNICAL: Explain concrete calculated astrological factors behind each conclusion.
Use relevant level-3 Dive Deep subsections without requiring unrelated methods.
''') + template
