# routes/financial_routes.py
from datetime import date, datetime
from typing import Optional

from auth import get_current_user
from db import get_conn_dict
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/financial", tags=["financial"])


def _coerce_datetime(val):
    """RealDict rows may return date/datetime/str from Postgres."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    s = str(val).replace("Z", "+00:00")
    if "T" not in s and len(s) <= 10:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    return datetime.fromisoformat(s.split("+")[0])


def _date_str(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return str(val)[:10]


@router.get("/sectors")
async def get_available_sectors():
    """Get list of available sectors"""
    from calculators.financial.sector_mapper import SECTOR_RULES

    return {
        "sectors": [
            {"name": sector, "ruler": rules["ruler"], "description": f"Ruled by {rules['ruler']}"}
            for sector, rules in SECTOR_RULES.items()
        ],
        "total": len(SECTOR_RULES),
    }


@router.get("/forecast/all")
async def get_all_sectors_forecast(current_user=Depends(get_current_user)):
    """
    Get 5-year forecast for ALL sectors with rise/fall periods
    Returns: Complete timeline with start/end dates for each trend
    """
    with get_conn_dict() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM market_forecast_metadata WHERE id = 1")
        meta = cursor.fetchone()

        if not meta:
            raise HTTPException(
                status_code=503,
                detail="Market forecast data not available. Please contact admin.",
            )

        cursor.execute(
            """
            SELECT sector, ruler, start_date, end_date, trend, intensity, reason
            FROM market_forecast_periods
            ORDER BY sector, start_date
            """
        )
        rows = cursor.fetchall()

    # Group by sector
    sectors = {}
    for row in rows:
        sector = row["sector"]
        if sector not in sectors:
            sectors[sector] = {"ruler": row["ruler"], "timeline": []}

        sectors[sector]["timeline"].append(
            {
                "start_date": _date_str(row["start_date"]),
                "end_date": _date_str(row["end_date"]),
                "trend": row["trend"],
                "intensity": row["intensity"],
                "reason": row["reason"],
            }
        )

    # Add summary
    for sector, data in sectors.items():
        data["summary"] = {
            "total_periods": len(data["timeline"]),
            "bullish_count": len([p for p in data["timeline"] if p["trend"] == "BULLISH"]),
            "bearish_count": len([p for p in data["timeline"] if p["trend"] == "BEARISH"]),
        }

    return {
        "period": f"{meta['start_year']} - {meta['end_year']}",
        "generated_at": meta["generated_at"],
        "sectors": sectors,
    }


@router.get("/forecast/{sector}")
async def get_sector_forecast(sector: str, current_user=Depends(get_current_user)):
    """
    Get forecast for a SPECIFIC sector
    Returns: Timeline with all rise/fall periods
    """
    with get_conn_dict() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT start_year, end_year FROM market_forecast_metadata WHERE id = 1")
        meta = cursor.fetchone()

        sector_decoded = sector.replace("%20", " ").replace("+", " ")

        cursor.execute(
            """
            SELECT * FROM market_forecast_periods
            WHERE sector = %s
            ORDER BY start_date
            """,
            (sector_decoded,),
        )
        rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector_decoded}' not found. Use /sectors to see available sectors.",
        )

    timeline = [
        {
            "start_date": _date_str(row["start_date"]),
            "end_date": _date_str(row["end_date"]),
            "trend": row["trend"],
            "intensity": row["intensity"],
            "reason": row["reason"],
            "duration_days": (_coerce_datetime(row["end_date"]) - _coerce_datetime(row["start_date"])).days,
        }
        for row in rows
    ]

    return {
        "sector": sector_decoded,
        "ruler": rows[0]["ruler"],
        "period": f"{meta['start_year']}-{meta['end_year']}" if meta else "N/A",
        "summary": {
            "total_periods": len(timeline),
            "bullish_count": len([p for p in timeline if p["trend"] == "BULLISH"]),
            "bearish_count": len([p for p in timeline if p["trend"] == "BEARISH"]),
        },
        "timeline": timeline,
    }


@router.get("/hot-opportunities")
async def get_hot_opportunities(intensity: Optional[str] = "High", current_user=Depends(get_current_user)):
    """
    Get all HIGH INTENSITY bullish periods across sectors
    Returns: Sorted list of best investment windows (one per sector)
    """
    with get_conn_dict() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sector, start_date, end_date, intensity, reason,
                   ROW_NUMBER() OVER (PARTITION BY sector ORDER BY start_date) as rn
            FROM market_forecast_periods
            WHERE trend = 'BULLISH' AND intensity = %s
            """,
            (intensity,),
        )
        rows = cursor.fetchall()

    opportunities = [
        {
            "sector": row["sector"],
            "start_date": _date_str(row["start_date"]),
            "end_date": _date_str(row["end_date"]),
            "intensity": row["intensity"],
            "reason": row["reason"],
            "duration_days": (_coerce_datetime(row["end_date"]) - _coerce_datetime(row["start_date"])).days,
        }
        for row in rows
        if row["rn"] == 1
    ]

    return {
        "total_opportunities": len(opportunities),
        "intensity_filter": intensity,
        "opportunities": opportunities,
    }


@router.get("/current-trends")
async def get_current_trends(date: Optional[str] = None, current_user=Depends(get_current_user)):
    """
    Get current trend for all sectors at a specific date
    date: YYYY-MM-DD format or None for today
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        ref_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    with get_conn_dict() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sector, ruler, trend, intensity, reason, start_date, end_date
            FROM market_forecast_periods
            WHERE %s::date BETWEEN start_date::date AND end_date::date
            """,
            (date,),
        )
        rows = cursor.fetchall()

    current_trends = {}
    for row in rows:
        end_dt = _coerce_datetime(row["end_date"])
        current_trends[row["sector"]] = {
            "ruler": row["ruler"],
            "trend": row["trend"],
            "intensity": row["intensity"],
            "reason": row["reason"],
            "valid_from": _date_str(row["start_date"]),
            "valid_until": _date_str(row["end_date"]),
            "days_remaining": (end_dt - ref_date).days,
        }

    return {"reference_date": date, "trends": current_trends}


@router.post("/analyze")
async def analyze_financial_chart(request: dict, current_user=Depends(get_current_user)):
    """Analyze user's birth chart for financial predictions"""
    print(f"[FINANCIAL] Analyze request from user {current_user.userid}")
    print(f"[FINANCIAL] Request data: {request}")

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[FINANCIAL] Querying trends for date: {today}")

    with get_conn_dict() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sector, ruler, trend, intensity, reason, start_date, end_date
            FROM market_forecast_periods
            WHERE %s::date BETWEEN start_date::date AND end_date::date
            """,
            (today,),
        )
        rows = cursor.fetchall()

    print(f"[FINANCIAL] Found {len(rows)} active sectors")

    sectors_analysis = []
    for row in rows:
        sectors_analysis.append(
            {
                "sector": row["sector"],
                "ruler": row["ruler"],
                "trend": row["trend"],
                "intensity": row["intensity"],
                "reason": row["reason"],
                "valid_until": _date_str(row["end_date"]),
            }
        )

    result = {
        "analysis_date": today,
        "sectors": sectors_analysis,
        "summary": {
            "bullish_count": len([s for s in sectors_analysis if s["trend"] == "BULLISH"]),
            "bearish_count": len([s for s in sectors_analysis if s["trend"] == "BEARISH"]),
            "neutral_count": len([s for s in sectors_analysis if s["trend"] == "NEUTRAL"]),
        },
    }

    print(f"[FINANCIAL] Returning analysis with {len(sectors_analysis)} sectors")
    return result


# ADMIN ONLY - Generate new forecast data
@router.post("/admin/regenerate")
async def regenerate_forecast(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    current_user=Depends(get_current_user),
):
    """
    Regenerate market forecast data and save to database.
    Available to all authenticated users.
    """
    if start_year is None:
        start_year = datetime.now().year
    if end_year is None:
        end_year = start_year + 5

    if start_year > end_year:
        raise HTTPException(
            status_code=400,
            detail=f"Start year ({start_year}) cannot be greater than end year ({end_year})",
        )

    years = (end_year - start_year) + 1

    from calculators.financial.financial_context_builder import FinancialContextBuilder

    print(f"🔄 Regenerating forecast for {start_year}-{end_year} ({years} year(s))...")

    builder = FinancialContextBuilder()
    data = builder.build_all_sectors_forecast(start_year, years)

    builder.save_to_database(data)

    return {
        "status": "success",
        "message": f"Forecast saved to database for {start_year}-{end_year}",
        "start_year": start_year,
        "end_year": end_year,
        "years_generated": years,
        "total_sectors": data["total_sectors"],
        "total_periods": sum(len(s["timeline"]) for s in data["sectors"].values()),
    }
