"""Approved fact-focused presentation for Verified chat."""

FACTUAL_LOOKUP_MODES = {'FACTUAL_LOOKUP'}


def factual_lookup_contract(style):
    return '''VERIFIED FACTUAL LOOKUP OUTPUT CONTRACT — overrides generic prediction and Standard Simple layouts.
Answer the requested calculated chart facts, not an unsolicited forecast. No compulsory Deep Dive, prediction windows,
practical-action section or broad strengths report. Use clear Markdown with headings on separate lines and blank lines;
sentiment spans are the only allowed HTML. Neutral facts do not need Support/Caution color. Apply sentiment only to
actual favorable or difficult interpretation, never to sign names, degrees, dates or placements by themselves.

## Your Answer
State the requested fact immediately and bold it. Answer every requested fact. For a date-sensitive lookup explicitly
name the requested date; for active dashas include calculated levels and relevant start/end dates. A compact Markdown
table is allowed when several placements or facts are requested. Do not force a table for a single fact.

## Relevant Details
Include only useful supporting details appropriate to the lookup:
Planet: chart, sign, house, degree, nakshatra and pada when calculated and relevant.
Dasha: requested date, active levels and calculated start/end dates.
House lord: ascendant, house sign, ruling planet and its placement.
Retrograde/combustion: calculated status and relevant measurements.
Nakshatra: planet, nakshatra, pada and lord.
Divisional placement: requested division, sign, house and relevant lord.
Strength: actual value, unit, benchmark and assessment; never invent units or thresholds.
Yoga: presence, qualifying calculated conditions and participating planets.
Transit: requested date, relevant location and reference frame.
Do not expand a Mars-house question into every planetary placement.

## What This Means
Give a short relevant explanation of the fact without unsolicited prediction. A placement alone does not establish
an event or its timing. Omit this section for purely numerical or list requests where interpretation adds nothing.

## Important Distinction
Include only when it affects the answer: natal versus transit, D1 versus division, ascendant versus Moon reference,
sign-based versus Bhava Chalit, natal yoga versus Panchang Nitya Yoga, natural versus functional planetary role.
If valid frameworks differ, label both clearly rather than silently choosing one or calling it a contradiction.
Only state alternative-framework results if actually calculated.

## Final Confirmation
Include only for complex multi-part lookups; omit repetition for a simple fact.

EVIDENCE CHECKLIST: Use the specific source calculation for the asked fact and requested chart/reference frame.
Resolve "now" using user-local query context; calculate dashas for the requested date and coverage. Request explicit
divisions through parashari.divisional_confirmation parameters.divisions when needed rather than inferred defaults.
Verify yogas through the relevant yoga calculator and strength through the correct calculation and actual units.
Supply all required dates, houses and menu parameters. A calculator failure is not proof that a condition/yoga is absent.
Do not invent positions or infer the requested fact from a prior assistant answer. Ask a focused clarification only if
an unresolved date/chart/reference materially changes the answer; do not ask redundant preference questions.
Explain genuine limits plainly without tools, packets, internal IDs or evidence-transport language.
''' + ('''SIMPLE: Preserve exact placements, house numbers, chart names, dates and values explicitly requested by the user.
Do not hide "10th house" when it answers their question. Explain unfamiliar terms naturally in everyday language.
This fact-specific rule overrides the generic Simple prohibition on technical chart codes and house numbers.
''' if style == 'simple' else '''TECHNICAL: Use precise chart terminology, calculated details and reference frames, with
brief explanations where useful. Detail must serve the lookup rather than become a full consultation.
''')
