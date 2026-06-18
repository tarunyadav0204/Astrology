from __future__ import annotations

"""Schema helpers for birth chart family metadata."""

from db import execute


def ensure_birth_chart_family_columns(conn) -> None:
    """Add optional family-tree metadata columns without disturbing old clients."""
    statements = [
        "ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS relation_order INTEGER",
        "ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS relation_side TEXT",
        "ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS relation_label TEXT",
        "ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS is_family_member BOOLEAN DEFAULT FALSE",
    ]
    for stmt in statements:
        execute(conn, stmt)


def normalize_chart_relation(value: str | None) -> str:
    rel = str(value or "other").strip().lower().replace(" ", "_")
    aliases = {
        "me": "self",
        "myself": "self",
        "wife": "spouse",
        "husband": "spouse",
        "partner": "spouse",
        "son": "child",
        "daughter": "child",
        "brother": "sibling",
        "sister": "sibling",
    }
    rel = aliases.get(rel, rel)
    allowed = {
        "self",
        "father",
        "mother",
        "spouse",
        "child",
        "sibling",
        "friend",
        "colleague",
        "shared",
        "other",
    }
    return rel if rel in allowed else "other"


def relation_defaults(relation: str, is_family_member):
    rel = normalize_chart_relation(relation)
    if rel in {"self", "father", "mother", "spouse", "child", "sibling"}:
        is_family_member = True
    elif is_family_member is None:
        is_family_member = rel in {"self", "father", "mother", "spouse", "child", "sibling"}
    elif isinstance(is_family_member, str):
        is_family_member = is_family_member.strip().lower() in {"1", "true", "yes", "y", "on"}
    return rel, bool(is_family_member)
