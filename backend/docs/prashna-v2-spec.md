# Praśna v2 — dependable single-lineage specification

## Product decision

Build one **Praśnatantra–Tājika question-chart system**. Do not combine it with
Praśna Mārga, KP, Parāśari voting, Jaimini techniques, tarot, numerology, or an
LLM's astrological judgement.

This choice is practical for a digital product: the method can be evaluated from
one clearly understood question, one recorded instant, and one location. Methods
that require ritual ārūḍha, cowries, gestures, omens, objects brought by the
questioner, or observations made by a trained practitioner cannot be silently
simulated by a phone.

The product promise is:

> A transparent implementation of a named classical question-chart method. It
> shows the traditional tendency, the rules that produced it, and when the method
> cannot decide. It is guidance under uncertainty, not a guaranteed fact.

Do not use "as implemented by the rishis", "certain prediction", "scientifically
proven", or "guaranteed accurate" in product copy.

## Source boundary

The normative specification must be frozen before implementation:

1. A critically examined Sanskrit edition of the Praśnatantra is the source for
   question-specific rules.
2. Saṃjñātantra/Hāyanaratna passages are used for the explicitly named Tājika
   configurations, dignities, aspects, orbs, houses, and strengths.
3. B. V. Raman's English edition is a useful translation and index, but an English
   paraphrase alone is not sufficient to resolve a disputed rule.
4. Every implemented rule has a source-ledger entry containing Sanskrit, literal
   translation, interpretive translation, edition/page/verse, required inputs,
   precedence, known variants, and implementation tests.
5. If sources disagree and no selected authority resolves the disagreement, the
   engine reports the variant. It does not average, vote, or choose whichever
   produces an answer.

Historical scholarship describes the received Praśnatantra as a hybrid Sanskrit
work with Indian and Perso-Arabic sources. "Classical" here therefore means
faithful to this declared textual tradition, not a claim of one universal ancient
Indian method.

## User contract

### A valid question

The app accepts one concrete, decision-relevant question about one defined matter.
It should normally be capable of becoming true or false, or clearly better or
worse, within a comprehensible context.

Good forms include:

- "Will this specific person call or message me?"
- "Will this person and I reconcile after our fight?"
- "Will this specific person marry me?"
- "Will I receive the job offer from Company X?"
- "Is this specific marriage proposal likely to proceed?"
- "Will this overdue payment be received?"
- "Is this particular property purchase likely to complete?"
- "Will my missing item be recovered?"
- "Is this planned journey likely to take place?"

Reject or ask the user to rewrite:

- several questions joined together;
- vague life readings such as "Tell me my future";
- repeated casting of the same unchanged question;
- an unclear subject, event, or relationship;
- requests for a guaranteed date when the selected textual rule does not supply a
  timing method;
- diagnosis, treatment, death, pregnancy certainty, legal verdict, financial
  instruction, or another high-stakes decision represented as certain.

### Selecting and casting

1. The backend publishes the enabled categories and exact supported questions,
   each with an immutable question ID.
2. The user selects a category and one question. No free-text classification or
   interpretation step is performed.
3. The backend resolves that ID to its fixed wording, topic, intent and classical
   house roles.
4. The chart instant is recorded when the user casts the selected question. The
   app records the current location and timezone at that instant.
5. That chart is immutable. Technical failure retries reuse the same instant;
   they never cast a new chart.

## Calculation profile

The production profile must contain exactly one documented choice for each item:

- zodiac and precession/ayanāṃśa;
- true or mean node, if nodes are used by a particular topic rule;
- ascendant and meridian calculation;
- house cusps and junctions;
- planet-to-house assignment;
- planetary true motion;
- orbs of light;
- combustion, solar rays, heliacal setting, and retrogradation;
- domicile, exaltation/fall, enemy signs, haddā, decan and ninth-part rulers;
- house, planet, aspect and itthaśāla strength.

For the selected Hāyanaratna profile, houses must be calculated from the ascendant
and meridian quadrants with cusps and junctions. Whole-sign occupancy cannot be
substituted. Modern ephemeris positions may be used, but the source's zodiac and
precession convention must be implemented and versioned rather than silently
replaced with Lahiri.

## Deterministic judgement pipeline

The engine evaluates and stores every intermediate result:

1. Validate the recorded instant, location, question and supported family.
2. Cast the chart using the frozen calculation profile.
3. Apply only the selected text's explicit chart-readability conditions.
4. Assign the ascendant ruler, matter ruler, Moon and any topic-specific roles.
5. Calculate house placement and all required strengths.
6. Calculate aspects, application/separation and all sixteen Tājika
   configurations, including their grades and destructive qualifications.
7. Apply the complete rule module for the selected question family, including
   exceptions and stated precedence.
8. Resolve only conclusions for which the source supplies a resolution rule.
9. If testimonies conflict without textual precedence, return **mixed**. If
   required information or a rule is absent, return **cannot judge**.
10. Calculate timing only when a documented timing rule applies. Astronomical
    contact time is not automatically an event date.

Allowed top-level results are:

- `favorable`: the complete module gives a supported positive judgement;
- `unfavorable`: the complete module gives a supported obstructed judgement;
- `mixed`: valid classical testimonies conflict without a textual resolution;
- `cannot_judge`: the question, chart, source coverage, or required input is
  insufficient.

There is no generic point score and no `any support => yes` rule. A question family
cannot be enabled in production until its entire declared module is implemented.

## Initial release scope

Start narrow. Enable modules separately in this order because their outcomes can
usually be defined and later checked:

1. lost-item recovery;
2. a specific job/application/promotion outcome;
3. receipt of a specific payment or gain;
4. renewed contact or reconciliation with one specific romantic partner;
5. a specific marriage proposal or marriage with one specific person;
6. a specific journey;
7. a specific property transaction.

Modern actions such as calling, messaging, or unblocking do not receive invented
planetary rules. They are treated as the precisely stated object of the question:
the seventh signifies the romantic counterpart or dispute (I.25), and the
declared general fulfilment rules (II.1, 3-4, 9 and 13) judge whether renewed
contact or reconciliation is supported. Marriage questions continue to use the
separate spouse-acquisition rules in II.62-66.

Health, pregnancy/children, death/longevity, litigation winners and speculative
financial questions remain unavailable until there is a separately reviewed
ethical and textual specification. The app can still encourage professional help
for those matters without producing a classical verdict.

## Explanation contract

The user sees:

1. **Your question** — the confirmed paraphrase and chart moment.
2. **Traditional indication** — favorable, unfavorable, mixed, or cannot judge.
3. **What supports this** — at most three decisive facts in everyday language.
4. **What obstructs this** — at most three decisive facts in everyday language.
5. **What this means for your decision** — a cautious practical interpretation
   that does not invent a remedy or certainty.
6. **Classical working** — expandable calculations, rule IDs, verses, variants,
   strengths and chart data.

Use "you" or a role such as "the applicant" in the primary UI. Technical terms
such as itthaśāla, radda and khallāsara appear only in the expandable working.
Do not display a numerical confidence percentage unless it comes from a published
outcome-calibration sample.

## Role of AI

AI may translate deterministic evidence into simpler language outside the
calculation contract.

AI may not:

- calculate the chart or rule matches;
- add an uncited astrological principle;
- resolve conflicting testimonies;
- infer a date, remedy, motive or promised event absent from engine evidence;
- change `cannot_judge` into a useful-sounding answer.

Every generated sentence must be traceable to structured engine fields or be
clearly labelled ordinary decision guidance.

## Reliability programme

Classical fidelity and real-world usefulness require different validation.

### Textual validation

- Have a Sanskrit scholar and an experienced Tājika practitioner review the
  source ledger and disputed readings independently.
- Build golden tests from every worked chart in the selected editions.
- Test ascendant, meridian, cusps, junctions, strengths, dignities, configurations,
  topic-rule matches and final textual resolution separately.
- Store the ruleset version with every reading so historical results remain
  reproducible.

### Outcome validation

- With consent, ask users later whether the defined event occurred.
- Freeze the prediction before learning the outcome.
- Report sample size, unresolved cases and accuracy by question family.
- Keep empirical calibration separate from the classical engine. Never tune
  hidden weights until desired answers appear.
- Do not advertise predictive reliability until the prospective sample is large
  enough and independently audited.

User trust comes from faithful calculation, visible limitations, reproducibility,
and saying `cannot_judge` when the method does not support an answer.

## Migration from the current implementation

Treat the existing engine as reference code, not as a base that must be preserved.
Reuse only components that pass the new specification independently, such as civil
time validation or raw Swiss Ephemeris access. Quarantine the current whole-sign
house assignment, partial-yoga judgement and Boolean verdict synthesis.

Implementation order:

1. Disable claims that the current verdict is a complete classical answer.
2. Build the source ledger and resolve the calculation profile.
3. Implement and golden-test astronomy, cusps, junctions and strengths.
4. Implement and golden-test all sixteen configurations.
5. Implement one complete question-family module.
6. Add the backend-owned guided-question flow and deterministic explanation model.
7. Obtain independent textual review.
8. Run a labelled pilot and outcome follow-up before enabling additional modules.

## Definition of done for one question family

A module is production-ready only when:

- every rule in its declared source boundary is represented or explicitly marked
  inapplicable with a reviewed reason;
- all shared calculation dependencies are complete;
- every output sentence is traceable;
- primary-text examples and independent hand calculations pass;
- conflicts and missing inputs fail closed;
- an external reviewer has signed off the source ledger;
- the UI never presents textual fidelity as guaranteed predictive truth.
