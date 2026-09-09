from __future__ import annotations

import re


_INTERNAL_MARKER_START = re.compile(
    r"\[\[(?:SH_D1_H\d*|HOME_|HEALTH_EVIDENCE_|RELATIVE_PROFILE_|MARRIED_LIFE_)",
    flags=re.IGNORECASE,
)


def strip_internal_evidence_markers(text: str, *, provisional: bool = False) -> str:
    """Remove model/composer evidence bindings from user-visible text.

    Evidence validation may be disabled, but these bindings are transport
    metadata and must never become visible or audible.  Provisional streaming
    hides an unfinished binding until the provider closes it; final cleanup
    also handles malformed marker fragments defensively.
    """
    visible = str(text or "")

    # Well-formed bindings. Match only known internal namespaces so ordinary
    # user-authored double brackets are preserved.
    visible = re.sub(
        r"\s*\[\[(?:SH_D1_H\d*|HOME_|HEALTH_EVIDENCE_|RELATIVE_PROFILE_|MARRIED_LIFE_)[\s\S]*?\]\]",
        "",
        visible,
        flags=re.IGNORECASE,
    )

    matches = list(_INTERNAL_MARKER_START.finditer(visible))
    if matches:
        last = matches[-1]
        suffix = visible[last.start():]
        if provisional and "]]" not in suffix:
            # Do not stream a half-written marker or anything after it. The
            # next cumulative checkpoint will restore genuine prose once the
            # binding is complete and stripped.
            visible = visible[: last.start()]
        else:
            # A provider can occasionally damage the opaque token by inserting
            # whitespace or natural-language text. Remove the recognizable
            # machine prefix without swallowing the surrounding answer.
            visible = re.sub(
                r"\[\[(?:SH_D1_H\d*|HOME_|HEALTH_EVIDENCE_|RELATIVE_PROFILE_|MARRIED_LIFE_)[A-Z0-9_:\-]*",
                "",
                visible,
                flags=re.IGNORECASE,
            )

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
