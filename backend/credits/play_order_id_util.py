"""Parse Google Play order IDs (GPA.*) for subscription renewals."""
from __future__ import annotations

import re
from typing import Optional, Tuple

# GPA.1234-5678-9012-34567..2 → base + index 2
_RENEWAL_SUFFIX_RE = re.compile(r"^(?P<base>.+)\.\.(\d+)$")


def normalize_play_order_id(order_id: Optional[str]) -> Optional[str]:
    oid = (order_id or "").strip()
    return oid or None


def play_order_id_base(order_id: Optional[str]) -> Optional[str]:
    """Parent order id shared across renewals (strip ..N suffix)."""
    oid = normalize_play_order_id(order_id)
    if not oid:
        return None
    m = _RENEWAL_SUFFIX_RE.match(oid)
    if m:
        return m.group("base")
    return oid


def play_order_renewal_index(order_id: Optional[str]) -> Optional[int]:
    """
    Renewal cycle index from ..N suffix.
    Initial purchase often has no suffix → None (sort first).
    """
    oid = normalize_play_order_id(order_id)
    if not oid:
        return None
    m = _RENEWAL_SUFFIX_RE.match(oid)
    if not m:
        return None
    try:
        return int(m.group(2))
    except ValueError:
        return None


def play_order_sort_key(order_id: Optional[str]) -> Tuple[int, int, str]:
    """Sort: base purchase first, then ..0, ..1, ..2."""
    oid = normalize_play_order_id(order_id) or ""
    idx = play_order_renewal_index(oid)
    if idx is None:
        return (0, -1, oid)
    return (1, idx, oid)
