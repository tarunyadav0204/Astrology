import json
from typing import List, Optional

from db import get_conn, execute


class SystemInstructionLoader:
    """Loads system instructions from database based on category configuration."""

    def get_instructions_for_category(self, category_key: str, tier_key: str = "normal") -> str:
        """Get assembled system instructions for a specific category and tier."""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT required_modules
                FROM prompt_category_config
                WHERE category_key = %s AND tier_key = %s
                """,
                (category_key, tier_key),
            )
            result = cur.fetchone()

        if not result or not result[0]:
            return self._get_all_active_instructions()

        try:
            required_module_keys = json.loads(result[0])
        except Exception:
            required_module_keys = [m.strip() for m in str(result[0]).split(",") if m.strip()]

        if not required_module_keys:
            return self._get_all_active_instructions()

        placeholders = ",".join(["%s"] * len(required_module_keys))
        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT instruction_text
                FROM prompt_instruction_modules
                WHERE module_key IN ({placeholders})
                  AND is_active = 1
                ORDER BY priority
                """,
                tuple(required_module_keys),
            )
            modules = cur.fetchall() or []

        instructions = "\n\n".join(row[0] for row in modules)
        return instructions if instructions else self._get_all_active_instructions()

    def _get_all_active_instructions(self) -> str:
        """Fallback: Get all active instructions."""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT instruction_text
                FROM prompt_instruction_modules
                WHERE is_active = 1
                ORDER BY priority
                """,
            )
            modules = cur.fetchall() or []
        return "\n\n".join(row[0] for row in modules)
