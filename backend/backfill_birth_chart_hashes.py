#!/usr/bin/env python3
"""
One-time: set birth_charts.birth_hash from decrypted date/time/latitude/longitude.
Run after migrations/add_birth_charts_birth_hash.sql (or rely on CreditService.init_tables ALTER).

  cd backend && POSTGRES_DSN=... .venv/bin/python backfill_birth_chart_hashes.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import execute, get_conn  # noqa: E402
from utils.birth_hash import birth_hash_from_parts  # noqa: E402


def main() -> None:
    try:
        from encryption_utils import EncryptionManager

        enc = EncryptionManager()
    except ValueError:
        enc = None
        print("No encryption manager — treating stored fields as plaintext")

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT id, date, time, latitude, longitude
            FROM birth_charts
            WHERE birth_hash IS NULL
            ORDER BY id
            """,
        )
        rows = cur.fetchall() or []

    updated = 0
    for row in rows:
        chart_id, raw_d, raw_t, raw_la, raw_lo = row[0], row[1], row[2], row[3], row[4]
        try:
            if enc:
                d = enc.decrypt(raw_d)
                t = enc.decrypt(raw_t)
                la = enc.decrypt(str(raw_la))
                lo = enc.decrypt(str(raw_lo))
            else:
                d, t, la, lo = raw_d, raw_t, str(raw_la), str(raw_lo)
            bh = birth_hash_from_parts(d, t, la, lo)
            if not bh:
                continue
            with get_conn() as conn:
                execute(
                    conn,
                    "UPDATE birth_charts SET birth_hash = ? WHERE id = ?",
                    (bh, chart_id),
                )
                conn.commit()
            updated += 1
        except Exception as exc:
            print(f"skip id={chart_id}: {exc}")

    print(f"Updated {updated} of {len(rows)} charts missing birth_hash")


if __name__ == "__main__":
    if not os.getenv("POSTGRES_DSN") and not os.getenv("DATABASE_URL"):
        print("Set POSTGRES_DSN or DATABASE_URL", file=sys.stderr)
        sys.exit(1)
    main()
