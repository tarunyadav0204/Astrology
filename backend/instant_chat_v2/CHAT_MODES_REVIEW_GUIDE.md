# AstroRoshni Instant Chat Design and Evidence Guide

> **Document status: IMPLEMENTED CONTRACT WITH LAUNCH GATES**
>
> This document contains both existing implementation and launch requirements. Every major section uses the following labels:
>
> - **IMPLEMENTED** — present in the current code path and covered by contract tests.
> - **LAUNCH-GATED** — requested by the planner, but the evidence ledger will mark it unavailable until its named calculator result is exposed.
> - **REQUIRED** — a product or astrology rule enforced by the current contract.

## Purpose of this document

This document explains, in simple English, how AstroRoshni should understand a question, choose the right kind of answer, collect astrological evidence, and write the final response.

It is meant for product and astrology review. It deliberately separates:

1. the chat product selected by the user;
2. the internal answer mode selected by the LLM;
3. the life area being examined;
4. the evidence available from our calculators; and
5. the final answer shown to the user.

The central rule is:

> The LLM understands the user's natural language. Calculators establish the astrological facts. The LLM then explains those facts in ordinary language. The LLM must not invent calculations.

### Executive summary

- The user chooses **Instant, Standard or Premium**.
- Inside Instant, the LLM chooses the answer operation and life domain.
- The same mode can be used for different life domains.
- The planner asks only for evidence relevant to that mode and domain.
- Calculated facts are stored in an auditable evidence ledger.
- Missing required evidence limits the answer; it must never be filled with plausible-sounding astrology.
- Every named methodology operation must call a real calculator before launch.
- Every completed answer must include understandable astrology and end with one natural follow-up question.
- There is no fixed 120-word product limit. The answer should be as short as possible while still answering properly and showing its astrological basis.

### Approved product decisions

1. Instant answers are **not** restricted to 120 words.
2. Every completed answer ends with **one natural follow-up question**.
3. Every answer contains **some understandable astrological evidence**. Astrology is not completely hidden.
4. Chart Facts, Location Recommendation and Muhurat are visibly distinct flows.
5. Compatibility is excluded from the current Instant launch scope.
6. Every methodology operation must be backed by a real calculator call before launch.
7. Event timing requires dasha support. Transit, divisional, double-transit and karaka support determine higher confidence.
8. When required evidence is missing because the question is unclear, Instant asks one clarification.
9. When a message contains materially different questions, the LLM identifies it as multi-part and asks the user to send only one question at a time.

---

## 1. Three meanings of “mode”

### A. User-facing chat product

| Product | What the user expects | Depth | Response style |
|---|---|---:|---|
| **Instant Chat** | A fast, natural conversation with an astrologer | Focused evidence for the current question | Short message bubbles, direct answer, natural follow-up question |
| **Standard Chat** | A complete chart-based answer to one question | Broader chart context and multiple supporting layers | Structured answer with explanation and supporting details |
| **Premium Chat** | A deep synthesis of a complex or important question | Maximum relevant Parashari, Nadi, Jaimini, KP, divisional and timing context | Long, detailed, multi-layer analysis |

This document is mainly about **Instant Chat**. Standard and Premium can use much larger evidence packages and longer answers. Instant must stay small and fast without becoming astrologically careless.

### B. Internal answer mode

The internal answer mode describes **what kind of answer the question needs**. For example:

- “How is my career this year?” needs a period forecast.
- “When will I get married?” needs an event likelihood and timing answer.
- “Why is my career stuck?” needs a problem diagnosis.
- “What kind of person will my spouse be?” needs a person profile.

The LLM selects this mode from the meaning of the conversation. Python must not use keyword matching to decide it.

### C. Life domain

The domain describes **which area of life needs evidence**: career, marriage, health, property, education, and so on.

Answer mode and domain are independent. For example, career can be asked as:

- a fact;
- a general outlook;
- a yearly forecast;
- an event prediction;
- a diagnosis;
- a comparison; or
- an action question.

---

## 2. End-to-end flow

```text
User's message and recent dialogue
        ↓
Multilingual LLM router
        ↓
Structured meaning: operation + domain + subject + time window + missing clarification
        ↓
Evidence plan: what must be calculated or retrieved
        ↓
Existing astrology calculators and normalized Instant context
        ↓
Evidence ledger: facts, sources, confidence and missing capabilities
        ↓
Evidence fusion: one verdict, ranked windows, support, pressure and limitations
        ↓
Answer contract: allowed claims, forbidden claims and output order
        ↓
One fast LLM composer call
        ↓
Short, streamed, ordinary-language answer
```

### What each stage owns

| Stage | Job | Must not do |
|---|---|---|
| **LLM router** | Understand any supported language, references, corrections and the real question | Calculate astrology or answer the question |
| **Planner** | Convert structured meaning into evidence requirements | Interpret raw user text |
| **Calculators / gateway** | Supply astrological facts | Write persuasive prose |
| **Evidence ledger** | Record what was found, its source and whether required evidence is missing | Hide missing evidence |
| **Fusion** | Decide the supported direction, confidence and timing windows | Invent a result when calculators disagree or are incomplete |
| **Answer contract** | Limit the composer to supported claims and the right format | Generate a second astrological opinion |
| **LLM composer** | Turn the verdict into natural language in the user's language | Recalculate, add dates, houses or certainty not present in evidence |

---

## 3. Instant answer modes

**Status: IMPLEMENTED framework with explicit calculator launch gates.**

These modes are accepted by the Instant router and their answer shapes and contracts exist. A named capability is considered available only when the evidence ledger contains a result from that calculator family. Missing mandatory evidence forces a limited or insufficient-evidence result; it is never replaced with a nearby summary.

### 3.1 Explanation or mechanism

**Used for:** “Why did you say October is stronger?” or “How did you predict promotion?”

**Evidence needed:** the exact earlier conclusion, activation mechanism, relevant house activation, dasha evidence and transit evidence used for that conclusion.

**Output:**

1. answer the “why” directly;
2. give the exact evidence chain in compact form; and
3. correct the earlier answer if it was too strong.

**Must not:** start a new broad reading, defend an unsupported claim, or wander into unrelated timing.

---

### 3.2 Trait or nature

**Used for:** “What kind of person am I?”, “How do I react under pressure?”

**Evidence needed:** natal personality structure, ascendant and Moon context, relevant lords and placements, area-specific behaviour evidence, and useful divisional confirmation.

**Output:** core temperament, emotional style, communication or expression, pressure response, observable behaviour, one strength and one caution.

**Must not:** let the current dasha become the entire personality, give generic praise, or turn the answer into event timing.

---

### 3.3 Person or relationship profile

**Used for:** “What will my spouse be like?” or “What is my mother-in-law's nature?”

**Evidence needed:** the correct derived-house frame for that person, the topic houses, person-profile signals, relevant divisional confirmation and supported activation mechanisms.

**Output:** clearly name whose profile is being described, then temperament, values, relating or communication style, and one caution.

**Important wording:** when only the native's chart is available, say **“Your chart's indications for your spouse…”**. Do not pretend we have the other person's birth chart.

**Must not:** use the native's ascendant as the other person's ascendant, call the native's dasha “her dasha” or “his dasha,” or add marriage timing unless asked.

---

### 3.4 Timing window or period forecast

**Used for:** “How is my career this year?”, “How will my health be in the next six months?”, “How is today?”

**Evidence needed:** natal promise for the topic, every material dasha phase inside the requested period, activated houses, topic confirmation, pressure indicators and dated transit activations or peaks.

**Output:**

1. direct overall verdict for the requested life area;
2. chronological phase changes across the whole period;
3. what each phase means in real life;
4. strongest opportunity and main pressure;
5. strongest supported peak, if one exists; and
6. one practical takeaway.

**Example shape for career:** “The year is productive but demanding. January–April brings heavier execution and competition. April–September favours consolidation. Activity rises after September, with the strongest supported delivery window in December.”

**Must not:** list dashas and houses without explaining the outcome, describe a whole year from one static dasha, or call a period a peak without a supplied transit activation peak.

---

### 3.5 Event likelihood or timing

**Used for:** “When will I get married?”, “Will I get promoted this year?”, “When will I get a job?”

**Evidence needed in this order:**

1. **Natal promise** — does the chart support the event?
2. **Dasha permission** — which future periods activate the event-producing houses and planets?
3. **Transit delivery** — when do transits repeat or trigger those natal and dasha connections?
4. **Confirmation** — relevant divisional, KP or Jaimini support where available.
5. **Ranked windows** — strongest, secondary and weaker windows inside the requested horizon.

**Transit delivery should examine:**

- transit connections with the active dasha planets' natal positions;
- repeated activation of the relevant natal houses;
- transit through a nakshatra connected to the natal nakshatra lord, when the calculator exposes it; and
- the existing house-activation and KP-active-house results.

**Output:** conditional yes/no/delayed/uncertain verdict, the best supported window, secondary window if useful, what supports it, what may obstruct it, and one natural follow-up question.

**Must not:** promise an event merely because houses are active, invent a date, use only the current dasha when a later period is stronger, or confuse a personal event window with a muhurat.

---

### 3.6 Potential or capacity

**Used for:** “Am I suited for business?”, “Can I succeed as a lawyer?”

**Evidence needed:** natal promise for the ability, supporting houses and lords, relevant divisional confirmation, and stable capacity indicators. Current timing is secondary unless the user asks “when.”

**Output:** direct statement of capacity, best-fit expression, main limitation, and practical direction.

**Must not:** confuse permanent ability with current timing or give generic encouragement without evidence.

---

### 3.7 Comparison or choice

**Used for:** “Business or job?”, “Promotion or job change?”, “Which of these two options is better?”

**Evidence needed:** separately calculated, option-specific evidence for every named option, with the same time horizon and comparable scores or criteria.

**Output:** compare each option, identify the stronger one only when the evidence gap is meaningful, state the distinct risk of each, and give a practical recommendation. If the result is close, say it is close.

**Must not:** choose a winner from shared general evidence, analyse only one side, or call an option “slightly stronger” after the evidence verdict says it is a close call.

---

### 3.8 Problem diagnosis

**Used for:** “Why is my career stuck?”, “Why does money not stay?”, “Why did this problem happen?”

**Evidence needed:** vulnerable topic areas, natal promise or weakness, current dasha activation, current or past trigger evidence, target-person frame when relevant, and supported pressure indicators.

**Output:** the real-life problem first, then the supported cause, the trigger that made it tangible if available, what changes it, and practical handling.

**Must not:** use generic reassurance, manufacture a dramatic cause, automatically show remedies, or claim medical causation.

---

### 3.9 Remedy or action plan

**Used for:** only an explicit remedy follow-up such as “Show my remedies.”

**Evidence needed:** the priority problem already established, relevant dasha and risk evidence, calculated special points where used, and the bounded remedy blueprint.

**Output:** a small number of relevant, prioritised actions or remedies and one caution.

**Must not:** infer remedy mode merely because the user asks “what should I do?”, show a generic catalogue, or use fear to sell a remedy.

---

### 3.10 Topic reading

**Used for:** “How is my career?”, “How is my relationship with my wife?”, “What should I focus on at work now?” when no bounded future period or specific event is requested.

**Evidence needed:** natal topic foundation, current timing, topic activations, support and pressure, plus relevant divisional or KP confirmation.

**Output:** plain verdict, likely real-life manifestations, strongest support, main friction, and practical direction.

**Must not:** dump house numbers, turn it into a lifetime reading, or invent exact timing that was not requested.

---

## 4. Distinct question flows

**Status: IMPLEMENTED as distinct planner and evidence-ledger flows. Runtime answers remain launch-gated when their dedicated calculator result is absent.**

These questions should not be forced into an ordinary predictive answer mode.

| Question type | Correct handling | Current review status |
|---|---|---|
| **Chart Facts** | Return exact calculated facts from any supported chart or system. Clearly name the chart, calculation setting and reference time. Do not turn the fact into a prediction unless the user separately asks for interpretation. | IMPLEMENTED for supported D charts, Swamsa and Karakamsha; unsupported charts are reported missing, never guessed |
| **Location Recommendation** | Clarify the user's goal and geographical scope, then rank goal-specific places, directions or location qualities using a dedicated location method. | IMPLEMENTED contract; answer is blocked unless the dedicated location result is exposed |
| **Muhurat / Election** | Require event, verified location, timezone and usable date range; call the dedicated Muhurat calculator and return ranked slots with support and blocks. | IMPLEMENTED distinct flow with verified/saved location; answer is blocked if calculation is absent |
| **Multi-part Question** | The LLM identifies that the message contains materially different questions and asks the user to send one question at a time. It may briefly list the detected parts so the user can choose. | IMPLEMENTED early return; zero astrology calculators run |
| **Compatibility** | Not included in the current Instant launch scope. Direct the user to the dedicated Partnership product when appropriate. | OUT OF SCOPE for Instant |

This distinction prevents a fast predictive answer from pretending to perform an exact lookup, compatibility, muhurat or location analysis.

### 4.1 Chart Facts must cover all supported charts

Chart Facts is not limited to D1 placements. It must be able to answer exact, non-predictive questions about:

- D1 and every supported divisional chart, including D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60 where the platform calculates them;
- transit charts at a supplied date, time, location, ayanamsha and node setting;
- Rashi, house, longitude, nakshatra, pada, retrograde and combustion status;
- ascendant and house cusps;
- Vimshottari and other supported dasha start/end dates and current levels;
- Chara Karakas, Karakamsha and Swamsa;
- KP cusps, star lord, sub lord, sub-sub lord and significators;
- Ashtakavarga, Shadbala, Yogas and other calculated technical outputs;
- special points such as Upapada, Darakaraka, Yogi, Avayogi, Badhaka and Maraka when calculated; and
- the calculation settings used, where those settings can change the result.

**Output format:** direct fact first, then a compact source label such as “D12 · Lahiri · Mean Node · birth time …”. No life prediction, generic advice or unrelated dasha commentary.

If the requested chart or fact cannot be calculated from the selected birth data, ask for the one missing input or state that the platform does not currently calculate it.

---

## 5. Evidence by life domain

**Status: IMPLEMENTED coverage registry.** The catalogue is an executable audit contract; calculator availability is still evaluated per requested operation at runtime.

The table below shows the current **intended evidence recipe**. A requested item may still be reported as missing if the current calculator gateway does not expose it.

| Domain | Main houses | Important supporting evidence |
|---|---|---|
| **Career / job / promotion** | 2, 6, 10, 11 | Career promise, dasha windows, house activations, D10, KP 10th cusp and active houses, Amatyakaraka, career transit triggers |
| **Business** | 2, 7, 10, 11 | Business promise, D10, KP 7th and 10th cusps, active houses, business transit triggers |
| **Marriage** | 2, 7, 11; 5 supports | Marriage promise, D9, KP 7th cusp, Darakaraka and Upapada, marriage transit triggers |
| **Love / relationship** | 2, 5, 7, 11 | Relationship foundation, D9, KP 7th cusp and active houses, relationship transit triggers |
| **Wealth / finance** | 2, 5, 9, 11 | Wealth foundation, current dasha, activations, KP active houses, wealth transit triggers |
| **Health** | 1, 6, 8, 12 | Health foundation, current dasha, activations, KP active houses, health triggers and explicitly calculated body-area susceptibility |
| **Children / progeny** | 2, 5, 11 | Progeny promise, D7, KP 5th cusp, dasha windows, progeny transit triggers |
| **Property / home** | 2, 4, 11, 12 | Property promise, D4, KP 4th cusp, dasha windows, property transit triggers |
| **Education** | 2, 4, 5, 9, 11 | Education promise, D24, KP 4th and 9th cusps, dasha windows, education transit triggers |
| **Foreign travel / relocation** | 3, 7, 9, 12 | Foreign promise, D4, KP 9th and 12th cusps, dasha windows, foreign transit triggers |
| **Mother** | 4 | Derived frame, D12, KP 4th cusp, current dasha and mother-related triggers |
| **Father** | 9 | Derived frame, D12, KP 9th cusp, current dasha and father-related triggers |
| **Siblings** | 3, 11 | Correct younger/elder derived frame, D3, KP 3rd and 11th cusps, sibling-related triggers |
| **Family** | 2, 4 | Family foundation, D12, KP 2nd and 4th cusps, family-related triggers |
| **Spirituality / purpose** | 5, 8, 9, 12 | Spiritual foundation, D9, Karakamsha and Swamsa, current dasha and spiritual triggers |
| **Vehicles** | 4, 11, 12 | Vehicle promise, D4, KP 4th cusp, dasha windows and vehicle transit triggers |
| **General timing** | Depends on the question | Current dasha, activations, KP active houses and only the topic-relevant evidence |

### 5.1 Expanded launch domain catalogue

The router must be able to express all of the following without using brittle keyword rules. Several are specialised subdomains because they require different astrological and safety evidence even when they belong to a broader life area.

| Domain or subdomain | Typical questions | Minimum evidence family before answering |
|---|---|---|
| **Self, temperament and behaviour** | “What kind of person am I?”, anger, communication, confidence | Natal personality axes, ascendant/Moon, relevant lords, observable behaviour confirmation |
| **Life direction and purpose** | “What should I do with my life?”, dharma, fulfilment | D1, D9, 1/5/9/10 houses, Atmakaraka, Karakamsha/Swamsa, dasha support when asking “now” |
| **Career and profession** | career outlook, role, recognition, workplace | Career promise, 2/6/10/11, D10, KP 10th, Amatyakaraka, dashas and career triggers |
| **Employment and job search** | getting a job, unemployment, joining date | Service/employment promise, 2/6/10/11, D10, KP 6th/10th/11th, dasha permission, transit delivery |
| **Promotion and authority** | promotion, leadership, government authority | 1/6/10/11, Sun/Saturn and relevant karaka support, D10, KP 10th/11th, ranked timing windows |
| **Job change or resignation** | switch, transfer, resign, role transition | Existing-job and change houses compared, D10, KP evidence, dasha and transit change triggers |
| **Business and entrepreneurship** | starting or growing a business | 2/3/7/10/11, D10, Mercury/Mars and business karakas as applicable, KP 7th/10th/11th, timing |
| **Business partnership** | partner reliability, partnership problems | Native's business-partnership promise and current timing; two-person compatibility is a separate product |
| **Projects, launches and execution** | audacious project, product launch, completion | Natal capacity, 3/6/10/11, active dasha delivery, transit activation timeline, execution risks |
| **Income and compensation** | salary, raise, professional income | 2/6/10/11, career context, D10, dasha and transit delivery |
| **Savings and wealth accumulation** | savings, wealth growth, money retention | 2/5/9/11, wealth promise, active periods, gain and loss modifiers |
| **Debt, loans and repayment** | loan approval, debt pressure, repayment | 2/6/8/11/12, debt promise, repayment/support houses, dasha and dated triggers |
| **Investment and trading risk** | investing, trading, speculation | 2/5/8/11/12, risk capacity, D2 where reliable, dasha/transit support; no guaranteed-return language |
| **Inheritance, insurance and settlements** | inheritance, insurance payment, alimony/settlement | 2/8/9/11, relevant family frame, legal/settlement evidence, dasha and transit delivery |
| **Marriage likelihood and timing** | “When will I marry?” | Natal promise, 2/7/11, D9, KP 7th, Darakaraka/Upapada, dasha permission, double transit and delivery triggers |
| **Love and romantic relationship** | love life, dating, commitment | 5/7/11, D9, KP 5th/7th, dasha and relationship triggers |
| **Existing marriage** | quality, conflict, separation risk, reconciliation | 2/7/8/11/12, D9, KP 7th, current dasha and transit pressure/support; no certainty of divorce |
| **Separation, divorce and reconciliation** | “Will we separate?”, “Will my spouse return?” | Existing-marriage promise, separation/reunion indicators, D9, KP, dasha permission and transit delivery; clarification of relationship status is mandatory |
| **Spouse or relative profile** | spouse, in-laws, parents, siblings, children | Correct derived-house frame plus relevant divisional and topic evidence; state that it is derived from the native's chart |
| **Family and domestic life** | family harmony, home environment | 2/4 and relevant derived houses, D12, current dasha and family triggers |
| **Mother** | mother's nature, relationship, wellbeing | Correct 4th-house frame, D12, KP 4th, dasha and triggers |
| **Father** | father's nature, relationship, wellbeing | Correct 9th-house frame, D12, KP 9th, dasha and triggers |
| **Siblings** | younger/elder sibling and relationship | Correct 3rd/11th derived frame, D3, KP 3rd/11th, dasha and triggers |
| **Children and progeny** | childbirth promise, timing, relationship with child | 2/5/11, D7, KP 5th, Jupiter/child karaka support, dasha and double-transit delivery |
| **Education and learning** | course, academic progress, higher education | 2/4/5/9/11, D24, KP 4th/5th/9th, dasha and education triggers |
| **Exams and competitive selection** | pass an exam, government selection, interview | Education promise plus 3/6/10/11 competition/result houses, D24/D10 as relevant, KP and dated timing |
| **Property, land and home** | buy/sell house, construction, possession | 2/4/11/12, D4, KP 4th, dasha and property transit triggers |
| **Vehicles** | purchase, sale, ownership issues | 4/11/12, D4/D16 where used, KP 4th, dasha and vehicle triggers |
| **Foreign travel** | trip, overseas opportunity | 3/7/9/12, travel promise, dasha and dated triggers |
| **Immigration and relocation** | visa, permanent settlement, moving abroad | 3/4/7/9/12, D4, KP 9th/12th, settlement promise, dasha and transit delivery |
| **Location recommendation** | best city/country/direction for a goal | Dedicated location method with clarified goal, scope and candidate places; separate from relocation timing |
| **General health susceptibility** | health outlook, vulnerable areas | 1/6/8/12, health foundation, explicitly calculated body zones, dasha and health triggers; never diagnose |
| **Disease or recurring condition** | repeated illness or chronic tendency | General health evidence plus condition-relevant calculated zones; answer only as susceptibility and timing pressure, not medical diagnosis |
| **Mental and emotional wellbeing** | anxiety, stress, emotional pressure | Moon/Mercury and 1/4/5/6/8/12 evidence, D30 where reliable, dasha/transit pressure; encourage professional support when appropriate |
| **Surgery** | need, timing or recovery support for surgery | Natal surgical susceptibility, 1/6/8/12 and body-area evidence, Mars/Saturn and relevant karakas, D30 where validated, dasha permission, double transit and ranked triggers; medical decision remains with doctors |
| **Accident and injury** | accident risk, why an injury occurred, vulnerable period | Accident susceptibility, 1/3/6/8/12, Mars/Saturn/Rahu/Ketu only when calculated, D3/D30 where validated, dasha plus dated transit trigger; no fear-based certainty |
| **Recovery and rehabilitation** | recovery period after illness/injury | Supported recovery houses and karakas, dasha progression and transit improvement windows; never promise medical outcome |
| **Legal disputes and litigation** | court case, dispute, settlement | 6/7/8/9/10/11/12 as relevant, opponent frame, KP 6th/7th/11th, dasha and resolution triggers; no legal advice |
| **Competition, rivals and enemies** | winning competition, workplace opposition | 3/6/10/11, strength versus obstruction, current dasha and transit triggers |
| **Reputation and public standing** | reputation, scandal, visibility | 1/5/9/10/11, D10, Sun and relevant karakas, KP 10th, dasha/transit support and risk |
| **Government and official matters** | approvals, authority, public service | Sun/Saturn and 6/9/10/11 evidence, D10, KP, dasha and dated official-result triggers |
| **Friends, networks and community** | friendships, social circle, helpful contacts | 3/7/11, relevant lords and karakas, current dasha, network support and conflict triggers |
| **Creativity, arts and public performance** | writing, music, acting, content creation | 2/3/5/10/11, Venus/Mercury and relevant karakas, D10/D24 where relevant, dasha and visibility triggers |
| **Sports and physical competition** | athletic potential, tournament or competitive performance | 1/3/5/6/10/11, Mars and strength evidence, D3/D10 where validated, dasha and dated competition triggers |
| **Research, occult and deep study** | research aptitude, astrology, hidden subjects | 5/8/9/12, Mercury/Jupiter/Ketu only when relevant, D20/D24, dasha support |
| **Spirituality and practice** | spiritual growth, teacher, practice | 5/8/9/12, D9, Atmakaraka, Karakamsha/Swamsa, current dasha and spiritual triggers |
| **Karma and repeating life patterns** | repeated themes, “why does this keep happening?”, past-life framing | Repeating natal and dasha patterns, relevant domain evidence, Karakamsha/Swamsa where applicable; present as symbolic astrological interpretation, not provable historical fact |
| **Retirement and later-life transition** | retirement timing, life after work | Career-to-withdrawal transition, 4/9/10/12, income security, dasha progression and transit triggers |
| **Adoption, stepchildren and guardianship** | adoption timing, relationship with non-biological child | Clarified relationship/legal context, child and legal domains combined, D7 and relevant derived frame, dasha and transit support |
| **Remedies** | explicit request for remedies | Previously established problem and bounded remedy blueprint; not a generic prediction mode |
| **Muhurat** | best time for an action | Dedicated event-specific Muhurat calculator with date range, location and timezone |

### 5.2 Separate technical or horary-style requests

The following are not ordinary natal-domain questions and should not be answered by pretending the existing birth-chart evidence is sufficient:

| Request | Required handling |
|---|---|
| **Birth-time rectification** | Dedicated rectification workflow using known life events; never change stored birth time from a chat guess |
| **Unknown birth time** | Explain which calculations are unavailable and use only methods explicitly designed for missing time |
| **Lost object, missing person or immediate yes/no Prashna** | Dedicated Prashna/horary method with question time and location, or mark unsupported |
| **Name selection / naming astrology** | Dedicated naming method with the required birth/nakshatra rules; do not improvise from natal prose |
| **Matching a date to a personal event** | Distinguish personal event timing from Muhurat; use both only when the product explicitly combines them |
| **Chart correction or software discrepancy** | Return exact calculation facts, settings and formulas through Chart Facts; do not resolve it through predictive prose |

### 5.3 Questions that require safety boundaries rather than ordinary prediction

The following must be separately identified by the LLM and handled with a safety-aware answer contract:

- death date, exact lifespan or certain fatal-event prediction;
- medical diagnosis, cancer prediction or replacing medical treatment;
- guaranteed investment return, gambling win or certain financial profit;
- guaranteed court outcome or replacement for legal advice;
- criminal accusation, infidelity presented as fact, or claims that another person is certainly deceiving the user;
- pregnancy or childbirth medical safety presented as a substitute for an obstetrician; and
- coercive, fear-based or expensive remedies.

The system may offer bounded astrological tendencies and practical, non-diagnostic guidance, but it must not provide false certainty in these areas.

### Health limitation

Health answers describe **astrological susceptibility**, not diagnosis. The answer may name a body area only when that exact area is present in calculated health evidence. No illness, recovery promise or danger window may be invented.

---

## 6. What the evidence ledger records

The evidence ledger is the auditable bridge between calculators and the answer.

| Record | What it means |
|---|---|
| **Current dasha** | The exact current MD, AD and PD levels supplied by calculation |
| **Active houses** | Houses currently activated by the available activation logic |
| **Primary drivers** | The strongest facts that should control the verdict |
| **Secondary modifiers** | Support, pressure or caution that modifies but does not silently replace the primary result |
| **Divisional confirmation** | Relevant D-chart confirmation that the gateway currently exposes |
| **KP signals** | Available KP significators, cusp or active-house evidence |
| **Current transits** | Topic-relevant current transit evidence |
| **Event timing verdict** | Supported timing direction and ranked windows |
| **Transit activation timeline** | Dated periods that pass natal-promise, dasha-permission and transit-delivery gates |
| **Future dasha windows** | Future MD/AD/PD periods inside the requested horizon |
| **Option comparison** | Separate evidence and comparison result for every named option |
| **Health body area** | Explicitly calculated susceptibility zones, if available |
| **Claim gates** | Rules such as “do not call this highly active unless a peak window exists” |

Every record should have a source, evidence ID, strength and value. This allows the test UI to show exactly why an answer was permitted.

---

## 7. What is sent to the final Instant answer model

The v2 design does **not** intend to send the entire raw chart workspace to the final writer. The final composer receives a compact, verdict-first brief containing:

- basic native identity needed for natural wording;
- the structured intent: domain, answer mode, time window and target person;
- the query plan and the user's real goal;
- the fused verdict, confidence and ranked windows;
- only the answer-bearing evidence needed for this question;
- missing required capabilities;
- the answer blueprint and forbidden-claim contract; and
- at most the most recent dialogue item needed for continuity.

For a period forecast, the compact evidence can include chronological phases, active areas, topic confirmation, transit peaks, key support and key risks. For a health answer, it can include only allowed susceptibility zones. For a comparison, it can include option-specific evidence.

### Important current limitation

The present `capability_gateway` consumes the **already-calculated Instant context** and converts it into the ledger. It does not yet independently execute every named Parashari, KP, Jaimini, divisional and transit operation in the methodology registry.

The present Instant v2 methodology registry also has **no explicit Nadi calculator capability**. Nadi must not be claimed as part of an Instant answer's evidence until a real Nadi operation is defined, executed and represented in the ledger. This does not describe the wider Standard or Premium pipelines; it is specifically a current Instant v2 gap.

Therefore:

- **required evidence** means what the method needs for a strong answer;
- **available evidence** means what the existing Instant context actually supplied; and
- **missing required capability** means the answer must be limited rather than invented.

This is the main implementation boundary we must review carefully. A methodology name in the registry is not proof that its dedicated calculator is already being called.

---

## 8. Standard Instant output contract

**Status: IMPLEMENTED.** There is no hard 120-word product limit; each answer mode has a proportional target and a larger safety ceiling.

There is no universal word ceiling. Instant should remain conversational and concise, but the correct length depends on the question:

- a Chart Fact may need one or two sentences;
- a simple topic answer may need roughly 100–160 words;
- a period forecast with materially different phases may need roughly 150–250 words;
- an event-timing answer may need enough space to give the verdict, windows, confidence evidence and caution; and
- an explanation requested by the user may be longer because the evidence chain is the point of the answer.

The composer should stop when it has answered the question properly. It must not pad an answer merely to reach a target.

### Default order

1. **Direct real-life answer** in the first sentence.
2. **Likely manifestation**: what the user may actually experience.
3. **Timing or phase difference**, only when relevant and supported.
4. **Understandable astrological basis** in every answer. Normally this should be one or two compact sentences naming the most important dasha, transit, divisional or karaka support without dumping the full evidence ledger.
5. **One material caution**, only when supported.
6. **One natural follow-up question** that continues the real conversation.

### Presentation rules

- Use daily language in the user's selected language and script.
- Stream short message-sized paragraphs rather than waiting for one large block.
- Lead with the answer, not “Saturn activates house 2.”
- Do not show remedies, feedback cards, mode suggestions, disclaimers or sales material inside an active Instant conversation.
- Do not automatically speak the answer. Show it first; the user may choose Listen.
- Show enough astrology in every answer for the user to recognise that it is chart-based. Keep the calculation workspace hidden, but do not make the result sound like generic AI advice.

### Forbidden output

- unsupported exact dates or certainty;
- house, lordship, placement or transit claims absent from evidence;
- generic “deeper reading would help” sales language;
- fear-based urgency;
- lists of planets and houses that make the user interpret the answer;
- calling a derived-person reading that person's own chart;
- choosing between options without option-specific evidence;
- calling background activity a “peak”; and
- repeating a clarification already resolved in conversation.

---

## 9. Example: “When will I get married?”

### Step 1: LLM understanding

- Operation: event likelihood or timing
- Domain: marriage
- Subject: self
- Time request: future; ask for horizon only if the conversation does not provide one
- Answer mode: event prediction

### Step 2: Evidence request

- natal marriage promise;
- relevant D1 and D9 support;
- KP 7th-cusp chain and active houses;
- Jaimini Darakaraka / Upapada support where available;
- future dasha periods activating 2, 7 and 11, with 5 as support;
- pressure from 1, 6, 8, 10 or 12 as modifiers, not automatic denial;
- dated transit triggers that repeat the natal and dasha promise; and
- ranked windows inside the chosen horizon.

### Step 3: Fusion

The verdict should separately decide:

- whether marriage is promised strongly, conditionally or weakly;
- which dasha periods permit the event;
- which transit windows are capable of delivering it;
- which window is strongest and why; and
- what factor may delay or complicate it.

### Step 4: User-facing answer shape

> “Marriage is supported, with the strongest window between [supported dates]. An earlier period around [secondary window] can bring a serious connection or decision, but the later window has stronger commitment and completion support. The main caution is [supported real-life pressure]. This result comes from the marriage promise being repeated by both the active period and the dated transit triggers. Are you currently in a relationship, or are you asking about a new match?”

The bracketed content must come from evidence. The composer cannot fill it from general astrological knowledge.

---

## 10. Clarification behaviour

Instant Chat should feel like a real astrologer, not a form.

### Ask one clarification when

- a pronoun or person is unresolved: “Will he return?”;
- a user requests compatibility; explain that it belongs to the dedicated Partnership product rather than trying to complete it inside Instant;
- muhurat lacks event, location, timezone or usable date range;
- a location recommendation lacks goal or India/abroad scope;
- named options are unclear; or
- the timeframe materially changes the required calculation.

If a question is multi-part, do not choose one part silently. Say, for example: “You have asked about career timing and marriage. I can calculate one accurately at a time—which one should we start with?”

### Do not ask again when

The user has answered the clarification. The conversation state must merge “spouse,” “first marriage,” or a correction such as “not my boyfriend—my husband” into the original question.

### Clarification questions are not predictions

They should be short, natural, and normally should not trigger a full calculation or consume the same response effort as a completed astrological answer.

---

## 11. Current implementation status

### Already represented in code

- multilingual LLM-owned intent and answer-mode routing;
- ten live Instant answer modes;
- subject and derived-house framing;
- domain methodology registry;
- evidence-plan compilation;
- auditable evidence ledger;
- fused verdict with missing-capability reporting;
- claim-bound answer specification;
- compact verdict-first composer brief;
- word limit and output-order contract; and
- test evidence surfaced for review.

### Still requiring design or implementation completion

- making exact chart facts a first-class live mode;
- fully wiring location recommendations;
- multi-part detection and the one-question-at-a-time clarification response;
- ensuring every named methodology operation executes a real calculator rather than relying on an aggregated context substitute;
- confirming that transit activation includes the required natal-position and nakshatra-lord repetition logic for every timed domain;
- excluding compatibility from Instant and keeping Muhurat in its dedicated flow;
- systematic astrology acceptance tests across all question families; and
- confirming actual prompt size, evidence use and response correctness in production-like tests.

---

## 12. Approved evidence-confidence policy

### 12.1 Event timing minimum

**Dasha support is mandatory.** Without a supportive dasha period, Instant must not give a positive event-timing prediction merely from transit activity.

### 12.2 Confidence layers

| Evidence present | Permitted conclusion |
|---|---|
| **Dasha support only** | A possible or permitted period, with low-to-moderate confidence; do not call it a delivery peak |
| **Dasha + relevant transit support** | Stronger timing support; may identify an active window when the transit is dated and topic-relevant |
| **Dasha + transit + relevant divisional confirmation** | High confidence in the topic promise and timing direction |
| **Dasha + transit + divisional + double-transit support** | High support for event manifestation in the supplied window |
| **Dasha + transit + divisional + double transit + relevant karaka support** | Highest available confidence, subject to contradictory evidence and real-world uncertainty |

Confidence is not a simple count. A contradiction can lower confidence, and the evidence must be relevant to the exact event. Karaka support cannot replace missing dasha permission.

### 12.3 Double-transit requirement

The methodology must define “double transit” precisely for each event family. The evidence record must state:

- which two slow-moving transit influences are being used;
- which natal house, lord, event point or dasha planet each is connecting with;
- the dates during which both conditions are active; and
- whether the result supports promise, delivery or pressure.

The composer may not simply say “double transit supports this” without this record.

### 12.4 Karaka support

The relevant karaka depends on the event. The evidence plan must request and record the correct karaka rather than generically treating Jupiter or Venus as support for every event.

### 12.5 Missing evidence and clarification

When required evidence is missing because the user's meaning, subject, timeframe, option, place or event is unclear, ask **one focused clarification** before calculating.

When the missing item is a technical capability that the user cannot supply, do not ask a meaningless clarification. The system should say that it cannot yet calculate that question responsibly, or provide only the strictly supported part while clearly naming the limitation. Before launch, all evidence marked mandatory for a supported question family must be implemented so this technical limitation is exceptional.

## 13. Remaining review checklist

The product decisions are now approved. The remaining review is technical and astrological:

1. Confirm the complete launch domain catalogue.
2. Approve the exact evidence recipe for each specialised domain, especially surgery, accident, litigation, debt, exams, separation and inheritance.
3. Define the precise double-transit rule for each timed event family.
4. Map every methodology operation to a real calculator endpoint and evidence schema.
5. Decide which question families are launch-supported and which should return “not yet supported.”
6. Build acceptance cases with known charts and astrologer-reviewed expected evidence.
