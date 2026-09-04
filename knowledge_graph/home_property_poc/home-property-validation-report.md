# Home, Property and Vehicles ontology validation report

- Ontology version: `0.5.0`
- Competency questions: **30**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `home_overview` | What does my chart show about home life? | `home_overview` | `ModeTopic` | 4 | 2 | PASS |
| `property_potential` | Does my chart support owning property? | `property_potential` | `ModeCapacity` | 6 | 2 | PASS |
| `property_purchase` | Should I buy a home now? | `property_purchase` | `ModeDecision` | 5 | 3 | PASS |
| `property_purchase_timing` | When will I buy a house? | `property_purchase_timing` | `ModeTiming` | 8 | 3 | PASS |
| `property_sale_timing` | When should I sell my property? | `property_sale_timing` | `ModeTiming` | 9 | 3 | PASS |
| `property_finance` | Is a home loan suitable for me? | `property_finance` | `ModeDecision` | 8 | 3 | PASS |
| `property_comparison` | Should I buy or rent? | `property_comparison` | `ModeComparison` | 8 | 3 | PASS |
| `construction_renovation` | Should I renovate my house? | `construction_renovation` | `ModeDecision` | 8 | 3 | PASS |
| `relocation_home` | Would moving homes suit me? | `relocation_home` | `ModeDecision` | 7 | 2 | PASS |
| `vehicle_potential` | Does my chart support owning a vehicle? | `vehicle_potential` | `ModeCapacity` | 7 | 3 | PASS |
| `vehicle_selection` | Which colour family suits my vehicle? | `vehicle_selection` | `ModeComparison` | 3 | 2 | PASS |
| `vehicle_timing` | When should I buy a vehicle? | `vehicle_timing` | `ModeTiming` | 10 | 4 | PASS |
| `property_remedy` | Which calculated remedy supports property obstacles? | `property_remedy` | `ModeRemedy` | 4 | 3 | PASS |
| `property_dispute_handoff` | Will I win my property dispute? | `property_dispute_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `muhurat_handoff` | Which date is best for property registration? | `muhurat_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `foreign_handoff` | Will I settle abroad through property? | `foreign_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `inheritance_handoff` | Will I inherit family property? | `inheritance_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `property_type_fit` | Is land, a flat or commercial property better for me? | `property_type_fit` | `ModeComparison` | 8 | 2 | PASS |
| `joint_property` | Is joint ownership with my spouse suitable? | `joint_property` | `ModeDecision` | 6 | 3 | PASS |
| `rental_income` | Does rental income suit my chart? | `rental_income` | `ModeCapacity` | 8 | 3 | PASS |
| `possession_documentation_timing` | When will I receive possession? | `possession_documentation_timing` | `ModeTiming` | 10 | 3 | PASS |
| `retrospective_property_timing` | When did I buy my first house? | `retrospective_property_timing` | `ModeTiming` | 9 | 3 | PASS |
| `property_portfolio_comparison` | Should I sell one property and buy another? | `property_portfolio_comparison` | `ModeComparison` | 9 | 3 | PASS |
| `vastu_handoff` | Is my home Vastu compliant? | `vastu_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `property_business_handoff` | Should I start a real-estate business? | `property_business_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `living_arrangement` | Am I more suited to living independently or with family? | `living_arrangement` | `ModeComparison` | 8 | 3 | PASS |
| `property_sale_decision` | Should I sell my property or continue holding it? | `property_sale_decision` | `ModeComparison` | 8 | 3 | PASS |
| `construction_timing` | When is a supportive period to renovate or construct my home? | `construction_timing` | `ModeTiming` | 11 | 3 | PASS |
| `relocation_timing` | When is my next supportive period to move home? | `relocation_timing` | `ModeTiming` | 10 | 3 | PASS |
| `property_obstacles` | Why do my property plans keep getting delayed or blocked? | `property_obstacles` | `ModeDiagnosis` | 9 | 2 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Home, Property and Vehicles QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
