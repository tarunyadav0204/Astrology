from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from db import execute, get_conn
from .catalog import SUBJECT_TYPES, catalog


router = APIRouter(prefix="/admin/sutra-rules", tags=["admin_sutra_rules"])

STREAMS = ["parashari", "jaimini", "kp", "nadi"]
CHARTS = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D20", "D24", "D30", "D60", "bhava_chalit"]
TOPICS = ["identity", "mind", "relationships", "career", "wealth", "health", "education", "spirituality", "timing"]
VISIBILITY = ["user_summary", "user_evidence", "astrologer_only", "admin_only"]
FACTS = [
    {"key": "planet.sign", "label": "Planet is in sign", "value_type": "sign", "subjects": "planets"},
    {"key": "planet.house", "label": "Planet is in house", "value_type": "house", "subjects": "planets"},
    {"key": "planet.nakshatra", "label": "Planet is in nakshatra", "value_type": "nakshatra", "subjects": "planets"},
    {"key": "planet.pada", "label": "Planet is in nakshatra pada", "value_type": "pada", "subjects": "planets"},
    {"key": "planet.degree", "label": "Planet degree", "value_type": "number", "subjects": "planets"},
    {"key": "planet.condition", "label": "Planet condition / dignity", "value_type": "condition"},
    {"key": "planet.relationship", "label": "Planet relationship / aspect", "value_type": "planet"},
    {"key": "house.lord.sign", "label": "Lord of house is in sign", "value_type": "sign", "subjects": "houses"},
    {"key": "house.lord.house", "label": "Lord of house is in house", "value_type": "house", "subjects": "houses"},
    {"key": "house.lord.nakshatra", "label": "Lord of house is in nakshatra", "value_type": "nakshatra", "subjects": "houses"},
    {"key": "house.lord.condition", "label": "Lord of house has condition", "value_type": "condition", "subjects": "houses"},
    {"key": "jaimini.karaka.placement", "label": "Chara karaka placement", "value_type": "karaka"},
    {"key": "jaimini.upapada.second_from", "label": "Second from Upapada", "value_type": "planet"},
    {"key": "jaimini.arudha.relationship", "label": "Arudha / Upapada relationship", "value_type": "reference"},
    {"key": "kp.cusp.sublord", "label": "KP cusp sub-lord", "value_type": "planet"},
    {"key": "kp.significator.houses", "label": "KP significator houses", "value_type": "houses"},
    {"key": "nadi.linkage", "label": "Nadi planetary linkage", "value_type": "planet"},
    {"key": "yoga.presence", "label": "Named yoga present", "value_type": "text"},
    {"key": "varga.repetition", "label": "Repeats in divisional chart", "value_type": "chart"},
    {"key": "dasha.chain", "label": "Dasha chain activation", "value_type": "planet"},
    {"key": "transit.contact", "label": "Transit contact", "value_type": "planet"},
]


class Condition(BaseModel):
    id: str
    subject_type: str
    stream: str
    subject: Dict[str, Any] = Field(default_factory=dict)
    predicate: str
    operator: str
    value: Any = None
    chart: Optional[str] = None
    required: bool = True

    def model_post_init(self, __context: Any) -> None:
        definition = SUBJECT_TYPES.get(self.subject_type)
        if not definition:
            raise ValueError(f"Unsupported subject type: {self.subject_type}")
        if self.stream not in definition["streams"]:
            raise ValueError(f"{self.subject_type} is not a {self.stream} proposition")
        if self.predicate not in definition["predicates"]:
            raise ValueError(f"Unsupported predicate {self.predicate} for {self.subject_type}")
        missing = [field for field in definition["fields"] if not self.subject.get(field)]
        if missing:
            raise ValueError(f"{self.subject_type} requires {', '.join(missing)}")


class SutraRulePayload(BaseModel):
    rule_key: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9._-]+$")
    title: str = Field(min_length=3, max_length=240)
    status: Literal["draft", "review", "active", "deprecated"] = "draft"
    primary_stream: str
    primary_chart: str
    category: str
    subcategory: str
    tags: List[str] = Field(default_factory=list)
    authority: Dict[str, Any] = Field(default_factory=dict)
    logic_operator: Literal["all", "any", "at_least"] = "all"
    conditions: List[Condition] = Field(default_factory=list)
    modifiers: Dict[str, List[Condition]] = Field(default_factory=lambda: {"supports": [], "weakens": [], "exceptions": []})
    outputs: Dict[str, str] = Field(default_factory=dict)
    visibility: str = "astrologer_only"
    safety: Dict[str, Any] = Field(default_factory=dict)
    reviewer_notes: str = ""


def require_admin(current_user=Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _ensure_schema(conn) -> None:
    execute(conn, """
        CREATE TABLE IF NOT EXISTS sutra_rules (
          id TEXT PRIMARY KEY, rule_key TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
          status TEXT NOT NULL, primary_stream TEXT NOT NULL, primary_chart TEXT NOT NULL,
          topics JSONB NOT NULL DEFAULT '[]'::jsonb, category TEXT, subcategory TEXT, tags JSONB NOT NULL DEFAULT '[]'::jsonb, authority JSONB NOT NULL DEFAULT '{}'::jsonb,
          logic_operator TEXT NOT NULL, conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
          modifiers JSONB NOT NULL DEFAULT '{}'::jsonb, outputs JSONB NOT NULL DEFAULT '{}'::jsonb,
          visibility TEXT NOT NULL, safety JSONB NOT NULL DEFAULT '{}'::jsonb,
          reviewer_notes TEXT NOT NULL DEFAULT '', created_by INTEGER, updated_by INTEGER,
          created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, "ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS category TEXT")
    execute(conn, "ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS subcategory TEXT")
    execute(conn, "ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb")


def _payload_values(payload: SutraRulePayload, user_id: int) -> tuple:
    data = payload.model_dump(mode="json")
    return (
        data["rule_key"], data["title"], data["status"], data["primary_stream"], data["primary_chart"], data["category"], data["subcategory"], json.dumps(data["tags"]), json.dumps(data["authority"]), data["logic_operator"],
        json.dumps(data["conditions"]), json.dumps(data["modifiers"]), json.dumps(data["outputs"]),
        data["visibility"], json.dumps(data["safety"]), data["reviewer_notes"], user_id,
    )


@router.get("/catalog")
def get_catalog(_: Any = Depends(require_admin)):
    return {**catalog(), "visibility": VISIBILITY}


@router.get("")
def list_rules(_: Any = Depends(require_admin)):
    with get_conn() as conn:
        _ensure_schema(conn)
        cursor = execute(conn, "SELECT * FROM sutra_rules ORDER BY updated_at DESC")
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.commit()
    return {"rules": rows}


@router.post("")
def create_rule(payload: SutraRulePayload, user: Any = Depends(require_admin)):
    rule_id = str(uuid4())
    with get_conn() as conn:
        _ensure_schema(conn)
        try:
            execute(conn, """INSERT INTO sutra_rules
              (id,rule_key,title,status,primary_stream,primary_chart,category,subcategory,tags,authority,logic_operator,conditions,modifiers,outputs,visibility,safety,reviewer_notes,created_by,updated_by)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s)""",
              (rule_id, *_payload_values(payload, int(user.userid)), int(user.userid)))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=409, detail=f"Could not save rule: {exc}") from exc
    return {"id": rule_id, "saved": True}


@router.put("/{rule_id}")
def update_rule(rule_id: str, payload: SutraRulePayload, user: Any = Depends(require_admin)):
    values = _payload_values(payload, int(user.userid))
    with get_conn() as conn:
        _ensure_schema(conn)
        row = execute(conn, """UPDATE sutra_rules SET rule_key=%s,title=%s,status=%s,primary_stream=%s,primary_chart=%s,category=%s,subcategory=%s,
          tags=%s::jsonb,authority=%s::jsonb,logic_operator=%s,conditions=%s::jsonb,modifiers=%s::jsonb,outputs=%s::jsonb,
          visibility=%s,safety=%s::jsonb,reviewer_notes=%s,updated_by=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s RETURNING id""",
          (*values, rule_id)).fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Sutra rule not found")
    return {"id": rule_id, "saved": True}
