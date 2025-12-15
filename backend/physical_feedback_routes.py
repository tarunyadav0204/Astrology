from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
import logging
from physical_traits_cache import PhysicalTraitsCache

router = APIRouter()

class FeedbackRequest(BaseModel):
    chart_data: Dict
    birth_data: Dict
    feedback: str  # "accurate" or "inaccurate"
    birth_chart_id: int = None

@router.post("/physical-feedback")
async def submit_physical_feedback(request: FeedbackRequest):
    """Store user feedback for physical trait predictions."""
    try:
        cache = PhysicalTraitsCache()
        birth_chart_id = request.birth_chart_id or request.chart_data.get('birth_chart_id', 0)
        print(f"📝 Storing feedback for birth_chart_id: {birth_chart_id}")
        cache.update_feedback(birth_chart_id, request.feedback)
        
        logging.info(f"📝 Physical traits feedback: {request.feedback} for chart {birth_chart_id}")
        
        return {"success": True, "message": "Feedback recorded"}
        
    except Exception as e:
        logging.error(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))