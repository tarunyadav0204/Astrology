# Education, Exams and Research ontology validation report

- Ontology version: `0.2.0`
- Competency questions: **22**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `education` | What does my chart show about my education? | `education` | `ModeTopic` | 10 | 4 | PASS |
| `education_timing` | Which periods are supportive for my studies? | `education_timing` | `ModeTiming` | 9 | 5 | PASS |
| `learning_style` | How do I learn and retain information best? | `learning_style` | `ModeCapacity` | 8 | 2 | PASS |
| `subject_fit` | Which subjects suit me best? | `subject_fit` | `ModeCapacity` | 8 | 3 | PASS |
| `course_comparison` | Should I study engineering or design? | `course_comparison` | `ModeComparison` | 8 | 3 | PASS |
| `higher_education` | Does my chart support higher studies or a PhD? | `higher_education` | `ModeCapacity` | 6 | 2 | PASS |
| `higher_education_timing` | When is higher study most supported? | `higher_education_timing` | `ModeTiming` | 8 | 5 | PASS |
| `exam_capacity` | What does my chart show about competitive exams? | `exam_capacity` | `ModeCapacity` | 8 | 3 | PASS |
| `exam_timing` | Will I clear this exam this year? | `exam_timing` | `ModeTiming` | 9 | 5 | PASS |
| `admission_capacity` | Does my chart support admission to a selective program? | `admission_capacity` | `ModeCapacity` | 7 | 3 | PASS |
| `admission_timing` | When is admission most likely to move forward? | `admission_timing` | `ModeTiming` | 10 | 5 | PASS |
| `scholarship` | Does my chart support a scholarship? | `scholarship` | `ModeCapacity` | 7 | 3 | PASS |
| `research` | Does my chart support serious research? | `research` | `ModeCapacity` | 9 | 3 | PASS |
| `research_timing` | When is my thesis likely to progress or complete? | `research_timing` | `ModeTiming` | 11 | 6 | PASS |
| `foreign_study` | Does my chart support studying abroad? | `foreign_study` | `ModeCapacity` | 7 | 2 | PASS |
| `foreign_study_comparison` | Is foreign education stronger for me than studying locally? | `foreign_study_comparison` | `ModeComparison` | 10 | 3 | PASS |
| `foreign_study_timing` | When is studying abroad most supported? | `foreign_study_timing` | `ModeTiming` | 9 | 5 | PASS |
| `education_obstacles` | Why do I struggle to concentrate or complete my studies? | `education_obstacles` | `ModeDiagnosis` | 14 | 4 | PASS |
| `education_resume` | Can I successfully return to study after a long break? | `education_resume` | `ModeCapacity` | 8 | 2 | PASS |
| `education_vs_work` | Should I pursue a Masters or work now? | `education_vs_work` | `ModeDecision` | 10 | 4 | PASS |
| `education_vs_work_timing` | Is this a better year for higher education or professional experience? | `education_vs_work_timing` | `ModeTiming` | 13 | 7 | PASS |
| `education_remedies` | Which calculated remedy is relevant for my recurring study difficulty? | `education_remedies` | `ModeRemedy` | 8 | 3 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Education, Exams and Research QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
