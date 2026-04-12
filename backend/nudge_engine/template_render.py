"""
Safe template rendering for nudge copy: only {identifier} placeholders, no format() attribute access.
"""
from __future__ import annotations

import re
from typing import Any, Dict, FrozenSet, Mapping, Optional

# Valid placeholder names: Python-like identifiers
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class TemplateRenderError(ValueError):
    """Invalid template or facts for a nudge trigger."""


def extract_placeholders(template: str) -> FrozenSet[str]:
    return frozenset(_PLACEHOLDER_RE.findall(template))


def validate_templates(
    title: str,
    body: str,
    question: Optional[str],
    allowed: FrozenSet[str],
) -> None:
    """Ensure every {name} in templates is in allowed; question may be None or blank."""
    for label, text in (("title", title), ("body", body)):
        if not (text or "").strip():
            raise TemplateRenderError(f"{label} template is required")
        for name in extract_placeholders(text):
            if name not in allowed:
                raise TemplateRenderError(
                    f"Disallowed placeholder '{{{name}}}' in {label}; allowed: {sorted(allowed)}"
                )
    if question is not None and question.strip():
        for name in extract_placeholders(question):
            if name not in allowed:
                raise TemplateRenderError(
                    f"Disallowed placeholder '{{{name}}}' in question; allowed: {sorted(allowed)}"
                )


def render_template(template: str, facts: Mapping[str, Any], allowed: FrozenSet[str]) -> str:
    """
    Replace {key} with str(facts[key]) for each placeholder in template.
    All placeholders must be allowed and present in facts.
    """
    names = extract_placeholders(template)
    for name in names:
        if name not in allowed:
            raise TemplateRenderError(f"Disallowed placeholder: {{{name}}}")
        if name not in facts:
            raise TemplateRenderError(f"Missing value for placeholder: {{{name}}}")
    # Replace longer names first so {planet_x} would win over {planet} if both existed (we don't use that)
    out = template
    for name in sorted(names, key=len, reverse=True):
        out = out.replace("{" + name + "}", str(facts[name]))
    return out


def render_all(
    title_t: str,
    body_t: str,
    question_t: Optional[str],
    facts: Mapping[str, Any],
    allowed: FrozenSet[str],
) -> tuple[str, str, Optional[str]]:
    validate_templates(title_t, body_t, question_t, allowed)
    title = render_template(title_t, facts, allowed)
    body = render_template(body_t, facts, allowed)
    question: Optional[str] = None
    if question_t is not None and question_t.strip():
        question = render_template(question_t, facts, allowed)
    return title, body, question
