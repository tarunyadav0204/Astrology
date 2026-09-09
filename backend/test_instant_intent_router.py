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

import ai.intent_router as intent_router_module
from ai.intent_router import IntentRouter, apply_semantic_resolution_cadence


def test_semantic_operational_cadence_bounds_any_active_process_without_text_parsing():
    for category, state, cadence, expected_days in (
        ("career", "pending_external", "days_to_weeks", 45),
        ("education", "awaiting_result", "weeks_to_months", 45),
        ("property", "in_progress", "months_to_year", 365),
        ("relationship", "submitted", "hours_to_days", 10),
    ):
        result = {
            "category": category,
            "answer_mode": "event_prediction",
            "temporal_intent": {
                "event_state": state,
                "expected_cadence": cadence,
                "explicit_timeframe": False,
            },
            "evidence_plan": {
                "question_parts": [{"part_id": "p1", "timeframe": {"kind": "open_future"}}]
            },
            "extracted_context": {},
        }
        apply_semantic_resolution_cadence(result)
        timeframe = result["evidence_plan"]["question_parts"][0]["timeframe"]
        assert timeframe["kind"] == "bounded_future"
        assert timeframe["duration_days"] == expected_days


def test_pending_single_step_is_capped_even_when_router_cadence_is_too_broad():
    result = {
        "answer_mode": "event_prediction",
        "temporal_intent": {
            "event_state": "pending_external",
            "expected_cadence": "weeks_to_months",
            "explicit_timeframe": False,
        },
        "evidence_plan": {
            "question_parts": [{"part_id": "p1", "timeframe": {"kind": "open_future"}}]
        },
    }
    apply_semantic_resolution_cadence(result)
    timeframe = result["evidence_plan"]["question_parts"][0]["timeframe"]
    assert timeframe["duration_days"] == 45


def test_explicit_extended_institutional_process_can_use_longer_horizon():
    result = {
        "answer_mode": "event_prediction",
        "temporal_intent": {
            "event_state": "pending_external",
            "expected_cadence": "months_to_year",
            "process_scale": "extended_institutional",
            "explicit_timeframe": False,
        },
        "evidence_plan": {
            "question_parts": [{"part_id": "p1", "timeframe": {"kind": "open_future"}}]
        },
    }
    apply_semantic_resolution_cadence(result)
    timeframe = result["evidence_plan"]["question_parts"][0]["timeframe"]
    assert timeframe["duration_days"] == 180


def test_routine_operational_scale_overrides_an_overly_broad_cadence():
    result = {
        "answer_mode": "event_prediction",
        "temporal_intent": {
            "event_state": "pending_external",
            "expected_cadence": "months_to_year",
            "process_scale": "routine_operational",
            "explicit_timeframe": False,
        },
        "evidence_plan": {
            "question_parts": [{"part_id": "p1", "timeframe": {"kind": "open_future"}}]
        },
    }
    apply_semantic_resolution_cadence(result)
    timeframe = result["evidence_plan"]["question_parts"][0]["timeframe"]
    assert timeframe["duration_days"] == 45


def test_implicit_router_bounded_window_is_replaced_by_operational_scope():
    result = {
        "answer_mode": "event_prediction",
        "temporal_intent": {
            "event_state": "pending_external",
            "expected_cadence": "weeks_to_months",
            "process_scale": "routine_operational",
            "explicit_timeframe": False,
        },
        "evidence_plan": {
            "question_parts": [{
                "part_id": "p1",
                "timeframe": {"kind": "bounded_future", "duration_months": 6},
            }]
        },
    }
    apply_semantic_resolution_cadence(result)
    timeframe = result["evidence_plan"]["question_parts"][0]["timeframe"]
    assert timeframe == {
        "kind": "bounded_future",
        "duration_days": 45,
        "granularity": "week",
        "source": "semantic_operational_cadence",
    }


def test_semantic_operational_cadence_never_overrides_user_stated_horizon():
    result = {
        "answer_mode": "event_prediction",
        "temporal_intent": {
            "event_state": "pending_external",
            "expected_cadence": "days_to_weeks",
            "explicit_timeframe": True,
        },
        "evidence_plan": {
            "question_parts": [{"part_id": "p1", "timeframe": {"kind": "bounded_future", "duration_months": 6}}]
        },
    }
    apply_semantic_resolution_cadence(result)
    assert result["evidence_plan"]["question_parts"][0]["timeframe"]["duration_months"] == 6


def test_love_marriage_pathway_guard_removes_generic_timing_contract():
    result = {
        "category": "marriage",
        "marriage_subtype": "love_vs_arranged",
        "mode": "LIFESPAN_EVENT_TIMING",
        "answer_mode": "event_prediction",
        "needs_transits": True,
        "period_window": {"kind": "current", "start": "2026-09-07", "end": "2026-09-07"},
        "evidence_plan": {
            "question_parts": [{
                "life_domain": "marriage",
                "event_profile": "marriage",
                "intent_families": ["event_timing"],
            }],
            "evidence_needs": [
                {"kind": "future_dasha_event_windows"},
                {"kind": "transit_event_windows"},
            ],
        },
    }

    intent_router_module.apply_marriage_routing_guards(result)

    assert result["answer_mode"] == "comparison_choice"
    assert result["mode"] == "ANALYZE_TOPIC_POTENTIAL"
    assert result["needs_transits"] is False
    assert "period_window" not in result
    part = result["evidence_plan"]["question_parts"][0]
    assert part["life_domain"] == "marriage"
    assert part["event_profile"] == "love_vs_arranged_marriage"
    assert part["intent_families"] == ["comparison"]
    assert part["timeframe"]["kind"] == "none"
    assert {row["kind"] for row in result["evidence_plan"]["evidence_needs"]} == {
        "natal_topic_foundation", "divisional_chart_context", "house_analysis",
    }


def test_love_marriage_event_profile_recovers_missing_top_level_subtype():
    result = {
        "category": "marriage",
        "answer_mode": "event_prediction",
        "evidence_plan": {
            "question_parts": [{"event_profile": "love_vs_arranged_marriage"}],
            "evidence_needs": [],
        },
    }

    intent_router_module.apply_marriage_routing_guards(result)

    assert result["marriage_subtype"] == "love_vs_arranged"
    assert result["answer_mode"] == "comparison_choice"


class _FakeResponse:
    def __init__(self, payload):
        self.text = json.dumps(payload)


class _FakeModel:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.prompts = []
        self._model_name = "fake-intent-model"

    async def generate_content_async(self, prompt, request_options=None):
        self.prompts.append(prompt)
        if not self.payloads:
            raise AssertionError("No fake intent response remains")
        return _FakeResponse(self.payloads.pop(0))


class _TestRouter(IntentRouter):
    def __init__(self, payload):
        payloads = payload if isinstance(payload, list) else [payload]
        self._fake_model = _FakeModel(payloads)

    def _get_instant_model(self):
        return self._fake_model

    def _get_instant_model_name(self):
        return self._fake_model._model_name

    async def _generate_instant_content(self, prompt, model_name, timeout_s):
        return await self._fake_model.generate_content_async(prompt)


class _TimeoutThenSuccessRouter(_TestRouter):
    def __init__(self, payload):
        super().__init__(payload)
        self.attempts = 0

    async def _generate_instant_content(self, prompt, model_name, timeout_s):
        self.attempts += 1
        if self.attempts == 1:
            raise TimeoutError()
        return await super()._generate_instant_content(prompt, model_name, timeout_s)


def test_instant_intent_model_uses_admin_selected_instant_model(monkeypatch):
    monkeypatch.setattr(intent_router_module, "get_instant_chat_model", lambda: "deepseek-chat")
    router = IntentRouter.__new__(IntentRouter)
    assert router._get_instant_model_name() == "deepseek-chat"


def test_instant_intent_generation_uses_deepseek_when_selected(monkeypatch):
    request_args = {}

    class _FakeCompletions:
        async def create(self, **kwargs):
            request_args.update(kwargs)
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"status":"READY"}'))],
                usage=types.SimpleNamespace(
                    prompt_tokens=12,
                    completion_tokens=4,
                    total_tokens=16,
                    prompt_tokens_details=types.SimpleNamespace(cached_tokens=2),
                ),
            )

    class _FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.chat = types.SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(AsyncOpenAI=_FakeAsyncOpenAI))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        intent_router_module,
        "get_instant_chat_llm_provider",
        lambda: intent_router_module.CHAT_LLM_DEEPSEEK,
    )

    router = IntentRouter.__new__(IntentRouter)
    response = asyncio.run(router._generate_instant_content("route this", "deepseek-chat", 5.0))

    assert response.text == '{"status":"READY"}'
    assert response.usage_metadata.prompt_token_count == 12
    assert response.usage_metadata.cached_content_token_count == 2
    assert request_args["model"] == "deepseek-chat"
    assert request_args["extra_body"] == {"thinking": {"type": "disabled"}}


def test_instant_router_retries_builtin_timeout_with_empty_message(monkeypatch):
    payload = _with_dialogue_state(
        {
            "status": "READY",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "answer_mode": "topic_reading",
            "extracted_context": {},
            "context_type": "birth",
            "category": "career",
            "needs_transits": False,
            "divisional_charts": ["D1", "D10"],
        }
    )
    router = _TimeoutThenSuccessRouter(payload)
    monkeypatch.setattr(intent_router_module.asyncio, "sleep", lambda *_: _async_noop())

    result = asyncio.run(
        router.classify_instant_intent(
            "How is my career overall?",
            [],
            language="english",
        )
    )

    assert router.attempts == 2
    assert result["status"] == "READY"
    assert result["category"] == "career"


async def _async_noop():
    return None


def _with_dialogue_state(payload):
    payload = dict(payload)
    status = str(payload.get("status") or "READY").upper()
    question = str(payload.get("clarification_question") or "").strip()
    payload.setdefault(
        "dialogue_state",
        {
            "request_summary": "test request",
            "known_facts": {},
            "unresolved_facts": ["topic"] if status == "CLARIFY" else [],
            "corrections": [],
            "ready_to_calculate": status == "READY",
            "readiness_reason": "test fixture",
            "last_clarification_question": question if status == "CLARIFY" else "",
        },
    )
    return payload


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
    router = _TestRouter(_with_dialogue_state(payload))
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
    router = _TestRouter(_with_dialogue_state(payload))
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
    router = _TestRouter(_with_dialogue_state(payload))
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


def test_instant_router_does_not_reinterpret_marriage_in_python():
    payload = {
        "status": "READY",
        "mode": "LIFESPAN_EVENT_TIMING",
        "extracted_context": {},
        "context_type": "birth",
        "category": "timing",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(_with_dialogue_state(payload))
    result = asyncio.run(
        router.classify_instant_intent(
            "When will I get married?",
            [],
            clarification_count=0,
            max_clarifications=3,
            language="english",
        )
    )
    assert result["category"] == "timing"
    assert result["mode"] == "LIFESPAN_EVENT_TIMING"


def test_instant_router_normalizes_mode_but_does_not_reinterpret_job_in_python():
    payload = {
        "status": "READY",
        "mode": "PREDICT_EVENT_TIMING",
        "extracted_context": {},
        "context_type": "birth",
        "category": "general",
        "needs_transits": True,
        "divisional_charts": ["D1", "D9"],
    }
    router = _TestRouter(_with_dialogue_state(payload))
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
    assert result["category"] == "general"


def test_instant_router_repairs_repeated_clarification_with_llm():
    repeated = _with_dialogue_state(
        {
            "status": "CLARIFY",
            "clarification_question": "Who does he refer to?",
            "mode": "LIFESPAN_EVENT_TIMING",
            "extracted_context": {},
            "context_type": "birth",
            "category": "relationship",
            "needs_transits": True,
            "divisional_charts": ["D1", "D9"],
        }
    )
    repeated["dialogue_state"]["unresolved_facts"] = ["identity_of_subject"]
    repaired = _with_dialogue_state(
        {
            "status": "READY",
            "clarification_question": "",
            "mode": "LIFESPAN_EVENT_TIMING",
            "target_subject_key": "spouse",
            "extracted_context": {},
            "context_type": "birth",
            "category": "relationship",
            "needs_transits": True,
            "divisional_charts": ["D1", "D9"],
        }
    )
    repaired["dialogue_state"]["known_facts"] = {"identity_of_subject": "spouse"}

    router = _TestRouter([repeated, repaired])
    result = asyncio.run(
        router.classify_instant_intent(
            "Will he come back?\nspouse",
            [],
            clarification_count=1,
            language="english",
            dialogue_state={
                "request_summary": "Whether he will return",
                "known_facts": {},
                "unresolved_facts": ["identity_of_subject"],
                "corrections": [],
                "ready_to_calculate": False,
                "last_clarification_question": "Who does he refer to?",
            },
            latest_user_reply="spouse",
        )
    )

    assert result["status"] == "READY"
    assert result["target_subject_key"] == "spouse"
    assert result["dialogue_state"]["unresolved_facts"] == []
    assert len(router._fake_model.prompts) == 2
    assert "CONTRACT REPAIR" in router._fake_model.prompts[1]


def test_new_remedy_request_discards_abandoned_marriage_clarification():
    payload = _with_dialogue_state(
        {
            "turn_relation": "new_request",
            "explicit_remedy_request": True,
            "status": "READY",
            "clarification_question": "",
            "route_action": "answer",
            "mode": "RECOMMEND_REMEDY_FOR_PROBLEM",
            "answer_mode": "remedy_action",
            "category": "career",
            "target_subject_key": "self",
            "extracted_context": {},
            "context_type": "birth",
            "needs_transits": False,
            "divisional_charts": ["D1", "D10"],
            "dialogue_state": {
                "request_summary": "Career remedies",
                "known_facts": {"topic": "career"},
                "unresolved_facts": [],
                "corrections": [],
                "ready_to_calculate": True,
                "readiness_reason": "Direct remedy request",
                "last_clarification_question": "",
            },
        }
    )
    router = _TestRouter(payload)
    result = asyncio.run(
        router.classify_instant_intent(
            "When will I get married? What about her career and family?\nShow my career remedies",
            [],
            clarification_count=1,
            language="english",
            dialogue_state={
                "request_summary": "Marriage timing or future spouse career and family",
                "known_facts": {"topic": "marriage"},
                "unresolved_facts": ["which_question_first"],
                "corrections": [],
                "ready_to_calculate": False,
                "last_clarification_question": "Which topic should I answer first?",
            },
            latest_user_reply="Show my career remedies",
        )
    )

    assert result["status"] == "READY"
    assert result["turn_relation"] == "new_request"
    assert result["explicit_remedy_request"] is True
    assert result["category"] == "career"
    assert result["answer_mode"] == "remedy_action"
    assert result["dialogue_state"]["known_facts"] == {"topic": "career"}
    assert result["dialogue_state"]["unresolved_facts"] == []


if __name__ == "__main__":
    test_instant_router_allows_clarify_for_broad_question()
    test_instant_router_not_limited_to_single_clarification()
    test_instant_router_keeps_ready_for_straightforward_daily()
    test_instant_router_does_not_reinterpret_marriage_in_python()
    test_instant_router_normalizes_mode_but_does_not_reinterpret_job_in_python()
    test_instant_router_repairs_repeated_clarification_with_llm()
    print("instant intent router tests passed")
