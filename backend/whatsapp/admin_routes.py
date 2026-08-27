"""Admin endpoints for discovering and sending approved WhatsApp templates."""
from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from db import execute, get_conn
from .messaging import fetch_whatsapp_message_templates, send_whatsapp_template

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/whatsapp", tags=["admin-whatsapp"])

MAX_RECIPIENTS = 100
_VARIABLE_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")


class RecipientRequest(BaseModel):
    user_ids: List[int] = Field(default_factory=list)


class VariableMapping(BaseModel):
    source: str = Field(..., min_length=1, max_length=32)
    value: Optional[str] = Field(default=None, max_length=2000)
    field: Optional[str] = Field(default=None, max_length=32)
    values: Dict[str, str] = Field(default_factory=dict)
    fallback: Optional[str] = Field(default=None, max_length=2000)
    generator: Optional[str] = Field(default=None, max_length=64)


class TemplateMappingRequest(RecipientRequest):
    template_name: str = Field(..., min_length=1, max_length=512)
    language: str = Field(..., min_length=1, max_length=32)
    mappings: Dict[str, VariableMapping] = Field(default_factory=dict)
    include_unlinked: bool = False


class TemplateSendRequest(TemplateMappingRequest):
    pass


def _require_admin(user: User) -> None:
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def _clean_user_ids(values: List[int]) -> List[int]:
    clean = sorted({int(value) for value in values if int(value) > 0})
    if not clean:
        raise HTTPException(status_code=400, detail="At least one valid user ID is required")
    if len(clean) > MAX_RECIPIENTS:
        raise HTTPException(
            status_code=400,
            detail=f"A maximum of {MAX_RECIPIENTS} users can be sent in one batch",
        )
    return clean


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _valid_recipient(value: Any) -> str:
    digits = _digits(value)
    return digits if 8 <= len(digits) <= 15 else ""


def _phone_number_id() -> str:
    return (
        os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
        or os.environ.get("WHATSAPP_NUDGE_PHONE_NUMBER_ID")
        or ""
    ).strip()


def _resolve_recipients(user_ids: List[int]) -> List[Dict[str, Any]]:
    clean = _clean_user_ids(user_ids)
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT userid, COALESCE(name, ''), COALESCE(phone, ''),
                   COALESCE(whatsapp_wa_id, ''), COALESCE(email, '')
            FROM users
            WHERE userid = ANY(%s)
            """,
            (clean,),
        )
        found = {int(row[0]): row for row in (cur.fetchall() or [])}

    rows: List[Dict[str, Any]] = []
    for user_id in clean:
        row = found.get(user_id)
        if not row:
            rows.append({"user_id": user_id, "status": "not_found", "sendable": False})
            continue
        linked_target = _valid_recipient(row[3])
        phone_target = _valid_recipient(row[2])
        if linked_target:
            status, target = "linked", linked_target
        elif phone_target:
            status, target = "phone_only", phone_target
        else:
            status, target = "no_phone", ""
        rows.append(
            {
                "user_id": user_id,
                "name": str(row[1] or ""),
                "phone": str(row[2] or ""),
                "email": str(row[4] or ""),
                "status": status,
                "sendable": bool(target),
                "recipient": target,
            }
        )
    return rows


def _template_variables(template: Dict[str, Any]) -> List[Dict[str, str]]:
    variables: List[Dict[str, str]] = []
    seen = set()
    for component in template.get("components") or []:
        component_type = str(component.get("type") or "").upper()
        if component_type in {"HEADER", "BODY"}:
            for token in _VARIABLE_RE.findall(str(component.get("text") or "")):
                item = {
                    "key": f"{component_type.lower()}.{token}",
                    "component": component_type,
                    "token": token,
                }
                if item["key"] not in seen:
                    variables.append(item)
                    seen.add(item["key"])
        elif component_type == "BUTTONS":
            for index, button in enumerate(component.get("buttons") or []):
                button_type = str(button.get("type") or "").upper()
                tokens = (
                    _VARIABLE_RE.findall(str(button.get("url") or ""))
                    if button_type == "URL"
                    else (["payload"] if button_type == "QUICK_REPLY" else [])
                )
                for token in tokens:
                    item = {
                        "key": f"button.{index}.{token}",
                        "component": "BUTTON",
                        "token": token,
                        "sub_type": button_type.lower(),
                        "label": (
                            f"button {index + 1} reply payload"
                            if button_type == "QUICK_REPLY"
                            else f"button {index + 1} URL value"
                        ),
                    }
                    if item["key"] not in seen:
                        variables.append(item)
                        seen.add(item["key"])
    return variables


def _unsupported_reason(template: Dict[str, Any]) -> Optional[str]:
    for component in template.get("components") or []:
        component_type = str(component.get("type") or "").upper()
        if component_type not in {"HEADER", "BODY", "FOOTER", "BUTTONS"}:
            return f"{component_type.lower()} components are not supported yet"
        if component_type == "HEADER":
            header_format = str(component.get("format") or "TEXT").upper()
            if header_format not in {"", "TEXT"}:
                return f"{header_format.lower()} header requires media upload support"
        elif component_type == "BUTTONS":
            for button in component.get("buttons") or []:
                button_type = str(button.get("type") or "").upper()
                if button_type not in {"URL", "QUICK_REPLY"}:
                    return f"{button_type.lower()} buttons are not supported yet"
    return None


def _template_dto(template: Dict[str, Any]) -> Dict[str, Any]:
    unsupported_reason = _unsupported_reason(template)
    variables = _template_variables(template)
    for variable in variables:
        variable["suggested_mapping"] = _suggested_mapping(template, variable)
    return {
        "id": template.get("id"),
        "name": template.get("name"),
        "language": template.get("language"),
        "status": template.get("status"),
        "category": template.get("category"),
        "components": template.get("components") or [],
        "variables": variables,
        "supported": unsupported_reason is None,
        "unsupported_reason": unsupported_reason,
    }


def _suggested_mapping(
    template: Dict[str, Any], variable: Dict[str, str]
) -> Dict[str, Any]:
    token = str(variable.get("token") or "").strip().lower()
    template_name = str(template.get("name") or "").strip().lower()
    if (
        variable.get("component") == "BUTTON"
        and variable.get("sub_type") == "url"
        and template_name == "credits_web_topup_bonus"
    ):
        return {"source": "generator", "generator": "credits_continue_token"}
    if token in {"customer_name", "user_name", "name", "first_name"}:
        return {"source": "user_field", "field": "name", "fallback": "there"}
    if token in {"userid", "user_id", "customer_id"}:
        return {"source": "user_field", "field": "userid"}
    if token in {"phone", "phone_number", "customer_phone"}:
        return {"source": "user_field", "field": "phone"}
    if token in {"email", "email_address", "customer_email"}:
        return {"source": "user_field", "field": "email"}
    return {"source": "fixed", "value": ""}


def _find_template(name: str, language: str) -> Dict[str, Any]:
    for template in fetch_whatsapp_message_templates(status="APPROVED"):
        if template.get("name") == name and template.get("language") == language:
            return template
    raise HTTPException(status_code=404, detail="Approved template or language not found")


def _build_send_components(
    template: Dict[str, Any], parameters: Dict[str, str]
) -> List[Dict[str, Any]]:
    unsupported_reason = _unsupported_reason(template)
    if unsupported_reason:
        raise HTTPException(status_code=400, detail=unsupported_reason)
    required = _template_variables(template)
    missing = [item["key"] for item in required if not str(parameters.get(item["key"], "")).strip()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing template parameters: {', '.join(missing)}",
        )

    components: List[Dict[str, Any]] = []
    for component_type in ("HEADER", "BODY"):
        items = [item for item in required if item["component"] == component_type]
        if items:
            components.append(
                {
                    "type": component_type.lower(),
                    "parameters": [_text_parameter(item, parameters) for item in items],
                }
            )
    for item in (item for item in required if item["component"] == "BUTTON"):
        _, index, _ = item["key"].split(".", 2)
        sub_type = item.get("sub_type") or "url"
        value = str(parameters[item["key"]]).strip()
        components.append(
            {
                "type": "button",
                "sub_type": sub_type,
                "index": index,
                "parameters": [
                    (
                        {"type": "payload", "payload": value[:200]}
                        if sub_type == "quick_reply"
                        else {"type": "text", "text": value[:2000]}
                    )
                ],
            }
        )
    return components


def _text_parameter(item: Dict[str, str], parameters: Dict[str, str]) -> Dict[str, str]:
    parameter = {
        "type": "text",
        "text": str(parameters[item["key"]]).strip()[:1024],
    }
    if not str(item["token"]).isdigit():
        parameter["parameter_name"] = str(item["token"])
    return parameter


def _eligible_recipients(
    recipients: List[Dict[str, Any]], include_unlinked: bool
) -> List[Dict[str, Any]]:
    return [
        row
        for row in recipients
        if row["status"] == "linked"
        or (include_unlinked and row["status"] == "phone_only")
    ]


def _resolve_mapping_value(
    mapping: VariableMapping,
    recipient: Dict[str, Any],
    *,
    generate: bool,
) -> str:
    source = str(mapping.source or "").strip().lower()
    fallback = str(mapping.fallback or "").strip()
    value = ""
    if source == "fixed":
        value = str(mapping.value or "").strip()
    elif source == "user_field":
        field = str(mapping.field or "").strip().lower()
        if field not in {"name", "userid", "phone", "email"}:
            raise ValueError(f"Unsupported user field: {field or 'missing'}")
        recipient_key = "user_id" if field == "userid" else field
        value = str(recipient.get(recipient_key) or "").strip()
    elif source == "per_user":
        value = str((mapping.values or {}).get(str(recipient["user_id"]), "")).strip()
    elif source == "generator":
        generator = str(mapping.generator or "").strip().lower()
        if generator not in {"credits_continue_token", "credits_continue_url"}:
            raise ValueError(f"Unsupported secure generator: {generator or 'missing'}")
        if not generate:
            return "Secure value generated at send time"
        from credits.web_continue import (
            build_continue_url,
            ensure_continue_link_environment_is_safe,
            get_or_create_continue_token,
        )

        ensure_continue_link_environment_is_safe()
        token = get_or_create_continue_token(int(recipient["user_id"]))
        value = build_continue_url(token) if generator == "credits_continue_url" else token
    else:
        raise ValueError(f"Unsupported mapping source: {source or 'missing'}")
    return (value or fallback).strip()


def _resolve_parameters_for_recipient(
    template: Dict[str, Any],
    mappings: Dict[str, VariableMapping],
    recipient: Dict[str, Any],
    *,
    generate: bool,
) -> tuple[Dict[str, str], List[str]]:
    values: Dict[str, str] = {}
    missing: List[str] = []
    for variable in _template_variables(template):
        key = variable["key"]
        mapping = mappings.get(key)
        if not mapping:
            missing.append(key)
            continue
        try:
            value = _resolve_mapping_value(mapping, recipient, generate=generate)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{key}: {exc}") from exc
        if not value:
            missing.append(key)
        else:
            values[key] = value
    return values, missing


def _mapping_preview(
    template: Dict[str, Any],
    mappings: Dict[str, VariableMapping],
    recipients: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    preview: List[Dict[str, Any]] = []
    for recipient in recipients:
        values, missing = _resolve_parameters_for_recipient(
            template, mappings, recipient, generate=False
        )
        preview.append(
            {
                "user_id": recipient["user_id"],
                "name": recipient.get("name") or "",
                "phone": recipient.get("phone") or "",
                "status": recipient["status"],
                "values": values,
                "missing": missing,
                "resolved": not missing,
            }
        )
    return preview


@router.get("/templates")
async def list_templates(current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    try:
        raw_templates = await run_in_threadpool(
            fetch_whatsapp_message_templates, status="APPROVED"
        )
        templates = [_template_dto(item) for item in raw_templates]
        templates.sort(key=lambda item: (str(item["name"]), str(item["language"])))
        return {"templates": templates}
    except Exception as exc:
        logger.exception("Failed to fetch Meta WhatsApp templates")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/validate-recipients")
async def validate_recipients(
    body: RecipientRequest, current_user: User = Depends(get_current_user)
):
    _require_admin(current_user)
    rows = await run_in_threadpool(_resolve_recipients, body.user_ids)
    return {
        "recipients": rows,
        "summary": {
            status: sum(1 for row in rows if row["status"] == status)
            for status in ("linked", "phone_only", "no_phone", "not_found")
        },
    }


@router.post("/preview")
async def preview_template_mapping(
    body: TemplateMappingRequest, current_user: User = Depends(get_current_user)
):
    _require_admin(current_user)
    recipients = await run_in_threadpool(_resolve_recipients, body.user_ids)
    template = await run_in_threadpool(
        _find_template, body.template_name.strip(), body.language.strip()
    )
    unsupported_reason = _unsupported_reason(template)
    if unsupported_reason:
        raise HTTPException(status_code=400, detail=unsupported_reason)
    eligible = _eligible_recipients(recipients, body.include_unlinked)
    preview = _mapping_preview(template, body.mappings, eligible)
    resolved = sum(1 for row in preview if row["resolved"])
    return {
        "recipients": recipients,
        "preview": preview,
        "summary": {
            status: sum(1 for row in recipients if row["status"] == status)
            for status in ("linked", "phone_only", "no_phone", "not_found")
        },
        "coverage": {
            "eligible": len(eligible),
            "resolved": resolved,
            "blocked": len(preview) - resolved,
        },
    }


@router.post("/send")
async def send_template(
    body: TemplateSendRequest, current_user: User = Depends(get_current_user)
):
    _require_admin(current_user)
    recipients = await run_in_threadpool(_resolve_recipients, body.user_ids)
    template = await run_in_threadpool(
        _find_template, body.template_name.strip(), body.language.strip()
    )
    phone_number_id = _phone_number_id()
    if not phone_number_id:
        raise HTTPException(
            status_code=503,
            detail="WHATSAPP_PHONE_NUMBER_ID is not configured on the server",
        )
    eligible = _eligible_recipients(recipients, body.include_unlinked)
    skipped = [row for row in recipients if row not in eligible]
    preview = _mapping_preview(template, body.mappings, eligible)
    unresolved = [row for row in preview if not row["resolved"]]
    if unresolved:
        details = "; ".join(
            f"user {row['user_id']}: {', '.join(row['missing'])}"
            for row in unresolved[:10]
        )
        raise HTTPException(
            status_code=400,
            detail=f"Template variables are unresolved for {len(unresolved)} recipient(s). {details}",
        )

    def _send(row: Dict[str, Any]) -> Dict[str, Any]:
        parameters, missing = _resolve_parameters_for_recipient(
            template, body.mappings, row, generate=True
        )
        if missing:
            return {
                "user_id": row["user_id"],
                "status": "failed",
                "error": f"Unresolved variables: {', '.join(missing)}",
            }
        components = _build_send_components(template, parameters)
        ok, error = send_whatsapp_template(
            to=row["recipient"],
            phone_number_id=phone_number_id,
            template_name=body.template_name.strip(),
            language_code=body.language.strip(),
            components_override=components,
            return_error=True,
        )
        return {
            "user_id": row["user_id"],
            "status": "accepted" if ok else "failed",
            "error": error,
        }

    def _send_all() -> List[Dict[str, Any]]:
        batch_results: List[Dict[str, Any]] = []
        if not eligible:
            return batch_results
        with ThreadPoolExecutor(max_workers=min(5, len(eligible))) as executor:
            futures = {executor.submit(_send, row): row for row in eligible}
            for future in as_completed(futures):
                try:
                    batch_results.append(future.result())
                except Exception as exc:
                    batch_results.append(
                        {
                            "user_id": futures[future]["user_id"],
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
        return batch_results

    results = await run_in_threadpool(_send_all)
    results.extend(
        {
            "user_id": row["user_id"],
            "status": "skipped",
            "error": row["status"],
        }
        for row in skipped
    )
    results.sort(key=lambda row: row["user_id"])
    accepted = sum(1 for row in results if row["status"] == "accepted")
    failed = sum(1 for row in results if row["status"] == "failed")
    logger.info(
        "Admin WhatsApp template send admin=%s template=%s language=%s accepted=%s failed=%s skipped=%s",
        current_user.userid,
        body.template_name,
        body.language,
        accepted,
        failed,
        len(results) - accepted - failed,
    )
    return {
        "ok": failed == 0,
        "accepted": accepted,
        "failed": failed,
        "skipped": len(results) - accepted - failed,
        "results": results,
    }
