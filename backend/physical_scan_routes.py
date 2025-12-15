from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from calculators.chart_calculator import ChartCalculator
from calculators.physical_trait_scanner import PhysicalTraitScanner
from calculators.gemini_physical_analyzer import GeminiPhysicalAnalyzer
from pydantic import BaseModel
from typing import Dict, Any
import logging

router = APIRouter()

class PhysicalScanRequest(BaseModel):
    birth_data: Dict[str, Any]
    birth_chart_id: int = None

@router.get("/scan-physical-test")
async def test_physical_scan_route():
    """Test endpoint to verify physical scan router is working"""
    print("🧪 Physical scan test endpoint hit!")
    logging.info("Physical scan test endpoint accessed")
    return {"status": "Physical scan router is working", "timestamp": "2025-12-15"}

@router.post("/scan-physical")
async def scan_physical_traits(request: PhysicalScanRequest, current_user = Depends(get_current_user)):
    """Scan physical traits from birth chart"""
    try:
        print(f"🔍 PHYSICAL SCAN ENDPOINT HIT - User: {current_user}")
        print(f"📊 FULL REQUEST: {request}")
        print(f"📊 Birth data: {request.birth_data}")
        print(f"🆔 Birth chart ID: {request.birth_chart_id}")
        print(f"🆔 Birth chart ID type: {type(request.birth_chart_id)}")
        logging.info(f"Physical scan request for user: {current_user}")
        logging.info(f"Birth data: {request.birth_data}")
        logging.info(f"Birth chart ID: {request.birth_chart_id}")
        
        # First calculate the chart
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**request.birth_data)
        
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        logging.info(f"Chart calculated - Ascendant: {chart_data.get('ascendant_sign')}, Planets: {list(chart_data.get('planets', {}).keys())}")
        
        # Get birth chart ID from request
        birth_chart_id = request.birth_chart_id
        print(f"🆔 Final birth_chart_id: {birth_chart_id} (type: {type(birth_chart_id)})")
        print(f"🔍 Is birth_chart_id None? {birth_chart_id is None}")
        print(f"🔍 Is birth_chart_id falsy? {not birth_chart_id}")
        
        # Check if feedback already exists
        from physical_traits_cache import PhysicalTraitsCache
        cache = PhysicalTraitsCache()
        has_feedback = cache.has_feedback(birth_chart_id) if birth_chart_id else False
        
        # Check cache first if we have a valid birth_chart_id
        cached_traits = cache.get_cached_traits(birth_chart_id) if birth_chart_id else None
        if cached_traits:
            print(f"📦 Using cached traits: {len(cached_traits)} traits")
            traits = cached_traits
        else:
            # Use Gemini AI for physical trait analysis
            try:
                print(f"🤖 Calling Gemini AI for analysis...")
                gemini_analyzer = GeminiPhysicalAnalyzer()
                traits = gemini_analyzer.analyze_physical_traits(chart_data, request.birth_data, birth_chart_id)
                logging.info(f"Gemini traits found: {len(traits)} - {[t.get('label', 'Unknown') for t in traits[:3]]}")
                # Caching is handled inside the analyzer now
            except Exception as gemini_error:
                logging.warning(f"Gemini analysis failed: {gemini_error}, falling back to traditional method")
                # Fallback to traditional scanner
                scanner = PhysicalTraitScanner(chart_calc)
                traits = scanner.scan_physical_features(request.birth_data)
                logging.info(f"Fallback traits found: {len(traits)} - {[t.get('label', 'Unknown') for t in traits[:3]]}")
                # Cache the fallback traits if we have a valid birth_chart_id
                if birth_chart_id:
                    cache.cache_traits(birth_chart_id, traits)
        
        print(f"✅ Physical scan completed - returning {len(traits)} traits")
        print(f"🔍 Sample trait: {traits[0] if traits else 'No traits'}")
        return {
            "success": True,
            "traits": traits,
            "count": len(traits),
            "has_feedback": has_feedback
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Physical scan error: {str(e)}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        logging.error(f"Physical scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Physical scan failed: {str(e)}")