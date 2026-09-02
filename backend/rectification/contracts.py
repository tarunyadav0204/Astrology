from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from .registry import EVENT_DEFINITIONS


DatePrecision = Literal["exact_day", "month", "year", "range"]
SourceReliability = Literal["documented", "confident_memory", "approximate_memory"]


class CreateRectificationCaseRequest(BaseModel):
    birth_chart_id: int
    uncertainty_minutes: int = Field(default=60, ge=1, le=60)
    window_start_local: Optional[str] = None
    window_end_local: Optional[str] = None

    @model_validator(mode="after")
    def validate_explicit_window(self):
        if bool(self.window_start_local) != bool(self.window_end_local):
            raise ValueError("Both window_start_local and window_end_local are required")
        return self


class CreateRectificationEventRequest(BaseModel):
    event_type: str
    date_start: date
    date_end: Optional[date] = None
    precision: DatePrecision = "exact_day"
    source_reliability: SourceReliability = "confident_memory"
    subtype: str = Field(default="", max_length=80)
    subject: str = Field(default="self", max_length=40)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        self.event_type = str(self.event_type or "").strip().lower()
        if self.event_type not in EVENT_DEFINITIONS:
            raise ValueError(f"Unsupported rectification event type: {self.event_type}")
        self.subject = str(self.subject or "self").strip().lower()
        if self.subject != "self":
            raise ValueError("Phase 1 rectification supports events experienced by the native only")
        if self.date_end is None:
            if self.precision == "month":
                self.date_start = self.date_start.replace(day=1)
                self.date_end = self.date_start.replace(
                    day=monthrange(self.date_start.year, self.date_start.month)[1]
                )
            elif self.precision == "year":
                self.date_start = date(self.date_start.year, 1, 1)
                self.date_end = date(self.date_start.year, 12, 31)
            elif self.precision == "range":
                raise ValueError("date_end is required when precision is range")
            else:
                self.date_end = self.date_start
        if self.date_end < self.date_start:
            raise ValueError("date_end cannot be earlier than date_start")
        if (self.date_end - self.date_start).days > 366:
            raise ValueError("One rectification event cannot span more than 366 days")
        return self


class UpdateRectificationEventRequest(BaseModel):
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    precision: Optional[DatePrecision] = None
    source_reliability: Optional[SourceReliability] = None
    subtype: Optional[str] = Field(default=None, max_length=80)
    subject: Optional[str] = Field(default=None, max_length=40)
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_subject(self):
        if self.subject is not None and str(self.subject).strip().lower() != "self":
            raise ValueError("Phase 1 rectification supports events experienced by the native only")
        return self


class StartRectificationRunRequest(BaseModel):
    minute_step: int = Field(default=1, ge=1, le=5)
