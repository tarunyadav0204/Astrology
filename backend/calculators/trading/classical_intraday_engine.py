from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
from threading import RLock
from types import SimpleNamespace
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from calculators.ashtakavarga_transit import AshtakavargaTransitCalculator
from calculators.base_calculator import BaseCalculator
from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from panchang.panchang_calculator import PanchangCalculator
from shared.dasha_calculator import DashaCalculator

from .market_calendar import MarketSessionCalendar


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
ANCHORS = frozenset({2, 5, 11})
PRESSURE = frozenset({8, 12})
SUPPORT_HOUSES = frozenset({1, 2, 5, 9, 10, 11})
TARA_NAMES = ("Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra", "Parama Mitra")
GOOD_TARA = frozenset({"Sampat", "Kshema", "Sadhana", "Mitra", "Parama Mitra"})
BAD_TARA = frozenset({"Vipat", "Pratyak", "Naidhana"})
GOOD_CHANDRA = frozenset({1, 3, 6, 7, 10, 11})
HORA_SEQUENCE = ("Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars")
BAD_TITHI = frozenset({4, 9, 14, 30})
BAD_YOGA = frozenset({1, 6, 9, 10, 13, 15, 17, 19, 27})
GOOD_CHOGHADIYA = frozenset({"Labha", "Shubha", "Amrita"})
BAD_CHOGHADIYA = frozenset({"Kala", "Udvega", "Roga"})

_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_LOCK = RLock()


def _house(chart: Mapping[str, Any], planet: str) -> int | None:
    try:
        return int((chart.get("planets") or {}).get(planet, {}).get("house"))
    except (TypeError, ValueError):
        return None


def _sign(chart: Mapping[str, Any], planet: str) -> int | None:
    try:
        return int((chart.get("planets") or {}).get(planet, {}).get("sign"))
    except (TypeError, ValueError):
        return None


def _aspect_offsets(planet: str) -> tuple[int, ...]:
    # Offset 7 means the seventh house from the planet. Nodes use only the
    # seventh aspect in this engine; no Rahu/Ketu fifth or ninth aspects.
    if planet == "Mars": return (4, 7, 8)
    if planet == "Jupiter": return (5, 7, 9)
    if planet == "Saturn": return (3, 7, 10)
    return (7,)


def _lordships(chart: Mapping[str, Any], planet: str) -> set[int]:
    houses = chart.get("houses") or []
    return {
        i + 1 for i, row in enumerate(houses[:12])
        if BaseCalculator.SIGN_LORDS.get(int(row.get("sign", -1))) == planet
    }


def _connections(chart: Mapping[str, Any], planet: str) -> set[int]:
    result = set(_lordships(chart, planet))
    occupied = _house(chart, planet)
    if occupied:
        result.add(occupied)
        result.update((((occupied + offset - 2) % 12) + 1) for offset in _aspect_offsets(planet))
    return result


def _transit_house_from_natal_asc(natal_chart: Mapping[str, Any], transit_chart: Mapping[str, Any], planet: str) -> int | None:
    sign = _sign(transit_chart, planet)
    if sign is None: return None
    natal_asc_sign = int(float(natal_chart.get("ascendant", 0)) // 30) % 12
    return ((sign - natal_asc_sign) % 12) + 1


def _moon_gandanta(longitude: float) -> bool:
    # Classical 48-arcminute zone on each side of the Cancer/Leo,
    # Scorpio/Sagittarius and Pisces/Aries junctions.
    return any(min((longitude - point) % 360, (point - longitude) % 360) <= 0.8 for point in (0.0, 120.0, 240.0))


def _is_combust(row: Mapping[str, Any]) -> bool:
    return str(row.get("combustion_status") or "").lower() == "combust"


def _is_weak(row: Mapping[str, Any]) -> bool:
    return str(row.get("dignity") or "").lower() in {"debilitated", "unfavorable"} or _is_combust(row)


def _is_strong(row: Mapping[str, Any]) -> bool:
    return str(row.get("dignity") or "").lower() in {"exalted", "moolatrikona", "own_sign", "favorable"} and not _is_combust(row)


def _at(moment: datetime) -> str:
    return moment.strftime("%H:%M")


class ClassicalIntradayTradingEngine:
    """Four-gate Jyotisha evidence engine for the native's intraday judgment climate.

    It does not predict market direction, a security, or profit. D1/D2 establish
    capacity, MD/AD/PD establish period permission, the daily layer establishes
    the changing climate, and the Muhurta layer ranks actual session segments.
    """

    schema_version = "classical_intraday.v1"

    def __init__(self, natal_chart: Mapping[str, Any], birth_data: Mapping[str, Any]):
        self.natal_chart = deepcopy(dict(natal_chart))
        self.birth_data = dict(birth_data)
        self.chart_calc = ChartCalculator({})
        self.panchang = PanchangCalculator()

    def calculate(self, target_date: str, *, current_location: Mapping[str, Any] | None, exchange: str = "NSE") -> dict[str, Any]:
        market = MarketSessionCalendar().session(target_date, exchange)
        location = self._location(current_location)
        packet: dict[str, Any] = {
            "schema_version": self.schema_version,
            "method": "D1/D2 → Vimshottari MD/AD/PD → daily gochara/Panchanga/AV → trading Muhurta",
            "scope": "native_judgment_and_execution_climate",
            "market": market,
            "location": location,
            "excluded_layers": ["D5", "Indu Lagna", "KP", "market-direction prediction", "weighted luck score"],
            "claim_rule": "This judges the trader's decision climate and timing. It does not predict index, ticker, option, or P&L direction.",
        }
        if not location.get("available"):
            packet.update({"available": False, "market_open": False, "participation": "sit_out", "reason": location["reason"], "windows": []})
            return packet
        packet["natal_baseline"] = self.natal_baseline()
        if not market["market_open"]:
            packet.update({"available": True, "market_open": False, "participation": "sit_out", "reason": market["reason"], "windows": []})
            return packet
        exchange_open = datetime.strptime(f"{target_date[:10]} {market['open']}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(market["timezone"]))
        try:
            local_zone = ZoneInfo(str(location["timezone"]))
        except Exception:
            local_zone = ZoneInfo("Asia/Kolkata")
            location["timezone"] = "Asia/Kolkata"
        open_dt = exchange_open.astimezone(local_zone).replace(tzinfo=None)
        period = self.period_permission(open_dt)
        daily = self.daily_climate(open_dt, location, period)
        participation = self._decision(period["status"], daily["status"])
        windows = self.muhurta_windows(open_dt, location, period, daily)
        if participation == "sit_out":
            for row in windows:
                row["usable_for_new_entry"] = False
                if row["verdict"] == "supportive": row["verdict"] = "avoid"
        packet.update({
            "available": True, "market_open": True, "period_permission": period,
            "daily_climate": daily, "participation": participation,
            "windows": windows,
            "entry_windows": [r for r in windows if r["verdict"] == "supportive" and r["usable_for_new_entry"]],
            "caution_windows": [r for r in windows if r["verdict"] != "supportive"],
        })
        return packet

    def _location(self, supplied: Mapping[str, Any] | None) -> dict[str, Any]:
        row = dict(supplied or {})
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if abs(lat) > 90 or abs(lon) > 180: raise ValueError
        except (KeyError, TypeError, ValueError):
            return {"available": False, "reason": "Current trading location is required to calculate local Panchanga, ascendant and Hora windows."}
        return {
            "available": True, "latitude": lat, "longitude": lon,
            "name": row.get("name") or "Current location",
            "timezone": row.get("timezone") or row.get("timezone_name") or "Asia/Kolkata",
            "source": row.get("source") or "device_or_user",
        }

    def natal_baseline(self) -> dict[str, Any]:
        cache_input = {
            "birth": {k: self.birth_data.get(k) for k in ("date", "time", "latitude", "longitude", "timezone")},
            "ascendant": self.natal_chart.get("ascendant"),
            "planets": {p: (self.natal_chart.get("planets") or {}).get(p) for p in PLANETS},
        }
        key = sha256(json.dumps(cache_input, sort_keys=True, default=str).encode()).hexdigest()
        with _CACHE_LOCK:
            if key in _CACHE: return deepcopy(_CACHE[key])
        dignity = PlanetaryDignitiesCalculator(self.natal_chart).calculate_planetary_dignities()
        carriers, pressure = [], []
        rows = {}
        for planet in PLANETS:
            connected = sorted(_connections(self.natal_chart, planet))
            rows[planet] = {"houses": connected, "dignity": dignity.get(planet, {}).get("dignity"), "combustion": dignity.get(planet, {}).get("combustion_status")}
            if len(set(connected) & ANCHORS) >= 2 and not _is_weak(dignity.get(planet, {})): carriers.append(planet)
            if set(connected) & ANCHORS and set(connected) & PRESSURE: pressure.append(planet)
        d2 = DivisionalChartCalculator(self.natal_chart).calculate_divisional_chart(2)["divisional_chart"]
        d2_dignity = PlanetaryDignitiesCalculator(d2).calculate_planetary_dignities()
        d2_evidence = []
        for house_no in (2, 11):
            sign = int((d2.get("houses") or [])[house_no - 1]["sign"])
            lord = BaseCalculator.SIGN_LORDS[sign]
            placed = _house(d2, lord)
            state = d2_dignity.get(lord, {})
            d2_evidence.append({"house": house_no, "lord": lord, "lord_house": placed, "dignity": state.get("dignity"), "combustion": state.get("combustion_status"), "supportive": bool(placed in SUPPORT_HOUSES and not _is_weak(state)), "vulnerable": bool(placed in {6, 8, 12} or _is_weak(state))})
        d2_support = any(x["supportive"] for x in d2_evidence)
        d2_pressure = any(x["vulnerable"] for x in d2_evidence)
        result = {
            "role": "background capacity; it cannot create today's verdict",
            "house_framework": {"2": "capital and retained resources", "3": "execution and self-effort", "5": "judgment and speculation", "6": "competition and debt", "8": "sudden reversal", "11": "realized gains", "12": "loss and leakage"},
            "planet_connections": rows, "support_carriers": carriers, "pressure_carriers": pressure,
            "speculation_capacity": "supported" if carriers and len(pressure) <= len(carriers) else ("qualified" if carriers else "weak"),
            "d2_retention_evidence": d2_evidence,
            "retention_capacity": "supportive" if d2_support and not d2_pressure else ("vulnerable" if d2_pressure and not d2_support else "mixed"),
        }
        with _CACHE_LOCK:
            if len(_CACHE) >= 256: _CACHE.pop(next(iter(_CACHE)))
            _CACHE[key] = deepcopy(result)
        return result

    def period_permission(self, moment: datetime) -> dict[str, Any]:
        dashas = DashaCalculator().calculate_current_dashas(self.birth_data, moment, strict=True)
        periods = []
        union: set[int] = set()
        for level, key in (("mahadasha", "mahadasha"), ("antardasha", "antardasha"), ("pratyantardasha", "pratyantardasha")):
            planet = str((dashas.get(key) or {}).get("planet"))
            linked = sorted(_connections(self.natal_chart, planet))
            union.update(linked)
            periods.append({"level": level, "planet": planet, "houses": linked, "supports": sorted(set(linked) & ANCHORS), "pressures": sorted(set(linked) & PRESSURE)})
        gain_complete = ANCHORS.issubset(union)
        gain_core = {5, 11}.issubset(union)
        severe_pressure = PRESSURE.issubset(union)
        if severe_pressure and not gain_complete: status = "adverse"
        elif gain_complete and not severe_pressure: status = "supportive"
        else: status = "mixed"
        return {"status": status, "active_periods": periods, "activated_houses": sorted(union), "gain_chain_complete": gain_complete, "speculation_gain_core": gain_core, "loss_chain_active": severe_pressure}

    def daily_climate(self, moment: datetime, location: Mapping[str, Any], period: Mapping[str, Any]) -> dict[str, Any]:
        transit = self._chart(moment, location)
        p = self._panchang_at(moment, location)
        natal_moon = _sign(self.natal_chart, "Moon")
        transit_moon = _sign(transit, "Moon")
        natal_nak = int(float((self.natal_chart.get("planets") or {})["Moon"]["longitude"]) // (360 / 27)) + 1
        transit_nak = int((p.get("nakshatra") or {}).get("number") or 1)
        tara = TARA_NAMES[(transit_nak - natal_nak) % 9]
        chandra_house = ((int(transit_moon) - int(natal_moon)) % 12) + 1
        support, obstruction = [], []
        if tara in GOOD_TARA: support.append({"group": "tara", "code": tara, "reason": f"{tara} Tara supports the native's effort."})
        elif tara in BAD_TARA: obstruction.append({"group": "tara", "code": tara, "major": True, "reason": f"{tara} Tara cautions against forcing decisions."})
        if chandra_house in GOOD_CHANDRA: support.append({"group": "chandra", "code": f"H{chandra_house}", "reason": f"The Moon is {chandra_house} from the natal Moon, a supportive Chandra-bala place."})
        elif chandra_house in {8, 12}: obstruction.append({"group": "chandra", "code": f"H{chandra_house}", "major": chandra_house == 8, "reason": f"The Moon is {chandra_house} from the natal Moon, increasing instability or depletion."})
        active_lords = [r["planet"] for r in period["active_periods"]]
        transit_support, transit_pressure = [], []
        for planet in active_lords:
            h = _transit_house_from_natal_asc(self.natal_chart, transit, planet)
            if h in ANCHORS: transit_support.append(f"{planet}:H{h}")
            if h in PRESSURE: transit_pressure.append(f"{planet}:H{h}")
        if transit_support: support.append({"group": "dasha_transit", "code": ", ".join(transit_support), "reason": "Active Vimshottari lords occupy trading-support houses in today's gochara chart."})
        if transit_pressure: obstruction.append({"group": "dasha_transit", "code": ", ".join(transit_pressure), "major": False, "reason": "Active Vimshottari lords occupy reversal or loss houses today."})
        av_rows = AshtakavargaTransitCalculator(self.birth_data, self.natal_chart).calculate_transit_snapshot(moment)
        relevant = [r for r in av_rows if r["planet"] in set(active_lords + ["Moon"])]
        rich = [r["planet"] for r in relevant if r["natal_bav_band"] == "bindu_rich" and r["natal_sav_band"] != "weak"]
        poor = [r["planet"] for r in relevant if r["natal_bav_band"] == "bindu_poor" and r["natal_sav_band"] == "weak"]
        if rich: support.append({"group": "ashtakavarga", "code": ", ".join(rich), "reason": "Relevant transits cross bindu-rich natal BAV signs without weak SAV support."})
        if poor: obstruction.append({"group": "ashtakavarga", "code": ", ".join(poor), "major": False, "reason": "Relevant transits cross bindu-poor BAV and weak SAV signs."})
        moon_longitude = float((transit.get("planets") or {}).get("Moon", {}).get("longitude") or 0.0)
        if _moon_gandanta(moon_longitude):
            obstruction.append({"group": "moon_gandanta", "code": "Moon Gandanta", "major": True, "reason": "The transit Moon is within the classical Gandanta junction, so fresh risk-taking is avoided."})
        vara_lord = str((p.get("vara") or {}).get("lord") or "")
        baseline = self.natal_baseline()
        if vara_lord in set(active_lords) or vara_lord in set(baseline["support_carriers"]):
            support.append({"group": "vara", "code": vara_lord, "reason": f"The weekday lord {vara_lord} is connected with the active period or natal trading support."})
        if vara_lord in set(baseline["pressure_carriers"]):
            obstruction.append({"group": "vara", "code": vara_lord, "major": False, "reason": f"The weekday lord {vara_lord} also carries natal reversal or loss pressure."})
        obstruction.extend(self._panchanga_obstructions(p))
        major_groups = {r["group"] for r in obstruction if r.get("major")}
        support_groups = {r["group"] for r in support}
        if period["status"] == "adverse" or len(major_groups) >= 2: status = "adverse"
        elif period["status"] == "supportive" and len(support_groups) >= 2 and not major_groups: status = "strong"
        else: status = "mixed"
        return {"status": status, "tara_bala": {"name": tara, "natal_nakshatra": natal_nak, "transit_nakshatra": transit_nak}, "chandra_bala": {"house_from_natal_moon": chandra_house}, "supports": support, "obstructions": obstruction, "ashtakavarga": relevant, "panchanga": self._compact_panchanga(p)}

    def muhurta_windows(self, open_dt: datetime, location: Mapping[str, Any], period: Mapping[str, Any], daily: Mapping[str, Any]) -> list[dict[str, Any]]:
        close_dt = open_dt + timedelta(hours=6, minutes=15)
        chogh = self.panchang.calculate_choghadiya(open_dt.strftime("%Y-%m-%d"), location["latitude"], location["longitude"], location["timezone"])["day_choghadiya"]
        horas = self._day_horas(open_dt, location)
        boundaries = {open_dt, close_dt}
        for collection in (chogh, horas):
            for row in collection:
                for key in ("start_time", "end_time"):
                    dt = datetime.fromisoformat(row[key])
                    if open_dt < dt < close_dt: boundaries.add(dt)
        # Panchanga changes and ascendant sign changes are real segment boundaries.
        for key in ("tithi", "nakshatra", "yoga"):
            end = (self._panchang_at(open_dt, location).get(key) or {}).get("end_time")
            if end:
                dt = datetime.fromisoformat(end)
                if open_dt < dt < close_dt: boundaries.add(dt)
        scan = open_dt
        old_sign = int(self._chart(scan, location)["ascendant"] // 30)
        old_pstate = self._panchanga_state(self._panchang_at(scan, location))
        while scan < close_dt:
            nxt = min(scan + timedelta(minutes=5), close_dt)
            new_sign = int(self._chart(nxt, location)["ascendant"] // 30)
            if new_sign != old_sign:
                left, right = scan, nxt
                for _ in range(9):
                    mid = left + (right - left) / 2
                    if int(self._chart(mid, location)["ascendant"] // 30) == old_sign: left = mid
                    else: right = mid
                boundaries.add(right.replace(second=0, microsecond=0))
            new_pstate = self._panchanga_state(self._panchang_at(nxt, location))
            if new_pstate != old_pstate:
                left, right = scan, nxt
                for _ in range(9):
                    mid = left + (right - left) / 2
                    if self._panchanga_state(self._panchang_at(mid, location)) == old_pstate: left = mid
                    else: right = mid
                boundaries.add(right.replace(second=0, microsecond=0))
            scan, old_sign, old_pstate = nxt, new_sign, new_pstate
        points = sorted(boundaries)
        return [self._judge_window(points[i], points[i + 1], location, period, daily, chogh, horas) for i in range(len(points) - 1) if points[i] < points[i + 1]]

    def _judge_window(self, start: datetime, end: datetime, location: Mapping[str, Any], period: Mapping[str, Any], daily: Mapping[str, Any], chogh: list[dict[str, Any]], horas: list[dict[str, Any]]) -> dict[str, Any]:
        mid = start + (end - start) / 2
        chart = self._chart(mid, location)
        dignity = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
        p = self._panchang_at(mid, location)
        ch = next((r for r in chogh if datetime.fromisoformat(r["start_time"]) <= mid < datetime.fromisoformat(r["end_time"])), {})
        hora = next((r for r in horas if datetime.fromisoformat(r["start_time"]) <= mid < datetime.fromisoformat(r["end_time"])), {})
        active = {r["planet"] for r in period["active_periods"]}
        natal_support = set(self.natal_baseline()["support_carriers"])
        natal_pressure = set(self.natal_baseline()["pressure_carriers"])
        supports, cautions = [], []
        if ch.get("name") in GOOD_CHOGHADIYA: supports.append(f"{ch['name']} Choghadiya")
        elif ch.get("name") in BAD_CHOGHADIYA: cautions.append(f"{ch['name']} Choghadiya")
        if hora.get("lord") in active or hora.get("lord") in natal_support: supports.append(f"{hora.get('lord')} Hora connects with an active/support carrier")
        if hora.get("lord") in natal_pressure: cautions.append(f"{hora.get('lord')} Hora carries natal reversal/loss pressure")
        asc_sign = int(chart["ascendant"] // 30)
        asc_lord = BaseCalculator.SIGN_LORDS[asc_sign]
        asc_state = dignity.get(asc_lord, {})
        major = _is_weak(asc_state) or _house(chart, asc_lord) in {8, 12}
        if not major and (_is_strong(asc_state) or _house(chart, asc_lord) in SUPPORT_HOUSES): supports.append("Muhurta ascendant lord is usable")
        else: cautions.append("Muhurta ascendant lord is weak or placed in a loss/reversal house")
        moon_house = _house(chart, "Moon")
        moon_state = dignity.get("Moon", {})
        if moon_house in GOOD_CHANDRA and not _is_weak(moon_state):
            supports.append(f"Muhurta Moon is usable in H{moon_house}")
        if moon_house in {8, 12} or _is_weak(moon_state):
            cautions.append(f"Muhurta Moon is pressured in H{moon_house}")
            if moon_house == 8: major = True
        anchor_lords = []
        for h in (2, 5, 11):
            lord = BaseCalculator.SIGN_LORDS[int(chart["houses"][h - 1]["sign"])]
            anchor_lords.append({"house": h, "lord": lord, "lord_house": _house(chart, lord), "dignity": dignity.get(lord, {}).get("dignity")})
        if sum(1 for r in anchor_lords if r["lord_house"] in SUPPORT_HOUSES and not _is_weak(dignity.get(r["lord"], {}))) >= 2: supports.append("At least two Muhurta trading-house lords are usable")
        impaired_anchors = [r for r in anchor_lords if r["lord_house"] in {8, 12} or _is_weak(dignity.get(r["lord"], {}))]
        if impaired_anchors:
            cautions.append("Trading-house lord pressure: " + ", ".join(f"H{r['house']} lord {r['lord']}" for r in impaired_anchors))
        if len(impaired_anchors) >= 2:
            major = True
        active_support = [f"{x}:H{_house(chart, x)}" for x in active if _house(chart, x) in ANCHORS]
        active_pressure = [f"{x}:H{_house(chart, x)}" for x in active if _house(chart, x) in PRESSURE]
        if active_support: supports.append("Active dasha lords support " + ", ".join(active_support))
        if active_pressure: cautions.append("Active dasha lords pressure " + ", ".join(active_pressure))
        p_obstructions = self._panchanga_obstructions(p)
        moon_longitude = float((chart.get("planets") or {}).get("Moon", {}).get("longitude") or 0.0)
        if _moon_gandanta(moon_longitude):
            p_obstructions.append({"group": "moon_gandanta", "code": "Moon Gandanta", "major": True, "reason": "Moon Gandanta makes this segment unsuitable for a fresh speculative entry."})
        if p_obstructions: cautions.extend(r["reason"] for r in p_obstructions)
        if any(r.get("major") for r in p_obstructions): major = True
        if daily["status"] == "adverse" or major: verdict = "avoid"
        elif len(supports) >= 2: verdict = "supportive"
        else: verdict = "neutral"
        return {"start": self._exchange_clock(start, location), "end": self._exchange_clock(end, location), "local_start": _at(start), "local_end": _at(end), "verdict": verdict, "usable_for_new_entry": verdict == "supportive", "hora_lord": hora.get("lord"), "choghadiya": ch.get("name"), "ascendant_sign": asc_sign, "panchanga": self._compact_panchanga(p), "trading_house_lords": anchor_lords, "supports": supports, "cautions": cautions}

    @staticmethod
    def _exchange_clock(moment: datetime, location: Mapping[str, Any]) -> str:
        try:
            local = moment.replace(tzinfo=ZoneInfo(str(location["timezone"])))
            return local.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
        except Exception:
            return _at(moment)

    def _day_horas(self, moment: datetime, location: Mapping[str, Any]) -> list[dict[str, Any]]:
        solar = self.panchang.get_local_sunrise_sunset(moment.strftime("%Y-%m-%d"), location["latitude"], location["longitude"], location["timezone"])
        sunrise, sunset = datetime.fromisoformat(solar["sunrise"]), datetime.fromisoformat(solar["sunset"])
        vara = self._panchang_at(sunrise, location)["vara"]["lord"]
        idx = HORA_SEQUENCE.index(vara)
        duration = (sunset - sunrise) / 12
        return [{"lord": HORA_SEQUENCE[(idx + i) % 7], "start_time": (sunrise + duration * i).isoformat(), "end_time": (sunrise + duration * (i + 1)).isoformat()} for i in range(12)]

    def _chart(self, moment: datetime, location: Mapping[str, Any]) -> dict[str, Any]:
        return self.chart_calc.calculate_chart(SimpleNamespace(date=moment.strftime("%Y-%m-%d"), time=moment.strftime("%H:%M:%S"), latitude=location["latitude"], longitude=location["longitude"], timezone=location["timezone"]))

    def _panchang_at(self, moment: datetime, location: Mapping[str, Any]) -> dict[str, Any]:
        return self.panchang.calculate_panchang(moment.strftime("%Y-%m-%d"), location["latitude"], location["longitude"], location["timezone"], time_str=moment.strftime("%H:%M:%S"), reference="moment")

    def _panchanga_obstructions(self, p: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = []
        tithi = int((p.get("tithi") or {}).get("number") or 0)
        yoga = int((p.get("yoga") or {}).get("number") or 0)
        karana = str((p.get("karana") or {}).get("name") or "")
        if tithi in BAD_TITHI: rows.append({"group": "panchanga_tithi", "code": f"Tithi {tithi}", "major": False, "reason": "Rikta or Amavasya Tithi calls for restraint in initiating risk."})
        if yoga in BAD_YOGA: rows.append({"group": "panchanga_yoga", "code": (p.get("yoga") or {}).get("name"), "major": True, "reason": f"{(p.get('yoga') or {}).get('name')} Yoga is an initiation obstruction in the selected rule set."})
        if karana == "Vishti": rows.append({"group": "panchanga_karana", "code": karana, "major": True, "reason": "Vishti Karana is avoided for a fresh speculative entry."})
        return rows

    @staticmethod
    def _compact_panchanga(p: Mapping[str, Any]) -> dict[str, Any]:
        return {key: {"number": (p.get(key) or {}).get("number"), "name": (p.get(key) or {}).get("name")} for key in ("tithi", "vara", "nakshatra", "yoga", "karana")}

    @staticmethod
    def _panchanga_state(p: Mapping[str, Any]) -> tuple[Any, ...]:
        return tuple(((p.get(key) or {}).get("number"), (p.get(key) or {}).get("name")) for key in ("tithi", "nakshatra", "yoga", "karana"))

    @staticmethod
    def _decision(period: str, daily: str) -> str:
        return {
            ("supportive", "strong"): "participate",
            ("supportive", "mixed"): "reduce_size",
            ("supportive", "adverse"): "sit_out",
            ("mixed", "strong"): "reduce_size",
            ("mixed", "mixed"): "cautious",
            ("mixed", "adverse"): "sit_out",
        }.get((period, daily), "sit_out")
