# Marriage and Relationship ontology validation report

- Ontology version: `0.3.1`
- Competency questions: **20**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `marriage_promise` | Is marriage possible in my kundali? | `marriage_promise` | `ModePromise` | 5 | 2 | PASS |
| `marriage_timing` | When will I get married? | `marriage_timing` | `ModeTiming` | 9 | 5 | PASS |
| `marriage_history` | When was I married? | `marriage_history` | `ModeRetrospective` | 8 | 3 | PASS |
| `married_life` | How is my married life? | `married_life` | `ModeOutlook` | 9 | 3 | PASS |
| `married_life_timing` | How will my marriage be this year? | `married_life_timing` | `ModeTiming` | 10 | 5 | PASS |
| `relationship_outlook` | How is my love life? | `relationship_outlook` | `ModeOutlook` | 6 | 2 | PASS |
| `relationship_timing` | When can this relationship become serious? | `relationship_timing` | `ModeTiming` | 7 | 4 | PASS |
| `separation_reconciliation` | Can this marriage recover after separation? | `separation_reconciliation` | `ModeOutlook` | 8 | 3 | PASS |
| `separation_reconciliation_timing` | Is this year supportive for reconciliation? | `separation_reconciliation_timing` | `ModeTiming` | 10 | 5 | PASS |
| `spouse_profile` | What kind of spouse am I likely to have? | `spouse_profile` | `ModeProfile` | 6 | 2 | PASS |
| `relationship_diagnosis` | Why do the same conflicts repeat in my marriage? | `relationship_diagnosis` | `ModeDiagnosis` | 8 | 3 | PASS |
| `marriage_remedies` | What remedies can support my marriage? | `marriage_remedies` | `ModeRemedy` | 3 | 1 | PASS |
| `love_arranged_marriage` | Is love marriage or arranged marriage more supported? | `love_arranged_marriage` | `ModeChoice` | 7 | 2 | PASS |
| `remarriage` | Will I remarry, and when? | `remarriage` | `ModeRemarriage` | 11 | 4 | PASS |
| `engagement_wedding_timing` | When are engagement and wedding separately supported? | `engagement_wedding_timing` | `ModeMilestone` | 9 | 3 | PASS |
| `spouse_meeting` | Where or how am I likely to meet my spouse? | `spouse_meeting` | `ModeMeeting` | 9 | 2 | PASS |
| `spouse_details` | What might my spouse do, where might they be from, and what may they look like? | `spouse_details` | `ModeDetailedProfile` | 8 | 2 | PASS |
| `affair_assessment` | Does the chart show an affair or third-party pressure? | `affair_assessment` | `ModeAffair` | 8 | 2 | PASS |
| `marriage_muhurat` | Find a marriage Muhurat in this date range. | `marriage_muhurat` | `ModeMuhurat` | 1 | 1 | PASS |
| `compatibility_analysis` | Analyze our marriage compatibility using both charts. | `compatibility_analysis` | `ModeCompatibility` | 3 | 1 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Marriage and Relationship QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
