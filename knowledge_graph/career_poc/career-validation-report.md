# Career ontology validation report

- Ontology version: `0.6.0`
- Competency questions: **29**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `career_promotion_vs_job_change` | Is promotion or a job change more likely in the next year? | `promotion_vs_job_change` | `ModeDecisionSupport` | 10 | 6 | PASS |
| `career_overall_static` | How is my career overall? | `general` | `ModeTopicReading` | 8 | 3 | PASS |
| `career_fit_static` | What kind of career suits me? | `career_fit` | `ModePotentialCapacity` | 8 | 3 | PASS |
| `career_resignation_decision` | Should I leave my current job? | `resignation` | `ModeDecisionSupport` | 10 | 5 | PASS |
| `career_recognition_diagnosis` | Why am I not getting recognition despite working hard? | `recognition` | `ModeProblemDiagnosis` | 6 | 3 | PASS |
| `career_manager_relationship` | How will my relationship with my manager develop? | `manager_relationship` | `ModeRelationshipReading` | 6 | 3 | PASS |
| `career_promotion_timing` | When will I get promoted? | `promotion` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_salary_increase` | Will I get a salary increase? | `salary_increase` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_business_employment` | Should I choose business or employment? | `business_vs_employment` | `ModePotentialCapacity` | 10 | 4 | PASS |
| `career_job_change_timing` | Is this a good period for changing jobs? | `job_change_timing` | `ModeDecisionSupport` | 10 | 5 | PASS |
| `career_workplace_conflict` | Why am I facing conflict at work? | `workplace_conflict` | `ModeProblemDiagnosis` | 6 | 3 | PASS |
| `career_employment` | When will I get a job? | `employment` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_offer` | Will I receive this job offer? | `offer` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_joining` | When will I join the new job? | `joining` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_job_security` | Is my job secure? | `job_security` | `ModeDecisionSupport` | 10 | 5 | PASS |
| `career_business` | How is business indicated for me? | `business` | `ModeTopicReading` | 8 | 4 | PASS |
| `career_business_launch` | When should I start my business? | `business_launch` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_business_success` | Will my existing business succeed? | `business_success` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_project` | Will this project succeed? | `project` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_leadership` | Am I suited for a leadership role? | `leadership` | `ModePotentialCapacity` | 8 | 4 | PASS |
| `career_government` | Will I get a government job? | `government` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_foreign` | Will I get a job abroad? | `foreign_career` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_return_to_work` | When will I return to work after my career break? | `return_to_work` | `ModeDecisionSupport` | 8 | 5 | PASS |
| `career_stagnation` | Why is my career not progressing? | `career_stagnation` | `ModeProblemDiagnosis` | 6 | 3 | PASS |
| `career_colleague_relationship` | Why am I having difficulty with my colleague? | `colleague_relationship` | `ModeRelationshipReading` | 6 | 3 | PASS |
| `career_subordinate_relationship` | How should I handle my direct report? | `subordinate_relationship` | `ModeRelationshipReading` | 5 | 3 | PASS |
| `career_client_relationship` | How will my relationship with this client develop? | `client_relationship` | `ModeRelationshipReading` | 6 | 3 | PASS |
| `career_partner_relationship` | How compatible am I with my business partner? | `business_partner_relationship` | `ModeRelationshipReading` | 6 | 3 | PASS |
| `career_mentor_relationship` | How will my relationship with my mentor develop? | `mentor_relationship` | `ModeRelationshipReading` | 6 | 3 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Career QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
