"""
Parse JSON from env vars that may contain literal newlines (e.g. service account keys in .env).
Use this for GOOGLE_SERVICE_ACCOUNT_KEY and similar inline JSON.
"""
import json
import os


def json_normalize_newlines(s: str) -> str:
    """
    Replace literal newlines inside JSON string values with \\n.
    Leaves newlines outside strings unchanged (valid JSON whitespace).
    """
    if not s:
        return s
    result = []
    i = 0
    in_string = False
    escape = False
    quote_char = None
    while i < len(s):
        c = s[i]
        if escape:
            result.append(c)
            escape = False
            i += 1
            continue
        if c == "\\":
            result.append(c)
            escape = True
            i += 1
            continue
        if in_string:
            if c == quote_char:
                in_string = False
                result.append(c)
            elif c == "\r" and i + 1 < len(s) and s[i + 1] == "\n":
                result.append("\\n")
                i += 1
            elif c in ("\r", "\n"):
                result.append("\\n")
            else:
                result.append(c)
            i += 1
            continue
        if c in ('"', "'"):
            in_string = True
            quote_char = c
            result.append(c)
        else:
            result.append(c)
        i += 1
    return "".join(result)


def parse_json_from_env(value: str):
    """
    Parse a JSON string that may come from an env var (e.g. .env with literal newlines).
    Extracts JSON by finding first { and last }, normalizes newlines inside string values, then parses.
    Returns the parsed object or None if invalid.
    """
    if not value or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    # Extract JSON object: from first { to last } (handles any surrounding quotes/newlines from .env)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    raw = raw[start : end + 1]
    try:
        normalized = json_normalize_newlines(raw)
        return json.loads(normalized)
    except (json.JSONDecodeError, ValueError):
        return None
