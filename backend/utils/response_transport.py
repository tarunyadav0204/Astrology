from __future__ import annotations

import re


_INTERNAL_MARKER_NAMESPACE = (
    r"(?:SH_D1_H\d*|HOME_|HEALTH_EVIDENCE_|RELATIVE_PROFILE_|MARRIED_LIFE_)"
)
_INTERNAL_MARKER_START = re.compile(
    rf"\[\[{_INTERNAL_MARKER_NAMESPACE}",
    flags=re.IGNORECASE,
)
_COMPLETE_MACHINE_MARKER = re.compile(
    rf"\s*\[\[{_INTERNAL_MARKER_NAMESPACE}[A-Z0-9_:\-]*\]\]",
    flags=re.IGNORECASE,
)
_MALFORMED_COMPLETE_MARKER = re.compile(
    rf"\[\[(?P<body>{_INTERNAL_MARKER_NAMESPACE}[\s\S]*?)\]\]",
    flags=re.IGNORECASE,
)
_MACHINE_MARKER_PREFIX = re.compile(
    rf"\[\[{_INTERNAL_MARKER_NAMESPACE}[A-Z0-9_:\-]*",
    flags=re.IGNORECASE,
)
_MACHINE_MARKER_BODY_PREFIX = re.compile(
    rf"{_INTERNAL_MARKER_NAMESPACE}[A-Z0-9_:\-]*",
    flags=re.IGNORECASE,
)
_MACHINE_MARKER_ORPHAN_SUFFIX = re.compile(
    r"(?:\s+|^)(?:\d*_?H\d+_[A-Z0-9_:\-]+|[A-Z][A-Z0-9_:\-]{5,})\s*$",
    flags=re.IGNORECASE,
)


def _preserve_prose_from_malformed_marker(match: re.Match[str]) -> str:
    """Remove marker syntax without deleting prose accidentally placed inside it."""
    body = str(match.group("body") or "")
    prefix = _MACHINE_MARKER_BODY_PREFIX.match(body)
    remainder = body[prefix.end() :] if prefix else body
    remainder = _MACHINE_MARKER_ORPHAN_SUFFIX.sub("", remainder).strip()
    return f" {remainder} " if remainder else " "


def strip_internal_evidence_markers(text: str, *, provisional: bool = False) -> str:
    """Remove model/composer evidence bindings from user-visible text.

    Evidence validation may be disabled, but these bindings are transport
    metadata and must never become visible or audible.  Provisional streaming
    hides an unfinished binding until the provider closes it; final cleanup
    also handles malformed marker fragments defensively.
    """
    visible = str(text or "")

    # Remove only syntactically valid machine tokens. Older cleanup removed
    # everything from a recognized opening through the next ``]]``. If a
    # provider inserted natural language inside a damaged token, that erased
    # a genuine sentence (and could even consume a later valid token).
    visible = _COMPLETE_MACHINE_MARKER.sub(" ", visible)

    # A damaged but closed marker may contain real answer prose. Preserve that
    # prose and discard only the recognizable machine prefix/suffix.
    visible = _MALFORMED_COMPLETE_MARKER.sub(
        _preserve_prose_from_malformed_marker,
        visible,
    )

    matches = list(_INTERNAL_MARKER_START.finditer(visible))
    if matches:
        last = matches[-1]
        suffix = visible[last.start():]
        machine_prefix = _MACHINE_MARKER_PREFIX.match(visible, last.start())
        after_prefix = visible[machine_prefix.end() :] if machine_prefix else ""
        if provisional and "]]" not in suffix and re.fullmatch(
            r"[A-Z0-9_:\-]*", after_prefix, flags=re.IGNORECASE
        ):
            # Hold a genuinely half-written machine token. If natural prose
            # already follows the prefix, retain it instead of hiding an
            # arbitrarily large portion of the streamed answer.
            visible = visible[: last.start()]
        else:
            # A provider can occasionally damage the opaque token by inserting
            # whitespace or natural-language text. Remove the recognizable
            # machine prefix without swallowing the surrounding answer.
            visible = _MACHINE_MARKER_PREFIX.sub(" ", visible)

    if provisional:
        # A provider chunk can stop before enough of the namespace exists for
        # the strict matcher above (for example ``[[SH_``). Hold any trailing
        # uppercase machine-looking bracket token until the next cumulative
        # checkpoint rather than reading it aloud.
        partial_start = visible.rfind("[[")
        if partial_start >= 0 and "]]" not in visible[partial_start:]:
            partial = visible[partial_start + 2 :]
            if re.fullmatch(r"[A-Z0-9_:\-]*", partial):
                visible = visible[:partial_start]

    # Remove orphaned machine-token tails left by a malformed opening marker.
    visible = re.sub(
        r"(?<![\w\[])\d*_?H\d+_[A-Z0-9_:\-]+\]\]",
        "",
        visible,
        flags=re.IGNORECASE,
    )
    visible = re.sub(r"\s+([,.;:!?।])", r"\1", visible)
    visible = re.sub(r"[ \t]{2,}", " ", visible)
    return visible.strip()
