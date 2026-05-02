import os
import sys
import types

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    import google.generativeai  # noqa: F401
except ModuleNotFoundError:
    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    genai_mod = types.ModuleType("google.generativeai")

    class _StubGenerativeModel:
        def __init__(self, *args, **kwargs):
            self._model_name = "stub-model"

    class _StubGenerationConfig:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

    def _configure(**kwargs):
        return None

    genai_mod.GenerativeModel = _StubGenerativeModel
    genai_mod.GenerationConfig = _StubGenerationConfig
    genai_mod.configure = _configure
    sys.modules["google.generativeai"] = genai_mod
    setattr(google_mod, "generativeai", genai_mod)

from ai.intent_router import _extract_month_window_from_question, _extract_specific_date_from_question, _is_transient_intent_error, apply_transit_timing_guards
from utils.query_context import resolve_query_now


def test_extract_specific_date_from_relative_day():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    assert _extract_specific_date_from_question("How is tomorrow for me?", now=now) == "2026-04-23"
    assert _extract_specific_date_from_question("What about day after tomorrow?", now=now) == "2026-04-24"


def test_extract_specific_date_from_explicit_month_day():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    assert _extract_specific_date_from_question("What happens on March 16th?", now=now) == "2026-03-16"
    assert _extract_specific_date_from_question("What happens on 16 March 2027?", now=now) == "2027-03-16"


def test_apply_transit_timing_guards_sets_exact_day_fields():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    result = {
        "category": "general",
        "mode": "ANALYZE_PERSONALITY",
        "extracted_context": {},
        "needs_transits": False,
    }
    apply_transit_timing_guards(result, "How is tomorrow?", current_year=2026, now=now)
    assert result["mode"] == "PREDICT_DAILY"
    assert result["context_type"] == "birth"
    assert result["analysis_type"] == "DAILY_PREDICTION"
    assert result["needs_transits"] is True
    assert result["dasha_as_of"] == "2026-04-23"
    assert result["transit_request"]["startYear"] == 2026
    assert result["transit_request"]["yearMonthMap"] == {"2026": ["April"]}


def test_apply_transit_timing_guards_prefers_llm_specific_date():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    result = {
        "category": "general",
        "mode": "ANALYZE_PERSONALITY",
        "extracted_context": {"specific_date": "2028-09-12"},
        "needs_transits": False,
    }
    apply_transit_timing_guards(result, "What will happen on that day I mentioned in September 2028?", current_year=2026, now=now)
    assert result["mode"] == "PREDICT_DAILY"
    assert result["dasha_as_of"] == "2028-09-12"
    assert result["transit_request"]["startYear"] == 2028
    assert result["transit_request"]["yearMonthMap"] == {"2028": ["September"]}


def test_extract_month_window_from_month_year_question():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    out = _extract_month_window_from_question("What will happen in October 2026?", now=now)
    assert out == {"year": 2026, "month": "October", "timeframe": "October 2026"}


def test_apply_transit_timing_guards_sets_month_window_for_month_year_question():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    result = {
        "category": "general",
        "mode": "ANALYZE_PERSONALITY",
        "extracted_context": {"timeframe": "October 2026"},
        "needs_transits": False,
    }
    apply_transit_timing_guards(result, "What will happen in October 2026?", current_year=2026, now=now)
    assert result["mode"] == "PREDICT_PERIOD_OUTLOOK"
    assert result["context_type"] == "birth"
    assert result["analysis_type"] == "PERIOD_OUTLOOK"
    assert result["needs_transits"] is True
    assert "dasha_as_of" not in result
    assert result["transit_request"]["startYear"] == 2026
    assert result["transit_request"]["yearMonthMap"] == {"2026": ["October"]}
    assert result["extracted_context"]["timeframe"] == "October 2026"
    assert "specific_date" not in result["extracted_context"]


def test_resolve_query_now_prefers_client_local_time():
    qc = {
        "timezone_name": "America/New_York",
        "utc_offset_minutes": -240,
        "client_now_iso": "2026-04-30T03:30:00Z",
    }
    resolved = resolve_query_now(qc)
    assert resolved.strftime("%Y-%m-%d") == "2026-04-29"


def test_transient_intent_error_detection_catches_prefill_cancellation():
    err = Exception("504 Thread is cancelled before we get prefill results.; Failed to close the streaming context; status = CANCELLED")
    assert _is_transient_intent_error(err) is True
