"""Shared Education, Exams and Research routing profiles.

The semantic router chooses the subtype.  Application code never infers a
subtype from English question text, which keeps multilingual routing stable.
"""

from __future__ import annotations

from typing import Any, Mapping


EDUCATION_CATEGORIES = frozenset({"education", "learning", "exams", "research"})

EDUCATION_SUBTYPE_ALIASES = {
    "general": "overall",
    "education": "overall",
    "learning": "learning_style",
    "stream": "subject_fit",
    "course": "subject_fit",
    "field": "subject_fit",
    "course_choice": "course_comparison",
    "masters": "higher_education",
    "phd": "higher_education",
    "competitive_exam": "exam_capacity",
    "exam": "exam_capacity",
    "exam_result": "exam_timing",
    "selection": "admission_timing",
    "admission": "admission_capacity",
    "funding": "scholarship",
    "study_abroad": "foreign_study",
    "study_abroad_timing": "foreign_study_timing",
    "restart": "education_resume",
    "dropout": "education_obstacles",
    "job_vs_study": "education_vs_work",
    "remedy": "education_remedies",
}

# Houses are ordered by decision importance.  Planets are significators to
# audit, not automatic benefics or verdicts.
EDUCATION_PROFILES: dict[str, dict[str, Any]] = {
    "overall": {"houses": [2, 4, 5, 9, 11], "planets": ["Mercury", "Jupiter", "Moon"]},
    "education_timing": {"houses": [2, 4, 5, 9, 11], "planets": ["Mercury", "Jupiter", "Moon", "Saturn"]},
    "learning_style": {"houses": [1, 2, 3, 4, 5], "planets": ["Mercury", "Moon", "Jupiter", "Saturn"]},
    "subject_fit": {"houses": [5, 9, 10, 2], "planets": ["Mercury", "Jupiter", "Mars", "Venus", "Saturn", "Rahu"]},
    "course_comparison": {"houses": [5, 9, 10, 11, 2], "planets": ["Mercury", "Jupiter", "Mars", "Venus", "Saturn", "Rahu"]},
    "higher_education": {"houses": [9, 5, 11], "planets": ["Jupiter", "Mercury", "Moon", "Saturn"]},
    "higher_education_timing": {"houses": [9, 5, 11], "planets": ["Jupiter", "Mercury", "Saturn", "Rahu"]},
    "exam_capacity": {"houses": [5, 6, 11, 9], "planets": ["Mercury", "Jupiter", "Sun", "Mars", "Saturn"]},
    "exam_timing": {"houses": [5, 6, 11, 9], "planets": ["Mercury", "Jupiter", "Sun", "Mars", "Saturn"]},
    "admission_capacity": {"houses": [4, 5, 9, 11], "planets": ["Mercury", "Jupiter", "Sun"]},
    "admission_timing": {"houses": [4, 5, 6, 9, 11], "planets": ["Mercury", "Jupiter", "Sun", "Saturn"]},
    "scholarship": {"houses": [2, 5, 9, 11], "planets": ["Jupiter", "Mercury", "Venus"]},
    "research": {"houses": [5, 8, 9, 11, 12, 10, 6], "planets": ["Mercury", "Jupiter", "Saturn", "Ketu", "Rahu"]},
    "research_timing": {"houses": [5, 8, 9, 11, 12, 10, 6], "planets": ["Mercury", "Jupiter", "Saturn", "Ketu"]},
    "foreign_study": {"houses": [9, 12, 11, 3], "planets": ["Jupiter", "Mercury", "Rahu", "Saturn"]},
    "foreign_study_comparison": {"houses": [9, 12, 11, 3, 4, 5], "planets": ["Jupiter", "Mercury", "Rahu", "Saturn", "Moon"]},
    "foreign_study_timing": {"houses": [9, 12, 11, 3], "planets": ["Jupiter", "Mercury", "Rahu", "Saturn"]},
    "education_obstacles": {"houses": [2, 3, 4, 5, 6, 8, 9, 11, 12], "planets": ["Mercury", "Moon", "Sun", "Mars", "Saturn", "Rahu", "Ketu"]},
    "education_resume": {"houses": [3, 4, 5, 9, 11], "planets": ["Mercury", "Jupiter", "Saturn"]},
    "education_vs_work": {"houses": [9, 5, 11, 10, 6, 2], "planets": ["Mercury", "Jupiter", "Saturn", "Sun"]},
    "education_vs_work_timing": {"houses": [9, 5, 11, 10, 6, 2], "planets": ["Mercury", "Jupiter", "Saturn", "Sun"]},
    "education_remedies": {"houses": [2, 4, 5, 6, 9], "planets": ["Mercury", "Jupiter", "Moon"]},
}

TIMING_EDUCATION_SUBTYPES = frozenset({
    "education_timing", "higher_education_timing", "exam_timing",
    "admission_timing", "research_timing", "foreign_study_timing",
    "education_vs_work_timing",
})


def normalize_education_subtype(value: Any) -> str:
    raw = str(value or "overall").strip().lower().replace("-", "_").replace(" ", "_")
    resolved = EDUCATION_SUBTYPE_ALIASES.get(raw, raw)
    return resolved if resolved in EDUCATION_PROFILES else "overall"


def education_profile(category: Any, subtype: Any = None) -> dict[str, Any]:
    category_key = str(category or "").strip().lower()
    inferred = subtype
    if not inferred and category_key == "exams":
        inferred = "exam_capacity"
    elif not inferred and category_key == "research":
        inferred = "research"
    resolved = normalize_education_subtype(inferred)
    return {"subtype": resolved, **EDUCATION_PROFILES[resolved]}


def is_education_category(value: Any) -> bool:
    return str(value or "").strip().lower() in EDUCATION_CATEGORIES


def is_education_timing(subtype: Any, answer_mode: Any = None) -> bool:
    return (
        normalize_education_subtype(subtype) in TIMING_EDUCATION_SUBTYPES
        or str(answer_mode or "").strip().lower() in {
            "event_prediction", "event_timing", "lifetime_event_timing",
            "month_timing", "timing_window", "daily_forecast",
        }
    )


def education_options(plan: Mapping[str, Any] | None) -> list[str]:
    plan = plan if isinstance(plan, Mapping) else {}
    values = plan.get("education_options") or plan.get("comparison_options") or []
    result: list[str] = []
    for value in values if isinstance(values, list) else []:
        if isinstance(value, Mapping):
            label = value.get("label") or value.get("target") or value.get("event_profile")
        else:
            label = value
        text = str(label or "").strip()
        if text and text not in result:
            result.append(text)
    return result[:6]
