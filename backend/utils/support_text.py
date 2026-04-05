"""
Strict sanitization for support ticket subject/body (plain text only).
"""
import re
from typing import Optional

# Reject embedded nulls, most control chars; allow newline/tab for multi-line messages.
_CTRL_EXCEPT_NL_TAB = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_MAX_SUBJECT = 200
_MAX_BODY = 8000


def sanitize_support_subject(raw: Optional[str]) -> str:
    if raw is None:
        return ""
    s = str(raw).replace("\x00", "")
    s = _CTRL_EXCEPT_NL_TAB.sub("", s)
    s = " ".join(s.split())
    if len(s) > _MAX_SUBJECT:
        s = s[:_MAX_SUBJECT]
    return s.strip()


def sanitize_support_body(raw: Optional[str]) -> str:
    if raw is None:
        return ""
    s = str(raw).replace("\x00", "")
    s = _CTRL_EXCEPT_NL_TAB.sub("", s)
    if len(s) > _MAX_BODY:
        s = s[:_MAX_BODY]
    return s.strip()
