from dataclasses import dataclass
from typing import Tuple

from .constants import SUPPORTED_REPORT_TYPES


@dataclass(frozen=True)
class ReportTypeConfig:
    key: str
    title: str
    page_count: int
    required_branches: Tuple[str, ...]
    enabled: bool = True
    summary: str | None = None


PARTNERSHIP_REPORT_CONFIG = ReportTypeConfig(
    key="partnership",
    title="Partnership Compatibility Report",
    page_count=20,
    required_branches=("kp", "jaimini", "nadi", "nakshatra", "d60"),
    enabled=True,
    summary="Premium two-chart partnership report.",
)

CAREER_REPORT_CONFIG = ReportTypeConfig(
    key="career",
    title="Career Report",
    page_count=20,
    required_branches=("kp", "jaimini", "nadi", "nakshatra", "d10"),
    enabled=False,
    summary="Coming soon",
)

WEALTH_REPORT_CONFIG = ReportTypeConfig(
    key="wealth",
    title="Wealth Report",
    page_count=27,
    required_branches=("kp", "jaimini", "nadi", "nakshatra", "d2"),
    enabled=True,
    summary="Premium single-chart wealth report with next 12 months of dasha timing.",
)

HEALTH_REPORT_CONFIG = ReportTypeConfig(
    key="health",
    title="Health Report",
    page_count=27,
    required_branches=("kp", "jaimini", "nadi", "nakshatra", "d30"),
    enabled=True,
    summary="Premium single-chart health report with constitution, D30 confirmation, and next 12 months of dasha timing.",
)

PROGENY_REPORT_CONFIG = ReportTypeConfig(
    key="progeny",
    title="Progeny Report",
    page_count=20,
    required_branches=("kp", "jaimini", "nadi", "nakshatra", "d7"),
    enabled=False,
    summary="Coming soon",
)

JANAM_KUNDLI_REPORT_CONFIG = ReportTypeConfig(
    key="janam_kundli",
    title="Janam Kundli Report",
    page_count=24,
    required_branches=("nakshatra", "d9", "d10", "ashtakavarga", "dasha", "yogas"),
    enabled=True,
    summary="Personalized 24-page Janam Kundli PDF with charts, dashas, yogas, and life guidance (English/Hindi).",
)


REPORT_TYPE_CONFIGS = {
    "partnership": PARTNERSHIP_REPORT_CONFIG,
    "career": CAREER_REPORT_CONFIG,
    "wealth": WEALTH_REPORT_CONFIG,
    "health": HEALTH_REPORT_CONFIG,
    "progeny": PROGENY_REPORT_CONFIG,
    "janam_kundli": JANAM_KUNDLI_REPORT_CONFIG,
}


def get_report_types() -> Tuple[str, ...]:
    return SUPPORTED_REPORT_TYPES
