from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from .models import EventRule, EventAnalysis, LifeEvent
from .analyzer import EventAnalyzer
from .rules_config import DEFAULT_RULES, HOUSE_SIGNIFICATIONS, PLANETARY_KARAKAS, BODY_PARTS_BY_HOUSE
import json

router = APIRouter(prefix="/rule-engine", tags=["Rule Engine"])
analyzer = EventAnalyzer()

@router.post("/analyze-event", response_model=EventAnalysis)
async def analyze_event(
    birth_chart: Dict[str, Any],
    event_date: str,
    event_type: str
):
    """Analyze a life event using the rule engine"""
    try:
        analysis = analyzer.analyze_event(birth_chart, event_date, event_type)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/rules", response_model=List[Dict])
async def get_all_rules():
    """Get all available rules"""
    return [
        {
            "id": rule_id,
            **rule_data
        }
        for rule_id, rule_data in DEFAULT_RULES.items()
    ]

@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    """Get a specific rule by ID"""
    if rule_id not in DEFAULT_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "id": rule_id,
        **DEFAULT_RULES[rule_id]
    }

@router.post("/rules")
async def create_rule(rule: EventRule):
    """Create a new rule (Admin only)"""
    # In production, add admin authentication
    DEFAULT_RULES[rule.id] = rule.dict()
    return {"message": "Rule created successfully", "rule_id": rule.id}

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule: EventRule):
    """Update an existing rule (Admin only)"""
    if rule_id not in DEFAULT_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    DEFAULT_RULES[rule_id] = rule.dict()
    return {"message": "Rule updated successfully"}

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule (Admin only)"""
    if rule_id not in DEFAULT_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    del DEFAULT_RULES[rule_id]
    return {"message": "Rule deleted successfully"}

@router.get("/event-types")
async def get_event_types():
    """Get all available event types"""
    return [
        {
            "id": rule_id,
            "name": rule_data["event_type"].replace("_", " ").title(),
            "karaka": rule_data["primary_karaka"],
            "houses": rule_data["house_significations"]
        }
        for rule_id, rule_data in DEFAULT_RULES.items()
    ]

@router.get("/search")
async def search_rules(q: str = Query(..., description="Search query")):
    """Search rules by planet, specification, house number, or any text"""
    query = q.lower().strip()
    results = {
        "rules": [],
        "house_significations": [],
        "planetary_karakas": [],
        "body_parts": []
    }
    
    # Search in rules
    for rule_id, rule in DEFAULT_RULES.items():
        if search_in_rule(rule, query):
            results["rules"].append({"id": rule_id, **rule})
    
    # Search in house significations
    for house_num, significations in HOUSE_SIGNIFICATIONS.items():
        if search_in_house_significations(house_num, significations, query):
            results["house_significations"].append({
                "house": house_num,
                "significations": significations
            })
    
    # Search in planetary karakas
    for planet, karakas in PLANETARY_KARAKAS.items():
        if search_in_planetary_karakas(planet, karakas, query):
            results["planetary_karakas"].append({
                "planet": planet,
                "karakas": karakas
            })
    
    # Search in body parts
    for house_num, body_parts in BODY_PARTS_BY_HOUSE.items():
        if search_in_body_parts(house_num, body_parts, query):
            results["body_parts"].append({
                "house": house_num,
                "body_parts": body_parts
            })
    
    return results

def search_in_rule(rule, query):
    """Search within a rule for the query"""
    # Check house numbers
    if query.isdigit() and int(query) in rule.get("house_significations", []):
        return True
    
    # Check planets
    planets = [rule.get("primary_karaka", "")] + rule.get("secondary_karakas", [])
    if any(query in planet.lower() for planet in planets):
        return True
    
    # Check event type and other text fields
    text_fields = [
        rule.get("event_type", ""),
        str(rule.get("house_significations", [])),
        str(rule.get("body_parts", [])),
        str(rule.get("activation_methods", [])),
        str(rule.get("classical_references", []))
    ]
    
    return any(query in field.lower() for field in text_fields)

def search_in_house_significations(house_num, significations, query):
    """Search in house significations"""
    if query.isdigit() and int(query) == house_num:
        return True
    
    if isinstance(significations, dict):
        all_significations = []
        for category in significations.values():
            all_significations.extend(category)
        return any(query in sig.lower() for sig in all_significations)
    else:
        return any(query in sig.lower() for sig in significations)

def search_in_planetary_karakas(planet, karakas, query):
    """Search in planetary karakas"""
    if query in planet.lower():
        return True
    return any(query in karaka.lower() for karaka in karakas)

def search_in_body_parts(house_num, body_parts, query):
    """Search in body parts"""
    if query.isdigit() and int(query) == house_num:
        return True
    
    all_parts = []
    if isinstance(body_parts, dict):
        for category in body_parts.values():
            if isinstance(category, list):
                all_parts.extend(category)
    
    return any(query in part.lower() for part in all_parts)

@router.post("/test-rule")
async def test_rule(
    rule_id: str,
    birth_chart: Dict[str, Any],
    event_date: str
):
    """Test a rule against sample data"""
    if rule_id not in DEFAULT_RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule = DEFAULT_RULES[rule_id]
    analysis = analyzer.analyze_event(birth_chart, event_date, rule["event_type"])
    
    return {
        "rule_id": rule_id,
        "analysis": analysis,
        "debug_info": {
            "rule_applied": rule["event_type"],
            "karaka_checked": rule["primary_karaka"],
            "houses_checked": rule["house_significations"]
        }
    }