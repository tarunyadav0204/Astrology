#!/usr/bin/env python3
"""Install the reviewed Abala/Prabhaa context pilot into the source catalogue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from classical_sources.deva_keralam_context_reconstruction import (
    ContextRepository,
    load_pilot_fixture,
)
from db import get_conn


def main() -> None:
    load_dotenv(BACKEND_DIR / ".env", override=False)
    fixture = load_pilot_fixture()
    with get_conn() as conn:
        result = ContextRepository(conn).install_fixture(fixture)
    print(json.dumps({**result, "context_block_key": fixture.context_block_key}, indent=2))


if __name__ == "__main__":
    main()
