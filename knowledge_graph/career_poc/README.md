# AstroRoshni Career ontology proof of concept

This is a deliberately small, editable ontology for validating the knowledge-graph model before hosting WebProtege or making the graph a runtime dependency. The canonical source is `astroroshni-career-poc.ttl`; `career-runtime-preview.json` is generated and must not be hand-edited.

## What the proof of concept covers

Version 0.5.0 models all 28 Career subtypes supported by the pre-graph Instant
Chat implementation. Every question type has expandable decision-stage
children, and every decision stage has required astrology-factor children.

| Question | Runtime topic | Reasoning path |
|---|---|---|
| How is my career overall? | `general` | Static D1 + D10 + Jaimini synthesis; no unsolicited timing |
| What kind of career suits me? | `career_fit` | Vocation and work-function synthesis; no unsolicited timing |
| Should I leave my current job? | `resignation` | Stay/change/separation/landing decision matrix with dasha and transit |
| Why am I not getting recognition despite working hard? | `recognition` | H6 effort -> H10 visibility -> H11 recognition -> H2 compensation diagnosis |
| How will my relationship with my manager develop? | `manager_relationship` | H9 guidance/manager + H10 authority + H6 friction + H11 support |
| When will I get promoted? | `promotion` | Visibility, recognition and compensation stages with dasha + transit confirmation |
| Will I get a salary increase? | `salary_increase` | H2 compensation + H10 role + H11 gain; income activity alone is insufficient |
| Should I choose business or employment? | `business_vs_employment` | H6 service versus H3/H7 enterprise, anchored by H10/H11 viability |
| Is this a good period for changing jobs? | `job_change_timing` | Movement, separation and landing rules evaluated separately |
| Why am I facing conflict at work? | `workplace_conflict` | H6 friction + H9 manager/guidance + H10 authority + H11 allies |

The remaining parity routes are `employment`, `offer`, `joining`,
`job_security`, `business`, `business_launch`, `business_success`, `project`,
`leadership`, `government`, `foreign_career`, `return_to_work`,
`career_stagnation`, `colleague_relationship`, `subordinate_relationship`,
`client_relationship`, `business_partner_relationship`, and
`mentor_relationship`. Career stagnation and recognition remain distinct
diagnostic routes.

This is ontology policy, not an astrology calculator. It describes **what must be calculated, what must not be introduced, which capability supplies it, how the evidence is explained, and what answer contract is used**. Existing deterministic calculators continue to calculate the chart.

## Schema in plain English

- `LifeDomain`: Career now; Health, Marriage and other modules later.
- `QuestionType`: a semantic intent returned by the multilingual intent LLM. It is not a keyword list.
- `AstrologyFactor`: houses, charts, Jaimini factors and timing factors required for a question.
- `CalculatorCapability`: an abstract executable operation bound to current application code.
- `DecisionRule`: a deterministic rule such as H6+H10 for current-job continuity.
- `EvidencePolicy`: how calculator results must be explained in “Why Tara says this.”
- `AnswerContract`: ordered semantic sections the writer must deliver in the user's selected language.
- `Guardrail`: invalid reasoning to prevent, such as giving dates for an overall-career question.

The key separation is:

```
multilingual question -> semantic QuestionType -> ontology contract
                    -> deterministic calculators -> evidence packet
                    -> one LLM answer writer -> localized answer
```

The graph does not parse the user's language and does not write the final answer. This preserves all-language support while making the astrology plan editable and testable.

## Validate locally

No new Python dependency is required:

```bash
python3 scripts/validate_career_ontology.py
```

The validator checks graph integrity and all 28 competency contracts. It generates:

- `career-runtime-preview.json`: an immutable runtime policy bundle for the backend.
- `career-validation-report.md`: a readable route-by-route review report.

It is a contract compiler/validator, not a full OWL reasoner. The generated files must not be hand-edited.

Run the focused contract tests with:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_career_ontology_contract.py -q
```

The backend adapter is `backend/instant_chat_v2/career_graph_policy.py`. It performs constant-time lookup against the compiled bundle and never queries WebProtege in a live request.

The graph is connected live through
`backend/instant_chat_v2/graph_live.py` and
`backend/instant_chat_v2/career_graph_runtime.py`. Before answer generation it
resolves:

- the routed Career question type and answer mode;
- graph-required factors against the evidence actually sent to the writer;
- graph exclusions, such as unsolicited dasha/transit evidence on a static question;
- the graph's calculator capabilities, decision rules and guardrails.

The live contract records typed evidence states such as
`answer_mode`, `missing_required_factors`, `unexpected_default_exclusions`, or
`unmapped_runtime_route`. The parity contract test requires every declared
legacy Career subtype to resolve to a compiled graph route; the mismatch remains
as a defensive signal for unexpected future routes.

The selected graph policy is attached to the deterministic answer specification
before the composer prompt is built. Its decision rules, guardrails, required
output sections and excluded factors are therefore enforced during generation.

## Import into WebProtege

1. Create a blank project in WebProtege.
2. Choose **Project -> Upload and merge** (wording can vary by WebProtege release).
3. Upload `astroroshni-career-poc.ttl` as Turtle/RDF.
4. Review `QuestionType` individuals first, then follow their `requiresFactor`, `requiresCapability`, `usesAnswerContract`, `hasEvidencePolicy` and `hasGuardrail` relations.
5. Give domain experts edit access and application engineers review/publish access.

Before hosting, also open this file once in Protege Desktop or WebProtege and run its ontology parser. For production CI, use ROBOT plus SHACL rather than relying only on the dependency-free validator.

## How you extend it yourself

For a new Career question:

1. Add a `QuestionType` individual with a permanent `stableId` and current backend `runtimeKey`.
2. Link only the houses and charts needed to answer it.
3. Link calculator capabilities; never put calculated chart values into the ontology.
4. Set default exclusions, especially timing for static questions.
5. Reuse or add an answer contract and an evidence policy.
6. Add at least one competency question to `competency-questions.json` before publishing.
7. Run the validator and review the generated runtime preview.

Labels and descriptions are editorial and can be translated. Stable IDs, runtime keys and calculator bindings are controlled fields and should require technical review.

## Production boundary

1. WebProtege is the authoring and review system.
2. A versioned export is committed to Git.
3. CI validates OWL/SHACL and runs competency questions.
4. The included compiler produces a compact, immutable JSON policy bundle.
5. The included backend adapter loads that bundle locally; it never queries WebProtege during a user request.
6. Live policy resolution runs against the final Instant Career route and compact evidence packet before generation.
7. Review mismatches until the graph and live behavior agree on each competency question.
8. After domain review, the graph policy can become authoritative and release metadata should record ontology, calculator and prompt versions for every answer.

This boundary keeps Instant Chat fast and prevents an authoring-server outage or accidental graph edit from affecting live answers.
