from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class EventRule(BaseModel):
    id: str
    event_type: str
    primary_karaka: str
    secondary_karakas: List[str] = []
    house_significations: List[int]
    activation_methods: List[str]
    transit_triggers: List[str]
    orb_settings: Dict[str, float] = {"conjunction": 3.0, "aspect": 5.0}
    weightage_factors: Dict[str, int] = {}
    classical_references: List[str] = []
    is_active: bool = True

class AnalysisFactor(BaseModel):
    factor_type: str  # "karaka", "dasha", "transit"
    description: str
    weight: int
    confidence: int
    explanation: str

class EventAnalysis(BaseModel):
    event_type: str
    event_date: str
    primary_factors: List[AnalysisFactor]
    dasha_activations: List[AnalysisFactor]
    transit_confirmations: List[AnalysisFactor]
    total_confidence: int
    classical_support: str
    detailed_explanation: str

class LifeEvent(BaseModel):
    id: Optional[int] = None
    user_id: int
    chart_id: int
    event_type: str
    title: str
    description: str
    event_date: str
    event_time: str
    analysis_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None