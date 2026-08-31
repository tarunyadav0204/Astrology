# Longevity validation baseline v1

This baseline was measured after correcting the Jaimini 2.1.9, 2.1.13, and 2.1.14 implementation defects documented in `longevity-validation.md`, and after making historical IANA timezone resolution use the birth date rather than the current date. Results measured before that timezone correction are invalid and superseded by this document.

## Cohort

- Five selected public figures.
- Three Rodden AA and two Rodden A birth records.
- Five-year observation interval preceding each event.
- Final 60 days excluded from ordinary control person-time.
- Birth-time sensitivity at −15, −5, 0, +5, and +15 minutes.

This is a seed regression cohort, not external validation and not an accuracy claim.

## Results

### Two-of-three descriptive convergence

- Event capture: **4/5 (80%)**.
- Positive ordinary control person-time: **4,773 / 8,830 days (54.05%)**.
- Event lift over ordinary person-time: **1.48×**.
- Lifespan compartment contained attained event age: **3/5**.
- Stable compartment and event convergence across ±15 minutes: **3/5**.

### Three-of-three descriptive convergence

- Event capture: **1/5 (20%)**.
- Positive ordinary control person-time: **1,470 / 8,830 days (16.65%)**.
- Event lift over ordinary person-time: **1.20×**.

## Interpretation

The seed cohort does not support predictive or severity claims. Two-of-three convergence is active for more than half of ordinary person-time. Three-of-three convergence is less common, but captures only one event and remains active for roughly one in six ordinary days. The calculator can expose the underlying classical layers, but their count must remain descriptive and visually neutral.

Birth-time robustness is also insufficient. JFK changes lifespan compartment within the ±15-minute band, while Steve Jobs changes event convergence. A direct lifespan or health-warning claim would therefore overstate precision.

## Current product decision

- Keep the workspace licensed and without direct navigation entry points.
- Present classical calculations and activation layers, not risk levels.
- Do not show percentages, probabilities, “critical” labels, or danger colors.
- Do not use the seed cohort to tune rules.
- Expand with a predeclared AA-first cohort and an untouched external-validation split before reconsidering predictive language.
