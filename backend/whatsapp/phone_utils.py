"""Phone / wa_id normalization for WhatsApp ↔ users.phone matching (mirrors main.py variants)."""
from __future__ import annotations

from typing import List, Optional


def wa_id_to_lookup_phone(wa_id: str) -> str:
    """Turn Meta `from` / wa_id (digits, no +) into a string we can pass to variant lookup."""
    d = "".join(c for c in (wa_id or "") if c.isdigit())
    if not d:
        return (wa_id or "").strip()
    if len(d) == 12 and d.startswith("91"):
        return "+" + d
    if len(d) == 10:
        return "+91" + d
    if len(d) == 11 and d.startswith("1"):
        return "+" + d
    return "+" + d


def phone_lookup_variants(phone: Optional[str]) -> List[str]:
    """Same rules as main._phone_lookup_variants — keep in sync for OTP + login."""
    if not phone:
        return []
    raw = (
        phone.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    digits = "".join(c for c in raw if c.isdigit())
    variants: List[str] = []

    def add(v: Optional[str]) -> None:
        if v and v not in variants:
            variants.append(v)

    add(phone.strip())
    add(raw)
    if digits:
        add(digits)
    if not digits:
        return variants

    if raw.startswith("+91") or (digits.startswith("91") and len(digits) >= 12):
        last10 = digits[-10:] if len(digits) >= 10 else digits
        if len(digits) == 12 and digits.startswith("91"):
            last10 = digits[2:]
        elif len(digits) == 10:
            last10 = digits
        add(last10)
        add(f"+91{last10}")
        add(f"91{last10}")
        add(f"0{last10}")
        add(digits)
        if raw.startswith("+"):
            add("+" + digits)
    elif raw.startswith("+1") or (len(digits) == 11 and digits.startswith("1")):
        national = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
        if len(national) == 10:
            add(national)
            add(f"+1{national}")
            add(f"1{national}")
    else:
        if len(digits) == 10:
            add(digits)
            add(f"+91{digits}")
            add(f"91{digits}")
            add(f"0{digits}")
            add(f"+1{digits}")
            add(f"1{digits}")
        elif len(digits) == 12 and digits.startswith("91"):
            last10 = digits[2:]
            add(last10)
            add(f"+91{last10}")
            add(digits)
            add(f"+{digits}")
    return variants


def canonical_phone_for_registration(wa_id: str) -> str:
    """Single canonical `users.phone` for new WhatsApp-only India signups."""
    d = "".join(c for c in (wa_id or "") if c.isdigit())
    if len(d) >= 12 and d.startswith("91"):
        return "+91" + d[-10:]
    if len(d) == 10:
        return "+91" + d
    if wa_id.strip().startswith("+"):
        return wa_id.strip()
    return "+" + d if d else (wa_id or "").strip()


def is_greeting(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    greetings = ("hi", "hello", "hey", "start", "namaste", "hii", "yo", "good morning", "good evening")
    if t in greetings:
        return True
    for g in ("hi ", "hello ", "hey ", "namaste"):
        if t.startswith(g):
            return True
    return False
