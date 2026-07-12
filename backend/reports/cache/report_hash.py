from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def normalize_birth_data(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "dict"):
        data = data.dict()
    elif not isinstance(data, dict):
        data = dict(data)
    keys = [
        "name",
        "date",
        "time",
        "place",
        "latitude",
        "longitude",
        "timezone",
        "gender",
        "relation",
        "relation_order",
        "relation_side",
        "relation_label",
        "is_family_member",
    ]
    return {key: data.get(key) for key in keys if key in data}


def build_pair_hash(person_a: Any, person_b: Any, report_type: str, language: str) -> str:
    payload = {
        "report_type": report_type,
        "language": (language or "english").strip().lower(),
        "person_a": normalize_birth_data(person_a),
        "person_b": normalize_birth_data(person_b),
    }
    digest = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(digest.encode("utf-8")).hexdigest()


def build_subject_hash(birth_data: Any, report_type: str, language: str) -> str:
    """Single-native cache key (wealth and other one-chart reports)."""
    payload = {
        "report_type": report_type,
        "language": (language or "english").strip().lower(),
        "subject": normalize_birth_data(birth_data),
    }
    digest = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(digest.encode("utf-8")).hexdigest()


def normalize_report_request(request: Any) -> Dict[str, Any]:
    if hasattr(request, "model_dump"):
        return request.model_dump()
    if hasattr(request, "dict"):
        return request.dict()
    return dict(request)


def normalize_language(language: Any) -> str:
    return (str(language or "english")).strip().lower() or "english"


def build_report_cache_key(request: Any) -> str:
    payload = normalize_report_request(request)
    report_type = payload.get("report_type", "partnership")
    language = payload.get("language", "english")
    if report_type == "wealth":
        subject = payload.get("birth_data") or payload.get("subject") or payload.get("person")
        return build_subject_hash(subject, report_type, language)
    person_a = payload.get("boy_birth_data") or payload.get("person_a")
    person_b = payload.get("girl_birth_data") or payload.get("person_b")
    return build_pair_hash(person_a, person_b, report_type, language)
