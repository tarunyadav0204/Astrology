"""Helpers for classifying Gemini / Vertex failures and user-facing error strings."""


def transient_gemini_error(error_msg: str) -> bool:
    """True when failure may resolve with a short backoff (overload, rate limits, timeouts)."""
    if not error_msg:
        return False
    s = error_msg.lower()
    markers = (
        "503",
        "429",
        "504",
        "high demand",
        "try again later",
        "service unavailable",
        "unavailable",
        "resource exhausted",
        "overloaded",
        "deadlineexceeded",
        "deadline exceeded",
        "timeout",
        "retryerror",
        "too many requests",
    )
    return any(m in s for m in markers)


def user_facing_gemini_error(err: str) -> str:
    """Shorter, user-safe message for DB/UI when the raw error is huge or vendor-specific."""
    if not err:
        return "Analysis failed. Please try again."
    low = err.lower()
    if "high demand" in low or "currently experiencing" in low:
        return "The AI service is temporarily busy. Please try again in a few minutes."
    if "retryerror" in low and "timeout" in low and "600" in err:
        return "The AI request timed out while the service was busy. Please try again shortly."
    if len(err) > 500:
        return err[:500] + "…"
    return err
