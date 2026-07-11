"""VIP tier feature credit pricing (same source as mobile MembershipComparison)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Mirrors astroroshni_mobile MembershipComparisonScreen FEATURE_ROWS
FEATURE_PRICING_ROWS: List[Tuple[str, str]] = [
    ("chat", "Standard chat"),
    ("instant_chat", "Instant chat"),
    ("speech_chat", "Speech chat (Tara)"),
    ("premium_chat", "Premium chat"),
    ("career", "Career analysis"),
    ("marriage", "Marriage analysis"),
    ("health", "Health analysis"),
    ("wealth", "Wealth analysis"),
    ("education", "Education analysis"),
    ("progeny", "Progeny analysis"),
    ("karma", "Karma analysis"),
    ("partnership", "Partnership compatibility"),
    ("ashtakavarga", "Ashtakavarga life predictions"),
    ("events", "Yearly event timeline"),
    ("business", "Business opening muhurat"),
    ("childbirth", "Childbirth muhurat"),
    ("gold", "Gold purchase muhurat"),
    ("griha_pravesh", "Griha pravesh muhurat"),
    ("vehicle", "Vehicle purchase muhurat"),
    ("trading", "Daily trading forecast"),
    ("trading_monthly", "Monthly trading calendar"),
    ("podcast", "Podcast (audio)"),
]


def _apply_tier_discount(regular: int, discount_percent: int) -> int:
    pct = max(0, min(100, int(discount_percent or 0)))
    return max(1, round(int(regular) * (100 - pct) / 100))


def _benefit_line_from_item(item: Any) -> Optional[str]:
    if isinstance(item, str):
        s = item.strip()
        if s and not (s.startswith("{") and s.endswith("}")):
            return s
        return None
    if isinstance(item, dict):
        for key in ("text", "label", "description", "title"):
            val = item.get(key)
            if val and str(val).strip():
                return str(val).strip()
    return None


def _lines_from_benefit_list(items: List[Any]) -> List[str]:
    out: List[str] = []
    for item in items:
        line = _benefit_line_from_item(item)
        if line:
            out.append(line)
    return out


def _is_plan_features_metadata(features: Dict[str, Any]) -> bool:
    """e.g. {"tier": true} stored in subscription_plans.features — flags, not marketing copy."""
    if not isinstance(features, dict):
        return False
    if features.get("benefits"):
        return False
    allowed = {
        "tier",
        "instant_chat_enabled",
        "speech_chat_enabled",
        "premium_chat_enabled",
    }
    for key, val in features.items():
        if key in allowed and isinstance(val, (bool, int, float)):
            continue
        return False
    return True


def parse_plan_benefits(features_raw: Any) -> List[str]:
    import json

    if features_raw is None:
        return []

    parsed: Any = features_raw
    if isinstance(features_raw, str):
        text = features_raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            lines = [ln.strip("- \t\r\n") for ln in text.splitlines()]
            return [ln for ln in lines if ln and not (ln.startswith("{") and ln.endswith("}"))]

    if isinstance(parsed, list):
        return _lines_from_benefit_list(parsed)
    if isinstance(parsed, dict):
        if _is_plan_features_metadata(parsed):
            return []
        arr = parsed.get("benefits")
        if isinstance(arr, list):
            return _lines_from_benefit_list(arr)
    return []


def get_base_pricing_with_originals(credit_service: Any) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Effective and display-original credit costs from credit_settings (no VIP tier)."""
    setting_keys = [
        ("chat", "chat_question_cost"),
        ("instant_chat", "instant_chat_cost"),
        ("speech_chat", "speech_chat_cost"),
        ("premium_chat", "premium_chat_cost"),
        ("partnership", "partnership_analysis_cost"),
        ("partnership_report", "partnership_report_cost"),
        ("events", "event_timeline_cost"),
        ("career", "career_analysis_cost"),
        ("career_report", "career_report_cost"),
        ("wealth", "wealth_analysis_cost"),
        ("wealth_report", "wealth_report_cost"),
        ("health", "health_analysis_cost"),
        ("health_report", "health_report_cost"),
        ("marriage", "marriage_analysis_cost"),
        ("education", "education_analysis_cost"),
        ("progeny", "progeny_analysis_cost"),
        ("progeny_report", "progeny_report_cost"),
        ("childbirth", "childbirth_planner_cost"),
        ("trading", "trading_daily_cost"),
        ("vehicle", "vehicle_purchase_cost"),
        ("griha_pravesh", "griha_pravesh_cost"),
        ("gold", "gold_purchase_cost"),
        ("business", "business_opening_cost"),
        ("karma", "karma_analysis_cost"),
        ("ashtakavarga", "ashtakavarga_life_predictions_cost"),
        ("podcast", "podcast_cost"),
    ]
    pricing: Dict[str, int] = {}
    pricing_original: Dict[str, int] = {}
    for short_key, setting_key in setting_keys:
        effective, original, discount = credit_service.get_credit_setting_and_original(setting_key)
        pricing[short_key] = int(effective)
        if discount is not None and int(discount) >= 0 and original != effective:
            pricing_original[short_key] = int(original)
    return pricing, pricing_original


def build_feature_pricing_for_tier(
    credit_service: Any,
    discount_percent: int,
) -> List[Dict[str, Any]]:
    """Per-feature credit costs at a given VIP discount (regular + tier price)."""
    pricing, pricing_original = get_base_pricing_with_originals(credit_service)
    rows: List[Dict[str, Any]] = []
    for key, label in FEATURE_PRICING_ROWS:
        effective = pricing.get(key)
        original = pricing_original.get(key)
        if effective is None and original is None:
            continue
        regular = int(original) if original is not None else int(effective)
        base_effective = int(effective) if effective is not None else regular
        tier_credits = _apply_tier_discount(regular, discount_percent)
        rows.append(
            {
                "key": key,
                "label": label,
                "regular_credits": regular,
                "base_credits": base_effective,
                "tier_credits": tier_credits,
                "has_admin_discount": base_effective < regular,
            }
        )
    return rows


def format_inr_from_paise(paise: int) -> str:
    rupees = paise / 100.0
    if rupees == int(rupees):
        return f"₹{int(rupees)}"
    return f"₹{rupees:.2f}"
