# Instant Career — Completion Checklist

This checklist is the delivery contract for making Instant Career reliable, specific, explainable, multilingual, and fast. An item is complete only when its implementation and regression tests both pass.

## 1. Career intent and conversation taxonomy

- [x] Distinguish general career, yearly/period outlook, job timing, specific job, offer, joining, promotion, job security, resignation, job change, career stagnation, suitable profession, job-vs-business, business launch/success, salary growth, workplace conflict, foreign career, government/private work, leadership, project success, career break and return-to-work.
- [x] Preserve the target person and career subject across follow-ups.
- [x] Ask one concise clarification when the requested career outcome or timeframe is genuinely ambiguous.
- [x] Reject or split multi-part questions rather than silently answering the wrong part.

## 2. Canonical astrology matrices

- [x] Define one canonical house/planet matrix per career subtype and remove conflicting mappings.
- [x] Keep career outcomes distinct from wealth outcomes; House 2 may explain compensation but must not replace the career answer.
- [x] Encode job, promotion, job-change and business combinations separately.

## 3. Natal promise packet

- [x] Always calculate the D1 career foundation: Houses 2, 6, 10 and 11, their lords, placements, occupants, aspects, dignity and functional condition.
- [x] Always calculate the D10 foundation: Lagna/lord, Houses 1, 6, 7, 10 and 11 as relevant, 10th lord, occupants, aspects and dignity.
- [x] Include Amatyakaraka, Sun, Saturn and Mercury; include A10/Arudha/Karkamsa only where they answer the question.
- [x] Never replace missing D1/D10 with D9 or issue a negative promise verdict merely because evidence assembly failed.
- [x] Surface a clear limited-evidence state if a mandatory calculation genuinely fails.

## 4. Career fit and working style

- [x] Reuse the existing deterministic Career Analysis engine through a compact Instant packet.
- [x] Calculate employment/business/hybrid inclination.
- [x] Calculate primary work function and rank up to three suitable fields with positive and negative evidence.
- [x] Calculate leadership/independent-contributor style, visibility and primary professional obstruction where relevant.

## 5. Career manifestation resolver

- [x] Translate activated combinations into adjudicated manifestations: workload, applications, interviews, visibility, conflict, role change, promotion, offer, joining, compensation, recognition, resignation, job loss and business expansion.
- [x] Separate Activation, Formalization/Offer, Joining/Execution and Stabilization.
- [x] Do not allow the LLM to infer a guaranteed event from house activation alone.
- [x] Attach supporting and obstructing evidence plus confidence to every manifestation.

## 6. Timing engine

- [x] Rank only present/future windows inside the requested horizon.
- [x] Require dasha support for event timing.
- [x] Raise confidence with D10 repetition, transit confirmation, double transit, natal re-contact or nakshatra-lord resonance.
- [x] Keep interview/activity windows separate from offer and joining windows.
- [x] Prevent past dates, invented exact dates and one-window-means-everything answers.

## 7. Answer contracts

- [x] General/topic answer: direct career condition, concrete lived effects, strongest support/pressure and natural follow-up.
- [x] Year/period answer: verdict, phases, likely professional outcomes, strongest window, caution and follow-up.
- [x] Event answer: possibility, activation window, offer/formalization window, joining/stabilization window and confidence.
- [x] Potential/fit answer: work function, top fields, work environment, job/business inclination and what to avoid.
- [x] Diagnosis answer: ranked cause of stagnation/problem and what changes it.
- [x] Remedy answer: actual short remedies with method, frequency and astrological reason—not generic career advice.
- [x] Keep some compact astrology in every answer without turning it into a house/dasha dump.
- [x] Produce the answer in the selected language without programmatic English rewriting.

## 8. “Why Tara says this” evidence

- [x] Group evidence as Career Foundation, Professional Signature, Current Timing, Transit Confirmation and Practical Meaning.
- [x] Show D1 and D10 facts without repetition or raw diagnostic noise.
- [x] Show the selected mode, source and confidence for internal QA without exposing implementation jargon to users.
- [x] Ensure every user-facing claim is traceable to supplied evidence.

## 9. Performance and safety

- [x] Preserve the single-LLM-call Instant contract.
- [x] Send a compact adjudicated career packet rather than the full Standard/Premium context.
- [x] Keep the first streamed text immediate and the completed answer conversational.
- [x] Avoid certainty, fabricated placements and unsupported career guarantees.

## 10. Verification suite

- [x] Add deterministic unit tests for every subtype matrix and manifestation combination.
- [x] Add regression tests for missing D1, business-house conflict, career-to-wealth drift and Activation/Offer/Joining separation.
- [x] Add conversation tests for self/spouse targeting, follow-ups and multi-part questions.
- [x] Add answer-contract tests for general, yearly, event, fit, diagnosis and remedy questions.
- [x] Add multilingual routing/output tests.
- [x] Run the focused Instant Career suite and broader Instant regression suite.
- [x] Record final test results and any deliberately deferred limitation in this document.

## Definition of done

Instant Career is complete only when all checklist items above are checked, tests pass, and representative questions produce a concrete career answer rather than an astrology summary, generic advice or a wealth forecast.

## Verification record — 23 August 2026

- Dedicated Instant Career tests: **10 passed**.
- Broader Instant routing, answer-mode, derivation and pipeline regressions: **141 passed**.
- Mobile translation audit: **passed across 11 languages**.
- Web production compile: **passed**.
- Deliberately deferred limitations: **none for this implementation scope**. Live model phrasing still remains observable runtime behaviour, while its permitted claims, evidence, format and career manifestations are bounded by the deterministic contracts covered above.
