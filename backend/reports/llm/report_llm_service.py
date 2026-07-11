from __future__ import annotations

from typing import Any, Dict

from marriage_matching.premium_report import generate_compatibility_premium_report


async def generate_partnership_premium_report(
    userid: int,
    boy_chart: Dict[str, Any],
    girl_chart: Dict[str, Any],
    boy_birth: Dict[str, Any],
    girl_birth: Dict[str, Any],
    *,
    language: str,
    force_regenerate: bool,
    effective_cost: int,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    return await generate_compatibility_premium_report(
        userid,
        boy_chart,
        girl_chart,
        boy_birth,
        girl_birth,
        language=language or "english",
        force_regenerate=force_regenerate,
        effective_cost=effective_cost,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
    )

