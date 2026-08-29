# Children, Parenthood and Progeny ontology validation report

- Ontology version: `0.1.0`
- Competency questions: **29**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `children_overview` | What does my chart show about children and parenthood? | `children_overview` | `ModeTopic` | 7 | 3 | PASS |
| `parenthood_capacity` | What kind of parent does my chart indicate I may become? | `parenthood_capacity` | `ModeCapacity` | 6 | 2 | PASS |
| `conception_capacity` | Does my chart support conception? | `conception_capacity` | `ModeCapacity` | 8 | 3 | PASS |
| `conception_timing` | When is my next supportive period for conception? | `conception_timing` | `ModeTiming` | 9 | 5 | PASS |
| `childbirth_timing` | Which period supports childbirth rather than only conception? | `childbirth_timing` | `ModeTiming` | 9 | 5 | PASS |
| `first_child_capacity` | Is the promise for a first child strong? | `first_child_capacity` | `ModeCapacity` | 6 | 3 | PASS |
| `first_child` | When is my first child most likely? | `first_child` | `ModeTiming` | 9 | 6 | PASS |
| `subsequent_child_capacity` | Does my chart support a second child? | `subsequent_child_capacity` | `ModeCapacity` | 7 | 3 | PASS |
| `subsequent_child` | When is the next supportive period for a second child? | `subsequent_child` | `ModeTiming` | 10 | 6 | PASS |
| `family_size_tendency` | Is my chart more supportive of a small or larger family? | `family_size_tendency` | `ModeCapacity` | 8 | 3 | PASS |
| `children_delay_diagnosis` | What is the main astrological reason for delay in having children? | `children_delay_diagnosis` | `ModeDiagnosis` | 11 | 3 | PASS |
| `assisted_conception` | Does my chart support assisted conception? | `assisted_conception` | `ModeDecision` | 8 | 3 | PASS |
| `assisted_conception_timing` | Which months are more supportive for beginning an IVF cycle? | `assisted_conception_timing` | `ModeTiming` | 11 | 5 | PASS |
| `adoption_pathway` | Does my chart support adoption? | `adoption_pathway` | `ModeCapacity` | 7 | 3 | PASS |
| `adoption_timing` | When is a supportive period to begin an adoption process? | `adoption_timing` | `ModeTiming` | 9 | 5 | PASS |
| `step_parenthood` | Does my chart support becoming a step-parent? | `step_parenthood` | `ModeCapacity` | 6 | 2 | PASS |
| `parenthood_decision` | Is this a supportive stage of life for me to become a parent? | `parenthood_decision` | `ModeDecision` | 7 | 2 | PASS |
| `parenthood_vs_career` | Should I prioritise parenthood or career growth? | `parenthood_vs_career` | `ModeDecision` | 8 | 3 | PASS |
| `parenthood_vs_career_timing` | Is this a better year for parenthood or professional expansion? | `parenthood_vs_career_timing` | `ModeTiming` | 11 | 6 | PASS |
| `parent_child_relationship` | Why do my child and I frequently clash? | `parent_child_relationship` | `ModeDiagnosis` | 6 | 2 | PASS |
| `parent_child_reconciliation_timing` | When is communication with my child likely to improve? | `parent_child_reconciliation_timing` | `ModeTiming` | 9 | 5 | PASS |
| `retrospective_child_timing` | Which past periods were most likely for childbirth? | `retrospective_child_timing` | `ModeTiming` | 8 | 5 | PASS |
| `children_remedy` | Which calculated remedy is most relevant for delayed conception? | `children_remedy` | `ModeRemedy` | 7 | 3 | PASS |
| `two_chart_children_handoff` | Do our charts jointly support having children? | `two_chart_children_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `child_chart_required_handoff` | What career will my child choose? | `child_chart_required_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `medical_safety_handoff` | Will my pregnancy be healthy and is this symptom dangerous? | `medical_safety_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `muhurat_handoff` | Which shortlisted embryo-transfer date has the cleanest Panchang? | `muhurat_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `legal_custody_handoff` | Will I get custody of my child? | `legal_custody_handoff` | `ModeHandoff` | 1 | 1 | PASS |
| `fetal_sex_refusal` | Will I have a son or daughter? | `fetal_sex_refusal` | `ModeRefusal` | 1 | 1 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Children, Parenthood and Progeny QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
