# Instant Chat question coverage contract

Instant Chat is tested as a three-axis matrix, not as a list of English keywords:

1. **Question operation** — what the user wants us to do.
2. **Life domain** — which astrological methodology/calculators are needed.
3. **Conversation state** — what is already known, ambiguous, corrected, or unsafe.

Natural-language classification remains LLM-owned across all supported languages. The
Python registry in `question_taxonomy.py` is an audit and test contract; it is not a
keyword router.

## Question operations

| Family | Effective answer must do |
|---|---|
| Exact chart/dasha fact | Return the exact calculated fact; do not manufacture a prediction. |
| Explanation/challenge | Explain the exact evidence chain and correct an overstated earlier claim. |
| Nature/temperament | Describe observable behavior, strength, pressure response and caution. |
| Other-person profile | Use the correct derived frame and clearly say it is derived from the native's chart. |
| Unbounded topic reading | Give a plain verdict, real-life manifestations, support, friction and direction. |
| Day/month/year outlook | Give the overall result and meaningful phase changes—not a date/dasha dump. |
| Event likelihood/timing | Check natal promise, dasha permission and transit delivery before ranking windows. |
| Capacity/suitability | Separate enduring ability from whether the present period supports using it. |
| Comparison/choice | Calculate each option separately; give a winner only when evidence separates them. |
| Problem diagnosis | Explain why it is happening now, the trigger if supported, and practical handling. |
| Action guidance | Say what to do/avoid now without silently converting the request into a remedy reading. |
| Remedy follow-up | Run only from the explicit remedy flow and keep the remedy set small and relevant. |
| Location recommendation | Resolve India/abroad/both and the life goal before ranking locations. |
| Compatibility | Require and identify both charts; never present a one-chart derived reading as compatibility. |
| Muhurat/election | Use the dedicated event, location and timezone-aware calculator—not personal event timing. |
| Multi-part question | Acknowledge that it contains multiple material asks and request one question at a time. Run no calculators until the user chooses. |

## Life domains

Career, employment and job search, promotion and authority, job change, projects,
business, marriage/spouse, love/relationship, separation/reconciliation, wealth,
income, debt, investment/trading, inheritance/settlement, health, mental wellbeing,
surgery, accident/injury, recovery, property/home, vehicles, children/pregnancy,
adoption, education, exams, foreign travel/visa, immigration/relocation, location
recommendation, mother, father, siblings, family, legal/litigation, competition,
government, reputation, friends/network, creativity, sports, research/occult,
spirituality, karma, life purpose, retirement, Muhurat, and general timing.

Each operation must work across each applicable domain. For example, “career” alone
does not prove coverage: career topic reading, annual career outlook, promotion timing,
career blockage, business-vs-job comparison and spouse-career derived reading are
different test cells.

## Conversation states

- Clear first turn: calculate immediately.
- Ambiguous reference: ask one natural, language-matched clarification.
- Short clarification reply: merge it and never repeat the resolved question.
- User correction: replace the assumption and continue from corrected state.
- Contextual follow-up: resolve “why?”, “after that?”, etc. from recent dialogue.
- Missing second chart/data: request only the material missing input.
- High-stakes/blocked request: apply safety policy without fabricating certainty.

## Correctness gate

An answer is not “correct” merely because its astrology sentence is plausible. It must:

1. answer the real-life question in the first sentence;
2. use the correct subject and timeframe;
3. bind each material claim to calculated evidence;
4. use natal promise, dasha permission and transit delivery when timing an event;
5. distinguish background activity from a dated high-activation peak;
6. translate evidence into likely real-life manifestations;
7. state limitations when a required capability is absent;
8. avoid unsupported certainty, dates, medical diagnosis and fear;
9. stay concise and continue the conversation naturally in the user's language.

The automated taxonomy test prevents router categories or answer families from being
added without a declared methodology and answer contract. Chart-based golden tests
then validate the high-risk cells against fixed calculator evidence.

## First acceptance bank

The executable question bank lives in `question_acceptance_cases.py`. It begins
with more than forty high-risk cells, including exact chart facts, annual career
and health outlooks, marriage/promotion/job/child/property/visa/vehicle timing,
derived readings for relatives, choices, recurring problems, location,
compatibility handoff, Muhurat, location recommendation, multi-part questions,
surgery, accident, ambiguity, correction, contextual
follow-ups and medical-safety cases. Each case declares its expected operation,
domain, subject and special correctness gate. It is intentionally a labelled
evaluation set—not a source of runtime keyword rules.
