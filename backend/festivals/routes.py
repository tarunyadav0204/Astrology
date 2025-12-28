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
    festivals = calculator.find_festival_dates(today.year, today.month, 28.6139, 77.2090, "amanta", "Asia/Kolkata")
    today_str = today.strftime("%Y-%m-%d")
    
    return {
        "date": today_str,
        "festivals": [f for f in festivals if f["date"] == today_str]
    }

@router.get("/month/{year}/{month}")
async def get_monthly_festivals(year: int, month: int, lat: float = 28.6139, lon: float = 77.2090, 
                              calendar_system: str = "amanta", timezone_offset: float = 5.5):
    """Get all festivals for a specific month with full Drik Panchang accuracy"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    if calendar_system not in ["amanta", "purnimanta"]:
        raise HTTPException(status_code=400, detail="Invalid calendar system. Use 'amanta' or 'purnimanta'")
    
    # Convert timezone offset to timezone name
    timezone_map = {
        5.5: "Asia/Kolkata",
        0: "UTC", 
        -5: "America/New_York",
        -8: "America/Los_Angeles",
        1: "Europe/London",
        -5: "America/Toronto"
    }
    timezone_name = timezone_map.get(timezone_offset, "Asia/Kolkata")
    
    festivals = calculator.find_festival_dates(year, month, lat, lon, calendar_system, timezone_name)
    vrats = calculator.get_monthly_vrats(year, month, lat, lon, calendar_system, timezone_name)
    
    return {
        "year": year,
        "month": month,
        "latitude": lat,
        "longitude": lon,
        "calendar_system": calendar_system,
        "timezone_offset": timezone_offset,
        "festivals": festivals,
        "vrats": vrats,
        "total_count": len(festivals) + len(vrats)
    }

@router.get("/year/{year}")
async def get_yearly_festivals(year: int, lat: float = 28.6139, lon: float = 77.2090):
    """Get all festivals for a year with geographic precision"""
    festivals = calculator.find_festival_dates(year, None, lat, lon, "amanta", "Asia/Kolkata")
    
    # Group by month
    monthly_data = {}
    for festival in festivals:
        month = int(festival["date"].split("-")[1])
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(festival)
    
    return {
        "year": year,
        "latitude": lat,
        "longitude": lon,
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