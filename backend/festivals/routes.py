"""
Festival API Routes
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from .festival_calculator import FestivalCalculator
from .festival_data import HINDU_FESTIVALS, FESTIVAL_CATEGORIES

router = APIRouter(prefix="/festivals", tags=["festivals"])
calculator = FestivalCalculator()

@router.get("/today")
async def get_today_festivals():
    """Get festivals for today"""
    today = datetime.now()
    festivals = calculator.find_festival_dates(today.year, today.month)
    today_str = today.strftime("%Y-%m-%d")
    
    return {
        "date": today_str,
        "festivals": [f for f in festivals if f["date"] == today_str]
    }

@router.get("/month/{year}/{month}")
async def get_monthly_festivals(year: int, month: int):
    """Get all festivals for a specific month"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    festivals = calculator.find_festival_dates(year, month)
    vrats = calculator.get_monthly_vrats(year, month)
    
    return {
        "year": year,
        "month": month,
        "festivals": festivals,
        "vrats": vrats,
        "total_count": len(festivals) + len(vrats)
    }

@router.get("/year/{year}")
async def get_yearly_festivals(year: int):
    """Get all festivals for a year"""
    festivals = calculator.find_festival_dates(year)
    
    # Group by month
    monthly_data = {}
    for festival in festivals:
        month = int(festival["date"].split("-")[1])
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(festival)
    
    return {
        "year": year,
        "monthly_festivals": monthly_data,
        "total_festivals": len(festivals)
    }

@router.get("/categories")
async def get_festival_categories():
    """Get festival categories"""
    return FESTIVAL_CATEGORIES

@router.get("/search")
async def search_festivals(q: str):
    """Search festivals by name, description, or significance"""
    if not q or len(q.strip()) < 2:
        return {"festivals": []}
    
    search_term = q.lower().strip()
    matches = []
    
    # Search through all festivals
    for key, festival in HINDU_FESTIVALS.items():
        # Check name, description, significance, and type
        searchable_text = (
            festival.get("name", "").lower() + " " +
            festival.get("description", "").lower() + " " +
            festival.get("significance", "").lower() + " " +
            festival.get("type", "").lower()
        )
        
        if search_term in searchable_text:
            matches.append({
                "id": key,
                **festival
            })
    
    return {"festivals": matches}

@router.get("/search/{festival_name}")
async def search_festival(festival_name: str):
    """Search for specific festival information"""
    festival_name = festival_name.lower().replace(" ", "_")
    
    if festival_name in HINDU_FESTIVALS:
        return HINDU_FESTIVALS[festival_name]
    
    # Search in festival names
    matches = []
    for key, festival in HINDU_FESTIVALS.items():
        if festival_name in festival["name"].lower():
            matches.append({
                "id": key,
                **festival
            })
    
    if matches:
        return {"matches": matches}
    
    raise HTTPException(status_code=404, detail="Festival not found")