"""Marriage election engine.

This is deliberately separate from the legacy ``vivah-muhurat`` endpoint.  The
legacy endpoint exposes fixed solar-day divisions; this engine verifies each
minute of a requested ceremony window and is able to compare both partners'
natal Moon positions when they have supplied complete birth details.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from calculators.chart_calculator import _SWISSEPH_CHART_LOCK
from calculators.muhurat_calculator import GULIKA_SEGMENTS, RAHU_SEGMENTS, YAMAGANDA_SEGMENTS
from calculators.verified_muhurat_calculator import VerifiedMuhuratCalculator, julian, sidereal_ascendant


class MarriageMuhuratCalculator(VerifiedMuhuratCalculator):
    """Versioned, conservative marriage-election policy for the mobile planner."""

    POLICY_VERSION = "vivaha_core_v1"
    # Rohini, Mrigashira, Magha, Uttara Phalguni, Hasta, Swati, Anuradha,
    # Uttara Ashadha, Uttara Bhadrapada and Revati.
    GOOD_NAKSHATRAS = {4, 5, 10, 12, 13, 15, 17, 21, 26, 27}
    # Used only when a strict search has no result. These are intentionally
    # surfaced as family-review candidates, not silently presented as strict
    # recommendations: regional wedding traditions differ materially here.
    DISCOVERY_NAKSHATRAS = {2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 17, 19, 21, 22, 24, 25, 26, 27}
    DISCOVERY_AVOID_YOGAS = {9, 10, 17, 19, 27}
    GOOD_TITHIS = {2, 3, 5, 6, 7, 10, 11, 12, 13}
    GOOD_LAGNAS = {1, 2, 5, 6, 8, 10, 11}
    GOOD_WEEKDAYS = {0, 2, 3, 4}  # Monday, Wednesday, Thursday, Friday

    @staticmethod
    def _moon_nakshatra(context):
        if not context:
            return None
        return int(context["positions"][swe.MOON] / (360 / 27)) + 1

    @staticmethod
    def _time_window(day: date, start: time, end: time, zone: ZoneInfo):
        begin = datetime.combine(day, start, zone)
        finish = datetime.combine(day, end, zone)
        # An end at or before start is an explicit overnight ceremony window.
        if finish <= begin:
            finish += timedelta(days=1)
        return begin, finish

    def search(self, request: dict):
        with _SWISSEPH_CHART_LOCK:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            try:
                strict = self._search(request, discovery_mode=False)
                if strict["recommendations"]:
                    return strict
                # A discovery planner must not turn a valid paid range search
                # into an empty experience merely because no narrow-policy
                # date falls in that horizon.
                return self._search(request, discovery_mode=True)
            finally:
                swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _search(self, request: dict, discovery_mode: bool):
        start = date.fromisoformat(request["start_date"])
        end = date.fromisoformat(request["end_date"])
        if end < start or (end - start).days >= 180:
            raise ValueError("Select an inclusive search period of 1–180 days")
        place = request["location"]
        zone = ZoneInfo(place["timezone"])
        lat, lon = float(place["latitude"]), float(place["longitude"])
        minimum = int(request.get("minimum_duration_minutes", 30))
        if not 10 <= minimum <= 180:
            raise ValueError("Minimum duration must be 10–180 minutes")
        allowed_start = time.fromisoformat(request.get("allowed_start") or "18:00")
        allowed_end = time.fromisoformat(request.get("allowed_end") or "23:30")
        partner_contexts = [
            self._build_natal_context(request.get("bride")),
            self._build_natal_context(request.get("groom")),
        ]
        natal_nakshatras = [self._moon_nakshatra(item) for item in partner_contexts if item]
        personalization = "couple natal Moon suitability" if len(natal_nakshatras) == 2 else "local Panchang policy only"
        candidates, rejected, errors, days_evaluated = [], Counter(), [], 0
        day = start
        while day <= end:
            if day.weekday() not in self.GOOD_WEEKDAYS:
                rejected["weekday_policy"] += 1
                day += timedelta(days=1)
                continue
            try:
                solar = self.panchang_calc.get_local_sunrise_sunset(day.isoformat(), lat, lon, place["timezone"])
                sunrise = datetime.fromisoformat(solar["sunrise"]).replace(tzinfo=zone)
                sunset = datetime.fromisoformat(solar["sunset"]).replace(tzinfo=zone)
                eighth = (sunset - sunrise) / 8
                forbidden = [
                    (sunrise + index * eighth, sunrise + (index + 1) * eighth)
                    for index in (RAHU_SEGMENTS[day.weekday()], YAMAGANDA_SEGMENTS[day.weekday()], GULIKA_SEGMENTS[day.weekday()])
                ]
                choghadiya = self.panchang_calc.calculate_choghadiya(day.isoformat(), lat, lon, place["timezone"])
                day_start, day_end = self._time_window(day, allowed_start, allowed_end, zone)
                cursor = day_start.replace(second=0, microsecond=0)
                run = None
                while cursor + timedelta(minutes=1) <= day_end:
                    endpoint = cursor + timedelta(minutes=1)
                    evaluated, reason = self._evaluate_minute(cursor, endpoint, lat, lon, forbidden, choghadiya, natal_nakshatras, partner_contexts, discovery_mode)
                    if reason:
                        rejected[reason] += 1
                        if run and (run["end_time"] - run["start_time"]).total_seconds() / 60 >= minimum:
                            candidates.append(run)
                        run = None
                    elif run and run["lagna"] == evaluated["lagna"] and run["panchang"] == evaluated["panchang"]:
                        run["end_time"] = endpoint
                        run["cautions"] = list(dict.fromkeys(run["cautions"] + evaluated["cautions"]))
                    else:
                        if run and (run["end_time"] - run["start_time"]).total_seconds() / 60 >= minimum:
                            candidates.append(run)
                        run = {**evaluated, "date": day.isoformat(), "start_time": cursor, "end_time": endpoint}
                    cursor = endpoint
                if run and (run["end_time"] - run["start_time"]).total_seconds() / 60 >= minimum:
                    candidates.append(run)
                days_evaluated += 1
            except (ValueError, RuntimeError, swe.Error) as exc:
                errors.append({"date": day.isoformat(), "reason": str(exc)[:150]})
            day += timedelta(days=1)
        candidates.sort(key=lambda row: (-row["score"], row["start_time"]))
        grouped = {}
        for row in candidates:
            row["duration_minutes"] = int((row["end_time"] - row["start_time"]).total_seconds() / 60)
            row["start_time"], row["end_time"] = row["start_time"].isoformat(), row["end_time"].isoformat()
            grouped.setdefault(row["date"], []).append(row)
        # A six-month discovery search can yield a large number of valid dates.
        # Return a concise, scored shortlist instead of making a user sift through
        # every day that happened to pass the policy.
        ranked_days = []
        for key, slots in grouped.items():
            slots.sort(key=lambda item: (-item["score"], item["start_time"]))
            ranked_days.append({"date": key, "slots": slots, "personalization": personalization, "score": slots[0]["score"]})
        ranked_days.sort(key=lambda item: (-item["score"], item["date"]))
        recommendations = [{**item, "rank": rank} for rank, item in enumerate(ranked_days[:12], start=1)]
        return {
            "status": "partial" if errors else "completed", "profile": self.POLICY_VERSION,
            "category": "Marriage Muhurat", "location": place, "period": f"{start} to {end}",
            "recommendations": recommendations, "rejected_dates": [], "total_candidates": len(candidates),
            "eligible_dates_found": len(ranked_days),
            "days_evaluated": days_evaluated, "rejection_counts": dict(rejected), "errors": errors,
            "personalization": personalization,
            "recommendation_level": "expanded_review" if discovery_mode else "strict",
            "selection_notice": ("No strict window fell in this period. These expanded candidates require confirmation with your family priest or tradition." if discovery_mode else "Strict marriage-policy windows, ranked for the selected period."),
            "limitations": ["A conservative, documented local Panchang policy; regional family traditions may differ.", "Compatibility analysis is not substituted for a ceremony-time election."],
        }

    def _evaluate_minute(self, start, endpoint, lat, lon, forbidden, choghadiya, natal_nakshatras, contexts, discovery_mode):
        if any(start < end and endpoint > begin for begin, end in forbidden):
            return None, "rahu_yamaganda_gulika"
        details = None
        for sample in (start, start + timedelta(seconds=30), endpoint):
            jd = julian(sample)
            positions = self._sidereal_positions(jd)
            sun, moon = positions[swe.SUN], positions[swe.MOON]
            tithi, nak, yoga, half = int(((moon - sun) % 360) / 12) + 1, int(moon / (360 / 27)) + 1, int(((moon + sun) % 360) / (360 / 27)) + 1, int(((moon - sun) % 360) / 6) + 1
            asc = int(sidereal_ascendant(jd, lat, lon) / 30)
            vishti = 2 <= half <= 57 and (half - 2) % 7 == 6
            if moon >= 300: return None, "panchak_policy"
            if tithi not in self.GOOD_TITHIS: return None, "tithi_policy"
            avoid_yogas = self.DISCOVERY_AVOID_YOGAS if discovery_mode else self.AVOID_YOGAS
            permitted_nakshatras = self.DISCOVERY_NAKSHATRAS if discovery_mode else self.GOOD_NAKSHATRAS
            if yoga in avoid_yogas: return None, "yoga_policy"
            if vishti: return None, "vishti_karana"
            if nak not in permitted_nakshatras: return None, "marriage_nakshatra_policy"
            if asc not in self.GOOD_LAGNAS: return None, "marriage_lagna_policy"
            choghadiya_weight = self._choghadiya_weight(sample, choghadiya)
            if not choghadiya_weight: return None, "choghadiya_policy"
            if self._angular_distance(sun, positions[swe.VENUS]) < 8 or self._angular_distance(sun, positions[swe.JUPITER]) < 9:
                return None, "marriage_karaka_combustion"
            tara = [((nak - natal) % 27) % 9 + 1 for natal in natal_nakshatras]
            if any(value in {1, 3, 5, 7} for value in tara): return None, "partner_tara_bala"
            chandra = []
            for context in contexts:
                if context:
                    distance = (int(moon / 30) - context["moon_sign"]) % 12 + 1
                    chandra.append(distance)
            if any(value in {2, 4, 5, 8, 9, 12} for value in chandra): return None, "partner_chandra_bala"
            tithi_weight = {2: 6, 3: 5, 5: 7, 6: 8, 7: 6, 10: 7, 11: 9, 12: 8, 13: 10}[tithi]
            lagna_weight = {1: 6, 2: 5, 5: 8, 6: 9, 8: 7, 10: 6, 11: 8}[asc]
            details = {"score": 50 + tithi_weight + lagna_weight + choghadiya_weight + (10 if len(natal_nakshatras) == 2 else 0), "lagna": self._sign_name(asc),
                       "panchang": {"tithi_number": tithi, "nakshatra_number": nak, "yoga_number": yoga, "karana_half": half},
                       "reasons": ["Passed the marriage Panchang, Lagna and caution-period policy."],
                       "positives": [("Expanded marriage-date candidate; confirm regional tradition." if discovery_mode else "Auspicious marriage Nakshatra and permitted Tithi are active.")],
                       "cautions": ((["This is an expanded discovery candidate, not a strict marriage-policy window."] if discovery_mode else []) + ([] if len(natal_nakshatras) == 2 else ["Partner birth data was not available; couple natal Moon checks were not applied."]))}
        return details, None

    def _choghadiya_weight(self, sample, data):
        weights = {"Amrit": 10, "Shubh": 8, "Labh": 6, "Chara": 3}
        for slot in (data.get("day_choghadiya", []) + data.get("night_choghadiya", [])):
            if slot.get("name") not in self.GOOD_CHOGHADIYA: continue
            try:
                begin, end = datetime.fromisoformat(slot["start_time"]), datetime.fromisoformat(slot["end_time"])
                if begin.tzinfo is None: begin, end = begin.replace(tzinfo=sample.tzinfo), end.replace(tzinfo=sample.tzinfo)
                if begin <= sample < end: return weights.get(slot["name"], 1)
            except (KeyError, ValueError, TypeError):
                continue
        return 0
