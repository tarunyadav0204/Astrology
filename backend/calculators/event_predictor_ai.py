from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Awaitable, Optional
from types import SimpleNamespace
import calendar
import json
import asyncio
import os
import time
import re
import google.generativeai as genai  # type: ignore[import-not-found]
from google.generativeai import caching as genai_caching  # type: ignore[import-not-found]
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.event_timeline_context_prune import prune_for_event_timeline
from ai.llm_roundtrip_log import log_llm_roundtrip
from utils.admin_settings import is_debug_logging_enabled

# Shared instruction block for Event Timeline (yearly + monthly deep): disambiguate which life channel
# a house activation targets (any house H), using karaka + afflicter flavour + topic-appropriate vargas.
BHAVA_MANIFESTATION_DISAMBIGUATION_BLOCK = """
### BHAVA-TO-MANIFESTATION DISAMBIGUATION (MANDATORY FOR ANY HOUSE YOU TREAT AS PRIMARY)

A single house has **many** classical significations (bhava themes). Activation or affliction of that house is a **general** signal. Do **not** treat the house number alone as sufficient to name the **exact life channel** (which person, asset, organ, or transaction) when several channels share that house.

Whenever a prediction's main trigger involves a **primary house H** (any house 1–12), you MUST **disambiguate** before stating a specific concrete event. Use this **fixed pipeline** every time.

**STEP 1 — Enumerate threads under house H (brief, in your reasoning)**  
List the **distinct** classical threads that house H can represent in context (people, places, things, abstract states). Do not collapse them into one vague phrase.

**STEP 2 — Map threads to natural karakas (standard jataka significators)**  
For each thread you might mention, name the **natural planet(s)** that classically govern that thread (e.g. Moon for mother/mind/fluids; Venus for spouse, vehicles, comforts; Mars for siblings, courage, disputes, heat; Saturn for chronicity, servants, structure; Sun for father/authority; Mercury for speech/commerce; Jupiter for children, wisdom, guru; etc.).  
**Rule:** The thread whose karaka is **most clearly** stressed or woven into the same trigger chain (conjunction, aspect, lordship bridge, dasha link) gets **higher weight** than threads whose karakas are clean and uninvolved.

**STEP 3 — Read the afflicting or activating planet by flavour**  
Use the **nature** of the planet driving the pattern (Mars: sudden, heat, cuts, conflict; Saturn: delay, decay, chronic; Rahu/Ketu: sudden, odd, hidden; etc.) to **colour** the scenario—not to **replace** Step 2.

**STEP 4 — Varga confirmation (topic-appropriate; only when D1 is ambiguous or you need specificity)**  
Do not use one fixed divisional for all houses. Pick divisional(s) that match the **life department** you are about to assert, when present in context:

- Parents / parent-line → favour **D12**
- Property / land / home as fixed asset → favour **D4**
- Marriage / partnership essence → favour **D9**
- Career / status → favour **D10**
- Progeny → favour **D7**
- Vehicles / comforts / sukha (when that is the claim) → favour **D16**
- Health / disease tendency (when that is the claim) → favour **D30**

If the relevant varga is missing from context, state that and **reduce specificity**.

**STEP 5 — Synchronization rule (non-negotiable)**  
You may state **one primary concrete channel** (specific person, asset, organ, etc.) **only if**:

1. House H is credibly activated or afflicted in D1 for that prediction, **and**
2. The **natural karaka** for that channel is credibly involved in the same logic chain, **and**
3. Where data exists, a **topic-appropriate varga** from Step 4 **does not contradict** that channel.

If any of these fail, you MUST either give **ranked possibilities** (most likely / also possible / less likely unless …) or keep the outcome at the **correct bhava level** (accurate but not over-specific).

**STEP 6 — Mandatory one-line tag in trigger_logic (or activation_reasoning / equivalent)**  
Append:

`[BHAVA-DISAMBIG: H={house_number} | Threads={short list} | Karaka-weight={which planets favoured and why in one clause} | Afflicter-flavour={planet} | Varga={which checked + outcome} → Primary={specific_channel OR general_OR_ranked}]`

Use placeholder labels literally as written so the structure is obvious; fill with real values for that event.

**FORBIDDEN**  
- Claiming a narrow concrete outcome from **house H alone** without karaka alignment.  
- Listing every signification of H as an undifferentiated "could be A or B or C" **without** completing Step 6.  
- Using a **single** divisional chart for all topics regardless of life department.

**NOTE:** Any single house (e.g. 4th: mother vs home vs vehicle) is only an **example** of this rule. Apply the **same pipeline** for **whichever house** is primary for that event.
"""


class EventPredictor:
    """
    AI-Powered Event Predictor using Grand Synthesis method.
    Implements "Natal-Transit Resonance" logic with Age-Based Context (Desha Kala Patra).
    """
    
    def __init__(self, chart_calculator, real_transit_calculator, dasha_calculator, ashtakavarga_calculator_cls):
        self.chart_calc = chart_calculator
        self.transit_calc = real_transit_calculator
        self.dasha_calc = dasha_calculator
        self.ashtakavarga_cls = ashtakavarga_calculator_cls
        self.model = None
        self.model_name = None
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            try:
                from utils.admin_settings import get_event_timeline_model, GEMINI_MODEL_OPTIONS
                name = get_event_timeline_model()
                fallbacks = [m[0] for m in GEMINI_MODEL_OPTIONS if m[0] != name]
                for model_name in [name] + fallbacks:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        self.model_name = model_name
                        print(f"✅ EventPredictor using {model_name}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

    @staticmethod
    def _env_bool(name: str, default: bool = False) -> bool:
        raw = (os.getenv(name) or "").strip().lower()
        if not raw:
            return default
        return raw in ("1", "true", "yes", "on")

    @staticmethod
    def _safe_int_env(name: str, default: int) -> int:
        raw = (os.getenv(name) or "").strip()
        try:
            return int(raw) if raw else default
        except Exception:
            return default

    @staticmethod
    def _month_ids_for_quarter(quarter_idx: int) -> List[int]:
        start = (quarter_idx - 1) * 3 + 1
        return [start, start + 1, start + 2]

    @staticmethod
    def _month_label(month_id: int) -> str:
        names = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return names[month_id] if 1 <= month_id <= 12 else f"Month {month_id}"

    @staticmethod
    def _intensity_rank(value: Any) -> int:
        s = str(value or "").strip().lower()
        if s == "high":
            return 3
        if s == "medium":
            return 2
        return 1

    @staticmethod
    def _clean_text(value: Any) -> str:
        return " ".join(str(value or "").replace("\n", " ").replace("\r", " ").split()).strip()

    @staticmethod
    def _clip_text(value: Any, limit: int = 140) -> str:
        text = EventPredictor._clean_text(value)
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

    @staticmethod
    def _monthly_domain_shards() -> List[Dict[str, Any]]:
        return [
            {
                "id": "career_finance",
                "label": "Career and Finance",
                "domains": ["career", "finance", "status", "gains", "business"],
            },
            {
                "id": "relationships_family",
                "label": "Relationships and Family",
                "domains": ["relationships", "marriage", "family", "children", "social"],
            },
            {
                "id": "health_inner",
                "label": "Health and Inner Life",
                "domains": ["health", "mental", "conflict", "debt", "spiritual"],
            },
            {
                "id": "property_travel_learning",
                "label": "Property, Travel and Learning",
                "domains": ["property", "home", "vehicles", "travel", "legal", "education"],
            },
        ]

    @staticmethod
    def _extract_life_stage_context(age: int) -> str:
        if age < 23:
            return """
**USER PROFILE: STUDENT (Education Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Primary signification is **EXAMS, GRADES, INTELLIGENCE**. (Secondary: Romance).
* **4th House:** Signifies **SCHOOLING/COLLEGE STUDY**.
* **9th House:** Signifies **HIGHER EDUCATION/ADMISSION/COLLEGE**.
* **11th House:** Signifies **EXAM RESULTS/ADMISSION SUCCESS**. (Not Salary).
* **6th House:** Signifies **COMPETITIVE EXAMS** (Not Divorce/Job).
* **10th House:** Signifies **ACADEMIC RANK/ACHIEVEMENT**.
"""
        if age > 60:
            return """
**USER PROFILE: SENIOR (Retirement/Moksha Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Signifies **GRANDCHILDREN/MANTRA/DEVOTION**.
* **6th House:** Signifies **HEALTH ISSUES/DISEASE**.
* **1st House:** Signifies **VITALITY/LONGEVITY**.
* **12th House:** Signifies **HOSPITALS/SPIRITUAL RETREAT**.
"""
        return """
**USER PROFILE: CAREER/ADULT (Artha/Kama Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Signifies **CHILDREN/SPECULATION**.
* **10th House:** Signifies **CAREER/PROMOTION**.
* **11th House:** Signifies **WEALTH/SALARY/GAINS**.
* **7th House:** Signifies **MARRIAGE/BUSINESS PARTNERS**.
"""

    async def predict_yearly_events(
        self,
        birth_data: Dict,
        year: int,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> Dict[str, Any]:
        try:
            print("\n" + "#"*100)
            print(f"🎯 STARTING YEARLY EVENT PREDICTION FOR {year}")
            print("#"*100)
            
            # Calculate Age for Context
            birth_year = int(birth_data['date'].split('-')[0])
            current_age = year - birth_year
            print(f"📊 Birth year: {birth_year}, Current age: {current_age}")
            
            print("\n🔄 Preparing yearly data...")
            raw_data = self._prepare_yearly_data(birth_data, year)
            print(f"✅ Yearly data prepared (length: {len(raw_data)} chars)")

            if self._env_bool("EVENT_TIMELINE_PARALLEL_YEARLY", default=False):
                print("\n⚡ Parallel yearly timeline enabled (with context cache)")
                ai_response = await self._predict_yearly_events_parallel_cached(
                    raw_data=raw_data,
                    year=year,
                    age=current_age,
                    progress_callback=progress_callback,
                )
            else:
                # Pass Age to prompt generator for Desha Kala Patra logic
                print("\n🔄 Creating prediction prompt...")
                prompt = self._create_prediction_prompt(raw_data, year, current_age)
                print(f"✅ Prompt created (length: {len(prompt)} chars)")

                print("\n🔄 Calling timeline LLM...")
                ai_response = await self._get_ai_prediction_async(prompt)
                print("✅ Timeline LLM returned response")

            if ai_response.pop("_timeline_invalid", False):
                return {
                    "year": year,
                    "status": "error",
                    "error": (
                        ai_response.get("error")
                        or "Timeline model returned empty or incomplete JSON (e.g. {})."
                    ),
                    "macro_trends": [],
                    "monthly_predictions": [],
                }

            run_usage = ai_response.pop("_llm_usage", None)
            if isinstance(run_usage, dict):
                print(
                    "\n📊 YEARLY TOKEN USAGE TOTAL (model-reported): "
                    f"input_tokens={int(run_usage.get('input_tokens') or 0)} "
                    f"output_tokens={int(run_usage.get('output_tokens') or 0)} "
                    f"cached_input_tokens={int(run_usage.get('cached_tokens') or 0)} "
                    f"non_cached_input_tokens={int(run_usage.get('non_cached_input_tokens') or 0)} "
                    f"total_tokens={int(run_usage.get('total_tokens') or 0)}"
                )

            final_response = {"year": year, "status": "success", **ai_response}
            final_response = self._attach_timeline_summary(year, final_response)
            if isinstance(run_usage, dict):
                final_response["_llm_usage_totals"] = run_usage
            print(f"\n✅ PREDICTION COMPLETE FOR {year}")
            print(f"   - Final response keys: {list(final_response.keys())}")
            print("#"*100 + "\n")
            
            return final_response
            
        except Exception as e:
            print(f"\n❌ ERROR IN predict_yearly_events:")
            print(f"   - Error type: {type(e).__name__}")
            print(f"   - Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"year": year, "status": "error", "error": str(e), "macro_trends": [], "monthly_predictions": []}

    async def _predict_yearly_events_parallel_cached(
        self,
        raw_data: str,
        year: int,
        age: int,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> Dict[str, Any]:
        if not self.model:
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": "Timeline model not initialized.",
            }

        require_cache = self._env_bool("EVENT_TIMELINE_REQUIRE_CONTEXT_CACHE", default=True)
        cache_ttl_s = max(300, self._safe_int_env("EVENT_TIMELINE_CACHE_TTL_S", 3600))
        cache_resource = None
        cache_setup_input_tokens = max(1, int(round(len(raw_data or "") / 4.0)))
        try:
            print(f"🗂️ Creating Gemini context cache (ttl={cache_ttl_s}s)...")
            cache_resource = await asyncio.to_thread(
                genai_caching.CachedContent.create,
                model=self.model_name or getattr(self.model, "model_name", None),
                display_name=f"event-timeline-{year}",
                contents=[raw_data],
                ttl=cache_ttl_s,
            )
            print(f"✅ Cache created: {getattr(cache_resource, 'name', 'unknown')}")
        except Exception as e:
            msg = f"Failed to create Gemini context cache: {type(e).__name__}: {e}"
            print(f"❌ {msg}")
            if require_cache:
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": msg,
                }
            print("⚠️ EVENT_TIMELINE_REQUIRE_CONTEXT_CACHE is disabled; falling back to single-call yearly.")
            prompt = self._create_prediction_prompt(raw_data, year, age)
            return await self._get_ai_prediction_async(prompt)

        try:
            quarter_tasks: List[asyncio.Task] = []
            for q in (1, 2, 3, 4):
                month_ids = self._month_ids_for_quarter(q)
                quarter_prompt = self._create_quarter_prompt(
                    year=year,
                    age=age,
                    quarter_idx=q,
                    month_ids=month_ids,
                )
                cached_model = genai.GenerativeModel.from_cached_content(cache_resource)
                async def _run_quarter(quarter_index: int, prompt: str, model_obj: Any):
                    result = await self._get_ai_prediction_async(
                        prompt,
                        model_override=model_obj,
                        llm_log_tag=f"event_timeline_q{quarter_index}",
                    )
                    return quarter_index, result

                quarter_tasks.append(asyncio.create_task(_run_quarter(q, quarter_prompt, cached_model)))

            quarter_results_by_index: Dict[int, Dict[str, Any]] = {}
            usage_totals = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "non_cached_input_tokens": 0,
                "total_tokens": 0,
                "cache_setup_input_tokens": int(cache_setup_input_tokens),
            }
            for task in asyncio.as_completed(quarter_tasks):
                try:
                    quarter_idx, res = await task
                except Exception as e:
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Quarter Q{quarter_idx} failed: {type(e).__name__}: {e}",
                    }

                if isinstance(res, Exception):
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Quarter Q{quarter_idx} failed: {type(res).__name__}: {res}",
                    }
                if not isinstance(res, dict) or res.get("_timeline_invalid"):
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Quarter Q{quarter_idx} returned invalid timeline JSON.",
                    }

                quarter_usage = res.get("_llm_usage") if isinstance(res, dict) else None
                if isinstance(quarter_usage, dict):
                    usage_totals["input_tokens"] += int(quarter_usage.get("input_tokens") or 0)
                    usage_totals["output_tokens"] += int(quarter_usage.get("output_tokens") or 0)
                    usage_totals["cached_tokens"] += int(quarter_usage.get("cached_tokens") or 0)
                    usage_totals["non_cached_input_tokens"] += int(
                        quarter_usage.get("non_cached_input_tokens") or 0
                    )
                    usage_totals["total_tokens"] += int(quarter_usage.get("total_tokens") or 0)

                quarter_results_by_index[quarter_idx] = res
                if progress_callback:
                    monthly_predictions: List[Dict[str, Any]] = []
                    macro_trends: List[str] = []
                    for q in sorted(quarter_results_by_index.keys()):
                        q_payload = quarter_results_by_index[q] or {}
                        monthly_predictions.extend(q_payload.get("monthly_predictions") or [])
                        for trend in q_payload.get("macro_trends") or []:
                            t = " ".join(str(trend or "").split()).strip()
                            if not t:
                                continue
                            word_count = len([w for w in t.split(" ") if w])
                            if word_count <= 3 or len(t) < 28:
                                continue
                            if t not in macro_trends:
                                macro_trends.append(t)
                    monthly_predictions = sorted(
                        [m for m in monthly_predictions if isinstance(m, dict)],
                        key=lambda m: int(m.get("month_id") or 99),
                    )
                    progress_payload = {
                        "status": "processing",
                        "year": year,
                        "completed_quarters": len(quarter_results_by_index),
                        "total_quarters": 4,
                        "months_ready": len(monthly_predictions),
                        "macro_trends": macro_trends,
                        "monthly_predictions": monthly_predictions,
                    }
                    progress_payload = self._attach_timeline_summary(year, progress_payload)
                    cb_result = progress_callback(progress_payload)
                    if asyncio.iscoroutine(cb_result):
                        await cb_result

            normalized = [quarter_results_by_index[q] for q in sorted(quarter_results_by_index.keys()) if q in quarter_results_by_index]
            merged = self._merge_quarter_predictions(normalized)
            merged["_llm_usage"] = usage_totals
            return merged
        finally:
            if cache_resource is not None:
                try:
                    await asyncio.to_thread(cache_resource.delete)
                    print("🧹 Deleted Gemini context cache.")
                except Exception as e:
                    print(f"⚠️ Failed to delete cache: {e}")

    def _merge_quarter_predictions(self, quarter_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        monthly_predictions: List[Dict[str, Any]] = []
        macro_trends: List[str] = []

        def _clean_prediction_text(text: Any) -> str:
            s = str(text or "")
            s = s.replace("\n", " ").replace("\r", " ")
            s = s.replace("\t", " ")
            s = s.strip()
            s = s.replace("  ", " ")
            # Strip known debug tag if leaked.
            while "[BHAVA-DISAMBIG:" in s and "]" in s:
                start = s.find("[BHAVA-DISAMBIG:")
                end = s.find("]", start)
                if end <= start:
                    break
                s = (s[:start] + " " + s[end + 1:]).strip()
            return " ".join(s.split())

        def _normalize_macro_trends(raw: Any) -> List[str]:
            """
            Defensive normalization:
            - expected shape: list[str]
            - reject string/dict accidental shapes to avoid char/key bullet spam in UI
            """
            if isinstance(raw, list):
                out: List[str] = []
                for item in raw:
                    if isinstance(item, str):
                        t = item.strip()
                        if t:
                            out.append(t)
                    elif isinstance(item, dict):
                        # Common LLM drift: {'summary': '...'} / {'key_indicators': [...]} etc.
                        # Keep values only when they are human-readable strings/lists of strings.
                        for v in item.values():
                            if isinstance(v, str):
                                vv = v.strip()
                                if vv:
                                    out.append(vv)
                            elif isinstance(v, list):
                                for lv in v:
                                    if isinstance(lv, str) and lv.strip():
                                        out.append(lv.strip())
                return out
            if isinstance(raw, str):
                # Treat plain string as single trend (do not iterate chars).
                t = raw.strip()
                return [t] if t else []
            return []

        def _is_descriptive_macro_trend(text: str) -> bool:
            t = " ".join(str(text or "").split()).strip()
            if not t:
                return False
            words = [w for w in t.split(" ") if w]
            word_count = len(words)
            char_count = len(t)
            # Heading-like fragments we do not want as standalone bullets.
            if word_count <= 3:
                return False
            if char_count < 28:
                return False
            # Prefer narrative lines; allow medium-length with punctuation or clear sentence cues.
            if char_count >= 48:
                return True
            if re.search(r"[,:;.!?]", t):
                return True
            if re.search(r"\b(with|because|while|after|during|through|indicates|suggests|marks)\b", t, re.I):
                return True
            return False

        for result in quarter_results:
            monthly_predictions.extend(result.get("monthly_predictions") or [])
            for trend in _normalize_macro_trends(result.get("macro_trends")):
                t = str(trend).strip()
                if t and _is_descriptive_macro_trend(t) and t not in macro_trends:
                    macro_trends.append(t)

        if len(monthly_predictions) != 12:
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Merged quarterly output has {len(monthly_predictions)} months; expected 12.",
            }

        ids = []
        for m in monthly_predictions:
            if not isinstance(m, dict):
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": "Merged quarterly output contains non-object month entries.",
                }
            ids.append(m.get("month_id"))
            events = m.get("events")
            if not isinstance(events, list) or len(events) == 0:
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": f"Month {m.get('month_id')} has no events in merged quarterly output.",
                }
            if len(events) < 6:
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": f"Month {m.get('month_id')} has {len(events)} events; minimum 6 required.",
                }
            for ev_idx, ev in enumerate(events, start=1):
                if not isinstance(ev, dict):
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Month {m.get('month_id')} contains non-object event entry.",
                    }
                pred = _clean_prediction_text(ev.get("prediction"))
                has_technical_noise = bool(
                    pred
                    and re.search(
                        r"(\[BHAVA-DISAMBIG:|\b(BHAVA|Karaka|Varga|Threads=|Afflicter)\b|\b\d{1,2}L\b)",
                        pred,
                        re.I,
                    )
                )
                if not pred or has_technical_noise:
                    event_type = str(ev.get("type") or "").strip() or "unknown"
                    pred_preview = str(ev.get("prediction") or "").replace("\n", " ").strip()
                    if len(pred_preview) > 180:
                        pred_preview = pred_preview[:180] + "..."
                    reason = "empty prediction" if not pred else "technical/jargon prediction"
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": (
                            f"Month {m.get('month_id')} event #{ev_idx} ({event_type}) invalid: {reason}. "
                            f"Raw prediction preview: {pred_preview or '<empty>'}"
                        ),
                    }
                ev["prediction"] = pred
        try:
            normalized_ids = sorted(int(x) for x in ids)
        except Exception:
            normalized_ids = []
        if normalized_ids != list(range(1, 13)):
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Merged quarterly output has invalid month_ids: {ids}.",
            }

        monthly_predictions.sort(key=lambda x: int(x.get("month_id", 0)))
        return {"macro_trends": macro_trends, "monthly_predictions": monthly_predictions}

    async def predict_monthly_deep(self, birth_data: Dict, year: int, month: int) -> Dict[str, Any]:
        """Generate exhaustive predictions for a single month (all triggers, all manifestations)."""
        try:
            print("\n" + "#"*100)
            print(f"🎯 MONTHLY DEEP DIVE FOR {year} MONTH {month}")
            print("#"*100)
            birth_year = int(birth_data['date'].split('-')[0])
            current_age = year - birth_year
            raw_data = self._prepare_yearly_data(birth_data, year)
            transit_facts = self._get_transit_facts_for_month(birth_data, year, month)
            dasha_facts = self._get_dasha_facts_for_month(birth_data, year, month)
            if self._env_bool("EVENT_TIMELINE_PARALLEL_MONTHLY", default=False):
                print("\n⚡ Parallel monthly deep enabled (with context cache + domain shards)")
                ai_response = await self._predict_monthly_deep_parallel_cached(
                    raw_data=raw_data,
                    year=year,
                    month=month,
                    age=current_age,
                    transit_facts=transit_facts,
                    dasha_facts=dasha_facts,
                )
            else:
                prompt = self._create_monthly_deep_prompt(
                    raw_data, year, month, current_age, transit_facts, dasha_facts
                )
                ai_response = await self._get_ai_prediction_async(prompt)
            if ai_response.pop("_timeline_invalid", False):
                return {
                    "year": year,
                    "status": "error",
                    "error": (
                        ai_response.get("error")
                        or "Monthly deep model returned empty or incomplete JSON."
                    ),
                    "dasha_facts": dasha_facts,
                    "transit_facts": transit_facts,
                    "macro_trends": [],
                    "monthly_predictions": [],
                }
            run_usage = ai_response.pop("_llm_usage", None) if isinstance(ai_response, dict) else None
            final_response = {
                "year": year,
                "status": "success",
                "dasha_facts": dasha_facts,
                "transit_facts": transit_facts,
                **ai_response,
            }
            final_response = self._attach_timeline_summary(year, final_response)
            if isinstance(run_usage, dict):
                final_response["_llm_usage_totals"] = run_usage
                print(
                    "\n📊 MONTHLY TOKEN USAGE TOTAL (model-reported): "
                    f"input_tokens={int(run_usage.get('input_tokens') or 0)} "
                    f"output_tokens={int(run_usage.get('output_tokens') or 0)} "
                    f"cached_input_tokens={int(run_usage.get('cached_tokens') or 0)} "
                    f"non_cached_input_tokens={int(run_usage.get('non_cached_input_tokens') or 0)} "
                    f"total_tokens={int(run_usage.get('total_tokens') or 0)}"
                )
            print(f"\n✅ MONTHLY DEEP COMPLETE FOR {year}-{month}")
            print("#"*100 + "\n")
            return final_response
        except Exception as e:
            print(f"\n❌ ERROR IN predict_monthly_deep: {e}")
            import traceback
            traceback.print_exc()
            return {"year": year, "status": "error", "error": str(e), "macro_trends": [], "monthly_predictions": []}

    async def _predict_monthly_deep_parallel_cached(
        self,
        raw_data: str,
        year: int,
        month: int,
        age: int,
        transit_facts: Dict[str, Any],
        dasha_facts: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.model:
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": "Timeline model not initialized.",
            }
        require_cache = self._env_bool("EVENT_TIMELINE_REQUIRE_CONTEXT_CACHE", default=True)
        cache_ttl_s = max(300, self._safe_int_env("EVENT_TIMELINE_CACHE_TTL_S", 3600))
        cache_resource = None
        cache_setup_input_tokens = max(1, int(round(len(raw_data or "") / 4.0)))
        try:
            print(f"🗂️ Creating Gemini context cache for monthly deep (ttl={cache_ttl_s}s)...")
            cache_resource = await asyncio.to_thread(
                genai_caching.CachedContent.create,
                model=self.model_name or getattr(self.model, "model_name", None),
                display_name=f"event-timeline-monthly-{year}-{month}",
                contents=[raw_data],
                ttl=cache_ttl_s,
            )
            print(f"✅ Monthly cache created: {getattr(cache_resource, 'name', 'unknown')}")
        except Exception as e:
            msg = f"Failed to create Gemini context cache for monthly deep: {type(e).__name__}: {e}"
            print(f"❌ {msg}")
            if require_cache:
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": msg,
                }
            prompt = self._create_monthly_deep_prompt(raw_data, year, month, age, transit_facts, dasha_facts)
            return await self._get_ai_prediction_async(prompt)

        try:
            shards = self._monthly_domain_shards()
            tasks: List[asyncio.Task] = []
            for shard in shards:
                prompt = self._create_monthly_deep_shard_prompt(
                    year=year,
                    month=month,
                    age=age,
                    transit_facts=transit_facts,
                    dasha_facts=dasha_facts,
                    shard=shard,
                )
                cached_model = genai.GenerativeModel.from_cached_content(cache_resource)

                async def _run_shard(shard_id: str, shard_prompt: str, model_obj: Any):
                    result = await self._get_ai_prediction_async(
                        shard_prompt,
                        model_override=model_obj,
                        llm_log_tag=f"event_timeline_monthly_{shard_id}",
                    )
                    return shard_id, result

                tasks.append(asyncio.create_task(_run_shard(shard["id"], prompt, cached_model)))

            results_by_shard: Dict[str, Dict[str, Any]] = {}
            usage_totals = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "non_cached_input_tokens": 0,
                "total_tokens": 0,
                "cache_setup_input_tokens": int(cache_setup_input_tokens),
            }
            for task in asyncio.as_completed(tasks):
                try:
                    shard_id, res = await task
                except Exception as e:
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Monthly shard failed: {type(e).__name__}: {e}",
                    }
                if not isinstance(res, dict) or res.get("_timeline_invalid"):
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Monthly shard {shard_id} returned invalid JSON.",
                    }
                shard_usage = res.get("_llm_usage")
                if isinstance(shard_usage, dict):
                    usage_totals["input_tokens"] += int(shard_usage.get("input_tokens") or 0)
                    usage_totals["output_tokens"] += int(shard_usage.get("output_tokens") or 0)
                    usage_totals["cached_tokens"] += int(shard_usage.get("cached_tokens") or 0)
                    usage_totals["non_cached_input_tokens"] += int(
                        shard_usage.get("non_cached_input_tokens") or 0
                    )
                    usage_totals["total_tokens"] += int(shard_usage.get("total_tokens") or 0)
                results_by_shard[shard_id] = res

            merged = self._merge_monthly_deep_shards(
                month=month,
                shard_results_by_id=results_by_shard,
            )
            merged["_llm_usage"] = usage_totals
            return merged
        finally:
            if cache_resource is not None:
                try:
                    await asyncio.to_thread(cache_resource.delete)
                    print("🧹 Deleted Gemini monthly context cache.")
                except Exception as e:
                    print(f"⚠️ Failed to delete monthly cache: {e}")

    def _create_monthly_deep_shard_prompt(
        self,
        year: int,
        month: int,
        age: int,
        transit_facts: Dict[str, Any],
        dasha_facts: Dict[str, Any],
        shard: Dict[str, Any],
    ) -> str:
        month_names = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_name = month_names[month] if 1 <= month <= 12 else f"Month {month}"
        domains = shard.get("domains") or []
        domains_line = ", ".join(str(d).strip() for d in domains if str(d).strip())
        return f"""You are an expert Vedic astrologer. Generate ONE SHARD for monthly deep-dive for {month_name} {year}.

You are shard `{shard.get("id")}` focused on domain group: {shard.get("label")}.
You MUST cover only these domains: [{domains_line}].

DASHA FACTS (copy exactly, do not change):
```json
{json.dumps(dasha_facts, indent=2)}
```

TRANSIT FACTS (copy exactly, do not change):
```json
{json.dumps(transit_facts, indent=2)}
```

Use cached context as ground truth for all chart computations, and apply Desha-Kala-Patra for age {age}.

OUTPUT JSON ONLY with keys:
{{
  "macro_trends": [],
  "monthly_predictions": [
    {{
      "month_id": {month},
      "focus_areas": ["..."],
      "covered_domains": ["{domains[0] if domains else 'career'}"],
      "events": [
        {{
          "type": "Event Type",
          "prediction": "Plain-language user-facing prediction",
          "activation_reasoning": "Astrological why",
          "possible_manifestations": [{{"scenario":"...","reasoning":"..."}}, {{"scenario":"...","reasoning":"..."}}],
          "trigger_logic": "dasha + transit logic",
          "start_date": "YYYY-MM-DD",
          "end_date": "YYYY-MM-DD",
          "intensity": "High|Medium|Low"
        }}
      ]
    }}
  ]
}}

Constraints:
1) Return exactly one month object with month_id={month}.
2) Return 5-8 events for this shard.
3) Every event MUST map to one of the allowed domains for this shard.
4) prediction MUST be non-empty plain language. Do not include technical tags in prediction.
5) covered_domains MUST list only domains from this shard that you actually covered.
"""

    def _merge_monthly_deep_shards(self, month: int, shard_results_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        expected_shards = self._monthly_domain_shards()
        covered_domains: set[str] = set()
        events: List[Dict[str, Any]] = []
        macro_trends: List[str] = []
        focus_areas: List[str] = []

        def _clean_text(v: Any) -> str:
            return " ".join(str(v or "").replace("\n", " ").split()).strip()

        seen_keys: set[str] = set()
        shard_event_counts: Dict[str, int] = {}
        for shard in expected_shards:
            shard_id = str(shard.get("id") or "").strip()
            if not shard_id or shard_id not in shard_results_by_id:
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": f"Monthly shard {shard_id or '<unknown>'} missing from merge results.",
                }
            res = shard_results_by_id.get(shard_id) or {}
            shard_event_counts[shard_id] = 0
            for trend in res.get("macro_trends") or []:
                t = _clean_text(trend)
                if t and t not in macro_trends:
                    macro_trends.append(t)
            months = res.get("monthly_predictions") or []
            if not months or not isinstance(months[0], dict):
                continue
            m = months[0]
            if int(m.get("month_id") or 0) != int(month):
                return {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                    "error": f"Monthly shard returned wrong month_id {m.get('month_id')} (expected {month}).",
                }
            for fa in m.get("focus_areas") or []:
                f = _clean_text(fa)
                if f and f not in focus_areas:
                    focus_areas.append(f)
            shard_domains = m.get("covered_domains") or []
            for d in shard_domains:
                domain = _clean_text(d).lower()
                if domain:
                    covered_domains.add(domain)
            for ev in m.get("events") or []:
                if not isinstance(ev, dict):
                    continue
                pred = _clean_text(ev.get("prediction"))
                if not pred:
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": "Monthly shard contains event with empty prediction.",
                    }
                if re.search(r"(\[BHAVA-DISAMBIG:|\b(BHAVA|Karaka|Varga|Threads=|Afflicter)\b|\b\d{1,2}L\b)", pred, re.I):
                    return {
                        "macro_trends": [],
                        "monthly_predictions": [],
                        "_timeline_invalid": True,
                        "error": f"Monthly shard contains technical prediction text: {pred[:120]}",
                    }
                key = f"{_clean_text(ev.get('type')).lower()}|{pred.lower()}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                ev["prediction"] = pred
                events.append(ev)
                shard_event_counts[shard_id] += 1

        empty_shards = [sid for sid, c in shard_event_counts.items() if c <= 0]
        if empty_shards:
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Monthly shards returned no usable events: {', '.join(empty_shards)}",
            }
        if len(events) < 20:
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Merged monthly deep has {len(events)} events; minimum 20 required.",
            }

        # Keep strongest and near-term items first if model produced too many.
        def _intensity_rank(v: Any) -> int:
            s = str(v or "").strip().lower()
            if s == "high":
                return 3
            if s == "medium":
                return 2
            return 1

        events.sort(key=lambda e: (-_intensity_rank(e.get("intensity")), str(e.get("start_date") or "9999-12-31")))
        events = events[:30]
        monthly = {
            "month_id": month,
            "focus_areas": focus_areas[:10],
            "covered_domains": sorted(covered_domains),
            "events": events,
        }
        return {"macro_trends": macro_trends[:6], "monthly_predictions": [monthly]}

    def _create_monthly_deep_prompt(self, raw_data: str, year: int, month: int, age: int, transit_facts: Dict[str, Any], dasha_facts: Dict[str, Any]) -> str:
        """Prompt for single-month exhaustive analysis (all triggers, all manifestations)."""
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        month_name = month_names[month] if 1 <= month <= 12 else f"Month {month}"
        return f"""You are an expert Vedic Astrologer. For {month_name} {year} ONLY, produce an EXHAUSTIVE deep-dive analysis.

**DASHA FACTS (GROUND TRUTH — DO NOT CHANGE):**
These are the computed Vimshottari dashas for the native for this month. They now include start/mid/end samples and any detected changes inside the month. You MUST copy the top-level MD/AD/PD/Sookshma exactly into activation_overview.dasha_focus and use `samples` / `changes` to narrow the execution window.
If any level is missing, say "Not provided" — do NOT guess.
```json
{json.dumps(dasha_facts, indent=2)}
```

**TRANSIT FACTS (GROUND TRUTH — DO NOT CHANGE):**
These are the computed whole-sign transit houses for the native for this month. They now include start/mid/end snapshots and whether a planet changes sign/house/nakshatra inside the month. You are STRICTLY FORBIDDEN from stating a different transit house for these planets.
If you cannot find a planet here, say "not provided" — do NOT guess.
```json
{json.dumps(transit_facts, indent=2)}
```

**ASTROLOGICAL CONTEXT (FULL JSON FROM CHAT CONTEXT BUILDER):**
```json
{raw_data}
```

**ASTROLOGICAL SYNTHESIS ENGINE (HOW TO PREDICT EVENTS):**
To predict specific events for the requested timeframe (e.g., "{month_name} {year}"), you MUST execute the following 5-step analytical process. Do not skip any steps.

**Step 1: Map the Active Dasha Network (The Promise)**
* Extract the active Dasha lords (Mahadasha, Antardasha, Pratyantardasha, Sookshma) from `current_dashas` in the JSON above or from DASHA FACTS.
* Look at `d1_chart` and `planetary_analysis` to define their NATAL baseline:
  - Which houses do these planets rule? (use `house_lordships`)
  - Which house do they sit in?
  - Crucial: What are their natal relationships? (Which planets are they conjunct with or aspecting in the birth chart?)

**Step 2: The Golden Trigger Rule (Transit Activation)**
Do not predict events based on transits alone. Transiting planets will ONLY trigger major events if they form a specific relationship with the active Dasha lords. You MUST scan `transit_facts` and `macro_transits_timeline` in the JSON for the following triggers:
  1. Natal Return: Is a transiting Dasha lord passing exactly over its natal sign/position?
  2. Relationship Recreation: Is a transiting Dasha lord moving over or aspecting a planet it has a relationship with in the NATAL chart? (e.g., If Natal Saturn aspects Natal Venus, look for Transit Saturn aspecting Transit/Natal Venus).
  3. Nakshatra Return: Is the transiting planet passing through its natal Nakshatra?
  4. **Sun Activation (Monthly Gating Rule):** Is the transiting **Sun** conjunct (same whole-sign) OR 7th-aspecting (Sun aspects 7th only per the standard Vedic aspect table) the **transit position/sign/house** of any active Dasha lord (MD/AD/Pratyantardasha/Sookshma)? If YES, treat that matched Dasha lord as FIRST to activate.
* Priority Logic: If Sun Activation is detected for ANY active Dasha lord, those dasha planets are the FIRST to activate. Otherwise, dasha planets that meet ANY of the Natal Return/Relationship Recreation/Nakshatra Return conditions are the FIRST to activate.

**Step 3: Filter Through Precision Checks (The Catalyst)**
Before finalizing the event, cross-reference the activated planets with the warning systems:
* Navatara Warnings: Use `navatara_warnings`. If the transiting activated planet is in a dangerous Tara (Vipat, Pratyari, Naidhana), the event will involve sudden obstacles.
* Sniper Points: Use `sniper_points`. If the transiting planet hits Bhrigu Bindu, 64th Navamsa, or 22nd Drekkana, predict a sudden, highly karmic/fated event.
* Age Activation: Check `nadi_age_activation`. If the activated planet matches the age-activated planet, the event is guaranteed to be a major life milestone.

**Step 4: Validate Event Quality (Ashtakavarga)**
* For the houses activated in Step 2, check their scores in `ashtakavarga` → `sarvashtakavarga`.
* Rule: If the activated house has high bindus (28+), the event manifests easily and successfully. If it has low bindus (<25), the event will bring friction, delays, or stress.

**Step 5: Event Synthesis & Output (House Combinations)**
Combine the significations of the activated houses to form specific, real-world events. Do not use vague astrology jargon.
* Example: If AD lord Mercury rules the 4th (Home) and transits the 10th (Career), AND recreates a natal aspect with the MD lord -> Predict: "Relocation due to a major career promotion or working from a new home office."
* Example: If PD lord is Mars (ruling 6th - Health), and transits over its natal position in the 2nd (Face/Throat) with low Ashtakavarga bindus -> Predict: "Acute health flare-up related to teeth, throat, or speech requiring immediate medical attention."
* CRITICAL COVERAGE RULE: You MUST consider **all significations of ALL activated houses** and systematically combine them. Your goal is to produce a **holistic, exhaustive list of distinct real-world events**, not just 2–3 highlights.

{BHAVA_MANIFESTATION_DISAMBIGUATION_BLOCK}

**OUTPUT REQUIREMENTS (JSON ONLY):**
1. Return ONLY ONE month object in `monthly_predictions` with `month_id = {month}`.
2. For that month, include an `activation_overview` object that:
   - Copies MD/AD/PD/Sookshma exactly from DASHA FACTS / `current_dashas` into `dasha_focus`.
   - Summarizes the key natal links of these planets.
   - Lists the key transit triggers (Natal Return, Relationship Recreation, Nakshatra Return, and/or Sun Activation) you used.
   - Lists the activated houses and why they are activated.
3. CRITICAL: Under `events`, create **at least 20 event objects** (more if many activation patterns exist). You MUST keep generating events until you have covered **all meaningful combinations of the activated houses and planets**. For EVERY event:
   - Provide `activation_reasoning` showing your work (e.g., "Because AD lord Rahu is transiting over its natal position in the 8th house, recreating its natal aspect with Saturn...").
   - Fill `prediction` with a clear, real-world scenario (Finance, Health, Career, Family, Real Estate, etc.).
   - Fill `possible_manifestations` as an array of objects with `scenario` and `reasoning`, linking back to houses and planets explicitly.
   - Use `start_date` and `end_date` to define the tightest realistic execution band you can infer from the dasha/transit periods. Prefer a 5-20 day band over the full month when `samples` or `changes` show a clear pivot.

**STRICT ANTI-HALLUCINATION RULES:**
* When you state a dasha planet, it must come from `current_dashas` or DASHA FACTS.
* When you state a transit house for Jupiter/Saturn/Rahu/Ketu, it must come from `macro_transits_timeline` or TRANSIT FACTS.
* When you mention aspects, you must follow the standard Vedic aspect table from the main instructions (Saturn 3/7/10, Jupiter 5/7/9, Mars 4/7/8, others 7th only). Do not invent aspect patterns.

Now return a single JSON object with this structure:
{{
    "macro_trends": [],
    "monthly_predictions": [
        {{
            "month_id": {month},
            "activation_overview": {{
                "dasha_focus": {{
                    "mahadasha": "PlanetName or 'Unknown'",
                    "antardasha": "PlanetName or 'Unknown'",
                    "pratyantardasha": "PlanetName or 'Unknown'",
                    "sookshma": "PlanetName or 'Not provided'"
                }},
                "dasha_lords_natal_links": [
                    "Describe key natal links for the active dasha lords (lordship + conjunction/aspect links + varga checks when relevant)"
                ],
                "transit_recreation": [
                    "Describe concrete transit→natal hits / nakshatra returns supported by the JSON data (do not guess transit houses)"
                ],
                "activated_houses": [1, 2, 7],
                "why_these_houses": "Explain WHY these houses are activated (dasha -> natal links -> transit recreation)."
            }},
            "focus_areas": ["list all focus areas for this month"],
            "events": [
                {{
                    "type": "Event Type",
                    "activation_reasoning": "FULL ACTIVATION LOGIC for THIS event: explicitly list MD/AD/PD(+Sookshma), their natal houses & lordships, the exact transit trigger (from macro_transits_timeline/transit_facts), and ALL houses activated before listing manifestations.",
                    "prediction": "Narrative description of the concrete life event.",
                    "possible_manifestations": [{{"scenario": "...", "reasoning": "..."}}, ...],
                    "trigger_logic": "Summarize the key dasha + transit pattern used.",
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "intensity": "High|Medium|Low"
                }}
            ]
        }}
    ]
}}"""

    def _get_transit_facts_for_month(self, birth_data: Dict, year: int, month: int) -> Dict[str, Any]:
        """
        Compute interval-based transit facts for a month instead of a single 1st-of-month snapshot.
        This gives the model a better execution-window picture for month-level timing.
        """
        try:
            natal_positions = self.transit_calc._calculate_natal_positions(birth_data)  # uses Swiss Ephemeris + Lahiri
            asc_lon = float(natal_positions.get('ascendant_longitude', 0.0)) if natal_positions else 0.0
            last_day = calendar.monthrange(year, month)[1]
            sample_points = {
                "start": datetime(year, month, 1, 12, 0, 0),
                "mid": datetime(year, month, min(15, last_day), 12, 0, 0),
                "end": datetime(year, month, last_day, 12, 0, 0),
            }

            def calc_snapshot(dt: datetime, planet: str) -> Dict[str, Any]:
                lon = self.transit_calc.get_planet_position(dt, planet)
                if lon is None:
                    return {}
                house = int(self.transit_calc.calculate_house_from_longitude(lon, asc_lon))
                sign_id = int(lon / 30) + 1
                nk = self.transit_calc.get_nakshatra_from_longitude(lon)
                return {
                    "dt": dt.strftime("%Y-%m-%d"),
                    "h": house,
                    "s": sign_id,
                    "dg": round(lon % 30, 2),
                    "nk": nk.get("name"),
                    "pd": nk.get("pada"),
                }

            planets = ['Saturn', 'Rahu', 'Ketu', 'Jupiter', 'Mars', 'Sun', 'Moon', 'Mercury', 'Venus']
            samples: Dict[str, Dict[str, Any]] = {}
            changes: Dict[str, Dict[str, Any]] = {}
            transit_houses: Dict[str, Any] = {}
            for planet in planets:
                planet_samples = {label: calc_snapshot(dt, planet) for label, dt in sample_points.items()}
                samples[planet] = planet_samples
                start_house = (planet_samples.get("start") or {}).get("h")
                end_house = (planet_samples.get("end") or {}).get("h")
                transit_houses[planet] = start_house
                sign_seq = [((planet_samples.get(label) or {}).get("s")) for label in ("start", "mid", "end")]
                house_seq = [((planet_samples.get(label) or {}).get("h")) for label in ("start", "mid", "end")]
                nk_seq = [((planet_samples.get(label) or {}).get("nk")) for label in ("start", "mid", "end")]
                changes[planet] = {
                    "house_change": bool(start_house is not None and end_house is not None and start_house != end_house),
                    "sign_change": len({s for s in sign_seq if s is not None}) > 1,
                    "nakshatra_change": len({n for n in nk_seq if n}) > 1,
                    "house_span": [h for h in house_seq if h is not None],
                }
            facts = {
                "sample_window_utc": {
                    "start": sample_points["start"].strftime('%Y-%m-%d %H:%M'),
                    "mid": sample_points["mid"].strftime('%Y-%m-%d %H:%M'),
                    "end": sample_points["end"].strftime('%Y-%m-%d %H:%M'),
                },
                "ascendant_longitude": asc_lon,
                "transit_houses": transit_houses,
                "samples": samples,
                "changes": changes,
            }
            return facts
        except Exception as e:
            return {"error": str(e), "transit_houses": {}}

    def _get_dasha_facts_for_month(self, birth_data: Dict, year: int, month: int) -> Dict[str, Any]:
        """Compute interval-based Vimshottari facts for the selected month."""
        try:
            last_day = calendar.monthrange(year, month)[1]
            sample_points = {
                "start": datetime(year, month, 1, 12, 0, 0),
                "mid": datetime(year, month, min(15, last_day), 12, 0, 0),
                "end": datetime(year, month, last_day, 12, 0, 0),
            }

            def pack_levels(dt: datetime) -> Dict[str, Any]:
                dashas = self.dasha_calc.calculate_current_dashas(birth_data, dt)
                return {
                    "sample_date_local": dt.strftime('%Y-%m-%d %H:%M'),
                    "mahadasha": (dashas.get('mahadasha') or {}).get('planet'),
                    "antardasha": (dashas.get('antardasha') or {}).get('planet'),
                    "pratyantardasha": (dashas.get('pratyantardasha') or {}).get('planet'),
                    "sookshma": (dashas.get('sookshma') or {}).get('planet'),
                }

            samples = {label: pack_levels(dt) for label, dt in sample_points.items()}
            daily_changes: List[Dict[str, Any]] = []
            prev_stack: Optional[tuple[Any, Any, Any, Any]] = None
            for day in range(1, last_day + 1):
                dt = datetime(year, month, day, 12, 0, 0)
                row = pack_levels(dt)
                stack = (
                    row.get("mahadasha"),
                    row.get("antardasha"),
                    row.get("pratyantardasha"),
                    row.get("sookshma"),
                )
                if prev_stack is not None and stack != prev_stack:
                    daily_changes.append(
                        {
                            "dt": dt.strftime("%Y-%m-%d"),
                            "from": {
                                "mahadasha": prev_stack[0],
                                "antardasha": prev_stack[1],
                                "pratyantardasha": prev_stack[2],
                                "sookshma": prev_stack[3],
                            },
                            "to": {
                                "mahadasha": stack[0],
                                "antardasha": stack[1],
                                "pratyantardasha": stack[2],
                                "sookshma": stack[3],
                            },
                        }
                    )
                prev_stack = stack
            return {
                "sample_window_local": {
                    "start": sample_points["start"].strftime('%Y-%m-%d %H:%M'),
                    "mid": sample_points["mid"].strftime('%Y-%m-%d %H:%M'),
                    "end": sample_points["end"].strftime('%Y-%m-%d %H:%M'),
                },
                "mahadasha": samples["start"].get("mahadasha"),
                "antardasha": samples["start"].get("antardasha"),
                "pratyantardasha": samples["start"].get("pratyantardasha"),
                "sookshma": samples["start"].get("sookshma"),
                "samples": samples,
                "changes": daily_changes,
            }
        except Exception as e:
            return {"error": str(e)}

    def _infer_event_domain(self, event: Dict[str, Any]) -> str:
        blob = " ".join(
            [
                self._clean_text(event.get("type")),
                self._clean_text(event.get("prediction")),
                self._clean_text(event.get("trigger_logic")),
                self._clean_text(event.get("activation_reasoning")),
            ]
        ).lower()
        rules = [
            ("marriage", ["marriage", "spouse", "partner", "relationship", "engagement", "wedding"]),
            ("career", ["career", "job", "profession", "promotion", "authority", "role", "business", "work"]),
            ("children", ["child", "children", "conception", "pregnancy", "ivf", "progeny"]),
            ("property", ["property", "home", "house", "vehicle", "land", "real estate", "relocation"]),
            ("wealth", ["money", "wealth", "finance", "salary", "income", "gains", "investment"]),
            ("health", ["health", "disease", "surgery", "recovery", "hospital", "vitality", "illness"]),
            ("education", ["education", "exam", "study", "learning", "admission", "degree"]),
            ("travel", ["travel", "foreign", "visa", "journey", "relocation abroad"]),
            ("legal", ["legal", "court", "litigation", "dispute", "conflict", "debt"]),
        ]
        for domain, keywords in rules:
            if any(word in blob for word in keywords):
                return domain
        return "general"

    def _event_score(self, event: Dict[str, Any], month_id: int) -> float:
        intensity = self._intensity_rank(event.get("intensity"))
        score = float(intensity * 3)
        if event.get("start_date"):
            score += 1.0
        if event.get("end_date"):
            score += 0.5
        if event.get("possible_manifestations"):
            try:
                score += min(len(event.get("possible_manifestations") or []), 5) * 0.2
            except Exception:
                pass
        trigger = self._clean_text(event.get("trigger_logic")).lower()
        if "nakshatra return" in trigger:
            score += 2.0
        if "double transit" in trigger or "triple confirmation" in trigger:
            score += 1.5
        score += max(0, 13 - int(month_id)) * 0.01
        return round(score, 2)

    def _build_timeline_candidate_windows(self, year: int, monthly_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for month in monthly_predictions:
            if not isinstance(month, dict):
                continue
            month_id = int(month.get("month_id") or 0)
            for event in month.get("events") or []:
                if not isinstance(event, dict):
                    continue
                domain = self._infer_event_domain(event)
                candidates.append(
                    {
                        "domain": domain,
                        "month_id": month_id,
                        "month": self._month_label(month_id),
                        "score": self._event_score(event, month_id),
                        "confidence": {3: "high", 2: "medium", 1: "low"}.get(self._intensity_rank(event.get("intensity")), "low"),
                        "window_type": "execution",
                        "prediction": self._clip_text(event.get("prediction"), 180),
                        "reason": self._clip_text(event.get("trigger_logic") or event.get("activation_reasoning"), 180),
                        "start_date": event.get("start_date") or "",
                        "end_date": event.get("end_date") or "",
                    }
                )
        candidates.sort(key=lambda row: (-float(row.get("score") or 0), int(row.get("month_id") or 99), str(row.get("domain") or "")))
        return candidates

    def _collapse_candidate_windows(self, year: int, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_domain: Dict[str, List[Dict[str, Any]]] = {}
        for row in candidates:
            by_domain.setdefault(str(row.get("domain") or "general"), []).append(row)

        windows: List[Dict[str, Any]] = []
        for domain, rows in by_domain.items():
            rows.sort(key=lambda r: int(r.get("month_id") or 99))
            cluster: List[Dict[str, Any]] = []
            for row in rows:
                if not cluster or int(row.get("month_id") or 0) <= int(cluster[-1].get("month_id") or 0) + 1:
                    cluster.append(row)
                else:
                    windows.append(self._finalize_window(year, domain, cluster))
                    cluster = [row]
            if cluster:
                windows.append(self._finalize_window(year, domain, cluster))
        windows.sort(key=lambda row: (-float(row.get("score") or 0), int(row.get("peak_month_id") or 99)))
        return windows[:10]

    def _finalize_window(self, year: int, domain: str, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        peak = max(cluster, key=lambda row: (float(row.get("score") or 0), -int(row.get("month_id") or 99)))
        start_month = int(cluster[0].get("month_id") or 0)
        end_month = int(cluster[-1].get("month_id") or 0)
        label = self._month_label(start_month) if start_month == end_month else f"{self._month_label(start_month)}-{self._month_label(end_month)}"
        avg_score = round(sum(float(row.get("score") or 0) for row in cluster) / max(len(cluster), 1), 2)
        return {
            "domain": domain,
            "label": f"{label} {year}",
            "start_month_id": start_month,
            "end_month_id": end_month,
            "peak_month_id": int(peak.get("month_id") or start_month),
            "peak_month": peak.get("month"),
            "window_type": "execution" if len(cluster) <= 2 else "promise",
            "score": avg_score,
            "confidence": peak.get("confidence"),
            "headline": peak.get("prediction"),
            "reason": peak.get("reason"),
            "months": [int(row.get("month_id") or 0) for row in cluster],
        }

    def _build_user_timeline_summary(self, year: int, monthly_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        candidates = self._build_timeline_candidate_windows(year, monthly_predictions)
        windows = self._collapse_candidate_windows(year, candidates)
        best_months = [
            {
                "month_id": int(row.get("month_id") or 0),
                "month": row.get("month"),
                "domain": row.get("domain"),
                "confidence": row.get("confidence"),
                "headline": row.get("prediction"),
            }
            for row in candidates[:6]
        ]
        turning_points = []
        for row in windows[:4]:
            turning_points.append(
                {
                    "domain": row.get("domain"),
                    "window": row.get("label"),
                    "peak_month": row.get("peak_month"),
                    "why": row.get("reason"),
                }
            )
        return {
            "best_months": best_months,
            "candidate_windows": windows,
            "turning_points": turning_points,
        }

    def _attach_timeline_summary(self, year: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return payload
        monthly_predictions = payload.get("monthly_predictions")
        if not isinstance(monthly_predictions, list) or not monthly_predictions:
            return payload
        for month in monthly_predictions:
            if not isinstance(month, dict):
                continue
            ranked_events = sorted(
                [ev for ev in (month.get("events") or []) if isinstance(ev, dict)],
                key=lambda ev: (-self._event_score(ev, int(month.get("month_id") or 0)), str(ev.get("start_date") or "")),
            )
            if ranked_events:
                top = ranked_events[:3]
                month["month_summary"] = {
                    "headline": self._clip_text(top[0].get("prediction"), 180),
                    "best_domains": [self._infer_event_domain(ev) for ev in top],
                    "execution_focus": [
                        {
                            "domain": self._infer_event_domain(ev),
                            "prediction": self._clip_text(ev.get("prediction"), 120),
                            "confidence": {3: "high", 2: "medium", 1: "low"}.get(self._intensity_rank(ev.get("intensity")), "low"),
                        }
                        for ev in top
                    ],
                }
        payload["timeline_summary"] = self._build_user_timeline_summary(year, monthly_predictions)
        return payload

    def _prepare_yearly_data(self, birth_data: Dict, year: int) -> str:
        """
        Use ChatContextBuilder for full chart math, then prune payload for event timeline only
        (yearly + monthly deep share this path). Pruning does not alter builder caches.
        """
        print(f"\n📊 Using ChatContextBuilder for comprehensive {year} analysis...")
        
        from chat.chat_context_builder import ChatContextBuilder
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime, timedelta)):
                    return obj.isoformat()
                return super().default(obj)
        
        context_builder = ChatContextBuilder()
        
        full_context = context_builder.build_annual_context(
            birth_data=birth_data,
            target_year=year,
            user_question=f"Predict life events for {year}",
            intent_result={'mode': 'annual_prediction', 'category': 'yearly_events'}
        )
        
        slim = prune_for_event_timeline(full_context)
        print(
            f"✅ Event timeline context: {len(full_context)} top-level keys → "
            f"{len(slim)} after prune"
        )
        
        return json.dumps(slim, indent=2, cls=DateTimeEncoder)

    def _create_prediction_prompt(self, raw_data: str, year: int, age: int) -> str:
        """
        Dynamically adjusts prompt based on User Age (Desha Kala Patra).
        """
        
        life_stage_context = self._extract_life_stage_context(age)

        test_month_raw = (os.getenv("EVENT_TIMELINE_TEST_MONTH") or "").strip()
        test_month_suffix = ""
        if test_month_raw.isdigit():
            tm = int(test_month_raw)
            if 1 <= tm <= 12:
                test_month_suffix = f"""

### TEST MODE — SINGLE MONTH ONLY (env EVENT_TIMELINE_TEST_MONTH={tm})
**Overrides output shape only** where this conflicts with instructions above.

1. `monthly_predictions` MUST contain **exactly one** object; that object's `month_id` must be the integer {tm}.
2. Include **3 to 8** `events` for that month (testing cap).
3. Per event, at least **2** `possible_manifestations` (skip the “minimum 6 manifestations” rule for this run).
4. `macro_trends`: **1 to 3** short strings.
5. Ignore requirements for **exactly 12 months** in `monthly_predictions`.

Return valid JSON with top-level keys `macro_trends` and `monthly_predictions` only.
"""
                print(f"\n🔧 EVENT_TIMELINE_TEST_MONTH={tm} — single-month yearly prompt override active\n")

        return f"""
You are an expert Vedic Astrologer predicting life events for {year}.

**COMPLETE ASTROLOGICAL CONTEXT (JSON FORMAT):**
The following JSON contains comprehensive astrological data:
- static_context: Birth chart (D1), all divisional charts (D2-D60 with house positions), yogas, planetary strengths, chara karakas, ashtakavarga
- dynamic_context: Year-long dasha periods, monthly transits, significant periods

**HOW TO USE THE DATA:**
- For career events: Check D1 10th house + D10 (dashamsha) + D24 (education)
- For marriage events: Check D1 7th house + D9 (navamsa) + D7 (children)
- For property events: Check D1 4th house + D4 (chaturthamsha) + D2 (wealth)
- For health events: Check D1 6th/8th house + D30 (trimshamsha diseases)
- For education events: Check D1 5th house + D24 (chaturvimshamsha)
- Use yogas, planetary strengths, and ashtakavarga scores for timing and intensity

```json
{raw_data}
```

{life_stage_context}

### CRITICAL: IDENTIFY THE YEAR'S TURNING POINT
**Before generating macro trends, identify the single most important planetary shift of the year.**

**Instructions:**
1. Scan all 12 months for major outer planet transits (Jupiter, Saturn, Rahu/Ketu sign changes)
2. Identify which transit will have the BIGGEST impact on the native's life
3. Label it as "The Year's Turning Point" in your macro_trends
4. Explain WHY the user's life will feel fundamentally different before and after this date
5. Specify the exact month when this pivot occurs

**Example Format:**
"The Year's Turning Point: Month 6 - Jupiter enters Cancer (your 10th house). Before this, career feels stagnant. After this, sudden promotions and recognition become possible. This is the dividing line of your year."

### CRITICAL RULES:

**1. CALENDAR INTEGRITY (MANDATORY):**
You MUST return exactly 12 month objects in the monthly_predictions array, covering January (month_id: 1) through December (month_id: 12).
- DO NOT skip months
- DO NOT re-index based on events found
- If a month has no major triggers, use the current Dasha Lords to predict routine maintenance activities for that month
- Each month_id must correspond to its calendar month (1=January, 2=February, etc.)

**1b. MONTH-LEVEL EXECUTION WINDOWS (MANDATORY):**
- Broad year language is not enough. Narrow to the month whenever the data supports it.
- For every Medium or High intensity event, fill `start_date` and `end_date` with the tightest plausible execution band you can justify.
- Prefer a 5-20 day execution window over a whole-month range when trigger clustering exists.
- If you cannot narrow beyond the month, say that clearly in `trigger_logic` instead of pretending exactness.

**2. DASHA INVIOLABILITY (FORBIDDEN TO VIOLATE):**
You are STRICTLY FORBIDDEN from changing the Dasha dates provided in the current_dashas context.
- DO NOT hallucinate dasha shifts
- DO NOT invent new dasha periods
- Use the provided dasha calendar EXACTLY as given
- If no trigger is found for the current PD Lord, look for triggers involving the AD Lord or MD Lord

**3. LORDSHIP INTEGRATION (ALWAYS STATE):**
ALWAYS state the planet's Natal Lordship before explaining its transit effect.
- Format: "Mercury as your 3rd and 12th lord transits..."
- This helps users understand WHY a planet matters to them

**4. DEBILITATION RULE:**
When a planet is debilitated in transit, do NOT just predict 'bad results'.
- Predict that the specific life department ruled by that planet (lordship) will require heavy effort or resource drain
- Example: "Sun (2L) debilitated in 4th = Spending wealth on home repairs" NOT just "Stress at home"

**5. DASHA LORD BRIDGE RULE (CRITICAL):**
When a Dasha Lord (MD/AD/PD) is hit by a transit, you MUST check ALL houses it rules natally, even if it sits in a different house.
- Example: If Transit Ketu crosses Natal Saturn, and Saturn rules the 7th house, you MUST predict effects on marriage/partnerships, NOT just the house Saturn sits in.
- Format: "Transit Ketu crosses Natal Saturn (7L, 8L) in 2nd house = Karmic obstruction affecting partnerships (7H) and sudden breaks in wealth (2H/8H)."

**6. VEDIC HOUSE COUNTING RULE (FORBIDDEN):**
NEVER count houses from a planetary cluster. This is Western astrology logic.
- ALWAYS count houses from the Lagna (Ascendant) or the current Dasha Lord's sign.
- WRONG: "Sun is 2nd from your natal cluster"
- RIGHT: "Sun transits 10th house from Lagna"

**7. THE "RULE OF THREE" MANIFESTATION SPECTRUM:**
For every High/Medium intensity event, you MUST provide comprehensive scenarios in the `possible_manifestations` array:
- Include scenarios covering Material/Artha (Career, Money, Property, Status)
- Include scenarios covering Internal/Emotional (Family, Peace of Mind, Relationships)
- Include scenarios covering Physical/Obstacle (Health, Energy, Challenges)
- Add additional scenarios for ANY other house combinations you identify

**The goal is MAXIMUM COMPREHENSIVE coverage. Generate AS MANY manifestations as the house activations allow - there is NO UPPER LIMIT.**

**8. THE MULTI-HOUSE SYNTHESIS ENGINE (BPHS LOGIC):**
A planet is a bridge. You are forbidden from predicting an isolated house result.
**Synthesis Formula:** [Planet] = ([Natal Lordship Houses] + [Transit House]) acting upon [Aspected Houses].
- *Example:* Jupiter (rules 6, 9) transiting 1H and aspecting 5H.
- *Synthesis:* "Your luck/fortune (9L) and service (6L) physically manifest (1H) to bring gains through creativity or children (5H aspect)."

**9. STRICT ACTIVATION HIERARCHY (DASHA-FIRST LOGIC):**
The Sun is only a timer; the Dasha Lords are the source.
1. **PRIMARY TRIGGER:** The PD Lord moves into a new house or hits a Natal Planet.
2. **SECONDARY TRIGGER:** A fast planet (Sun/Mars/Venus) conjuncts or aspects the current MD, AD, or PD Lord.
3. **TERTIARY TRIGGER (Resonance):** A fast planet transits the house RULED by the MD, AD, or PD Lord.
4. **THE "STUN" TRIGGER:** Transit Saturn and Transit Jupiter both aspect the same house (Double Transit). If this occurs, intensity is ALWAYS 'High'.
5. **THE DOUBLE-ASPECT RULE:** If two slow planets (Saturn/Jupiter/Rahu/Ketu) aspect the same house, that house is 'ON FIRE'. Predict a major life milestone for that house, even if the Sun is not there.

**10. THE "STUNNING" PATTERN DETECTOR (Year-Independent):**
You are required to scan the provided transit data for the following "High-Certainty" patterns:

* **Pattern 1: The Double Transit (The King Maker):** Check if Transit Saturn and Transit Jupiter both aspect the same house at any point in the year.
    - If found: Label this as a "Major Financial/Life Anchor" in macro_trends.
    - Explain that when the two heavyweights focus on one house, concrete results are GUARANTEED.
* **Pattern 2: The Nodal Return/Reverse:** Check if Transit Rahu or Ketu is conjunct your Natal Rahu or Ketu.
    - This marks a "Karmic Reset" year.
* **Pattern 3: Dasha Chhidra (The Threshold):** If the user is in the last 3 months of a Mahadasha or Antardasha, predict "Sudden Endings/New Chapters."

**11. MANDATORY TRIGGER REASONING (No Guesswork):**
For every month, you must justify the prediction using this exact chain:
1. **Source:** Identify the Dasha Lord (MD/AD/PD) acting this month.
2. **Timer:** Identify the fast planet (Sun/Mars/etc.) hitting that Dasha Lord or its ruled house.
3. **Constraint:** You are strictly forbidden from giving Saturn an 11th aspect. Saturn aspects only 3, 7, and 10.
4. **Validation:** In the trigger_logic field, you MUST write the formula:
   "Trigger = [Fast Planet] @ [Degree] hitting [Natal/Dasha Point]."

**CRITICAL SUN DEMOTION RULE:**
If a month contains a PRIMARY Trigger (PD Lord sign change) or a SECONDARY Trigger (any planet hitting a Dasha Lord), you are FORBIDDEN from mentioning the Sun's ingress in the trigger_logic. The Sun should only be used as a secondary 'timer' to pinpoint the 5-day window, NOT as the primary reason for the event.

**12. THE MANIFESTATION SPECTRUM (Comprehensive Coverage Rule):**
For every event, the `possible_manifestations` array MUST contain AT LEAST 6 scenarios:
- **MINIMUM 6 manifestations** for ALL intensity levels (High, Medium, Low)
- Generate MORE than 6 if multiple houses are activated through lordship, transit, aspects, conjunctions, and Nakshatra Return
- Each scenario should combine different house significations
- Cover Material (career, money, property), Emotional (relationships, family), and Physical (health, vitality) domains
- Include scenarios for specialized house combinations (e.g., 3H+8H+12H = "Secret foreign correspondence")
- Explore ALL combinations of activated houses - aim for comprehensive coverage

**13. ASTRONOMICAL INTEGRITY & ASPECT RULES:**
If you hallucinate an impossible aspect, the analysis is invalid.
- **Saturn:** 3rd, 7th, 10th aspects ONLY. (Saturn in 9H DOES NOT aspect 7H).
- **Mars:** 4th, 7th, 8th aspects ONLY.
- **Jupiter:** 5th, 7th, 9th aspects ONLY.
- **Others (Sun/Mer/Ven/Moon):** 7th aspect ONLY.

**ASTRONOMICAL GUARDRAIL:** If a planet is in House X, it can only affect Houses [X+2, X+6, X+9] for Saturn, [X+3, X+6, X+7] for Mars, and [X+4, X+6, X+8] for Jupiter. Any other house citation is an error.

**14. TRANSIT SUN DEPENDENCY RULE:**
The Sun is a TIMER, not a SOURCE. Fast-moving planets (Sun, Moon, Mercury, Venus, Mars) can only be PRIMARY triggers if:
1. They directly aspect or conjoin a Dasha Lord (MD/AD/PD)
2. They activate the natal position of a Dasha Lord
3. NO slow-moving planet (Jupiter, Saturn, Rahu, Ketu) has a major movement that month

**If a month has a major PD Lord ingress (e.g., Jupiter enters a new sign in Month 6), the PD Lord MUST be the PRIMARY trigger, NOT the Sun's ingress into that month's sign.**

**Example of CORRECT trigger_logic:**
- WRONG: "Transit Sun enters Cancer in July" (when Jupiter also enters Cancer that month)
- RIGHT: "Jupiter (PD Lord) enters Cancer (10th house), amplified by Sun joining the same sign"

**15. FINAL GUARDRAIL: ASPECT MATH (MANDATORY):**
Perform this calculation for every aspect citation to prevent hallucinations:

**Saturn Aspects (3rd, 7th, 10th only):**
- Saturn in House 1: aspects Houses 3, 7, 10
- Saturn in House 2: aspects Houses 4, 8, 11
- Saturn in House 3: aspects Houses 5, 9, 12
- Saturn in House 4: aspects Houses 6, 10, 1
- Saturn in House 5: aspects Houses 7, 11, 2
- Saturn in House 6: aspects Houses 8, 12, 3
- Saturn in House 7: aspects Houses 9, 1, 4
- Saturn in House 8: aspects Houses 10, 2, 5
- Saturn in House 9: aspects Houses 11, 3, 6
- Saturn in House 10: aspects Houses 12, 4, 7
- Saturn in House 11: aspects Houses 1, 5, 8
- Saturn in House 12: aspects Houses 2, 6, 9

**Jupiter Aspects (5th, 7th, 9th only):**
- Jupiter in House 1: aspects Houses 5, 7, 9
- Jupiter in House 2: aspects Houses 6, 8, 10
- Jupiter in House 3: aspects Houses 7, 9, 11
- Jupiter in House 4: aspects Houses 8, 10, 12
- Jupiter in House 5: aspects Houses 9, 11, 1
- Jupiter in House 6: aspects Houses 10, 12, 2
- Jupiter in House 7: aspects Houses 11, 1, 3
- Jupiter in House 8: aspects Houses 12, 2, 4
- Jupiter in House 9: aspects Houses 1, 3, 5
- Jupiter in House 10: aspects Houses 2, 4, 6
- Jupiter in House 11: aspects Houses 3, 5, 7
- Jupiter in House 12: aspects Houses 4, 6, 8

**Mars Aspects (4th, 7th, 8th only):**
- Mars in House 1: aspects Houses 4, 7, 8
- Mars in House 2: aspects Houses 5, 8, 9
- Mars in House 3: aspects Houses 6, 9, 10
- Mars in House 4: aspects Houses 7, 10, 11
- Mars in House 5: aspects Houses 8, 11, 12
- Mars in House 6: aspects Houses 9, 12, 1
- Mars in House 7: aspects Houses 10, 1, 2
- Mars in House 8: aspects Houses 11, 2, 3
- Mars in House 9: aspects Houses 12, 3, 4
- Mars in House 10: aspects Houses 1, 4, 5
- Mars in House 11: aspects Houses 2, 5, 6
- Mars in House 12: aspects Houses 3, 6, 7

**All Other Planets (7th aspect only):**
- Planet in House X: aspects House (X+6) mod 12

**CRITICAL:** If your prediction mentions an aspect not on this list, it is a hallucination. DELETE IT.

**16. THE "SOURCE vs TIMER" ENFORCEMENT (CRITICAL):**
The Sun is never the "Why," only the "When."
- **Source Identification:** Every event MUST start by identifying which Dasha Lord (MD/AD/PD) or Heavyweight (Jup/Sat) is "owning" that house this month.
- **The Sun's Role:** Use the Sun ingress ONLY to define the specific 5-day window.
- **Forbidden Logic:** Do not say "Sun enters House X, therefore House X events happen." If House X is not ruled by a Dasha Lord or holding a major planet, that month's intensity must be 'Low' or 'Routine'.

**DASHA FILTER (MANDATORY):**
If the Sun enters a house that is NOT:
1. Ruled by the current MD, AD, or PD Lord, OR
2. Occupied by a Dasha Lord in transit, OR
3. Aspected by a Dasha Lord

Then the intensity for that month MUST be labeled 'Low' and the prediction should focus on the Dasha Lord's long-term aspect instead of the Sun's movement.

**Example:** "March: While the Sun transits your 10th house, this is NOT a career breakthrough month because your MD Lord Saturn is in the 9th house aspecting the 6th house (service). The real focus is on structured service work, not career elevation."

**17. VEDIC ASPECT HARD-CODING:**
You are forbidden from calculating aspects. Use this fixed logic:
- **Saturn:** Aspects [X+2, X+6, X+9] signs from its position.
- **Mars:** Aspects [X+3, X+6, X+7] signs from its position.
- **Jupiter:** Aspects [X+4, X+6, X+8] signs from its position.
If Saturn is in House 9, it aspects 11, 3, and 6. It CANNOT aspect House 4 or 7.

**18. THE "GOLDEN HOUSE" DETECTOR (Double Transit Stunner):**
Search for any house receiving aspects from BOTH Transit Saturn AND Transit Jupiter. If found, this is the "Golden House" of the year.
- Label this in macro_trends as "The Million Dollar Window" or "Major Life Milestone Zone"
- Scenario A for that month MUST be a major life milestone (e.g., Wealth explosion, Birth, Property acquisition, Marriage)
- Explain the contrast: Saturn brings structure/discipline, Jupiter brings expansion/luck, together they create CONCRETE MANIFESTATION

**19. COMPREHENSIVE MANIFESTATION ENGINE:**
For the `possible_manifestations` array, generate AS MANY predictions as possible by examining ALL activated houses:

**STEP 1: Identify ALL Activated Houses**
For the triggering planet, list:
1. Houses it RULES (lordship)
2. House it TRANSITS (current position)
3. Houses it ASPECTS (from transit position)
4. Houses where it CONJOINS other planets

**STEP 2: Generate Predictions for EACH House Combination**
For every combination of activated houses, create a distinct manifestation scenario.

**MANDATORY COUNTS:**
- **ALL Intensities:** MINIMUM 6 manifestations per month
- Generate MORE if multiple houses are activated
- Cover ALL activated houses through lordship, transit, aspects, and conjunctions

**Example:** Mercury (3L, 12L) transits 8H, aspects 2H, conjoins Sun (2L):
- "Short travel (3L) for hidden financial matters (8H/2H)"
- "Expenses (12L) on occult research (8H) affecting family wealth (2H)"
- "Communication (3L) about joint assets (8H) with authority figures (Sun)"
- "Documents/contracts (3L) regarding inheritance (8H) causing expenditure (12L)"
- "Sibling (3L) health crisis (8H/12H) requiring family funds (2H)"
- "Secret correspondence (3L/8H) about foreign expenses (12L)"
- "Research project (8H) requiring communication skills (3L) and financial investment (2H)"
- "Transformation (8H) in how you communicate (3L) about money (2H)"
- "Hidden knowledge (8H) shared through writing/speaking (3L) generating income (2H)"
- "Psychological counseling (8H) involving siblings (3L) and family resources (2H)"
- "Foreign travel (12L) for research (8H) requiring communication (3L)"
- "Mystical studies (8H/12L) taught to others (3L) for income (2H)"

**GOAL:** Generate MAXIMUM manifestations by exploring EVERY possible house combination. There is NO upper limit.

**QUALITY CHECK:** Before finalizing, count your manifestations. EVERY month must have AT LEAST 6 manifestations. Generate more if multiple houses are involved.

**20. THE CONVICTION ENGINE (FORBIDDEN LOGIC ERRORS):**
To sell the user on this product, you must prove you are tracking their specific Dasha Lords:

- **MD/AD/PD Overlordship:** Identify the current MD Lord, AD Lord, and PD Lord from the provided dasha data.
- **The "Source" Test:** Before writing a monthly prediction, ask: "Which house does my MD, AD, or PD Lord occupy or aspect in transit this month?"
- **The "Timer" Demotion:** The Sun's ingress is only relevant if it hits a Dasha Lord (MD/AD/PD). If the Sun enters a house with no Dasha Lord activity, label the month as "Routine Maintenance" and focus on the MD/AD/PD Lord's long-term aspect instead.
- **Example:** "Even though the Sun is in House 4, the REAL story this month is your MD Lord Saturn's 10th aspect on House 6, creating a bridge between your philosophy (9H) and your service (6H)."

**21. THE DOUBLE-ASPECT WEALTH ANCHOR:**
If two slow planets (Saturn/Jupiter/Rahu/Ketu) aspect the same house, that house is 'ON FIRE'.
- **Requirement:** Scan for houses receiving aspects from BOTH Transit Saturn AND Transit Jupiter using the EXACT aspect tables from Section 9.
- **Action:** Highlight this house in EVERY monthly prediction from the month it begins as a secondary 'Wealth Anchor' or 'Life Milestone Zone'.
- **Intensity:** Any month where this double-aspect is active must have at least one High-intensity event related to that house.
- **Example:** "Transit Saturn (9H) aspects 6H via 10th aspect. Transit Jupiter (1H) does NOT aspect 11H (Jupiter only aspects 5th, 7th, 9th from its position). Therefore, there is NO double-aspect on the 11th house."

**CRITICAL ASPECT VERIFICATION:**
Before claiming a double-aspect, you MUST verify using Section 9 tables:
- Jupiter in House 1 aspects: 5, 7, 9 (NOT 11)
- Saturn in House 9 aspects: 11, 3, 6 (NOT 7)
- If your calculation shows a different result, it is WRONG. Use the table.

**22. THE MULTI-VARGA VERIFICATION (MANDATORY):**
You MUST use the Divisional Charts to 'Audit' the D1 transit prediction:

**VARGA AUDIT PROTOCOL:**
1. **Career Events (10H):** Check D1 10th house + D10 (Dashamsha) chart. Is the transit lord strong in D10? If the planet is debilitated or weak in D10, reduce intensity to Low.
2. **Marriage Events (7H):** Check D1 7th house + D9 (Navamsa) chart. Verify the planet's dignity in D9.
3. **Wealth Events (2H/11H):** Check D1 2nd/11th house + D2 (Hora) chart for wealth confirmation.
4. **Property Events (4H):** Check D1 4th house + D4 (Chaturthamsha) chart.
5. **Education Events (5H):** Check D1 5th house + D24 (Chaturvimshamsha) chart.
6. **Health Events (6H/8H):** Check D1 6th/8th house + D30 (Trimshamsha) chart.

**MANDATORY CITATION:**
In the trigger_logic field, you MUST cite the Varga confirmation:
- Example: "Transit Jupiter (10L) enters 1H (D1) + Jupiter is EXALTED in D10 Aries = Career breakthrough confirmed by Dashamsha."
- Counter-example: "Transit Sun enters 10H (D1) but Sun is DEBILITATED in D10 Libra = Career recognition blocked, reduce to Low intensity."

**RULE:** If D1 suggests a material event but the corresponding Varga shows weakness, you MUST reduce the intensity and predict obstacles/delays instead of success.

**23. ASHTAKAVARGA INTENSITY FILTER (MANDATORY):**
Verify EVERY prediction using the Sarvashtakavarga bindu scores from `ashtakavarga['d1_rashi']['sarvashtakavarga']`:

**BINDU INTERPRETATION:**
- **Bindus < 22:** "High Resistance" - The house is BLOCKED. Predict delays, obstacles, or failure to manifest. Intensity must be Low.
- **Bindus 22-24:** "Moderate Resistance" - Events require heavy effort and may face setbacks. Intensity should be Low to Medium.
- **Bindus 25-28:** "Neutral/Routine" - Normal manifestation with standard effort.
- **Bindus 29-30:** "Good Conductivity" - Events manifest with moderate ease.
- **Bindus > 30:** "High Conductivity" - The house is FRUITFUL. Events manifest effortlessly and strongly. Boost intensity to High.

**MANDATORY CITATION:**
In the trigger_logic field, you MUST cite the Bindu count for the transit sign:
- Example: "Transit Sun enters Aquarius (8H) with 22 bindus = Low energy month, transformations blocked, expect frustration rather than breakthroughs."
- Example: "Transit Jupiter enters Cancer (10H) with 35 bindus = Career gains flow effortlessly, high conductivity for recognition."

**CRITICAL RULE:** If a transit enters a sign with < 25 bindus, you are FORBIDDEN from predicting "High Intensity" events. The house lacks the strength to deliver results. Predict delays, obstacles, or internal processing instead.

**24. JAIMINI KARAKA RESONANCE (MANDATORY):**
Use the Chara Karakas from `static_context['chara_karakas']` to identify "Resonance Points":

**KARAKA ACTIVATION:**
- **Atmakaraka (AK):** Soul purpose, self-identity
- **Amatyakaraka (AmK):** Career, profession, advisors
- **Bhratrukaraka (BK):** Siblings, courage, skills
- **Matrukaraka (MK):** Mother, property, emotions
- **Putrakaraka (PK):** Children, creativity, intelligence
- **Gnatikaraka (GK):** Obstacles, enemies, diseases
- **Darakaraka (DK):** Spouse, partnerships

**RESONANCE RULE:**
When a transit planet CONJUNCTS or ASPECTS a Chara Karaka, this is a "Resonance Point" that amplifies the event:
- Example: "Transit Sun conjuncts your Amatyakaraka Mercury in February = Your Career Significator is illuminated, triggering a professional pivot or deep research breakthrough."
- Example: "Transit Saturn aspects your Darakaraka Venus = Your Marriage Significator faces karmic testing, relationship restructuring likely."

**MANDATORY CITATION:**
In the trigger_logic field, cite Karaka activations:
- "KARAKA RESONANCE: Transit [Planet] hits [Karaka Name] [Natal Planet] = [Signification] amplified."

**RULE:** If a transit hits a Chara Karaka, the intensity should be boosted by one level (Low→Medium, Medium→High) due to the soul-level significance.

**25. NAKSHATRA RETURN ACTIVATION (SUPREME TRIGGER):**
When a Dasha Lord (MD/AD/PD) transits through its own NATAL NAKSHATRA, this creates a "Nakshatra Return" - the most powerful resonance activation.

**NAKSHATRA RETURN DETECTION:**
The transit data now includes `nakshatra` and `pada` fields for slow-moving planets (Jupiter, Saturn, Rahu, Ketu).

**PROTOCOL:**
1. **Identify Natal Nakshatra:** Check `planetary_analysis[planet]['nakshatra']['name']` for each Dasha Lord
2. **Check Transit Nakshatra:** Look at `macro_transits_timeline[planet][period]['nakshatra']`
3. **Match Detection:** If transit nakshatra == natal nakshatra = NAKSHATRA RETURN
4. **Intensity Override:** Nakshatra Return = AUTOMATIC High intensity (overrides all other rules including low Ashtakavarga)

**EXAMPLES:**
- "Jupiter (MD Lord) natal nakshatra = Pushya. In May 2026, Transit Jupiter enters Pushya nakshatra (pada 2) = NAKSHATRA RETURN. Jupiter's significations (wisdom, expansion, children, wealth) manifest with supreme power."
- "Saturn (AD Lord) natal nakshatra = Uttara Bhadrapada. In October 2026, Transit Saturn enters Uttara Bhadrapada (pada 1) = NAKSHATRA RETURN. Saturn's karmic lessons intensify to maximum."

**TRIGGER HIERARCHY (UPDATED):**
- **SUPREME TRIGGER (Overrides ALL):** Nakshatra Return of MD/AD/PD Lord
- **PRIMARY TRIGGER:** Dasha Lord sign change or conjunction with natal planet
- **SECONDARY TRIGGER:** Fast planet hits Dasha Lord
- **TERTIARY TRIGGER:** Fast planet transits house ruled by Dasha Lord

**MANDATORY CITATION:**
In trigger_logic field:
- "NAKSHATRA RETURN: [Planet] (MD/AD/PD Lord) transits its natal nakshatra [Name] pada [X] = SUPREME ACTIVATION of [all significations]. Intensity: HIGH (automatic override)."

**CRITICAL RULES:**
1. If ANY Dasha Lord experiences Nakshatra Return, that month MUST have at least one High-intensity event
2. Nakshatra Return overrides low Ashtakavarga scores - the event WILL manifest despite house weakness
3. The manifestation will be related to ALL houses the Dasha Lord rules + the house it transits
4. Pada number indicates the specific flavor: Pada 1 (initiation), Pada 2 (accumulation), Pada 3 (communication), Pada 4 (completion)
5. **MANDATORY OPENING PHRASE:** If Nakshatra Return is detected, you MUST start the prediction with: "⭐ A RARE STAR ALIGNMENT occurs this month: [Planet] returns to its birth nakshatra [Name]..."

**NAKSHATRA NAMING REQUIREMENT:**
For EVERY High/Medium intensity prediction, you MUST explicitly name at least ONE transit nakshatra and explain its effect:
- Example: "Saturn transits Purva Bhadrapada nakshatra (ruled by Jupiter), creating a bridge between discipline and expansion."
- Example: "Jupiter in Punarvasu nakshatra (ruled by Jupiter itself) amplifies wisdom and renewal themes."
- Format: "[Planet] in [Nakshatra Name] nakshatra (ruled by [Lord]) = [Specific effect on user's life]."

**REVERSE NODAL RETURN SPECIFICITY:**
If Transit Rahu/Ketu are in opposite signs from Natal Rahu/Ketu, this is a "Reverse Nodal Return":
- You MUST specify the EXACT life departments being reset
- Example: "Reverse Nodal Return: Rahu in 8H (inherited wealth) ↔ Ketu in 2H (earned wealth) = A karmic reset of your relationship with money - what you inherit vs. what you earn."
- DO NOT use generic phrases like "significant reset" - be SPECIFIC about which houses are involved

**26. SUDARSHANA CHAKRA TRIPLE VERIFICATION (MANDATORY):**
For every High/Medium intensity event, verify activation from THREE perspectives:

**THE THREE CHARTS:**
1. **From Lagna (Ascendant):** Physical manifestation, external events
2. **From Moon:** Emotional/mental experience, inner feelings
3. **From Sun:** Soul purpose, authority, father's influence

**VERIFICATION PROTOCOL:**
- Count houses from Lagna, Moon, and Sun separately
- Check which house the transit activates from each reference point
- If 2+ perspectives show positive activation → High intensity
- If only 1 perspective shows activation → Medium intensity
- If all 3 perspectives show activation → "Triple Confirmation" = Guaranteed manifestation

**EXAMPLE:**
"Transit Jupiter enters Cancer (your 10th house from Lagna, 7th house from Moon, 5th house from Sun):
- From Lagna: Career elevation (10H)
- From Moon: Partnership expansion (7H)
- From Sun: Creative recognition (5H)
= TRIPLE CONFIRMATION: Multi-dimensional success combining career, relationships, and creativity."

**MANDATORY CITATION:**
In trigger_logic field:
- "SUDARSHANA: Transit [Planet] activates [X]H from Lagna, [Y]H from Moon, [Z]H from Sun = [Interpretation]. Confirmation level: [1/2/3 charts]."

**INTENSITY RULE:**
- 3/3 charts confirm = High intensity + "Guaranteed manifestation" label
- 2/3 charts confirm = High intensity
- 1/3 charts confirm = Medium intensity
- 0/3 charts confirm = Low intensity (routine maintenance)

{BHAVA_MANIFESTATION_DISAMBIGUATION_BLOCK}

### OUTPUT JSON STRUCTURE:
{{
    "macro_trends": ["Trend 1", "Trend 2", "Trend 3"],
    "monthly_predictions": [
        {{
            "month_id": 1,
            "focus_areas": ["Career", "Health", "Finance", "Relationships", "Family", "Travel"],
            "events": [
                {{
                    "type": "Event Type",
                    "prediction": "Main narrative combining all house significations",
                    "possible_manifestations": [
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}}
                    ],
                    "trigger_logic": "PRIMARY: ... | SECONDARY: ... | HOUSES INVOLVED: [List ALL activated houses]",
                    "start_date": "2026-02-10",
                    "end_date": "2026-02-18",
                    "intensity": "High"
                }}
            ]
        }}
    ]
}}

**CRITICAL:** The example above shows 8 manifestations for a High-intensity event. You MUST generate AT LEAST this many.

**OPTIONAL USER-FACING SUMMARY LAYER (PREFERRED):**
You may include a top-level `timeline_highlights` array with 3-6 concise execution windows:
[
  {{
    "window": "July 2026",
    "domain": "career",
    "confidence": "high",
    "headline": "Visible career rise or role elevation becomes much more likely",
    "why": "PD lord shifts and receives strong transit reinforcement"
  }}
]
If you include this, keep it month-specific and user-friendly.

**CRITICAL MANIFESTATION FORMAT:**
Each item in possible_manifestations MUST be an object with TWO fields:
1. **"scenario"**: A DETAILED prediction (3-5 sentences) describing:
   - WHAT will happen (the event itself)
   - HOW it will unfold (the process/sequence)
   - WHEN during the period it's most likely
   - WHO or WHAT will be involved
   - The OUTCOME or result

2. **"reasoning"**: A COMPREHENSIVE explanation (4-6 sentences) citing ALL relevant astrological factors:
   - Start with the primary planet and its complete lordship (e.g., "Mercury, ruling your 3rd house of communication and 12th house of expenses...")
   - Explain the transit house and its significations in detail
   - Describe which houses are aspected and why that matters
   - Cite the nakshatra and its lord's influence on the manifestation
   - Include the Ashtakavarga bindu score and what it means for this specific event
   - Mention Varga confirmation if relevant (D10 for career, D9 for marriage, etc.)
   - Explain the Dasha activation if the Dasha Lord is involved
   - Connect all factors into a coherent astrological narrative

**FORBIDDEN:** Short, cryptic reasoning like "Mercury (3L, 12L) transits 8H." This is TOO BRIEF.

**REQUIRED:** Detailed, educational reasoning that teaches the user WHY this prediction is valid.

**EXAMPLE OF CORRECT FORMAT:**
{{
    "scenario": "You may embark on a short journey for confidential financial matters involving inheritance or joint assets. This occurs mid-month when Moon transits supportive signs, requiring discretion with documents and family meetings.",
    "reasoning": "Mercury (3L communication, 12L expenses) transits 8H (secrets/inheritance) aspecting 2H (family wealth), creating a 2-3-8-12 house combination. Transit in Mrigashira nakshatra (Mars-ruled) adds urgency. Aquarius has 22 bindus indicating moderate resistance."
}}

**LENGTH REQUIREMENTS:**
- Scenario: 30-40 words (concise, specific prediction)
- Reasoning: 40-50 words (brief astrological justification)
- Both fields must be clear and direct

**MANDATORY COUNTS (STRICTLY ENFORCED):**
- High Intensity: MINIMUM 6 manifestations (generate more if many houses activated)
- Medium Intensity: MINIMUM 6 manifestations (generate more if many houses activated)
- Low Intensity: MINIMUM 6 manifestations

**CRITICAL:** EVERY month must have AT LEAST 6 manifestations covering ALL activated houses through lordship, transit, aspects, and conjunctions.

**CRITICAL:** Count your manifestations before finalizing. If you have fewer than the minimum, you MUST add more by exploring additional house combinations.
{test_month_suffix}
"""

    def _create_quarter_prompt(self, year: int, age: int, quarter_idx: int, month_ids: List[int]) -> str:
        life_stage_context = self._extract_life_stage_context(age)
        return f"""
You are an expert Vedic Astrologer predicting life events for Quarter {quarter_idx} of {year}.

IMPORTANT:
- Full astrological context is already provided via cached content.
- Do not ask for or expect missing context.

{life_stage_context}

Return ONLY valid JSON with top-level keys: `macro_trends` and `monthly_predictions`.

Output constraints:
1. `monthly_predictions` MUST contain exactly 3 month objects.
2. Allowed `month_id` values are exactly: {month_ids[0]}, {month_ids[1]}, {month_ids[2]}.
3. Do not emit any other month_id.
4. Each month must include `focus_areas` and `events`.
5. For EACH month, `events` must contain at least 6 event objects.
6. For EVERY event, `prediction` is MANDATORY and must be plain-language user-facing text.
7. Put technical astrology reasoning in `activation_reasoning` and/or `trigger_logic`, NOT inside `prediction`.
8. Narrow to month-level timing. For High/Medium events, `start_date` and `end_date` should usually be tighter than the full month when the data allows.
8. NEVER include bracketed debug tags like `[BHAVA-DISAMBIG: ...]` inside `prediction` or scenario text.
9. Each event must include: `type`, `prediction`, `possible_manifestations`, `start_date`, `end_date`, `intensity`.
10. Use strict Vedic aspect logic; do not invent aspects.

Plain-language style for `prediction`:
- 1-3 short sentences.
- Describe what may happen in real life this month.
- Avoid jargon like house numbers, karaka/varga labels, and disambiguation tags.

{BHAVA_MANIFESTATION_DISAMBIGUATION_BLOCK}
"""

    def _get_nakshatra_lord(self, longitude: float) -> str:
        """Helper to get Nakshatra Lord from longitude"""
        lords = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
        nak_idx = int(longitude / 13.333333)
        return lords[nak_idx % 9]

    def _format_chart(self, chart):
        return ", ".join([f"{p}:{d['sign_name']}" for p, d in chart['planets'].items() if p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']])

    async def _get_ai_prediction_async(
        self,
        prompt: str,
        model_override: Any = None,
        llm_log_tag: str = "event_timeline_generation",
    ) -> Dict[str, Any]:
        """Gemini API call for event timeline generation."""
        llm_start = time.time()
        debug_logging = is_debug_logging_enabled()
        token_usage: Dict[str, Any] = {"input_tokens": 0, "output_tokens": 0}
        selected_model = model_override or self.model
        model_name = getattr(selected_model, "model_name", None)

        def run_sync_gemini():
            print("\n" + "="*100)
            print("🚀 STARTING GEMINI API CALL")
            print("="*100)

            if not selected_model:
                print("❌ ERROR: No Gemini model initialized (API Key missing)")
                raise Exception("No API Key")

            print(f"✅ Model initialized: {selected_model}")

            safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in
                     ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                      "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]

            print(f"Prompt length: {len(prompt)} characters")
            print(f"Safety settings: {len(safety)} categories")
            print(f"Response format: application/json")
            print("="*100)

            if debug_logging:
                print("\n📤 FULL REQUEST TO GEMINI (debug_logging_enabled=true):")
                print("="*100)
                print("PROMPT START")
                print("="*100)
                print(prompt)
                print("="*100)
                print("PROMPT END")
                print("="*100)

            print("\n⏳ Calling Gemini API...")
            resp = selected_model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                safety_settings=safety
            )
            print("✅ Gemini API call completed")

            response_text = resp.text
            usage_meta = getattr(resp, "usage_metadata", None)
            usage = {
                "input_tokens": int(getattr(usage_meta, "prompt_token_count", 0) or 0),
                "output_tokens": int(getattr(usage_meta, "candidates_token_count", 0) or 0),
                "cached_tokens": int(getattr(usage_meta, "cached_content_token_count", 0) or 0),
                "total_tokens": int(getattr(usage_meta, "total_token_count", 0) or 0),
            }

            print(f"Response length: {len(response_text)} characters")
            print(
                "Gemini usage: "
                f"input_tokens={usage['input_tokens']} "
                f"output_tokens={usage['output_tokens']} "
                f"cached_tokens={usage['cached_tokens']} "
                f"total_tokens={usage['total_tokens']}"
            )
            print("="*100)
            if debug_logging:
                print("\n📥 FULL RESPONSE FROM GEMINI (debug_logging_enabled=true):")
                print("="*100)
                print("RESPONSE START")
                print("="*100)
                print(response_text)
                print("="*100)
                print("RESPONSE END")
                print("="*100)

            return response_text, usage

        try:
            print("\n🔄 Starting async Gemini call...")
            resp_text, token_usage = await asyncio.to_thread(run_sync_gemini)
            
            print("\n🔄 Parsing JSON response...")
            # Gemini sometimes returns valid JSON plus trailing text.
            # Use raw_decode to parse the first JSON value and ignore the rest.
            cleaned = (resp_text or "").lstrip()
            try:
                parsed_response, end_idx = json.JSONDecoder().raw_decode(cleaned)
                if end_idx < len(cleaned):
                    trailing = cleaned[end_idx:].strip()
                    if trailing:
                        print(f"⚠️ WARNING: Trailing non-JSON content ignored (len={len(trailing)})")
            except json.JSONDecodeError:
                parsed_response = json.loads(cleaned)
            print(f"✅ JSON parsed successfully")
            
            # Handle if Gemini returns a list instead of dict
            if isinstance(parsed_response, list):
                print(f"⚠️ WARNING: Gemini returned a list instead of dict")
                print(f"   - List length: {len(parsed_response)}")
                if parsed_response:
                    print(f"   - First item type: {type(parsed_response[0])}")
                    if isinstance(parsed_response[0], dict):
                        print(f"   - First item keys: {list(parsed_response[0].keys())}")
                        # Check if first item has the expected structure
                        if 'macro_trends' in parsed_response[0] and 'monthly_predictions' in parsed_response[0]:
                            print(f"   - Detected wrapped response, extracting first item")
                            parsed_response = parsed_response[0]
                        elif 'month_id' in parsed_response[0]:
                            print(f"   - Detected month objects, wrapping as monthly_predictions")
                            parsed_response = {"macro_trends": [], "monthly_predictions": parsed_response}
                        else:
                            print(f"   - Unknown structure, returning empty")
                            parsed_response = {"macro_trends": [], "monthly_predictions": []}
                else:
                    print(f"   - Empty list, returning empty structure")
                    parsed_response = {"macro_trends": [], "monthly_predictions": []}

            if not isinstance(parsed_response, dict):
                print(
                    f"\n⚠️ TIMELINE JSON root is not an object: {type(parsed_response).__name__!r}"
                )
                parsed_response = {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                }
            elif parsed_response == {} or "monthly_predictions" not in parsed_response:
                print(
                    "\n⚠️ TIMELINE LLM returned empty object or missing monthly_predictions. "
                    "Raw text (first 4000 chars):"
                )
                print((resp_text or "")[:4000])
                parsed_response = {
                    "macro_trends": [],
                    "monthly_predictions": [],
                    "_timeline_invalid": True,
                }
            else:
                if "macro_trends" not in parsed_response:
                    parsed_response["macro_trends"] = []
                if not isinstance(parsed_response.get("monthly_predictions"), list):
                    print("\n⚠️ monthly_predictions is not a list; treating as failed parse.")
                    parsed_response["monthly_predictions"] = []
                    parsed_response["_timeline_invalid"] = True
                elif len(parsed_response.get("monthly_predictions") or []) == 0:
                    print("\n⚠️ monthly_predictions is empty; treating as failed parse.")
                    parsed_response["_timeline_invalid"] = True
                    parsed_response["error"] = "Timeline model returned zero monthly predictions."

            print(f"   - Keys in response: {list(parsed_response.keys())}")

            if isinstance(parsed_response, dict):
                if "macro_trends" in parsed_response:
                    print(f"   - macro_trends count: {len(parsed_response['macro_trends'])}")
                if "monthly_predictions" in parsed_response:
                    print(
                        f"   - monthly_predictions count: {len(parsed_response['monthly_predictions'])}"
                    )

            llm_ok = not bool(parsed_response.get("_timeline_invalid"))
            if debug_logging:
                log_llm_roundtrip(
                    tag=llm_log_tag,
                    provider="gemini",
                    model=model_name,
                    prompt=prompt,
                    response_text=resp_text,
                    success=llm_ok,
                    error=parsed_response.get("error") if not llm_ok else None,
                    usage=token_usage,
                    elapsed_s=time.time() - llm_start,
                )
            reported_input_tokens = int(token_usage.get("input_tokens") or 0)
            reported_output_tokens = int(token_usage.get("output_tokens") or 0)
            reported_cached_tokens = int(token_usage.get("cached_tokens") or 0)
            reported_non_cached_input_tokens = max(
                reported_input_tokens - reported_cached_tokens,
                0,
            )
            reported_total_tokens = int(token_usage.get("total_tokens") or 0)
            print(
                "\n📊 TIMELINE TOKEN USAGE (model-reported): "
                f"input_tokens={reported_input_tokens} "
                f"output_tokens={reported_output_tokens} "
                f"cached_input_tokens={reported_cached_tokens} "
                f"non_cached_input_tokens={reported_non_cached_input_tokens} "
                f"total_tokens={reported_total_tokens}"
            )
            parsed_response["_llm_usage"] = {
                "input_tokens": reported_input_tokens,
                "output_tokens": reported_output_tokens,
                "cached_tokens": reported_cached_tokens,
                "non_cached_input_tokens": reported_non_cached_input_tokens,
                "total_tokens": reported_total_tokens,
            }
            print("\n✅ TIMELINE LLM call completed - Returning parsed response")
            return parsed_response

        except json.JSONDecodeError as je:
            if debug_logging:
                log_llm_roundtrip(
                    tag=llm_log_tag,
                    provider="gemini",
                    model=model_name,
                    prompt=prompt,
                    response_text=resp_text if "resp_text" in locals() else None,
                    success=False,
                    error=f"json_decode_error: {je}",
                    usage=token_usage,
                    elapsed_s=time.time() - llm_start,
                )
            print(f"\n❌ JSON DECODE ERROR:")
            print(f"   - Error: {str(je)}")
            print(f"   - Response text: {resp_text[:500]}...")
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Timeline JSON parse error: {je}",
            }
        except Exception as e:
            if debug_logging:
                log_llm_roundtrip(
                    tag=llm_log_tag,
                    provider="gemini",
                    model=model_name,
                    prompt=prompt,
                    response_text=resp_text if "resp_text" in locals() else None,
                    success=False,
                    error=str(e),
                    usage=token_usage,
                    elapsed_s=time.time() - llm_start,
                )
            print(f"\n❌ TIMELINE LLM ERROR:")
            print(f"   - Error type: {type(e).__name__}")
            print(f"   - Error message: {str(e)}")
            import traceback
            print(f"   - Traceback:")
            traceback.print_exc()
            return {
                "macro_trends": [],
                "monthly_predictions": [],
                "_timeline_invalid": True,
                "error": f"Timeline LLM request failed: {type(e).__name__}: {e}",
            }
