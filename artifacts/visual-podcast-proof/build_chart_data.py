"""Decrypt the selected chart locally and calculate its real sidereal D1 positions."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / ".env")

from calculators.chart_calculator import ChartCalculator  # noqa: E402
def main() -> None:
    decrypted = json.loads((HERE / "context-decrypted.json").read_text(encoding="utf-8"))
    birth = SimpleNamespace(
        name=decrypted.get("name") or "",
        date=decrypted["date"],
        time=decrypted["time"],
        latitude=float(decrypted["latitude"]),
        longitude=float(decrypted["longitude"]),
        timezone=decrypted.get("timezone") or "UTC+5:30",
        place=decrypted.get("place") or "",
        gender=decrypted.get("gender") or "",
    )
    chart = ChartCalculator({}).calculate_chart(birth)
    planets = []
    for name, raw in (chart.get("planets") or {}).items():
        if not isinstance(raw, dict):
            continue
        planets.append({
            "name": str(name),
            "longitude": float(raw.get("longitude") or 0),
            "sign": raw.get("sign"),
            "house": int(raw.get("house") or 0),
            "degree": float(raw.get("degree") or raw.get("degrees") or 0),
            "retrograde": bool(raw.get("retrograde") or raw.get("is_retrograde")),
        })
    output = {
        "chart_id": decrypted.get("birth_chart_id"),
        "display_name": str(decrypted.get("name") or "").split(" ", 1)[0],
        "ascendant": float(chart.get("ascendant") or 0),
        "ascendant_sign": chart.get("ascendant_sign"),
        "planets": planets,
    }
    (HERE / "chart-data.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"planets": len(planets), "chart_id": output["chart_id"]}))


if __name__ == "__main__":
    main()
