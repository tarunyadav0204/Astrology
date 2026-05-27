import asyncio
import json
import os
import sys
import types

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _ensure_google_stub():
    try:
        import google.generativeai  # noqa: F401
        return
    except ModuleNotFoundError:
        google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
        genai_mod = types.ModuleType("google.generativeai")

        class _StubGenerativeModel:
            def __init__(self, *args, **kwargs):
                self._model_name = kwargs.get("model_name", "stub-model")

            async def generate_content_async(self, *args, **kwargs):
                raise RuntimeError("Stub model should be overridden in tests")

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


_ensure_google_stub()

from ai.intent_router import IntentRouter


class _FakeResponse:
    def __init__(self, payload):
        self.text = json.dumps(payload)


class _FakeModel:
    def __init__(self, payload):
        self.payload = payload
        self._model_name = "fake-intent-model"

    async def generate_content_async(self, prompt, request_options=None):
        return _FakeResponse(self.payload)


class _TestRouter(IntentRouter):
    def __init__(self, payload):
        super().__init__()
        self._payload = payload

    def _get_model(self):
        return _FakeModel(self._payload)


def test_instant_router_allows_clarify_for_broad_question():
    payload = {
        "status": "CLARIFY",
        "clarification_question": "Do you want career, relationship, or money first?",
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "extracted_context": {},
        "context_type": "birth",
        "category": "general",
        "needs_transits": False,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "Tell me about my life",
            [],
            clarification_count=0,
            max_clarifications=3,
            language="english",
        )
    )
    assert result["status"] == "CLARIFY"
    assert result["chart_insights"] == []
    assert "career" in result["clarification_question"].lower()


def test_instant_router_not_limited_to_single_clarification():
    payload = {
        "status": "CLARIFY",
        "clarification_question": "Is this about career timing or relationship timing?",
        "mode": "LIFESPAN_EVENT_TIMING",
        "extracted_context": {},
        "context_type": "birth",
        "category": "timing",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "When will it happen?",
            [{"question": "Tell me what happens", "response": "Please specify the topic."}],
            clarification_count=1,
            max_clarifications=3,
            language="english",
        )
    )
    assert result["status"] == "CLARIFY"
    assert result["category"] == "timing"


def test_instant_router_keeps_ready_for_straightforward_daily():
    payload = {
        "status": "READY",
        "mode": "PREDICT_DAILY",
        "daily_intent_confirmed": True,
        "extracted_context": {"specific_date": "2026-05-02", "specific_date_basis": "relative_user_day"},
        "context_type": "birth",
        "category": "general",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
        "transit_request": {
            "startYear": 2026,
            "endYear": 2026,
            "yearMonthMap": {"2026": ["May"]},
        },
    }
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "How is tomorrow for me?",
            [],
            clarification_count=0,
            max_clarifications=3,
            language="english",
            query_context={
                "timezone_name": "Asia/Kolkata",
                "utc_offset_minutes": 330,
                "client_now_iso": "2026-05-01T08:00:00Z",
            },
        )
    )
    assert result["status"] == "READY"
    assert result["mode"] == "PREDICT_DAILY"
    assert result["extracted_context"]["specific_date"] == "2026-05-02"


def test_instant_router_refines_marriage_from_weak_timing_category():
    payload = {
        "status": "READY",
        "mode": "LIFESPAN_EVENT_TIMING",
        "extracted_context": {},
        "context_type": "birth",
        "category": "timing",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "When will I get married?",
            [],
            clarification_count=0,
            max_clarifications=3,
            language="english",
        )
    )
    assert result["category"] == "marriage"
    assert result["mode"] == "LIFESPAN_EVENT_TIMING"


def test_instant_router_normalizes_predict_event_timing_and_refines_job():
    payload = {
        "status": "READY",
        "mode": "PREDICT_EVENT_TIMING",
        "extracted_context": {},
        "context_type": "birth",
        "category": "general",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "When will I get a job?",
            [],
            clarification_count=0,
            max_clarifications=3,
            language="english",
        )
    )
    assert result["mode"] == "LIFESPAN_EVENT_TIMING"
    assert result["category"] == "job"


if __name__ == "__main__":
    test_instant_router_allows_clarify_for_broad_question()
    test_instant_router_not_limited_to_single_clarification()
    test_instant_router_keeps_ready_for_straightforward_daily()
    test_instant_router_refines_marriage_from_weak_timing_category()
    test_instant_router_normalizes_predict_event_timing_and_refines_job()
    print("instant intent router tests passed")
