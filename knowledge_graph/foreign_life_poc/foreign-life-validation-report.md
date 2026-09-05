# Travel, Relocation and Foreign Life ontology validation report

- Ontology version: `0.1.0`
- Competency questions: **33**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `foreign_overview` | What does my chart show about travel and foreign life? | `foreign_overview` | `ModeTopic` | 11 | 1 | PASS |
| `travel_tendency` | Do I have a strong travel tendency? | `travel_tendency` | `ModeCapacity` | 6 | 1 | PASS |
| `short_travel` | Does my chart support frequent short trips? | `short_travel` | `ModeCapacity` | 4 | 1 | PASS |
| `short_travel_timing` | When is my next short trip? | `short_travel_timing` | `ModeTiming` | 7 | 2 | PASS |
| `long_travel` | Does my chart support long journeys? | `long_travel` | `ModeCapacity` | 7 | 1 | PASS |
| `long_travel_timing` | When will I make a long journey? | `long_travel_timing` | `ModeTiming` | 10 | 2 | PASS |
| `travel_purpose` | Will my travel be mainly for work, study or relationships? | `travel_purpose` | `ModeTopic` | 9 | 1 | PASS |
| `travel_obstacles` | Why are my travel plans repeatedly blocked? | `travel_obstacles` | `ModeDiagnosis` | 8 | 1 | PASS |
| `retrospective_travel` | When did my major foreign journey occur? | `retrospective_travel` | `ModeTiming` | 10 | 2 | PASS |
| `domestic_relocation` | Does my chart support relocation? | `domestic_relocation` | `ModeCapacity` | 7 | 1 | PASS |
| `domestic_relocation_timing` | When is a supportive period to relocate within my country? | `domestic_relocation_timing` | `ModeTiming` | 10 | 2 | PASS |
| `stay_vs_relocate` | Should I stay where I am or relocate? | `stay_vs_relocate` | `ModeComparison` | 9 | 2 | PASS |
| `temporary_vs_permanent` | Is foreign life temporary or permanent for me? | `temporary_vs_permanent` | `ModeComparison` | 10 | 2 | PASS |
| `foreign_travel` | Will I travel abroad? | `foreign_travel` | `ModeCapacity` | 7 | 1 | PASS |
| `foreign_travel_timing` | When will I travel abroad? | `foreign_travel_timing` | `ModeTiming` | 10 | 2 | PASS |
| `foreign_residence` | Does my chart support living abroad? | `foreign_residence` | `ModeCapacity` | 9 | 1 | PASS |
| `foreign_residence_timing` | When can I begin living abroad? | `foreign_residence_timing` | `ModeTiming` | 12 | 2 | PASS |
| `permanent_settlement` | Can I settle abroad permanently? | `permanent_settlement` | `ModeCapacity` | 9 | 1 | PASS |
| `settlement_timing` | When is permanent foreign settlement supported? | `settlement_timing` | `ModeTiming` | 12 | 2 | PASS |
| `visa_support` | Does my chart support my visa process? | `visa_support` | `ModeCapacity` | 9 | 1 | PASS |
| `visa_timing` | When is my visa process better supported? | `visa_timing` | `ModeTiming` | 12 | 2 | PASS |
| `migration_pathway` | Is work, study, marriage or family my stronger route abroad? | `migration_pathway` | `ModeTopic` | 12 | 1 | PASS |
| `return_home` | Does my chart support returning home after living abroad? | `return_home` | `ModeCapacity` | 9 | 1 | PASS |
| `return_home_timing` | When is returning home supported? | `return_home_timing` | `ModeTiming` | 12 | 2 | PASS |
| `foreign_life_adjustment` | How well will I adjust emotionally to life abroad? | `foreign_life_adjustment` | `ModeTopic` | 8 | 1 | PASS |
| `foreign_obstacles` | Why does foreign settlement keep getting delayed? | `foreign_obstacles` | `ModeDiagnosis` | 11 | 1 | PASS |
| `foreign_remedy` | Which calculated remedy supports my foreign-life obstacles? | `foreign_remedy` | `ModeRemedy` | 12 | 1 | PASS |
| `location_comparison` | Is Canada or Australia a better fit for me? | `location_comparison` | `ModeComparison` | 11 | 2 | PASS |
| `location_recommendation_handoff` | Which country in the world is best for me? | `location_recommendation_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `legal_immigration_handoff` | Am I legally eligible and will my visa be approved? | `legal_immigration_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `muhurat_handoff` | Which exact date should I depart? | `muhurat_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `travel_safety_handoff` | Can you guarantee my trip will be safe? | `travel_safety_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `other_person_handoff` | Will my adult child settle abroad? | `other_person_handoff` | `ModeHandoff` | 1 | 1 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Travel, Relocation and Foreign Life QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
