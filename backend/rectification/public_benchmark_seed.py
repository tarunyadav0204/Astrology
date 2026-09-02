"""Create a private, development-only seed cohort from Astro-Databank XML.

Astro-Databank research_data is licensed for astrological research and must not
be redistributed or embedded in a product. This importer only writes ignored
``*.private.json`` files for local deterministic validation. It is not an AI
training or service-ingestion path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from utils.timezone_service import get_iana_timezone

from .benchmark import BLINDED_DATASET_SCHEMA_VERSION, TRUTH_VAULT_SCHEMA_VERSION


ADB_PUBLIC_SAMPLE_URL = "https://www.astro.com/adbexport/c_sample.xml"
MAPPED_EVENT_CODES = {
    "Relationship : Marriage": "marriage",
    "Work : New Job": "career_change",
    "Work : New Career": "career_change",
    "Work : Gain social status": "promotion",
    "Social : Begin a program of study": "education",
    "Social : End a program of study": "education",
    "Family : Change residence": "relocation",
}


def _coordinate(value: str, positive: str, negative: str) -> float:
    raw = str(value or "").strip().lower()
    direction = next((token for token in (positive, negative) if token in raw), None)
    if not direction:
        raise ValueError(f"Unsupported Astro-Databank coordinate {value!r}")
    degrees, minutes = raw.split(direction, 1)
    result = float(degrees) + float(minutes or 0) / 60.0
    return -result if direction == negative else result


def _event_date(event: ET.Element) -> Optional[Tuple[str, str]]:
    node = event.find("./event_data/sbdate")
    if node is None:
        return None
    year = int(node.get("iyear") or 0)
    month = int(node.get("imonth") or 0)
    day = int(node.get("iday") or 0)
    if year <= 0:
        return None
    if month <= 0:
        return f"{year:04d}-01-01", "year"
    if day <= 0:
        return f"{year:04d}-{month:02d}-01", "month"
    try:
        return date(year, month, day).isoformat(), "exact_day"
    except ValueError:
        return None


def _time_seconds(value: str) -> int:
    pieces = str(value or "").strip().split(":")
    if len(pieces) not in {2, 3}:
        raise ValueError("Astro-Databank time is not minute-resolved")
    hour, minute = int(pieces[0]), int(pieces[1])
    second = int(pieces[2]) if len(pieces) == 3 else 0
    return hour * 3600 + minute * 60 + second


def _clock(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def _anonymous_id(dataset_id: str, adb_id: str) -> str:
    digest = hashlib.sha256(f"{dataset_id}:{adb_id}".encode("utf-8")).hexdigest()[:16]
    return f"public-aa-{digest}"


def _mapped_events(entry: ET.Element, birth_year: int) -> list[Dict[str, Any]]:
    rows = []
    seen = set()
    for source in entry.findall("./research_data/events/event"):
        event_type = MAPPED_EVENT_CODES.get(str(source.get("sevcode") or ""))
        resolved = _event_date(source)
        if not event_type or not resolved:
            continue
        event_date, precision = resolved
        if int(event_date[:4]) < birth_year:
            continue
        identity = (event_type, event_date, precision)
        if identity in seen:
            continue
        seen.add(identity)
        rows.append({
            "id": f"event-{len(rows) + 1}",
            "event_type": event_type,
            "date_start": event_date,
            "precision": precision,
            # ADB event rows identify candidates; independent source audit is
            # required before promoting a case to holdout evidence.
            "source_reliability": "approximate_memory",
            "metadata": {"adb_event_code": str(source.get("sevcode") or "")},
        })
    return rows


def build_seed_cohort(
    *,
    xml_path: Path | str,
    dataset_id: str,
    count: int,
    random_seed: int,
    min_exact_events: int = 2,
    holdout_count: int = 0,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    root = ET.parse(str(xml_path)).getroot()
    rng = random.Random(random_seed)
    candidates = []
    for entry in root.findall("adb_entry"):
        public = entry.find("public_data")
        if public is None or (public.findtext("roddenrating") or "").strip() != "AA":
            continue
        bdata = public.find("bdata")
        birth_date = bdata.find("sbdate") if bdata is not None else None
        birth_time = bdata.find("sbtime") if bdata is not None else None
        place = bdata.find("place") if bdata is not None else None
        if birth_date is None or birth_time is None or place is None:
            continue
        try:
            year = int(birth_date.get("iyear") or 0)
            month = int(birth_date.get("imonth") or 0)
            day = int(birth_date.get("iday") or 0)
            born = date(year, month, day)
            truth_seconds = _time_seconds(birth_time.text or "")
            # A fixed two-hour window can place truth uniformly only away from
            # civil-day edges; edge cases belong in a later cross-midnight test.
            if not 7200 <= truth_seconds <= 86399 - 7200:
                continue
            latitude = _coordinate(place.get("slati") or "", "n", "s")
            longitude = _coordinate(place.get("slong") or "", "e", "w")
            timezone = get_iana_timezone(latitude, longitude)
        except (ImportError, TypeError, ValueError):
            continue
        events = _mapped_events(entry, born.year)
        if len(events) < 4 or sum(
            event["precision"] == "exact_day" for event in events
        ) < min_exact_events:
            continue
        candidates.append({
            "entry": entry,
            "public": public,
            "birth_date": born,
            "truth_seconds": truth_seconds,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "place": place.text or "",
            "events": events,
        })
    rng.shuffle(candidates)
    selected = candidates[:count]
    if len(selected) < count:
        raise ValueError(f"Only {len(selected)} AA records have four mapped event candidates")
    if not 0 <= int(holdout_count) < count:
        raise ValueError("holdout_count must be at least zero and smaller than count")

    cases, truth = [], []
    development_count = count - int(holdout_count)
    for index, candidate in enumerate(selected):
        entry = candidate["entry"]
        case_id = _anonymous_id(dataset_id, str(entry.get("adb_id") or ""))
        # The Phase 1 engine scans on a whole-minute grid. Keep the hidden
        # recorded minute on that grid; otherwise a window beginning at :11 or
        # :49 seconds can never evaluate a minute-resolved AA birth time.
        truth_position = rng.randint(0, 120) * 60
        start = candidate["truth_seconds"] - truth_position
        end = start + 120 * 60
        adb_link = (candidate["entry"].findtext("./text_data/adb_link") or "").strip()
        cases.append({
            "id": case_id,
            # Assigned before event audit or any scoring run.  The candidate
            # order is already deterministically shuffled above.
            "split": "development" if index < development_count else "holdout",
            "window_strategy": "blinded_uniform_truth_position",
            "event_source_audit": "astrodatabank_research_events_require_independent_verification",
            "chart": {
                "name": "Anonymous public AA record",
                "date": candidate["birth_date"].isoformat(),
                "latitude": candidate["latitude"],
                "longitude": candidate["longitude"],
                "timezone": candidate["timezone"],
                "place": candidate["place"],
            },
            "window_start_local": _clock(start),
            "window_end_local": _clock(end),
            "events": candidate["events"],
            # Keep the identifying entry URL in the truth vault, not in the
            # blinded candidate file consumed by the scorer.
            "source": {"provider": "Astro-Databank"},
        })
        truth.append({
            "id": case_id,
            "verified_local_time": _clock(candidate["truth_seconds"]),
            "verification_source": adb_link or ADB_PUBLIC_SAMPLE_URL,
            "verification_rating": "Rodden AA",
        })
    blinded = {
        "schema_version": BLINDED_DATASET_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "cohort_status": (
            "development_seed_event_sources_unaudited"
            if not holdout_count else "preassigned_development_holdout_event_sources_unaudited"
        ),
        "minimum_exact_events": min_exact_events,
        "source": ADB_PUBLIC_SAMPLE_URL,
        "cases": cases,
    }
    vault = {
        "schema_version": TRUTH_VAULT_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "cohort_status": blinded["cohort_status"],
        "truth": truth,
    }
    return blinded, vault


def _private_output(path: str) -> Path:
    resolved = Path(path)
    if not resolved.name.endswith(".private.json"):
        raise ValueError("Astro-Databank-derived research output must end in .private.json")
    return resolved


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a private Astro-Databank AA seed cohort")
    parser.add_argument("--xml", required=True, help="Locally downloaded official ADB research XML")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--random-seed", type=int, required=True)
    parser.add_argument("--min-exact-events", type=int, default=2)
    parser.add_argument("--holdout-count", type=int, default=0)
    parser.add_argument("--blinded-output", required=True)
    parser.add_argument("--truth-output", required=True)
    parser.add_argument("--acknowledge-adb-research-terms", action="store_true")
    args = parser.parse_args(argv)
    if not args.acknowledge_adb_research_terms:
        parser.error("--acknowledge-adb-research-terms is required")
    blinded, truth = build_seed_cohort(
        xml_path=args.xml,
        dataset_id=args.dataset_id,
        count=args.count,
        random_seed=args.random_seed,
        min_exact_events=args.min_exact_events,
        holdout_count=args.holdout_count,
    )
    blinded_path = _private_output(args.blinded_output)
    truth_path = _private_output(args.truth_output)
    blinded_path.parent.mkdir(parents=True, exist_ok=True)
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    blinded_path.write_text(json.dumps(blinded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    truth_path.write_text(json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "dataset_id": args.dataset_id,
        "cases": len(blinded["cases"]),
        "status": blinded["cohort_status"],
        "blinded_output": str(blinded_path),
        "truth_output": str(truth_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
