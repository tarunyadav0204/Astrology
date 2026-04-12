"""
Load merged trigger definition (DB overrides + code defaults) for scan-time use.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from . import db as nudge_db
from .config_validate import validate_and_normalize_config
from .template_render import render_all
from .trigger_defaults import TriggerDefaultSpec, get_spec

logger = logging.getLogger(__name__)


@dataclass
class MergedTriggerDefinition:
    """Resolved definition used when emitting nudges."""

    trigger_key: str
    enabled: bool
    priority: int
    title_template: str
    body_template: str
    question_template: str
    config: Dict[str, Any]

    def render_copy(self, facts: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
        spec = get_spec(self.trigger_key)
        if not spec:
            raise KeyError(self.trigger_key)
        return render_all(
            self.title_template,
            self.body_template,
            self.question_template,
            facts,
            spec.allowed_placeholders,
        )


def _parse_config_json(raw: Optional[str], trigger_key: str) -> Dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            return {}
        return validate_and_normalize_config(trigger_key, obj)
    except Exception as e:
        logger.warning("Invalid config_json for %s, using defaults: %s", trigger_key, e)
        return validate_and_normalize_config(trigger_key, {})


def merge_row(spec: TriggerDefaultSpec, row: Optional[tuple]) -> MergedTriggerDefinition:
    """
    row: (enabled, priority, title_template, body_template, question_template, config_json)
    or None if no DB row.
    """
    if not row:
        config = validate_and_normalize_config(spec.trigger_key, {})
        return MergedTriggerDefinition(
            trigger_key=spec.trigger_key,
            enabled=True,
            priority=spec.default_priority,
            title_template=spec.title_template,
            body_template=spec.body_template,
            question_template=spec.question_template,
            config=config,
        )

    enabled, priority, title_t, body_t, question_t, config_json = row
    config = _parse_config_json(config_json, spec.trigger_key)
    return MergedTriggerDefinition(
        trigger_key=spec.trigger_key,
        enabled=bool(enabled),
        priority=(int(priority) if priority is not None else spec.default_priority),
        title_template=(title_t or spec.title_template).strip() or spec.title_template,
        body_template=(body_t or spec.body_template).strip() or spec.body_template,
        question_template=(question_t or spec.question_template).strip()
        or spec.question_template,
        config=config,
    )


def load_merged_definition(conn, trigger_key: str) -> MergedTriggerDefinition:
    spec = get_spec(trigger_key)
    if not spec:
        raise KeyError(f"Unknown trigger_key: {trigger_key}")
    row = nudge_db.fetch_trigger_definition_row(conn, trigger_key)
    return merge_row(spec, row)
