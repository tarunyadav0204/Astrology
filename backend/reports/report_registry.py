from .report_types import REPORT_TYPE_CONFIGS, get_report_types


def get_report_config(report_type: str):
    return REPORT_TYPE_CONFIGS.get(report_type)


def list_supported_report_types():
    return [
        {
            "key": key,
            "title": config.title,
            "page_count": config.page_count,
            "required_branches": list(config.required_branches),
            "enabled": config.enabled,
            "summary": config.summary,
        }
        for key, config in REPORT_TYPE_CONFIGS.items()
    ]


def get_required_calculators(report_type: str):
    config = get_report_config(report_type)
    return list(config.required_branches) if config else []


def get_required_branches(report_type: str):
    return get_required_calculators(report_type)
