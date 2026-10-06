from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from db import execute, get_conn
from .catalog import SUBJECT_TYPES, catalog


router = APIRouter(prefix="/admin/sutra-rules", tags=["admin_sutra_rules"])

DEVA_KERALAM_EDITION_KEY = "deva_keralam_volume_1_scan"

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


def _rows(cursor) -> List[Dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _row(cursor) -> Optional[Dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    value = cursor.fetchone()
    return dict(zip(columns, value)) if value else None


def _status_counts(conn, table: str, column: str, *, edition_column: str = "edition_key") -> Dict[str, int]:
    # Identifiers are internal constants supplied only by callers below.
    cursor = execute(
        conn,
        f"SELECT {column}, COUNT(*) AS count FROM {table} "
        f"WHERE {edition_column} = %s GROUP BY {column} ORDER BY {column}",
        (DEVA_KERALAM_EDITION_KEY,),
    )
    return {str(row[0]): int(row[1]) for row in cursor.fetchall()}


@router.get("/catalog")
def get_catalog(_: Any = Depends(require_admin)):
    return {**catalog(), "visibility": VISIBILITY}


@router.get("/classical-packs")
def list_classical_packs(_: Any = Depends(require_admin)):
    from classical_rules.registry import list_packs
    return {"packs": list(list_packs())}


@router.get("/classical-packs/{work_key}/{chapter}")
def get_classical_pack(work_key: str, chapter: int, _: Any = Depends(require_admin)):
    from classical_rules.registry import get_pack
    try:
        return get_pack(work_key, chapter)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/deva-keralam/coverage")
def get_deva_keralam_coverage(_: Any = Depends(require_admin)):
    """Return import and review coverage without returning copyrighted text."""
    with get_conn() as conn:
        coverage = _row(execute(
            conn,
            """
            SELECT edition_key, expected_pages, catalogued_pages, ocr_complete_pages,
                   verified_pages, catalogued_passages, executable_passages, source_linked_rules
              FROM classical_source_coverage
             WHERE edition_key = %s
            """,
            (DEVA_KERALAM_EDITION_KEY,),
        ))
        latest_run = _row(execute(
            conn,
            """
            SELECT import_run_key, status, page_start, page_end, pages_completed, pages_failed,
                   started_at, completed_at, error_message
              FROM classical_source_import_runs
             WHERE edition_key = %s
             ORDER BY started_at DESC
             LIMIT 1
            """,
            (DEVA_KERALAM_EDITION_KEY,),
        ))
        page_ocr = _status_counts(conn, "classical_source_pages", "ocr_status")
        page_review = _status_counts(conn, "classical_source_pages", "review_status")
        context_review = _status_counts(conn, "classical_context_blocks", "context_status")
        passage_review = _status_counts(conn, "classical_passages", "review_status")
        passage_execution = _status_counts(conn, "classical_passages", "executable_status")

    if coverage is None:
        coverage = {
            "edition_key": DEVA_KERALAM_EDITION_KEY,
            "expected_pages": 0,
            "catalogued_pages": 0,
            "ocr_complete_pages": 0,
            "verified_pages": 0,
            "catalogued_passages": 0,
            "executable_passages": 0,
            "source_linked_rules": 0,
        }
    if latest_run:
        total = max(int(latest_run["page_end"]) - int(latest_run["page_start"]) + 1, 1)
        processed = int(latest_run["pages_completed"]) + int(latest_run["pages_failed"])
        latest_run["total_pages"] = total
        latest_run["processed_pages"] = processed
        latest_run["progress_percent"] = round(min(processed / total, 1.0) * 100, 2)
    return {
        "edition_key": DEVA_KERALAM_EDITION_KEY,
        "coverage": coverage,
        "latest_import_run": latest_run,
        "status_totals": {
            "page_ocr": page_ocr,
            "page_review": page_review,
            "context_review": context_review,
            "passage_review": passage_review,
            "passage_execution": passage_execution,
        },
        "source_text_included": False,
    }


@router.get("/deva-keralam/pages")
def list_deva_keralam_pages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ocr_status: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    _: Any = Depends(require_admin),
):
    filters = ["edition_key = %s"]
    params: List[Any] = [DEVA_KERALAM_EDITION_KEY]
    if ocr_status:
        filters.append("ocr_status = %s")
        params.append(ocr_status)
    if review_status:
        filters.append("review_status = %s")
        params.append(review_status)
    where = " AND ".join(filters)
    with get_conn() as conn:
        total_row = execute(conn, f"SELECT COUNT(*) FROM classical_source_pages WHERE {where}", tuple(params)).fetchone()
        cursor = execute(
            conn,
            f"""
            SELECT source_page_id, pdf_page, printed_page_label, chapter_label,
                   ocr_engine, ocr_languages, ocr_confidence, ocr_status, review_status,
                   last_import_run_key, updated_at,
                   (raw_ocr <> '') AS has_raw_ocr,
                   (corrected_text <> '') AS has_corrected_text,
                   (image_object_key <> '') AS has_page_image
              FROM classical_source_pages
             WHERE {where}
             ORDER BY pdf_page
             LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        pages = _rows(cursor)
    return {
        "edition_key": DEVA_KERALAM_EDITION_KEY,
        "pages": pages,
        "pagination": {"total": int(total_row[0] if total_row else 0), "limit": limit, "offset": offset},
        "source_text_included": False,
    }


@router.get("/deva-keralam/passages")
def list_deva_keralam_passages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    review_status: Optional[str] = Query(None),
    executable_status: Optional[str] = Query(None),
    _: Any = Depends(require_admin),
):
    filters = ["passage.edition_key = %s"]
    params: List[Any] = [DEVA_KERALAM_EDITION_KEY]
    if review_status:
        filters.append("passage.review_status = %s")
        params.append(review_status)
    if executable_status:
        filters.append("passage.executable_status = %s")
        params.append(executable_status)
    where = " AND ".join(filters)
    with get_conn() as conn:
        total_row = execute(conn, f"SELECT COUNT(*) FROM classical_passages passage WHERE {where}", tuple(params)).fetchone()
        cursor = execute(
            conn,
            f"""
            SELECT passage.passage_key, passage.context_block_key, passage.chapter_number,
                   passage.verse_start, passage.verse_end, passage.title, passage.classification,
                   passage.source_text_status, passage.review_status, passage.textual_confidence,
                   passage.executable_status, passage.pdf_page_start, passage.pdf_page_end,
                   passage.printed_page_start, passage.printed_page_end,
                   (passage.source_text <> '') AS has_source_text,
                   (passage.translation_text <> '') AS has_translation,
                   (passage.editor_notes <> '') AS has_editor_notes,
                   COUNT(DISTINCT anchor.anchor_type || ':' || anchor.anchor_value) AS anchor_count,
                   COUNT(DISTINCT link.rule_key || ':' || link.rule_version::text) AS linked_rule_count
              FROM classical_passages passage
              LEFT JOIN classical_passage_anchors anchor ON anchor.passage_key = passage.passage_key
              LEFT JOIN classical_rule_source_links link ON link.passage_key = passage.passage_key
             WHERE {where}
             GROUP BY passage.passage_key
             ORDER BY passage.pdf_page_start NULLS LAST, passage.verse_start, passage.passage_key
             LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        passages = _rows(cursor)
    return {
        "edition_key": DEVA_KERALAM_EDITION_KEY,
        "passages": passages,
        "pagination": {"total": int(total_row[0] if total_row else 0), "limit": limit, "offset": offset},
        "source_text_included": False,
    }


@router.get("/deva-keralam/executable-rules")
def list_deva_keralam_executable_rules(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    _: Any = Depends(require_admin),
):
    status_filter = " AND rule.status = %s" if status else ""
    params: List[Any] = [DEVA_KERALAM_EDITION_KEY]
    if status:
        params.append(status)
    with get_conn() as conn:
        total_row = execute(
            conn,
            f"""
            SELECT COUNT(DISTINCT (rule.rule_key, rule.version))
              FROM classical_rule_versions rule
              JOIN classical_rule_source_links link
                ON link.rule_key = rule.rule_key AND link.rule_version = rule.version
              JOIN classical_passages passage ON passage.passage_key = link.passage_key
             WHERE passage.edition_key = %s{status_filter}
            """,
            tuple(params),
        ).fetchone()
        cursor = execute(
            conn,
            f"""
            WITH selected_rules AS (
              SELECT DISTINCT rule.rule_key, rule.version, rule.title, rule.rule_type,
                     rule.scope, rule.status, rule.calculator_binding, rule.topics, rule.created_at
                FROM classical_rule_versions rule
                JOIN classical_rule_source_links link
                  ON link.rule_key = rule.rule_key AND link.rule_version = rule.version
                JOIN classical_passages passage ON passage.passage_key = link.passage_key
               WHERE passage.edition_key = %s{status_filter}
               ORDER BY rule.rule_key, rule.version DESC
               LIMIT %s OFFSET %s
            )
            SELECT selected.*, link.relationship, passage.passage_key,
                   passage.verse_start, passage.verse_end, passage.pdf_page_start,
                   passage.pdf_page_end, passage.review_status AS source_review_status,
                   passage.textual_confidence AS source_textual_confidence,
                   passage.executable_status AS source_executable_status
              FROM selected_rules selected
              LEFT JOIN classical_rule_source_links link
                ON link.rule_key = selected.rule_key AND link.rule_version = selected.version
              LEFT JOIN classical_passages passage ON passage.passage_key = link.passage_key
             ORDER BY selected.rule_key, selected.version DESC, passage.verse_start
            """,
            (*params, limit, offset),
        )
        rows = _rows(cursor)

    rules: List[Dict[str, Any]] = []
    by_key: Dict[tuple, Dict[str, Any]] = {}
    rule_fields = (
        "rule_key", "version", "title", "rule_type", "scope", "status",
        "calculator_binding", "topics", "created_at",
    )
    for row in rows:
        identity = (row["rule_key"], row["version"])
        rule = by_key.get(identity)
        if rule is None:
            rule = {key: row[key] for key in rule_fields}
            rule["sources"] = []
            by_key[identity] = rule
            rules.append(rule)
        if row.get("passage_key"):
            rule["sources"].append({
                "passage_key": row["passage_key"],
                "relationship": row["relationship"],
                "verse_start": row["verse_start"],
                "verse_end": row["verse_end"],
                "pdf_page_start": row["pdf_page_start"],
                "pdf_page_end": row["pdf_page_end"],
                "review_status": row["source_review_status"],
                "textual_confidence": row["source_textual_confidence"],
                "executable_status": row["source_executable_status"],
            })
    return {
        "edition_key": DEVA_KERALAM_EDITION_KEY,
        "rules": rules,
        "pagination": {"total": int(total_row[0] if total_row else 0), "limit": limit, "offset": offset},
        "source_text_included": False,
    }


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
