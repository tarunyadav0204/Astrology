from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import swisseph as swe

from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.chart_calculator import _SWISSEPH_CHART_LOCK
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.shadbala_calculator import ShadbalaCalculator
from calculators.shoola_dasha_calculator import ShoolaDashaCalculator
from panchang.panchang_calculator import PanchangCalculator
from shared.dasha_calculator import DashaCalculator


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
SIGN_NATURES = {0: "Movable", 1: "Fixed", 2: "Dual"}
EXALTATION = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBILITATION = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9, "Venus": 5, "Saturn": 0}
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
SHADBALA_REQUIRED = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
PARASHARI_ASPECTS = {
    "Sun": {6}, "Moon": {6}, "Mars": {3, 6, 7}, "Mercury": {6},
    "Jupiter": {4, 6, 8}, "Venus": {6}, "Saturn": {2, 6, 9},
}
AYU_RANGES = {
    "Alpayu": {"label": "Alpayu", "range": "0–36", "baseline_window": [30, 36], "tier": 0},
    "Madhyayu": {"label": "Madhyayu", "range": "36–72", "baseline_window": [60, 72], "tier": 1},
    "Purnayu": {"label": "Purnayu", "range": "72–108+", "baseline_window": [72, 84], "tier": 2},
}
AYU_MAX_AGES = {"Alpayu": 36, "Madhyayu": 72, "Purnayu": None}
PARENT_SUPPORT_LABELS = {
    "Alpayu": "Lower derived vitality support",
    "Madhyayu": "Moderate derived vitality support",
    "Purnayu": "Higher derived vitality support",
}
SUBJECTS = {
    "self": {"label": "Native", "derived_house": 1, "offset": 0, "karaka": "Moon", "jaimini_karaka": None},
    "mother": {"label": "Mother", "derived_house": 4, "offset": 3, "karaka": "Moon", "jaimini_karaka": "Matrukaraka"},
    "father": {"label": "Father", "derived_house": 9, "offset": 8, "karaka": "Sun", "jaimini_karaka": "Bhratrukaraka"},
}
PAIR_CATEGORY = {
    ("Movable", "Movable"): "Purnayu",
    ("Fixed", "Fixed"): "Alpayu",
    ("Dual", "Dual"): "Madhyayu",
    ("Movable", "Fixed"): "Madhyayu",
    ("Movable", "Dual"): "Alpayu",
    ("Fixed", "Dual"): "Purnayu",
}


def _nature(sign: int) -> str:
    return SIGN_NATURES[int(sign) % 3]


def _house_from_sign(sign: int, asc_sign: int) -> int:
    return ((int(sign) - int(asc_sign)) % 12) + 1


def _pair_category(left: int, right: int) -> str:
    key = tuple(sorted((_nature(left), _nature(right)), key=("Movable", "Fixed", "Dual").index))
    return PAIR_CATEGORY[key]


def _arudha_for_house(chart: Dict[str, Any], house: int) -> int:
    asc_sign = int(chart.get("ascendant", 0) / 30) % 12
    source_sign = (asc_sign + house - 1) % 12
    lord_sign = int(chart.get("planets", {}).get(SIGN_LORDS[source_sign], {}).get("sign", 0))
    distance = (lord_sign - source_sign) % 12
    if distance == 0:
        return (source_sign + 9) % 12
    if distance == 6:
        return (source_sign + 3) % 12
    return (lord_sign + distance) % 12


def _planet_house(chart: Dict[str, Any], planet: str) -> int:
    asc_sign = int(chart.get("ascendant", 0) / 30) % 12
    return _house_from_sign(chart.get("planets", {}).get(planet, {}).get("sign", 0), asc_sign)


def _format_longitude(data: Dict[str, Any]) -> str:
    degree = float(data.get("degree", data.get("longitude", 0) % 30) or 0)
    whole = int(degree)
    minutes = int(round((degree - whole) * 60))
    if minutes == 60:
        whole += 1
        minutes = 0
    return f"{whole}° {minutes:02d}′"


class LongevityCalculator:
    """Build a stable, UI- and chat-ready longevity evidence contract.

    The result reports classical lifespan categories and independently calculated
    activation layers. It never asserts a date of death or emits a risk percentage.
    """

    def __init__(
        self,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any],
        subject: str = "self",
        ashtakavarga_profile: str = "pvr_narasimha_rao",
    ):
        subject = str(subject or "self").strip().lower()
        if subject not in SUBJECTS:
            raise ValueError("subject must be self, mother, or father")
        self.birth = dict(birth_data)
        self.chart = chart_data
        self.planets = chart_data.get("planets", {})
        self.subject_key = subject
        self.subject = dict(SUBJECTS[subject])
        self.native_asc_sign = int(chart_data.get("ascendant", 0) / 30) % 12
        self.asc_sign = (self.native_asc_sign + self.subject["offset"]) % 12
        self.divisional = DivisionalChartCalculator(chart_data)
        self.d3 = self.divisional.calculate_divisional_chart(3).get("divisional_chart", {})
        self.d9 = self.divisional.calculate_divisional_chart(9).get("divisional_chart", {})
        self.d12 = self.divisional.calculate_divisional_chart(12).get("divisional_chart", {})
        self.ashtakavarga = AshtakavargaCalculator(
            self.birth,
            self.chart,
            reduction_profile=ashtakavarga_profile,
        )
        self._shadbala_cache: Optional[Dict[str, Any]] = None
        self._hora_lagna_cache: Optional[Dict[str, Any]] = None
        self.sensitive = self._sensitive_points()

    def calculate(self, *, as_of: Optional[datetime] = None, horizon_years: int = 12) -> Dict[str, Any]:
        as_of = as_of or datetime.now()
        pillars, compartment = self._pillars_and_compartment(as_of)
        safeguards = self._arishta_bhanga_evidence()
        marakas = self._rank_marakas()
        windows = self._activation_windows(compartment, safeguards, as_of, horizon_years)
        current = self._current_activation(windows, as_of)
        primary = marakas[0] if marakas else {}
        return {
            "schema_version": "longevity.v2",
            "rule_registry_version": "longevity.rules.v1",
            "calculated_at": as_of.isoformat(timespec="seconds"),
            "calculation_convention": {
                "ashtakavarga_profile": self.ashtakavarga.reduction_profile,
                "label": self.ashtakavarga.ekadhipatya_profile["label"],
                "source": self.ashtakavarga.ekadhipatya_profile["source"],
                "source_url": self.ashtakavarga.ekadhipatya_profile["source_url"],
                "mixed_higher_empty_rule": self.ashtakavarga.ekadhipatya_profile["mixed_higher_empty_rule"],
                "count_ascendant_as_occupant": self.ashtakavarga.ekadhipatya_profile["count_ascendant_as_occupant"],
                "scope": "Changes Ekadhipatya Shodhana and Shodhya-Pinda-derived timing only; raw BAV, SAV and Kakshya geometry are unchanged.",
            },
            "subject": {
                "key": self.subject_key,
                "label": self.subject["label"],
                "derived_house": self.subject["derived_house"],
                "derived_sign": SIGN_NAMES[self.asc_sign],
                "natural_karaka": self.subject["karaka"],
                "source": "native_chart" if self.subject_key != "self" else "birth_chart",
            },
            "verdict": {
                "compartment": compartment,
                "primary_threat": {
                    "planet": primary.get("planet"),
                    "classical_factor_count": primary.get("classical_factor_count", 0),
                    "protective_factor_count": primary.get("protective_factor_count", 0),
                    "prominence": primary.get("prominence", "No listed classical linkage"),
                    "summary": primary.get("summary", "No dominant crisis factor"),
                    "factors": primary.get("factors", []),
                    "protective_factors": primary.get("protective_factors", []),
                },
                "current_activation": current,
                # Compatibility alias. This object intentionally has no numerical score.
                "current_vulnerability": current,
            },
            "pillars": pillars,
            "safeguards": safeguards,
            "maraka_dossier": {
                "badhaka_house": self.sensitive["badhaka"]["house"],
                "ranked_planets": marakas,
                "sensitive_points": self.sensitive,
            },
            "activation_windows": windows,
            # Compatibility alias for v1 clients. Entries use the v2 activation contract.
            "crisis_windows": windows,
            "chat_context": {
                "context_type": "deterministic_longevity_evidence",
                "schema_version": "longevity.v2",
                "subject": self.subject_key,
                "ashtakavarga_profile": self.ashtakavarga.reduction_profile,
                "verdict": compartment,
                "top_crisis_planets": [item["planet"] for item in marakas[:3]],
                "sensitive_points": self.sensitive,
                "classical_modifications": compartment.get("classical_modifications"),
                "safeguards": safeguards,
                "activation_windows": windows[:6],
                "guardrail": "Describe the supplied classical activations and their limitations; never predict a death date or convert them into a probability or medical claim.",
            },
            "disclaimer": "Astrological longevity categories and activation layers are traditional interpretive tools, not medical facts, probabilities, or a prediction of death. Parent views are derived from the native's chart and do not replace a parent's own birth chart. Seek qualified medical care for health concerns.",
        }

    def _pillars_and_compartment(self, as_of: datetime) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        lagna_lord = SIGN_LORDS[self.asc_sign]
        eighth_sign = (self.asc_sign + 7) % 12
        eighth_lord = SIGN_LORDS[eighth_sign]
        pair_eighth_lord = (
            SIGN_LORDS[(self.asc_sign + 2) % 12]
            if self.subject_key == "self" and eighth_lord == lagna_lord
            else eighth_lord
        )
        karaka = self.subject["karaka"]
        karaka_sign = int(self.planets[karaka]["sign"])
        saturn_sign = int(self.planets["Saturn"]["sign"])
        if self.subject_key == "self":
            hora_lagna = self._hora_lagna()
            third_reference_sign = hora_lagna["sign_id"]
            pairs = [
                ("Lagnesha + 8th Lord" if pair_eighth_lord == eighth_lord else "Lagnesha + 8th-from-8th Lord", int(self.planets[lagna_lord]["sign"]), int(self.planets[pair_eighth_lord]["sign"])),
                ("Moon + Saturn", karaka_sign, saturn_sign),
                ("Lagna + Hora Lagna", self.asc_sign, third_reference_sign),
            ]
        else:
            d12_asc = int(self.d12.get("ascendant", 0) / 30) % 12
            d12_parent_sign = (d12_asc + self.subject["offset"]) % 12
            pairs = [
                ("Derived Lagnesha + 8th Lord", int(self.planets[lagna_lord]["sign"]), int(self.planets[eighth_lord]["sign"])),
                (f"{karaka} + Saturn", karaka_sign, saturn_sign),
                (f"Derived {self.subject['label']} Lagna + D12", self.asc_sign, d12_parent_sign),
            ]
        pair_rows = []
        votes: List[str] = []
        for label, left, right in pairs:
            category = _pair_category(left, right)
            votes.append(category)
            pair_rows.append({
                "label": label,
                "left": {"sign": SIGN_NAMES[left], "nature": _nature(left)},
                "right": {"sign": SIGN_NAMES[right], "nature": _nature(right)},
                "verdict": category,
            })
        if self.subject_key == "self":
            if pair_eighth_lord != eighth_lord:
                pair_rows[0]["right"]["derivation"] = (
                    f"{lagna_lord} rules both Lagna and the eighth; {pair_eighth_lord}, lord of the eighth from the eighth, is used as the second member"
                )
            pair_rows[2]["right"].update({
                "longitude": round(hora_lagna["longitude"], 6),
                "derivation": hora_lagna["derivation"],
                "sunrise": hora_lagna["sunrise"],
            })
        counts = {category: votes.count(category) for category in AYU_RANGES}
        majority = max(counts, key=counts.get)
        selection_rule = "Jaimini 2.1.7: agreement of at least two pairs"
        if self.subject_key == "self" and self._subject_house("Moon") in {1, 7}:
            majority = votes[1]
            selection_rule = "Jaimini 2.1.9: Moon in Lagna or seventh gives precedence to the Moon–Saturn pair"
        elif max(counts.values()) == 1:
            majority = votes[2]
            selection_rule = "Jaimini 2.1.8: all three differ, so Lagna–Hora Lagna prevails"

        strength = self._relative_strength(lagna_lord, pair_eighth_lord)
        modification = self._jaimini_kakshya_modification(majority, pair_rows)
        modification, age_validation = self._reconcile_with_attained_age(modification, as_of)
        final_name = modification["final_compartment"]
        base = dict(AYU_RANGES[final_name])
        base.update({
            "pair_majority": majority,
            "agreement": f"{counts[majority]} of 3 pairs",
            "selection_rule": selection_rule,
            "adjustment": modification["summary"],
            "classical_modifications": modification,
            "age_validation": age_validation,
            "confidence": "Moderate" if max(counts.values()) == 1 or age_validation["reconciled"] else "High",
            "derived_from_native": self.subject_key != "self",
        })
        if self.subject_key != "self":
            base.update({
                "classical_category": final_name,
                "classical_range": AYU_RANGES[final_name]["range"],
                "label": PARENT_SUPPORT_LABELS[final_name],
                "range": None,
                "is_direct_lifespan_estimate": False,
                "interpretation": f"Secondary {self.subject['label'].lower()} vitality evidence derived from the native's house {self.subject['derived_house']} and D12. It does not calculate the parent's age or lifespan; the parent's own birth chart is required for direct Ayurdaya.",
            })

        sav = self.ashtakavarga.calculate_sarvashtakavarga().get("sarvashtakavarga", {})
        eighth_bindus = int(sav.get(eighth_sign, sav.get(str(eighth_sign), 0)) or 0)
        d12_confirmation = self.sensitive.get("d12_confirmation")
        pillars = [
            {
                "id": "jaimini",
                "title": "Jaimini 3-Pairs" if self.subject_key == "self" else f"Derived {self.subject['label']} 3-Pairs",
                "verdict": final_name if self.subject_key == "self" else PARENT_SUPPORT_LABELS[final_name],
                "detail": f"Base selection: {majority}; {selection_rule}; final compartment: {final_name}" if self.subject_key == "self" else f"Technical three-pair category: {final_name}. Displayed only as {PARENT_SUPPORT_LABELS[final_name].lower()}; this is not the parent's lifespan compartment.",
                "pairs": pair_rows,
                "modifications": modification,
            },
            {"id": "parashari", "title": "Parashari Strength", "verdict": strength["verdict"], "detail": strength["detail"], "metrics": strength},
            {
                "id": "ashtakavarga" if self.subject_key == "self" else "d12",
                "title": "Ashtakavarga · 8th-house support (SAV)" if self.subject_key == "self" else "D12 Parental Confirmation",
                "verdict": ("Above-average support" if eighth_bindus >= 28 else "Near-average support" if eighth_bindus >= 24 else "Below-average support") if self.subject_key == "self" else d12_confirmation["verdict"],
                "detail": (f"The 8th-house sign has {eighth_bindus} Sarvashtakavarga bindus versus the standard per-sign reference of approximately 28. This is a secondary resilience indicator, not a lifespan in years, and it does not change the Ayurdaya compartment.") if self.subject_key == "self" else d12_confirmation["detail"],
                "metrics": ({
                    "eighth_house_sav_bindus": eighth_bindus,
                    "standard_per_sign_reference": 28,
                    "difference_from_reference": eighth_bindus - 28,
                    "effect_on_lifespan_compartment": "None — supporting evidence only",
                } if self.subject_key == "self" else {
                    "eighth_house_bindus": eighth_bindus,
                    "average_reference": 28,
                    "d12_parent_lagna": d12_confirmation["parent_lagna"],
                    "d12_parent_eighth": d12_confirmation["parent_eighth"],
                    "mitigated": d12_confirmation["mitigated"],
                }),
            },
        ]
        return pillars, base

    def _reconcile_with_attained_age(
        self,
        modification: Dict[str, Any],
        as_of: datetime,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Reject a lifespan band that is already disproved by the native's attained age.

        This is an observational consistency check, not a new Ayurdaya rule. The
        engine retains the originally calculated category and convention in the
        audit payload while preventing an impossible historical band from being
        presented as the current verdict.
        """
        result = {**modification, "rules": [dict(rule) for rule in modification.get("rules", [])]}
        calculated = result["final_compartment"]
        validation = {
            "applicable": self.subject_key == "self",
            "reconciled": False,
            "calculated_compartment": calculated,
            "final_compartment": calculated,
            "completed_age": None,
            "running_age": None,
            "reason": "Parent age is not inferred from a derived native-chart view" if self.subject_key != "self" else "Calculated band is consistent with attained age",
        }
        if self.subject_key != "self":
            return result, validation

        try:
            birth_date = datetime.strptime(str(self.birth.get("date", ""))[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            validation["applicable"] = False
            validation["reason"] = "Birth date unavailable for attained-age validation"
            return result, validation

        as_of_date = as_of.date()
        completed_age = as_of_date.year - birth_date.year - (
            (as_of_date.month, as_of_date.day) < (birth_date.month, birth_date.day)
        )
        if completed_age < 0:
            validation["applicable"] = False
            validation["reason"] = "Birth date is after the calculation date"
            return result, validation

        validation.update({"completed_age": completed_age, "running_age": completed_age + 1})
        calculated_max = AYU_MAX_AGES[calculated]
        if calculated_max is None or completed_age <= calculated_max:
            return result, validation

        base_compartment = result.get("base_compartment", calculated)
        base_max = AYU_MAX_AGES[base_compartment]
        if base_max is None or completed_age <= base_max:
            reconciled = base_compartment
            reason = (
                f"The {calculated} adjustment is contradicted by attained age {completed_age}; "
                f"the unreduced {base_compartment} majority is retained"
            )
        else:
            reconciled = next(
                name for name in ("Alpayu", "Madhyayu", "Purnayu")
                if AYU_MAX_AGES[name] is None or completed_age <= AYU_MAX_AGES[name]
            )
            reason = (
                f"The calculated {calculated} band is contradicted by attained age {completed_age}; "
                f"{reconciled} is the minimum observationally possible compartment"
            )

        classical_net_shift = result.get("net_shift", 0)
        for rule in result["rules"]:
            if rule.get("applied") and rule.get("effect") in {"harana", "hrasa"}:
                rule["used_in_final_verdict"] = False
                rule["validation_status"] = "contradicted_by_attained_age"
                rule["calculated_effect"] = f"{base_compartment} → {calculated}"
                rule["final_verdict_effect"] = f"Excluded; final compartment remains {reconciled}"
                rule["status_explanation"] = (
                    f"This classical rule triggered and calculated {base_compartment} → {calculated}. "
                    f"It is not used in the final verdict because the resulting band ends at age "
                    f"{AYU_MAX_AGES[calculated]}, while the native has already completed {completed_age} years."
                )

        result.update({
            "calculated_final_compartment": calculated,
            "final_compartment": reconciled,
            "classical_net_shift": classical_net_shift,
            "net_shift": AYU_RANGES[reconciled]["tier"] - AYU_RANGES[base_compartment]["tier"],
            "summary": reason,
        })
        validation.update({
            "reconciled": True,
            "final_compartment": reconciled,
            "reason": reason,
        })
        return result, validation

    def _relative_strength(self, lagna_lord: str, eighth_lord: str) -> Dict[str, Any]:
        shadbala = self._get_shadbala()
        lagna_data = self.planets.get(lagna_lord, {})
        eighth_data = self.planets.get(eighth_lord, {})
        lagna_rupas = float(shadbala.get(lagna_lord, {}).get("total_rupas", 0) or 0)
        eighth_rupas = float(shadbala.get(eighth_lord, {}).get("total_rupas", 0) or 0)
        lagna_house = self._subject_house(lagna_lord)
        eighth_house = self._subject_house(eighth_lord)
        lagna_sign = int(lagna_data.get("sign", 0))
        eighth_sign = int(eighth_data.get("sign", 0))
        lagna_meets_shadbala = bool(lagna_rupas and lagna_rupas >= SHADBALA_REQUIRED.get(lagna_lord, 0))
        eighth_meets_shadbala = bool(eighth_rupas and eighth_rupas >= SHADBALA_REQUIRED.get(eighth_lord, 0))
        lagna_strong = lagna_sign == EXALTATION.get(lagna_lord) or lagna_sign in OWN_SIGNS.get(lagna_lord, set()) or lagna_meets_shadbala
        eighth_weak = eighth_sign == DEBILITATION.get(eighth_lord) or (bool(eighth_rupas) and not eighth_meets_shadbala)
        afflicted_lagna = self._house_has_malefic(1) and self._house_has_malefic(8) and not self._jupiter_protects_house(1) and not self._jupiter_protects_house(8)
        severe_stress = lagna_sign == DEBILITATION.get(lagna_lord) and lagna_house in {6, 8, 12} and afflicted_lagna
        vitality_support = lagna_strong and lagna_house in {1, 4, 5, 7, 9, 10}
        verdict = "Strong vitality" if vitality_support else "Vitality under pressure" if severe_stress else "Balanced vitality"
        return {
            "verdict": verdict,
            "detail": f"{lagna_lord} in house {lagna_house} is weighed against {eighth_lord} in house {eighth_house}",
            "lagna_lord": lagna_lord,
            "eighth_lord": eighth_lord,
            "lagna_lord_house": lagna_house,
            "eighth_lord_house": eighth_house,
            "lagna_lord_shadbala_rupas": round(lagna_rupas, 2) if lagna_rupas else None,
            "eighth_lord_shadbala_rupas": round(eighth_rupas, 2) if eighth_rupas else None,
            "lagna_lord_meets_required_shadbala": lagna_meets_shadbala,
            "eighth_lord_meets_required_shadbala": eighth_meets_shadbala,
            "eighth_lord_weak_evidence": eighth_weak,
            "tier_offset": 0,
            "used_for_compartment_change": False,
            "afflicted_lagna_and_eighth": afflicted_lagna,
        }

    def _hora_lagna(self) -> Dict[str, Any]:
        """BPHS Ch. 5.4–5: Sun at sunrise + one sign per 2½ elapsed ghatis."""
        if self._hora_lagna_cache is not None:
            return self._hora_lagna_cache
        date_text = str(self.birth.get("date", ""))[:10]
        time_text = str(self.birth.get("time", "12:00:00"))
        time_parts = time_text.split(":")
        birth_time = datetime.strptime(
            f"{date_text} {int(time_parts[0]):02d}:{int(time_parts[1]):02d}:{int(float(time_parts[2])) if len(time_parts) > 2 else 0:02d}",
            "%Y-%m-%d %H:%M:%S",
        )
        latitude = float(self.birth["latitude"])
        longitude = float(self.birth["longitude"])
        timezone = self.birth.get("timezone")
        reference_date = birth_time.date()
        with _SWISSEPH_CHART_LOCK:
            panchang = PanchangCalculator()
            timings = panchang.get_local_sunrise_sunset(reference_date.isoformat(), latitude, longitude, timezone)
            sunrise = datetime.fromisoformat(timings["sunrise"])
            if birth_time < sunrise:
                reference_date -= timedelta(days=1)
                timings = panchang.get_local_sunrise_sunset(reference_date.isoformat(), latitude, longitude, timezone)
                sunrise = datetime.fromisoformat(timings["sunrise"])
            sunrise_packet = panchang.calculate_panchang(reference_date.isoformat(), latitude, longitude, timezone, reference="sunrise")
            sunrise_jd = float(sunrise_packet["reference_jd"])
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            sunrise_sun = swe.calc_ut(sunrise_jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360
        elapsed_hours = (birth_time - sunrise).total_seconds() / 3600.0
        elapsed_ghatis = elapsed_hours * 2.5
        elapsed_signs = elapsed_ghatis / 2.5
        hora_longitude = (sunrise_sun + elapsed_signs * 30.0) % 360
        self._hora_lagna_cache = {
            "sign_id": int(hora_longitude / 30),
            "longitude": hora_longitude,
            "sunrise_sun_longitude": sunrise_sun,
            "elapsed_ghatis": elapsed_ghatis,
            "sunrise": sunrise.isoformat(),
            "derivation": "BPHS Ch. 5.4–5: Sun longitude at local sunrise + elapsed ghatis ÷ 2.5 signs",
        }
        return self._hora_lagna_cache

    def _get_shadbala(self) -> Dict[str, Any]:
        if self._shadbala_cache is None:
            try:
                self._shadbala_cache = ShadbalaCalculator(self.chart, self.birth).calculate_shadbala()
            except Exception:
                self._shadbala_cache = {}
        return self._shadbala_cache

    @staticmethod
    def _jaimini_sign_aspects(source: int, target: int) -> bool:
        """Jaimini rashi drishti: movable→fixed, fixed→movable, dual→dual."""
        source, target = int(source) % 12, int(target) % 12
        if source == target:
            return False
        source_nature, target_nature = _nature(source), _nature(target)
        if source_nature == "Movable" and target_nature == "Fixed":
            return target != (source + 1) % 12
        if source_nature == "Fixed" and target_nature == "Movable":
            return target != (source - 1) % 12
        return source_nature == target_nature == "Dual"

    def _paksha(self) -> str:
        elongation = (float(self.planets["Moon"]["longitude"]) - float(self.planets["Sun"]["longitude"])) % 360
        return "shukla" if 0 < elongation <= 180 else "krishna"

    def _natural_malefics(self) -> set[str]:
        malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
        if self._paksha() == "krishna":
            malefics.add("Moon")
        mercury_sign = int(self.planets.get("Mercury", {}).get("sign", -1))
        if mercury_sign >= 0 and any(int(self.planets.get(p, {}).get("sign", -2)) == mercury_sign for p in malefics):
            malefics.add("Mercury")
        return malefics

    def _jaimini_influences(self, target_planet: str) -> Dict[str, List[str]]:
        target_sign = int(self.planets[target_planet]["sign"])
        malefics = self._natural_malefics()
        influencing: List[str] = []
        for planet, data in self.planets.items():
            if planet == target_planet or planet not in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}:
                continue
            source_sign = int(data.get("sign", -1))
            if source_sign == target_sign or self._jaimini_sign_aspects(source_sign, target_sign):
                influencing.append(planet)
        return {
            "malefic": [p for p in influencing if p in malefics],
            "benefic": [p for p in influencing if p not in malefics],
        }

    def _jaimini_kakshya_modification(self, majority: str, pair_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply only Upadesha Sutras 2.1.10–14 as discrete compartment shifts."""
        if self.subject_key != "self":
            return {
                "source": "Jaimini Upadesha Sutras 2.1.10–14",
                "convention": "Not extended to a parent derived-lagna proxy",
                "base_compartment": majority,
                "final_compartment": majority,
                "net_shift": 0,
                "summary": "No Kakshya change on a derived parent view",
                "rules": [],
            }

        tier = AYU_RANGES[majority]["tier"]
        rules: List[Dict[str, Any]] = []
        saturn_sign = int(self.planets["Saturn"]["sign"])
        saturn_determines = len(pair_rows) > 1 and pair_rows[1]["verdict"] == majority
        saturn_influences = self._jaimini_influences("Saturn")
        saturn_dignity_exception = saturn_sign in OWN_SIGNS["Saturn"] or saturn_sign == EXALTATION["Saturn"]
        saturn_malefic_condition = bool(saturn_influences["malefic"])
        saturn_applies = saturn_determines and not saturn_dignity_exception and saturn_malefic_condition and tier > 0
        if saturn_applies:
            tier -= 1
        rules.append({
            "id": "jaimini_2_1_10_13_saturn_hrasa",
            "effect": "harana",
            "applied": saturn_applies,
            "used_in_final_verdict": saturn_applies,
            "validation_status": "accepted" if saturn_applies else "not_triggered",
            "determinant": saturn_determines,
            "exception": "own_or_exalted" if saturn_dignity_exception else None,
            "evidence": f"Saturn in {SIGN_NAMES[saturn_sign]}; benefic influences: {', '.join(saturn_influences['benefic']) or 'none'}; malefic influences: {', '.join(saturn_influences['malefic']) or 'none'}",
            "requirement": "Under the selected Rath reading of Sutras 2.1.10–13, Saturn must determine the selected compartment, receive malefic influence, and be neither in its own nor exaltation sign",
            "status_explanation": (
                f"Applied because the Moon–Saturn pair determines {majority}, Saturn receives malefic influence, and it is neither in its own nor exaltation sign."
                if saturn_applies else
                "Not applied because Saturn does not determine the selected compartment, lacks the selected Sutra 2.1.13 malefic-influence condition, is own/exalted, or the result is already at the lowest tier."
            ),
            "interpretive_profile": "Sanjay Rath: Sutra 2.1.13 requires malefic influence; other translations reverse this condition, so the profile is explicit",
        })

        jupiter_house = self._subject_house("Jupiter")
        jupiter_influences = self._jaimini_influences("Jupiter")
        jupiter_unaffiliated = not jupiter_influences["benefic"] and not jupiter_influences["malefic"]
        jupiter_qualifies = jupiter_house in {1, 7} and jupiter_unaffiliated
        jupiter_applies = jupiter_qualifies and tier < 2
        if jupiter_applies:
            tier += 1
        rules.append({
            "id": "jaimini_2_1_14_jupiter_vriddhi",
            "effect": "vriddhi",
            "applied": jupiter_applies,
            "used_in_final_verdict": jupiter_applies,
            "validation_status": "accepted" if jupiter_applies else "not_triggered",
            "qualified": jupiter_qualifies,
            "unaffiliated": jupiter_unaffiliated,
            "ceiling_reached": jupiter_qualifies and tier == 2 and not jupiter_applies,
            "evidence": f"Jupiter in house {jupiter_house}; benefic influences: {', '.join(jupiter_influences['benefic']) or 'none'}; malefic influences: {', '.join(jupiter_influences['malefic']) or 'none'}",
            "requirement": "Jaimini 2.1.14: Jupiter must occupy the 1st or 7th and be unaffiliated under the selected translation",
            "status_explanation": (
                f"Applied because Jupiter is in house {jupiter_house} without association or Jaimini sign-aspect influence from another graha."
                if jupiter_applies else
                f"Not applied because Jupiter is in house {jupiter_house}, benefic influences are {', '.join(jupiter_influences['benefic']) or 'none'}, and malefic influences are {', '.join(jupiter_influences['malefic']) or 'none'}; house and unaffiliated conditions must both be satisfied."
            ),
        })
        final_name = ["Alpayu", "Madhyayu", "Purnayu"][tier]
        net_shift = tier - AYU_RANGES[majority]["tier"]
        summary = "Jaimini Kakshya Vriddhi applied" if net_shift > 0 else "Jaimini Kakshya Hrasa applied" if net_shift < 0 else "No net Jaimini Kakshya change"
        return {
            "source": "Jaimini Upadesha Sutras 2.1.10–14",
            "convention": "Saturn is determinant only when the Moon–Saturn pair agrees with the selected three-pair result; Sutras 12–13 exceptions are honored",
            "base_compartment": majority,
            "final_compartment": final_name,
            "net_shift": net_shift,
            "summary": summary,
            "rules": rules,
        }

    def _house_has_malefic(self, house: int) -> bool:
        return any(self._subject_house(planet) == house for planet in ("Mars", "Saturn", "Rahu", "Ketu"))

    def _subject_house(self, planet: str) -> int:
        sign = int(self.planets.get(planet, {}).get("sign", 0))
        return _house_from_sign(sign, self.asc_sign)

    def _native_house(self, planet: str) -> int:
        sign = int(self.planets.get(planet, {}).get("sign", 0))
        return _house_from_sign(sign, self.native_asc_sign)

    def _native_house_for_subject_house(self, house: int) -> int:
        return ((self.subject["derived_house"] - 1 + house - 1) % 12) + 1

    def _jupiter_protects_house(self, house: int) -> bool:
        target_sign = (self.asc_sign + house - 1) % 12
        jupiter_sign = int(self.planets.get("Jupiter", {}).get("sign", -1))
        return ((target_sign - jupiter_sign) % 12) in {0, 4, 6, 8}

    def _parashari_influences_sign(self, target_sign: int) -> Dict[str, List[str]]:
        malefics = self._natural_malefics()
        influencing: List[str] = []
        for planet, offsets in PARASHARI_ASPECTS.items():
            source_sign = int(self.planets.get(planet, {}).get("sign", -1))
            if source_sign < 0:
                continue
            if source_sign == target_sign or ((int(target_sign) - source_sign) % 12) in offsets:
                influencing.append(planet)
        for node in ("Rahu", "Ketu"):
            if int(self.planets.get(node, {}).get("sign", -1)) == int(target_sign):
                influencing.append(node)
        return {
            "malefic": [p for p in influencing if p in malefics],
            "benefic": [p for p in influencing if p not in malefics],
        }

    def _planet_is_strong(self, planet: str) -> Dict[str, Any]:
        sign = int(self.planets.get(planet, {}).get("sign", -1))
        rupas = float(self._get_shadbala().get(planet, {}).get("total_rupas", 0) or 0)
        required = SHADBALA_REQUIRED.get(planet)
        dignity = "exalted" if sign == EXALTATION.get(planet) else "own_sign" if sign in OWN_SIGNS.get(planet, set()) else None
        meets_shadbala = bool(required and rupas and rupas >= required)
        return {
            "strong": bool(dignity or meets_shadbala),
            "dignity": dignity,
            "shadbala_rupas": round(rupas, 2) if rupas else None,
            "required_rupas": required,
            "meets_required_shadbala": meets_shadbala,
        }

    def _birth_day_night(self) -> Dict[str, Any]:
        try:
            date_text = str(self.birth.get("date", ""))[:10]
            time_text = str(self.birth.get("time", "12:00:00"))
            birth_time = datetime.strptime(f"{date_text} {time_text[:8]}", "%Y-%m-%d %H:%M:%S") if len(time_text.split(":")) >= 3 else datetime.strptime(f"{date_text} {time_text[:5]}", "%Y-%m-%d %H:%M")
            with _SWISSEPH_CHART_LOCK:
                timings = PanchangCalculator().get_local_sunrise_sunset(
                    date_text,
                    float(self.birth["latitude"]),
                    float(self.birth["longitude"]),
                    self.birth.get("timezone"),
                )
            sunrise = datetime.fromisoformat(timings["sunrise"])
            sunset = datetime.fromisoformat(timings["sunset"])
            is_day = sunrise <= birth_time < sunset
            return {
                "known": True,
                "period": "day" if is_day else "night",
                "sunrise": timings["sunrise"],
                "sunset": timings["sunset"],
            }
        except Exception as exc:
            return {"known": False, "period": None, "reason": str(exc)}

    def _arishta_bhanga_evidence(self) -> Dict[str, Any]:
        """Evaluate BPHS Ch. 10 antidotes without turning them into percentages."""
        if self.subject_key != "self":
            return {
                "source": "Brihat Parashara Hora Shastra, Ch. 10.2–5",
                "title": "BPHS early-life cancellation audit",
                "scope": "native_birth_chart_only",
                "applicable": False,
                "active": False,
                "summary": "Not transferred from the native to a derived parent chart",
                "interpretation": "These native early-life cancellation combinations are not inferred for a parent from the child's chart.",
                "rules": [],
            }

        rules: List[Dict[str, Any]] = []
        angular_benefics = [p for p in ("Mercury", "Jupiter", "Venus") if self._subject_house(p) in {1, 4, 7, 10}]
        angular_checks = [{
            "label": "Mercury, Jupiter or Venus occupies house 1, 4, 7 or 10",
            "passed": bool(angular_benefics),
            "detail": f"Qualifying angular benefics: {', '.join(angular_benefics) or 'none'}",
        }]
        rules.append({
            "id": "bphs_10_2_benefic_in_kendra",
            "label": "Benefic in a Kendra",
            "applied": bool(angular_benefics),
            "status": "satisfied" if angular_benefics else "not_satisfied",
            "requirement": "At least one of Mercury, Jupiter or Venus must occupy an angular house: 1, 4, 7 or 10.",
            "condition_checks": angular_checks,
            "evidence": f"Angular benefics: {', '.join(angular_benefics) or 'none'}",
        })

        jupiter_strength = self._planet_is_strong("Jupiter")
        jupiter_lagna = self._subject_house("Jupiter") == 1
        jupiter_checks = [
            {"label": "Jupiter occupies the 1st house", "passed": jupiter_lagna, "detail": f"Jupiter is in house {self._subject_house('Jupiter')}"},
            {"label": "Jupiter is strong", "passed": jupiter_strength["strong"], "detail": f"Shadbala {jupiter_strength['shadbala_rupas'] or 'unavailable'} rupas; required {jupiter_strength['required_rupas']} rupas, or qualifying own/exaltation dignity"},
        ]
        jupiter_applied = all(check["passed"] for check in jupiter_checks)
        rules.append({
            "id": "bphs_10_3_strong_jupiter_in_lagna",
            "label": "Strong Jupiter in Lagna",
            "applied": jupiter_applied,
            "status": "satisfied" if jupiter_applied else "partially_satisfied" if any(check["passed"] for check in jupiter_checks) else "not_satisfied",
            "requirement": "Jupiter must both occupy the 1st house and meet the configured strength test.",
            "condition_checks": jupiter_checks,
            "placement_present": jupiter_lagna,
            "strength": jupiter_strength,
            "evidence": f"Jupiter house {self._subject_house('Jupiter')}",
        })

        lagna_lord = SIGN_LORDS[self.asc_sign]
        lagna_lord_strength = self._planet_is_strong(lagna_lord)
        lagna_lord_angle = self._subject_house(lagna_lord) in {1, 4, 7, 10}
        lagna_lord_checks = [
            {"label": f"{lagna_lord} occupies house 1, 4, 7 or 10", "passed": lagna_lord_angle, "detail": f"{lagna_lord} is in house {self._subject_house(lagna_lord)}"},
            {"label": f"{lagna_lord} is strong", "passed": lagna_lord_strength["strong"], "detail": f"Shadbala {lagna_lord_strength['shadbala_rupas'] or 'unavailable'} rupas; required {lagna_lord_strength['required_rupas']} rupas, or qualifying own/exaltation dignity"},
        ]
        lagna_lord_applied = all(check["passed"] for check in lagna_lord_checks)
        rules.append({
            "id": "bphs_10_4_strong_lagna_lord_in_kendra",
            "label": "Strong Lagna lord in a Kendra",
            "applied": lagna_lord_applied,
            "status": "satisfied" if lagna_lord_applied else "partially_satisfied" if any(check["passed"] for check in lagna_lord_checks) else "not_satisfied",
            "requirement": f"The Lagna lord {lagna_lord} must both occupy house 1, 4, 7 or 10 and meet the configured strength test.",
            "condition_checks": lagna_lord_checks,
            "planet": lagna_lord,
            "placement_present": lagna_lord_angle,
            "strength": lagna_lord_strength,
            "evidence": f"{lagna_lord} in house {self._subject_house(lagna_lord)}",
        })

        day_night = self._birth_day_night()
        lagna_influences = self._parashari_influences_sign(self.asc_sign)
        paksha = self._paksha()
        shukla_night = day_night["known"] and day_night["period"] == "night" and paksha == "shukla"
        krishna_day = day_night["known"] and day_night["period"] == "day" and paksha == "krishna"
        paksha_time_match = shukla_night or krishna_day
        required_aspect = "benefic" if shukla_night else "malefic" if krishna_day else None
        aspect_present = bool(lagna_influences[f"{required_aspect}"]) if required_aspect else False
        verse_five = paksha_time_match and aspect_present
        verse_five_checks = [
            {"label": "Birth is Shukla Paksha at night or Krishna Paksha during the day", "passed": paksha_time_match, "detail": f"{paksha.title()} Paksha; {day_night.get('period') or 'day/night unavailable'}"},
            {"label": f"The selected translation's required {required_aspect or 'corresponding'} influence aspects Lagna", "passed": aspect_present, "detail": f"Lagna benefics: {', '.join(lagna_influences['benefic']) or 'none'}; malefics: {', '.join(lagna_influences['malefic']) or 'none'}"},
        ]
        rules.append({
            "id": "bphs_10_5_paksha_day_night_lagna_aspect",
            "label": "Paksha, day/night and Lagna aspect",
            "applied": verse_five,
            "status": "satisfied" if verse_five else "partially_satisfied" if any(check["passed"] for check in verse_five_checks) else "not_satisfied",
            "requirement": "Under the selected BPHS translation: Shukla-night requires a benefic Lagna aspect; Krishna-day requires a malefic Lagna aspect.",
            "condition_checks": verse_five_checks,
            "paksha": paksha,
            "day_night": day_night,
            "lagna_influences": lagna_influences,
            "evidence": f"{paksha.title()} Paksha; {day_night.get('period') or 'day/night unavailable'}; Lagna benefics {', '.join(lagna_influences['benefic']) or 'none'}, malefics {', '.join(lagna_influences['malefic']) or 'none'}",
        })
        active = any(rule["applied"] for rule in rules)
        satisfied_count = sum(1 for rule in rules if rule["status"] == "satisfied")
        partial_count = sum(1 for rule in rules if rule["status"] == "partially_satisfied")
        return {
            "source": "Brihat Parashara Hora Shastra, Ch. 10.2–5",
            "title": "BPHS early-life cancellation audit",
            "scope": "balarishta_and_natal_evil_cancellation",
            "applicable": True,
            "active": active,
            "summary": f"{satisfied_count} of 4 listed combinations fully satisfied; {partial_count} partially satisfied",
            "interpretation": "This audits four BPHS combinations associated with cancellation of Balarishta or natal affliction. It is not a current health-risk score, does not mean that protection is absent, and does not prescribe a remedy.",
            "classification_policy": "Used only as early-life natal cancellation evidence. It is not converted into an invented percentage, does not change the adult Ayurdaya compartment, and is not reused as a blanket adult-period cancellation.",
            "rules": rules,
        }

    def _sensitive_points(self) -> Dict[str, Any]:
        d3_asc = int(self.d3.get("ascendant", 0) / 30) % 12
        kharesh_sign = (d3_asc + 7) % 12
        d9_planets = self.d9.get("planets", {})
        moon_64_sign = (int(d9_planets.get("Moon", {}).get("sign", 0)) + 3) % 12
        d9_asc = int(self.d9.get("ascendant", 0) / 30) % 12
        lagna_64_sign = (d9_asc + 3) % 12
        badhaka_house = 11 if self.asc_sign % 3 == 0 else 9 if self.asc_sign % 3 == 1 else 7
        badhaka_sign = (self.asc_sign + badhaka_house - 1) % 12
        derived_eighth_native_house = self._native_house_for_subject_house(8)
        a8_sign = _arudha_for_house(self.chart, derived_eighth_native_house)
        karakas = CharaKarakaCalculator(self.chart).calculate_chara_karakas().get("chara_karakas", {})
        ak = karakas.get("Atmakaraka", {}).get("planet")
        amk = karakas.get("Amatyakaraka", {}).get("planet")
        reference = amk if ak and self._subject_house(ak) == 8 else ak
        reference_sign = int(self.planets.get(reference, {}).get("sign", self.asc_sign))
        maheshwara_sign = (reference_sign + 7) % 12
        maheshwara = SIGN_LORDS[maheshwara_sign]
        second_lord = SIGN_LORDS[(self.asc_sign + 1) % 12]
        eighth_lord = SIGN_LORDS[(self.asc_sign + 7) % 12]
        rudra = max((second_lord, eighth_lord), key=lambda p: self._basic_planet_strength(p))
        timing_planet, timing_house = (
            ("Saturn", 8) if self.subject_key == "self" else
            ("Moon", 4) if self.subject_key == "mother" else
            ("Sun", 9)
        )
        shodhya_timing = self.ashtakavarga.calculate_shodhya_timing(timing_planet, timing_house)
        common = {
            "kharesh_22nd_drekkana": {"sign_id": kharesh_sign, "sign": SIGN_NAMES[kharesh_sign], "lord": SIGN_LORDS[kharesh_sign], "derivation": "8th sign from D3 ascendant"},
            "navamsha_64_moon": {"sign_id": moon_64_sign, "sign": SIGN_NAMES[moon_64_sign], "lord": SIGN_LORDS[moon_64_sign], "derivation": "4th sign from Moon in D9"},
            "navamsha_64_lagna": {"sign_id": lagna_64_sign, "sign": SIGN_NAMES[lagna_64_sign], "lord": SIGN_LORDS[lagna_64_sign], "derivation": "4th sign from Lagna in D9"},
            "badhaka": {"house": badhaka_house, "native_house": self._native_house_for_subject_house(badhaka_house), "sign_id": badhaka_sign, "sign": SIGN_NAMES[badhaka_sign], "lord": SIGN_LORDS[badhaka_sign], "derivation": f"House {badhaka_house} from derived {self.subject['label']} Lagna"},
            "mrityu_pada_a8": {"sign_id": a8_sign, "sign": SIGN_NAMES[a8_sign], "lord": SIGN_LORDS[a8_sign]},
            "maheshwara": {"planet": maheshwara, "reference_karaka": reference, "sign": SIGN_NAMES[maheshwara_sign]},
            "rudra": {"planet": rudra, "candidates": list(dict.fromkeys((second_lord, eighth_lord)))},
            "ashtakavarga_timing": {
                **shodhya_timing,
                "sign": shodhya_timing.get("rashi"),
                "derivation": f"{timing_planet} BAV house {timing_house} × {timing_planet} Shodhya Pinda",
            },
        }
        if self.subject_key == "self":
            return common

        second_sign = (self.asc_sign + 1) % 12
        third_sign = (self.asc_sign + 2) % 12
        seventh_sign = (self.asc_sign + 6) % 12
        eighth_sign = (self.asc_sign + 7) % 12
        d12_confirmation = self._d12_parent_confirmation()
        karaka = self.subject["karaka"]
        jaimini_planet = karakas.get(self.subject["jaimini_karaka"], {}).get("planet")
        try:
            sav = self.ashtakavarga.calculate_sarvashtakavarga().get("sarvashtakavarga", {})
            eighth_bindus = int(sav.get(eighth_sign, sav.get(str(eighth_sign), 0)) or 0)
        except Exception:
            eighth_bindus = 0
        common.update({
            "parental_eighth": {"native_house": derived_eighth_native_house, "derived_house": 8, "sign_id": eighth_sign, "sign": SIGN_NAMES[eighth_sign], "lord": SIGN_LORDS[eighth_sign], "sav_bindus": eighth_bindus, "derivation": f"8th from derived {self.subject['label']} Lagna"},
            "parental_third": {"native_house": self._native_house_for_subject_house(3), "derived_house": 3, "sign_id": third_sign, "sign": SIGN_NAMES[third_sign], "lord": SIGN_LORDS[third_sign], "derivation": f"3rd from derived {self.subject['label']} Lagna"},
            "derived_maraka_second": {"native_house": self._native_house_for_subject_house(2), "derived_house": 2, "sign_id": second_sign, "sign": SIGN_NAMES[second_sign], "lord": SIGN_LORDS[second_sign], "derivation": f"2nd from derived {self.subject['label']} Lagna"},
            "derived_maraka_seventh": {"native_house": self._native_house_for_subject_house(7), "derived_house": 7, "sign_id": seventh_sign, "sign": SIGN_NAMES[seventh_sign], "lord": SIGN_LORDS[seventh_sign], "derivation": f"7th from derived {self.subject['label']} Lagna"},
            "parent_karaka": {"planet": karaka, "sign_id": int(self.planets.get(karaka, {}).get("sign", 0)), "sign": SIGN_NAMES[int(self.planets.get(karaka, {}).get("sign", 0))], "native_house": self._native_house(karaka), "derived_house": self._subject_house(karaka), "jaimini_karaka": self.subject["jaimini_karaka"], "jaimini_planet": jaimini_planet, "derivation": f"Natural karaka for {self.subject['label'].lower()}"},
            "d12_confirmation": d12_confirmation,
        })
        return common

    def _d12_parent_confirmation(self) -> Dict[str, Any]:
        d12_asc = int(self.d12.get("ascendant", 0) / 30) % 12
        parent_sign = (d12_asc + self.subject["offset"]) % 12
        eighth_sign = (parent_sign + 7) % 12
        planets = self.d12.get("planets", {})
        karaka = self.subject["karaka"]

        def d12_house(planet: str) -> int:
            return _house_from_sign(int(planets.get(planet, {}).get("sign", 0)), parent_sign)

        stressed = d12_house(karaka) in {6, 8, 12} or any(d12_house(p) == 8 for p in ("Mars", "Saturn", "Rahu", "Ketu"))
        protected = False
        for planet, aspects in (("Jupiter", {0, 4, 6, 8}), ("Venus", {0, 6})):
            source = int(planets.get(planet, {}).get("sign", -99))
            if source >= 0 and any(((target - source) % 12) in aspects for target in (parent_sign, eighth_sign)):
                protected = True
        mitigated = protected and stressed
        verdict = "Protected despite stress" if mitigated else "Supportive" if protected else "Stressed" if stressed else "Neutral"
        return {
            "sign_id": eighth_sign,
            "sign": SIGN_NAMES[eighth_sign],
            "lord": SIGN_LORDS[eighth_sign],
            "parent_lagna": SIGN_NAMES[parent_sign],
            "parent_eighth": SIGN_NAMES[eighth_sign],
            "parent_lagna_lord": SIGN_LORDS[parent_sign],
            "parent_eighth_lord": SIGN_LORDS[eighth_sign],
            "karaka": karaka,
            "stressed": stressed,
            "protected": protected,
            "mitigated": mitigated,
            "verdict": verdict,
            "detail": f"D12 {self.subject['label']} Lagna is {SIGN_NAMES[parent_sign]}; its 8th is {SIGN_NAMES[eighth_sign]}. {('Benefic protection moderates the stress.' if mitigated else 'Benefic support is present.' if protected else 'Stress factors are present.' if stressed else 'No dominant D12 stress signature is present.')}",
            "derivation": f"{self.subject['derived_house']}th-house parent reference applied in D12",
        }

    def _basic_planet_strength(self, planet: str) -> int:
        data = self.planets.get(planet, {})
        sign = int(data.get("sign", 0))
        score = 0
        if sign == EXALTATION.get(planet): score += 3
        if sign in OWN_SIGNS.get(planet, set()): score += 2
        if self._subject_house(planet) in {1, 4, 7, 10}: score += 1
        return score

    def _rank_marakas(self) -> List[Dict[str, Any]]:
        second_sign, seventh_sign = (self.asc_sign + 1) % 12, (self.asc_sign + 6) % 12
        maraka_lords = {SIGN_LORDS[second_sign], SIGN_LORDS[seventh_sign]}
        if self.subject_key == "self":
            special_lords = {
                self.sensitive["kharesh_22nd_drekkana"]["lord"],
                self.sensitive["navamsha_64_moon"]["lord"],
                self.sensitive["navamsha_64_lagna"]["lord"],
            }
        else:
            special_lords = {
                self.sensitive["parental_eighth"]["lord"],
                self.sensitive["parental_third"]["lord"],
                self.sensitive["d12_confirmation"]["parent_eighth_lord"],
            }
        badhaka_lord = self.sensitive["badhaka"]["lord"]
        ranked = []
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            data = self.planets.get(planet, {})
            sign = int(data.get("sign", 0))
            house = self._subject_house(planet)
            native_house = self._native_house(planet)
            factors, protective_factors = [], []
            if planet in maraka_lords:
                factors.append(f"Rules the 2nd or 7th from {self.subject['label']} Lagna")
            if planet == badhaka_lord:
                factors.append(f"Badhakesh for house {self.sensitive['badhaka']['house']}")
            if planet in special_lords:
                factors.append("Rules a critical derived or divisional point" if self.subject_key != "self" else "Rules the 22nd Drekkana or 64th Navamsha")
            if house in {2, 7}:
                factors.append(f"Occupies derived maraka house {house} (native H{native_house})")
            associated = [p for p in maraka_lords if p != planet and int(self.planets.get(p, {}).get("sign", -1)) == sign]
            if associated:
                factors.append(f"Associated with maraka lord {', '.join(associated)}")
            saturn_sign = int(self.planets.get("Saturn", {}).get("sign", -1))
            if planet != "Saturn" and ((sign - saturn_sign) % 12) in {0, 2, 6, 9} and (planet in maraka_lords or planet == badhaka_lord):
                factors.append("Receives Saturn association")
            jupiter_sign = int(self.planets.get("Jupiter", {}).get("sign", -1))
            if planet != "Jupiter" and ((sign - jupiter_sign) % 12) in {4, 6, 8}:
                protective_factors.append("Receives Jupiter aspect")
            factor_count = len(factors)
            prominence = "Multiple classical linkages" if factor_count >= 2 else "One classical linkage" if factor_count == 1 else "No listed classical linkage"
            ranked.append({
                "planet": planet, "classical_factor_count": factor_count,
                "protective_factor_count": len(protective_factors), "prominence": prominence,
                "house": house, "native_house": native_house,
                "sign": SIGN_NAMES[sign], "longitude": _format_longitude(data),
                "factors": factors,
                "protective_factors": protective_factors,
                "summary": f"{planet} in {SIGN_NAMES[sign]} · {'derived ' if self.subject_key != 'self' else ''}house {house}{f' (native H{native_house})' if self.subject_key != 'self' else ''} · {prominence.lower()}",
            })
        return sorted(ranked, key=lambda row: (-row["classical_factor_count"], row["protective_factor_count"], row["planet"]))

    def _macro_dasha_activation(self, mahadasha: str, antardasha: str) -> Dict[str, Any]:
        if self.subject_key == "self":
            sources = {
                "2nd lord": SIGN_LORDS[(self.asc_sign + 1) % 12],
                "7th lord": SIGN_LORDS[(self.asc_sign + 6) % 12],
                "Badhaka lord": self.sensitive["badhaka"]["lord"],
                "22nd Drekkana lord": self.sensitive["kharesh_22nd_drekkana"]["lord"],
                "64th Navamsha Moon lord": self.sensitive["navamsha_64_moon"]["lord"],
                "64th Navamsha Lagna lord": self.sensitive["navamsha_64_lagna"]["lord"],
            }
        else:
            sources = {
                "derived 2nd lord": self.sensitive["derived_maraka_second"]["lord"],
                "derived 7th lord": self.sensitive["derived_maraka_seventh"]["lord"],
                "derived Badhaka lord": self.sensitive["badhaka"]["lord"],
                "derived parental 8th lord": self.sensitive["parental_eighth"]["lord"],
                "D12 parental 8th lord": self.sensitive["d12_confirmation"]["parent_eighth_lord"],
            }
        active = {label: planet for label, planet in sources.items() if planet in {mahadasha, antardasha}}
        return {
            "hit": bool(active),
            "active_lords": active,
            "evidence": [f"{planet} is active as {label}" for label, planet in active.items()],
        }

    def _activation_windows(self, compartment: Dict[str, Any], safeguards: Dict[str, Any], as_of: datetime, horizon_years: int) -> List[Dict[str, Any]]:
        end = as_of + timedelta(days=365.25 * max(1, min(horizon_years, 30)))
        try:
            dasha_rows = DashaCalculator().iter_ad_periods(self.birth, as_of, end)
        except Exception:
            dasha_rows = []
        try:
            relative_house_idx = self.subject["offset"] if self.subject_key != "self" else None
            shoola = ShoolaDashaCalculator(self.chart).calculate_shoola_dasha(self.birth, relative_house_idx=relative_house_idx).get("all_periods", [])
        except Exception:
            shoola = []
        windows: List[Dict[str, Any]] = []
        birth_date = datetime.strptime(str(self.birth["date"])[:10], "%Y-%m-%d") if self.subject_key == "self" else None
        for row in dasha_rows:
            start = datetime.strptime(row["start_date"], "%Y-%m-%d")
            finish = datetime.strptime(row["end_date"], "%Y-%m-%d")
            macro = self._macro_dasha_activation(row["mahadasha"], row["antardasha"])
            cursor = start
            while cursor <= finish:
                stamp = cursor.strftime("%Y-%m-%d")
                active_shoola = next((p for p in shoola if p["start_date"] <= stamp <= p["end_date"]), None)
                meso = self._shoola_activation(active_shoola)
                micro = self._transit_activation(cursor)
                systems = {"macro_vimshottari": macro["hit"], "meso_shoola": meso["hit"], "micro_transit_bav": micro["hit"]}
                confirmation_count = sum(1 for hit in systems.values() if hit)
                level, label = self._convergence_classification(confirmation_count)
                if birth_date is not None:
                    age = (cursor - birth_date).days / 365.2425
                    khanda_min, khanda_max = compartment["baseline_window"]
                    khanda_status = "before" if age < khanda_min else "within" if age <= khanda_max else "after"
                else:
                    age = None
                    khanda_status = "not_applicable"
                parent_d12_stress = self.subject_key == "self" or self.sensitive["d12_confirmation"]["stressed"]
                early_life_cancellation = self.subject_key == "self" and age is not None and age < 32 and safeguards.get("active", False)
                reasons = [
                    *(macro["evidence"] if macro["hit"] else []),
                    *(meso["evidence"] if meso["hit"] else []),
                    *(micro["evidence"] if micro["hit"] else []),
                ]
                notes = []
                if early_life_cancellation:
                    notes.append("BPHS Ch. 10 early-life Arishta-Bhanga condition is present; it is shown separately and does not create a numerical adjustment")
                if self.subject_key != "self":
                    notes.append(f"D12 parental stress confirmation: {'present' if parent_d12_stress else 'absent'}; the parent's own chart remains required")
                candidate = {
                    "start_date": stamp, "end_date": stamp,
                    "mahadasha": row["mahadasha"], "antardasha": row["antardasha"],
                    "dasha_period": {"start_date": row.get("ad_start", row["start_date"]), "end_date": row.get("ad_end", row["end_date"]), "boundary_type": "actual_antardasha"},
                    "shoola_sign": active_shoola.get("sign_name") if active_shoola else None,
                    "level": level, "label": label,
                    "components": {"vimshottari": bool(macro["hit"]), "shoola": bool(meso["hit"]), "transit_bav": bool(micro["hit"])},
                    "convergence": {
                        "confirmed_systems": confirmation_count,
                        "systems_considered": 3,
                        "systems": systems,
                        "classification_basis": "Descriptive count of independently calculated classical systems; not a probability, percentage, or classical numerical score",
                        "macro": macro, "meso": meso, "micro": micro,
                    },
                    "khanda_boundary": {
                        "status": khanda_status,
                        "age_at_start": round(age, 1) if age is not None else None,
                        "age_at_end": round(age, 1) if age is not None else None,
                        "baseline_window": compartment["baseline_window"] if self.subject_key == "self" else None,
                        "policy": "Khanda is contextual evidence only and is not converted into a mortality claim." if self.subject_key == "self" else "Parent age and Khanda are not calculated from the child's age; the parent's own birth chart is required.",
                    },
                    "parent_corroboration": None if self.subject_key == "self" else {
                        "d12_stress_present": parent_d12_stress,
                        "own_parent_chart_required": True,
                    },
                    "reasons": reasons,
                    "supporting_observations": [*micro.get("non_qualifying_observations", []), *notes],
                }
                if windows and self._same_activation_segment(windows[-1], candidate):
                    windows[-1]["end_date"] = stamp
                    windows[-1]["khanda_boundary"]["age_at_end"] = candidate["khanda_boundary"]["age_at_end"]
                else:
                    windows.append(candidate)
                cursor += timedelta(days=1)
        return sorted(windows, key=lambda item: item["start_date"])

    @staticmethod
    def _convergence_classification(count: int) -> Tuple[str, str]:
        return {
            0: ("none", "No listed classical activation"),
            1: ("single", "Single-system activation"),
            2: ("convergent", "Two-system convergence"),
            3: ("strong_convergence", "Three-system convergence"),
        }[max(0, min(3, int(count)))]

    @staticmethod
    def _same_activation_segment(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
        fields = ("mahadasha", "antardasha", "shoola_sign", "level", "label", "components", "reasons", "supporting_observations", "dasha_period")
        return all(left.get(field) == right.get(field) for field in fields) and left.get("khanda_boundary", {}).get("status") == right.get("khanda_boundary", {}).get("status")

    def _shoola_activation(self, period: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not period:
            return {"hit": False, "evidence": [], "supporting_influences": []}
        sign = int(period["sign_id"])
        eighth_sign = (self.asc_sign + 7) % 12
        trishoola = {(eighth_sign + offset) % 12 for offset in (0, 4, 8)}
        a8 = self.sensitive["mrityu_pada_a8"]["sign_id"]
        maheshwara = self.sensitive["maheshwara"]["planet"]
        occupied_by_maheshwara = int(self.planets.get(maheshwara, {}).get("sign", -1)) == sign
        exact_factors = []
        if sign in trishoola:
            exact_factors.append("Trishoola sign")
        if sign == a8:
            exact_factors.append("A8 sign")
        if occupied_by_maheshwara:
            exact_factors.append(f"contains Maheshwara {maheshwara}")
        malefics = [p for p in ("Mars", "Saturn", "Rahu") if ((sign - int(self.planets.get(p, {}).get("sign", -99))) % 12) in ({0, 3, 6, 7} if p == "Mars" else {0, 2, 6, 9} if p == "Saturn" else {0})]
        return {
            "hit": bool(exact_factors),
            "sign": SIGN_NAMES[sign],
            "evidence": [f"Shoola Dasha activates {SIGN_NAMES[sign]} as {factor}" for factor in exact_factors],
            "supporting_influences": malefics,
        }

    def _transit_activation(self, when: datetime) -> Dict[str, Any]:
        try:
            with _SWISSEPH_CHART_LOCK:
                swe.set_sid_mode(swe.SIDM_LAHIRI)
                jd = swe.julday(when.year, when.month, when.day, 12.0)
                flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
                saturn_longitude = swe.calc_ut(jd, swe.SATURN, flags)[0][0] % 360
                rahu_longitude = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0] % 360
                sun_longitude = swe.calc_ut(jd, swe.SUN, flags)[0][0] % 360
                saturn_sign = int(saturn_longitude / 30)
                rahu_sign = int(rahu_longitude / 30)
                sun_sign = int(sun_longitude / 30)
        except Exception:
            return {"hit": False, "primary": [], "confirmers": [], "evidence": [], "non_qualifying_observations": ["Transit calculation unavailable"]}
        primary, confirmers = [], []
        if self.subject_key == "self":
            sensitive_signs = {self.sensitive["kharesh_22nd_drekkana"]["sign_id"], self.sensitive["navamsha_64_moon"]["sign_id"], int(self.planets[SIGN_LORDS[(self.asc_sign + 7) % 12]]["sign"])}
        else:
            sensitive_signs = {self.sensitive["parental_eighth"]["sign_id"], int(self.planets[self.sensitive["parental_eighth"]["lord"]]["sign"])}
        if saturn_sign in sensitive_signs:
            primary.append(f"Saturn transits sensitive {SIGN_NAMES[saturn_sign]}")
        kakshya = self.ashtakavarga.calculate_kakshya_activation("Saturn", saturn_longitude)
        if kakshya and not kakshya["active"]:
            primary.append(f"Saturn crosses {kakshya['kakshya_ruler']} Kakshya without a Saturn-BAV bindu")
        shodhya_timing = self.sensitive.get("ashtakavarga_timing", {})
        transit_nakshatra = int(saturn_longitude / (360 / 27)) + 1
        if transit_nakshatra in shodhya_timing.get("vimshottari_group_numbers", []):
            primary.append(f"Saturn activates the {shodhya_timing.get('nakshatra')} Shodhya-Pinda nakshatra group")
        lagna_lord_sign = int(self.planets[SIGN_LORDS[self.asc_sign]]["sign"])
        moon_sign = int(self.planets["Moon"]["sign"])
        ketu_sign = (rahu_sign + 6) % 12
        if self.subject_key == "self":
            if rahu_sign in {lagna_lord_sign, moon_sign} or ketu_sign in {lagna_lord_sign, moon_sign}:
                confirmers.append("Rahu–Ketu axis crosses Moon or Lagnesha sign")
        else:
            karaka = self.subject["karaka"]
            karaka_sign = int(self.planets.get(karaka, {}).get("sign", -1))
            if saturn_sign == karaka_sign:
                primary.append(f"Saturn occupies natal {karaka} sign, the {self.subject['label'].lower()} karaka")
            if karaka_sign in {rahu_sign, ketu_sign}:
                confirmers.append(f"Nodal axis occupies natal {karaka} sign")
        trigger_roots = {self.sensitive["badhaka"]["sign_id"], (self.asc_sign + 7) % 12, self.sensitive["kharesh_22nd_drekkana"]["sign_id"]}
        trigger_trines = {((root + offset) % 12) for root in trigger_roots for offset in (0, 4, 8)}
        if sun_sign in trigger_trines:
            confirmers.append("Solar-month trigger is active")
        hit = bool(primary) and bool(confirmers)
        observations = [*primary, *confirmers]
        return {
            "hit": hit,
            "primary": primary,
            "confirmers": confirmers,
            "evidence": observations if hit else [],
            "non_qualifying_observations": [] if hit else observations,
            "saturn_sign": SIGN_NAMES[saturn_sign],
            "rahu_sign": SIGN_NAMES[rahu_sign],
            "sun_sign": SIGN_NAMES[sun_sign],
            "kakshya": kakshya,
        }

    @staticmethod
    def _current_activation(windows: Iterable[Dict[str, Any]], as_of: datetime) -> Dict[str, Any]:
        stamp = as_of.strftime("%Y-%m-%d")
        active = next((row for row in windows if row["start_date"] <= stamp <= row["end_date"]), None)
        if not active:
            return {"level": "none", "label": "No listed classical activation", "confirmed_systems": 0, "systems_considered": 3, "window": None}
        return {
            "level": active["level"], "label": active["label"],
            "confirmed_systems": active["convergence"]["confirmed_systems"],
            "systems_considered": active["convergence"]["systems_considered"],
            "window": active,
        }
