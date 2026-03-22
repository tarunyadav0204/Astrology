from datetime import datetime, timedelta
from typing import Dict, List

from psycopg2 import IntegrityError

from db import execute, get_conn


def _is_active_sql() -> str:
    """
    promo_codes.is_active may be BOOLEAN (from init_tables) or TEXT (from SQLite migration).
    """
    return """(
        is_active IS TRUE
        OR COALESCE(LOWER(TRIM(is_active::text)), 'true') IN ('true', '1', 't')
    )"""


class PromoCodeManager:
    """Promo bulk creation and stats (Postgres via db.py)."""

    def __init__(self):
        pass

    def create_bulk_codes(
        self,
        prefix: str,
        count: int,
        credits: int,
        max_uses: int = 1,
        max_uses_per_user: int = 1,
        expires_days: int = 30,
    ) -> List[str]:
        """Create multiple promo codes with sequential numbering"""
        codes: List[str] = []
        expires_at = datetime.now() + timedelta(days=expires_days)

        with get_conn() as conn:
            for i in range(1, count + 1):
                code = f"{prefix}{i:03d}"
                try:
                    execute(
                        conn,
                        """
                        INSERT INTO promo_codes (code, credits, max_uses, max_uses_per_user, expires_at, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (code, credits, max_uses, max_uses_per_user, expires_at, None),
                    )
                    codes.append(code)
                except IntegrityError:
                    continue
            conn.commit()

        return codes

    def get_usage_stats(self) -> Dict:
        """Get promo code usage statistics"""
        active_cond = _is_active_sql()
        with get_conn() as conn:
            cur = execute(conn, "SELECT COUNT(*) FROM promo_codes", ())
            total_codes = cur.fetchone()[0]

            cur = execute(
                conn,
                f"SELECT COUNT(*) FROM promo_codes WHERE {active_cond}",
                (),
            )
            active_codes = cur.fetchone()[0]

            cur = execute(conn, "SELECT COUNT(*) FROM promo_codes WHERE used_count > 0", ())
            used_codes = cur.fetchone()[0]

            cur = execute(conn, "SELECT COALESCE(SUM(credits_earned), 0) FROM promo_code_usage", ())
            total_credits = cur.fetchone()[0] or 0

            week_ago = datetime.now() - timedelta(days=7)
            cur = execute(
                conn,
                "SELECT COUNT(*) FROM promo_code_usage WHERE used_at > ?",
                (week_ago,),
            )
            recent_usage = cur.fetchone()[0]

        return {
            "total_codes": total_codes,
            "active_codes": active_codes,
            "used_codes": used_codes,
            "total_credits_distributed": int(total_credits),
            "recent_usage_7_days": recent_usage,
        }

    def deactivate_expired_codes(self) -> int:
        """Deactivate expired promo codes (TEXT or BOOLEAN is_active)."""
        now = datetime.now()
        active_cond = _is_active_sql()
        with get_conn() as conn:
            try:
                cur = execute(
                    conn,
                    f"""
                    UPDATE promo_codes
                    SET is_active = FALSE
                    WHERE expires_at < ? AND ({active_cond})
                    """,
                    (now,),
                )
                n = cur.rowcount
            except Exception:
                cur = execute(
                    conn,
                    f"""
                    UPDATE promo_codes
                    SET is_active = '0'
                    WHERE expires_at < ? AND ({active_cond})
                    """,
                    (now,),
                )
                n = cur.rowcount
            conn.commit()
            return n
