from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class BirthInput(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str = ""
    latitude: float
    longitude: float
    timezone: Optional[str] = None
    gender: Optional[str] = None
    relation: Optional[str] = "other"
    relation_order: Optional[int] = None
    relation_side: Optional[str] = ""
    relation_label: Optional[str] = ""
    is_family_member: Optional[bool] = None


class PartnershipReportRequest(BaseModel):
    report_type: Literal["partnership"] = "partnership"
    boy_birth_data: BirthInput
    girl_birth_data: BirthInput
    language: str = "english"
    chart_style: Literal["north", "south", "both"] = "both"
    force_regenerate: bool = False
    include_images: bool = True


class WealthReportRequest(BaseModel):
    report_type: Literal["wealth"] = "wealth"
    birth_data: BirthInput
    language: str = "english"
    chart_style: Literal["north", "south", "both"] = "both"
    force_regenerate: bool = False
    include_images: bool = True


class HealthReportRequest(BaseModel):
    report_type: Literal["health"] = "health"
    birth_data: BirthInput
    language: str = "english"
    chart_style: Literal["north", "south", "both"] = "both"
    force_regenerate: bool = False
    include_images: bool = True


class ReportBranding(BaseModel):
    """Practice / pandit branding stamped on generated PDF cover + footer."""

    business_name: str = ""
    tagline: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    address: str = ""
    show_powered_by: bool = True


class JanamKundliReportRequest(BaseModel):
    report_type: Literal["janam_kundli"] = "janam_kundli"
    birth_data: BirthInput
    language: str = "english"
    chart_style: Literal["north", "south", "both"] = "both"
    force_regenerate: bool = False
    include_images: bool = True
    branding: Optional[ReportBranding] = None


class ReportMetric(BaseModel):
    label: str
    value: str
    tone: Optional[str] = None


class ReportPage(BaseModel):
    page_number: int
    title: str
    subtitle: Optional[str] = None
    summary: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    metrics: List[ReportMetric] = Field(default_factory=list)
    chart_refs: List[str] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    cta: Optional[str] = None
    section_key: Optional[str] = None
    skip_render: bool = False


class ReportDocument(BaseModel):
    report_id: str
    report_type: str
    language: str
    generated_at: datetime
    report_version: str
    status: str = "completed"
    pair: Dict[str, Any]
    score_summary: Dict[str, Any] = Field(default_factory=dict)
    branch_payloads: Dict[str, Any] = Field(default_factory=dict)
    pages: List[ReportPage] = Field(default_factory=list)
    chart_manifest: List[Dict[str, Any]] = Field(default_factory=list)
    faq: List[Dict[str, Any]] = Field(default_factory=list)
    cta: Dict[str, Any] = Field(default_factory=dict)
    premium_report: Dict[str, Any] = Field(default_factory=dict)
    chart_data: Dict[str, Any] = Field(default_factory=dict)
    chart_style: str = "north"
    cached: bool = False
    branding: Dict[str, Any] = Field(default_factory=dict)
