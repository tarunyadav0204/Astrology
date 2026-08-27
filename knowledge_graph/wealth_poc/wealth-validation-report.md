# Wealth and Finance ontology validation report

- Ontology version: `0.2.0`
- Competency questions: **20**
- Result: **PASS**

| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |
|---|---|---|---|---:|---:|---|
| `wealth_overall` | What does my chart show about wealth? | `wealth` | `ModeTopic` | 16 | 7 | PASS |
| `wealth_source` | What is my strongest way to build wealth? | `wealth_source` | `ModeCapacity` | 13 | 7 | PASS |
| `wealth_diagnosis` | Why do my savings remain unstable? | `wealth_diagnosis` | `ModeDiagnosis` | 12 | 6 | PASS |
| `wealth_timing` | When is my next wealth growth period? | `wealth_timing` | `ModeTiming` | 17 | 10 | PASS |
| `income` | How stable is my income? | `income` | `ModeTopic` | 13 | 8 | PASS |
| `income_timing` | When can my income improve? | `income_timing` | `ModeTiming` | 12 | 8 | PASS |
| `multiple_income` | Does my chart support multiple income streams? | `multiple_income` | `ModeCapacity` | 12 | 7 | PASS |
| `debt` | What does my chart show about debt? | `debt` | `ModeTopic` | 10 | 5 | PASS |
| `debt_diagnosis` | Why am I struggling to clear my loans? | `debt_diagnosis` | `ModeDiagnosis` | 10 | 5 | PASS |
| `debt_repayment` | When can I become debt-free? | `debt_repayment` | `ModeTiming` | 12 | 7 | PASS |
| `loan_support` | Is this a supportive period for loan approval? | `loan_support` | `ModeDecision` | 10 | 5 | PASS |
| `investment` | Does my chart support active investing? | `investment` | `ModeCapacity` | 13 | 7 | PASS |
| `investing_vs_trading` | Is long-term investing or active trading better for me? | `investing_vs_trading` | `ModeComparison` | 12 | 6 | PASS |
| `investment_timing` | Is this a supportive period for investing? | `investment_timing` | `ModeTiming` | 12 | 6 | PASS |
| `investment_risk` | Why do my investments fluctuate so much? | `investment_risk` | `ModeDiagnosis` | 12 | 6 | PASS |
| `loss_vulnerability` | Where is my chart most vulnerable to financial loss? | `loss_vulnerability` | `ModeTopic` | 12 | 5 | PASS |
| `inheritance` | Does my chart support inheritance or settlement? | `inheritance` | `ModeTopic` | 10 | 6 | PASS |
| `inheritance_timing` | When may an inheritance or settlement move forward? | `inheritance_timing` | `ModeTiming` | 10 | 6 | PASS |
| `windfall` | Does my chart show a lottery or sudden windfall? | `windfall` | `ModeCapacity` | 14 | 7 | PASS |
| `wealth_remedies` | Which calculated remedy is relevant for recurring financial instability? | `wealth_remedies` | `ModeRemedy` | 7 | 2 | PASS |

## Release checks

- All graph references resolve.
- Stable IDs and QuestionType runtime keys are unique.
- Every required calculator capability has an executable binding.
- Evidence policies, answer contracts and guardrails are present for every route.
- Every Wealth and Finance QuestionType has decision-stage children, and every decision stage has astrology-factor children.
- Static routes exclude timing and do not invoke dasha/transit calculators.

This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.
