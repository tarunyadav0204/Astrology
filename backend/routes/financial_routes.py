# routes/financial_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import sqlite3
from auth import get_current_user

router = APIRouter(prefix="/api/financial", tags=["financial"])

def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/sectors")
async def get_available_sectors():
    """Get list of available sectors"""
    from calculators.financial.sector_mapper import SECTOR_RULES
    
    return {
        "sectors": [
            {
                "name": sector,
                "ruler": rules["ruler"],
                "description": f"Ruled by {rules['ruler']}"
            }
            for sector, rules in SECTOR_RULES.items()
        ],
        "total": len(SECTOR_RULES)
    }

@router.get("/forecast/all")
async def get_all_sectors_forecast(current_user = Depends(get_current_user)):
    """
    Get 5-year forecast for ALL sectors with rise/fall periods
    Returns: Complete timeline with start/end dates for each trend
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get metadata
    cursor.execute("SELECT * FROM market_forecast_metadata WHERE id = 1")
    meta = cursor.fetchone()
    
    if not meta:
        conn.close()
        raise HTTPException(
            status_code=503,
            detail="Market forecast data not available. Please contact admin."
        )
    
    # Get all periods grouped by sector
    cursor.execute("""
        SELECT sector, ruler, start_date, end_date, trend, intensity, reason
        FROM market_forecast_periods
        ORDER BY sector, start_date
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Group by sector
    sectors = {}
    for row in rows:
        sector = row['sector']
        if sector not in sectors:
            sectors[sector] = {
                "ruler": row['ruler'],
                "timeline": []
            }
        
        sectors[sector]['timeline'].append({
            "start_date": row['start_date'],
            "end_date": row['end_date'],
            "trend": row['trend'],
            "intensity": row['intensity'],
            "reason": row['reason']
        })
    
    # Add summary
    for sector, data in sectors.items():
        data['summary'] = {
            "total_periods": len(data['timeline']),
            "bullish_count": len([p for p in data['timeline'] if p['trend'] == 'BULLISH']),
            "bearish_count": len([p for p in data['timeline'] if p['trend'] == 'BEARISH'])
        }
    
    return {
        "period": f"{meta['start_year']} - {meta['end_year']}",
        "generated_at": meta['generated_at'],
        "sectors": sectors
    }

@router.get("/forecast/{sector}")
async def get_sector_forecast(sector: str, current_user = Depends(get_current_user)):
    """
    Get forecast for a SPECIFIC sector
    Returns: Timeline with all rise/fall periods
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get metadata for period info
    cursor.execute("SELECT start_year, end_year FROM market_forecast_metadata WHERE id = 1")
    meta = cursor.fetchone()
    
    # URL decode and match sector name
    sector_decoded = sector.replace("%20", " ").replace("+", " ")
    
    cursor.execute("""
        SELECT * FROM market_forecast_periods
        WHERE sector = ?
        ORDER BY start_date
    """, (sector_decoded,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector_decoded}' not found. Use /sectors to see available sectors."
        )
    
    timeline = [{
        "start_date": row['start_date'],
        "end_date": row['end_date'],
        "trend": row['trend'],
        "intensity": row['intensity'],
        "reason": row['reason'],
        "duration_days": (
            datetime.fromisoformat(row['end_date']) - 
            datetime.fromisoformat(row['start_date'])
        ).days
    } for row in rows]
    
    return {
        "sector": sector_decoded,
        "ruler": rows[0]['ruler'],
        "period": f"{meta['start_year']}-{meta['end_year']}" if meta else "N/A",
        "summary": {
            "total_periods": len(timeline),
            "bullish_count": len([p for p in timeline if p['trend'] == 'BULLISH']),
            "bearish_count": len([p for p in timeline if p['trend'] == 'BEARISH'])
        },
        "timeline": timeline
    }

@router.get("/hot-opportunities")
async def get_hot_opportunities(
    intensity: Optional[str] = "High",
    current_user = Depends(get_current_user)
):
    """
    Get all HIGH INTENSITY bullish periods across sectors
    Returns: Sorted list of best investment windows (one per sector)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sector, start_date, end_date, intensity, reason,
               ROW_NUMBER() OVER (PARTITION BY sector ORDER BY start_date) as rn
        FROM market_forecast_periods
        WHERE trend = 'BULLISH' AND intensity = ?
    """, (intensity,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Filter to get only first occurrence per sector
    opportunities = [{
        "sector": row['sector'],
        "start_date": row['start_date'],
        "end_date": row['end_date'],
        "intensity": row['intensity'],
        "reason": row['reason'],
        "duration_days": (
            datetime.fromisoformat(row['end_date']) - 
            datetime.fromisoformat(row['start_date'])
        ).days
    } for row in rows if row['rn'] == 1]
    
    return {
        "total_opportunities": len(opportunities),
        "intensity_filter": intensity,
        "opportunities": opportunities
    }

@router.get("/current-trends")
async def get_current_trends(
    date: Optional[str] = None,
    current_user = Depends(get_current_user)
):
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
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sector, ruler, trend, intensity, reason, start_date, end_date
        FROM market_forecast_periods
        WHERE ? BETWEEN start_date AND end_date
    """, (date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    current_trends = {}
    for row in rows:
        end_date = datetime.fromisoformat(row['end_date'])
        current_trends[row['sector']] = {
            "ruler": row['ruler'],
            "trend": row['trend'],
            "intensity": row['intensity'],
            "reason": row['reason'],
            "valid_from": row['start_date'],
            "valid_until": row['end_date'],
            "days_remaining": (end_date - ref_date).days
        }
    
    return {
        "reference_date": date,
        "trends": current_trends
    }

@router.post("/analyze")
async def analyze_financial_chart(request: dict, current_user = Depends(get_current_user)):
    """Analyze user's birth chart for financial predictions"""
    from datetime import datetime
    
    print(f"[FINANCIAL] Analyze request from user {current_user.userid}")
    print(f"[FINANCIAL] Request data: {request}")
    
    # Get current trends
    conn = get_db()
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[FINANCIAL] Querying trends for date: {today}")
    
    cursor.execute("""
        SELECT sector, ruler, trend, intensity, reason, start_date, end_date
        FROM market_forecast_periods
        WHERE ? BETWEEN start_date AND end_date
    """, (today,))
    
    rows = cursor.fetchall()
    print(f"[FINANCIAL] Found {len(rows)} active sectors")
    conn.close()
    
    sectors_analysis = []
    for row in rows:
        sectors_analysis.append({
            "sector": row['sector'],
            "ruler": row['ruler'],
            "trend": row['trend'],
            "intensity": row['intensity'],
            "reason": row['reason'],
            "valid_until": row['end_date']
        })
    
    result = {
        "analysis_date": today,
        "sectors": sectors_analysis,
        "summary": {
            "bullish_count": len([s for s in sectors_analysis if s['trend'] == 'BULLISH']),
            "bearish_count": len([s for s in sectors_analysis if s['trend'] == 'BEARISH']),
            "neutral_count": len([s for s in sectors_analysis if s['trend'] == 'NEUTRAL'])
        }
    }
    
    print(f"[FINANCIAL] Returning analysis with {len(sectors_analysis)} sectors")
    return result

# ADMIN ONLY - Generate new forecast data
@router.post("/admin/regenerate")
async def regenerate_forecast(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    current_user = Depends(get_current_user)
):
    """
    Regenerate market forecast data and save to database.
    Available to all authenticated users.
    """
    # Default to current year if not provided
    if start_year is None:
        start_year = datetime.now().year
    if end_year is None:
        end_year = start_year + 5
    
    # Validation
    if start_year > end_year:
        raise HTTPException(
            status_code=400, 
            detail=f"Start year ({start_year}) cannot be greater than end year ({end_year})"
        )
    
    # Calculate years span - if same year, generate for 1 year only
    years = (end_year - start_year) + 1
    
    from calculators.financial.financial_context_builder import FinancialContextBuilder
    
    print(f"🔄 Regenerating forecast for {start_year}-{end_year} ({years} year(s))...")
    
    builder = FinancialContextBuilder()
    data = builder.build_all_sectors_forecast(start_year, years)
    
    # Save to database
    builder.save_to_database(data)
    
    return {
        "status": "success",
        "message": f"Forecast saved to database for {start_year}-{end_year}",
        "start_year": start_year,
        "end_year": end_year,
        "years_generated": years,
        "total_sectors": data['total_sectors'],
        "total_periods": sum(len(s['timeline']) for s in data['sectors'].values())
    }
