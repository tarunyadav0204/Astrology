# Health ontology validation report

- Ontology version: `0.1.0`
- Competency questions: **10**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `health_constitution` | What health vulnerabilities does my chart show? | `health` | `ModeConstitutional` | 13 | 6 | PASS |
| `mental_constitution` | What mental-wellbeing vulnerabilities does my chart show? | `mental_wellbeing` | `ModeMentalWellbeing` | 12 | 5 | PASS |
| `surgery_constitution` | Does my chart show surgical susceptibility? | `surgery` | `ModeSafetyAssessment` | 10 | 5 | PASS |
| `accident_constitution` | Does my chart show accident susceptibility? | `accident` | `ModeSafetyAssessment` | 10 | 5 | PASS |
| `recovery_constitution` | What recovery support does my chart show? | `recovery` | `ModeRecoverySupport` | 11 | 5 | PASS |
| `health_timing` | How will my health be this year? | `health_timing` | `ModePeriodForecast` | 12 | 7 | PASS |
| `mental_timing` | How will my mental wellbeing be this year? | `mental_wellbeing_timing` | `ModePeriodForecast` | 13 | 7 | PASS |
| `surgery_timing` | Is this a sensitive period for surgery? | `surgery_timing` | `ModePeriodForecast` | 11 | 7 | PASS |
| `accident_timing` | Are there periods requiring extra accident caution this year? | `accident_timing` | `ModePeriodForecast` | 11 | 7 | PASS |
| `recovery_timing` | When is recovery support stronger? | `recovery_timing` | `ModePeriodForecast` | 12 | 7 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Health QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
