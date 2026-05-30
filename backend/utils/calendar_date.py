"""Parse calendar dates from API / mobile clients (YYYY-MM-DD or ISO 8601 datetime)."""


def parse_calendar_date_y_m_d(date_str: str) -> tuple[int, int, int]:
    """
    Return (year, month, day) integers.

    Accepts:
      - YYYY-MM-DD
      - YYYY-MM-DDThh:mm:ss.sssZ (and other ISO variants)
      - YYYY-MM-DD hh:mm:ss (space separator)
    """
    if date_str is None:
        raise ValueError("date_str is required")
    s = str(date_str).strip()
    if not s:
        raise ValueError("date_str is empty")
    if "T" in s:
        s = s.split("T", 1)[0]
    elif len(s) > 10 and s[10] == " ":
        s = s[:10]
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError(f"Unrecognized date format: {date_str!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])
