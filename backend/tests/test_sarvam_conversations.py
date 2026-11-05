import asyncio
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ai import sarvam_conversations


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [{"message": {"content": "A concise reply."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }


class _Client:
    captured = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, *, headers, json):
        type(self).captured = {"url": url, "headers": headers, "json": json}
        return _Response()


def test_compose_uses_conversations_model_without_reasoning(monkeypatch):
    from utils import admin_settings
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: {"sarvam_api_key": "test-key"}.get(key))
    monkeypatch.setattr(sarvam_conversations.httpx, "AsyncClient", _Client)

    result = asyncio.run(sarvam_conversations.compose(
        system_prompt="Be concise.", prompt="Hello", timeout_s=5,
    ))

    assert result["text"] == "A concise reply."
    assert result["usage"]["input_tokens"] == 10
    assert _Client.captured["url"] == "https://api.sarvam.ai/v1/chat/completions"
    assert _Client.captured["json"]["model"] == "sarvam-105b-conversations"
    assert _Client.captured["json"]["reasoning_effort"] is None
    assert _Client.captured["json"]["stream"] is False


def test_verified_sarvam_agent_uses_supported_output_limit(monkeypatch):
    """Sarvam rejects the old 6,000-token Verified request with HTTP 422."""
    import copy
    import httpx
    from chat import verified_chat_pipeline as pipeline

    captured = []

    class Response:
        def __init__(self, payload):
            self.payload = payload
            self.is_error = False

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class Client:
        calls = 0

        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            captured.append(copy.deepcopy(json))
            type(self).calls += 1
            if type(self).calls == 1:
                message = {"content": None, "tool_calls": [{
                    "id": "baseline", "type": "function",
                    "function": {"name": "get_instant_baseline", "arguments": "{}"},
                }]}
            elif type(self).calls == 2:
                message = {"content": "Evidence inspected.", "tool_calls": []}
            else:
                message = {"content": None, "tool_calls": [{
                    "id": "final", "type": "function",
                    "function": {
                        "name": "submit_verified_answer",
                        "arguments": '{"answer":"An evidence-based verified answer.","fact_ids":[]}',
                    },
                }]}
            return Response({"choices": [{"message": message}], "usage": {}})

    monkeypatch.setattr(pipeline, "get_sarvam_api_key", lambda: "test-key")
    monkeypatch.setattr(httpx, "AsyncClient", Client)

    result = asyncio.run(pipeline.run_sarvam_verified_calculator_agent(
        question="Tell me about my career.", language="english", birth_data={},
        instant_context={}, history=[], model_name="sarvam-105b-conversations", timeout_s=60,
    ))

    assert result["success"] is True
    assert captured
    assert all(payload["max_tokens"] == 4096 for payload in captured)
    assert all(payload["reasoning_effort"] is None for payload in captured)
    assert captured[-1]["tool_choice"] == {
        "type": "function", "function": {"name": "submit_verified_answer"},
    }
    assert any(
        tool["function"]["name"] == "submit_verified_answer"
        for tool in captured[-1]["tools"]
    )
    assistant_tool_message = captured[1]["messages"][-2]
    assert assistant_tool_message["role"] == "assistant"
    assert "content" not in assistant_tool_message


def test_sarvam_tool_payload_compacts_each_evidence_branch():
    from chat.verified_chat_pipeline import _compact_sarvam_tool_payload

    payload = {
        "natal": {"facts": "N" * 12_000},
        "dasha": {"facts": "D" * 12_000},
        "topic": {"facts": "T" * 12_000},
    }
    compact = _compact_sarvam_tool_payload(payload, 9_000)

    assert set(compact) == {"natal", "dasha", "topic"}
    assert all(value["truncated"] is True for value in compact.values())


def test_verified_sarvam_fact_ledger_rejects_wrong_career_identities():
    from chat.verified_chat_pipeline import _validate_sarvam_verified_fact_ledger

    ledger = {
        "D1": {"tenth_lord": "Venus", "house_lordships": {"Venus": [3, 10]}},
        "D10": {"planet_placements": {"Venus": {"dignity": "neutral"}}},
        "divisional_charts": {"D10": {"Venus": {"dignity": "neutral"}}},
        "ashtakavarga": {
            "10": {"bav": {"Saturn": 4}},
            "4": {"bav": {"Mercury": 4}},
        },
    }
    answer = (
        "Mercury is the lord of your 10th house. Venus is exalted in D10. "
        "The BAV for Saturn in House 10 is 3. The BAV for Mercury in House 4 is 6."
    )

    errors = _validate_sarvam_verified_fact_ledger(answer, ledger)

    assert any("Mercury" in error and "House 10 lord" in error for error in errors)
    assert any("D10 Venus dignity" in error for error in errors)
    assert any("Saturn BAV" in error for error in errors)
    assert any("Mercury BAV" in error for error in errors)


def test_verified_sarvam_fact_ledger_rejects_wrong_divisional_house():
    from chat.verified_chat_pipeline import _validate_sarvam_verified_fact_ledger

    ledger = {
        "D1": {"house_lordships": {}, "planet_placements": {}},
        "D10": {"planet_placements": {"Mars": {"house": 5, "dignity": "exalted"}}},
        "divisional_charts": {"D10": {"Mars": {"house": 5, "dignity": "exalted"}}},
        "ashtakavarga": {}, "current_dashas": {},
    }

    errors = _validate_sarvam_verified_fact_ledger(
        "Mars is exalted in the tenth house of D10.", ledger,
    )

    assert any("D10 Mars" in error and "House 5" in error for error in errors)


def test_verified_sarvam_fact_ledger_rejects_wrong_pratyantardasha_lord():
    from chat.verified_chat_pipeline import _validate_sarvam_verified_fact_ledger

    ledger = {
        "D1": {"house_lordships": {}, "planet_placements": {}},
        "D10": {}, "divisional_charts": {}, "ashtakavarga": {},
        "current_dashas": {"pratyantardasha": {"planet": "Mercury"}},
    }

    errors = _validate_sarvam_verified_fact_ledger(
        "You are in the Mercury-Jupiter sub-period (PD).", ledger,
    )

    assert any("Current PD is Mercury" in error for error in errors)


def test_verified_sarvam_hidden_fact_ids_are_language_neutral():
    from chat.verified_chat_pipeline import (
        _sarvam_verified_fact_ids,
        _strip_sarvam_verified_fact_ids,
        _validate_sarvam_verified_fact_ids,
    )

    ledger = {
        "D1": {"house_lordships": {"Venus": [10]}, "planet_placements": {}},
        "D10": {},
        "divisional_charts": {"D9": {"Saturn": {"house": 6, "sign_name": "Libra", "dignity": "exalted"}}},
        "ashtakavarga": {}, "current_dashas": {},
    }
    fact_ids = _sarvam_verified_fact_ids(ledger)
    marker = "[[FACT:D1:Venus:LORD:H10]]"
    tamil_answer = f"உங்கள் தொழில் வீட்டின் அதிபதி சுக்கிரன். {marker}"

    assert _validate_sarvam_verified_fact_ids(tamil_answer, fact_ids) == []
    assert _validate_sarvam_verified_fact_ids("[[FACT:D9:Saturn:HOUSE:6]]", fact_ids) == []
    assert marker not in _strip_sarvam_verified_fact_ids(tamil_answer)
    assert _validate_sarvam_verified_fact_ids("உங்கள் தொழில் பாதை நல்லது.", fact_ids)


def test_verified_sarvam_accepts_dasha_id_aliases_and_natal_house():
    from chat.verified_chat_pipeline import _sarvam_verified_fact_ids, _validate_sarvam_verified_fact_ids

    ledger = {
        "D1": {"house_lordships": {}, "planet_placements": {"Jupiter": {"house": 4}, "Mercury": {"house": 4}}},
        "D10": {}, "ashtakavarga": {},
        "current_dashas": {"md": {"planet": "Jupiter"}, "ad": {"planet": "Mercury"}, "pd": {"planet": "Mercury"}},
    }
    fact_ids = _sarvam_verified_fact_ids(ledger)
    ids = "[[FACT:Dasha:MD:Jupiter]] [[FACT:Dasha:MD:H4]] [[FACT:Dasha:AD:Mercury]] [[FACT:Dasha:PD:Mercury]]"

    assert _validate_sarvam_verified_fact_ids(ids, fact_ids) == []


def test_verified_sarvam_invalid_calculator_arguments_do_not_abort(monkeypatch):
    import copy
    import httpx
    from chat import verified_chat_pipeline as pipeline

    class Response:
        is_error = False

        def __init__(self, message):
            self.message = message

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": self.message}], "usage": {}}

    class Client:
        calls = 0
        payloads = []

        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            type(self).payloads.append(copy.deepcopy(json))
            type(self).calls += 1
            if type(self).calls == 1:
                message = {"content": None, "tool_calls": [{"id": "baseline", "type": "function", "function": {"name": "get_instant_baseline", "arguments": "{}"}}]}
            elif type(self).calls == 2:
                message = {"content": None, "tool_calls": [{"id": "invalid", "type": "function", "function": {"name": "get_deterministic_evidence", "arguments": '{\"capability_id\": \"parashari.divisional_confirmation\", \"parameters\": {\"divisions\": [120]}}'}}]}
            elif type(self).calls == 3:
                message = {"content": "Use the baseline.", "tool_calls": []}
            else:
                message = {"content": "A verified answer."}
            return Response(message)

    monkeypatch.setattr(pipeline, "get_sarvam_api_key", lambda: "test-key")
    monkeypatch.setattr(pipeline, "_calculate_requested_capabilities", lambda *args: (_ for _ in ()).throw(ValueError("Unsupported divisional chart")))
    monkeypatch.setattr(httpx, "AsyncClient", Client)

    result = asyncio.run(pipeline.run_sarvam_verified_calculator_agent(
        question="Health", language="english", birth_data={}, instant_context={}, history=[],
        model_name="sarvam-105b", timeout_s=60,
    ))

    assert result["success"] is True
    tool_message = Client.payloads[2]["messages"][-1]
    assert "invalid_calculator_parameters" in tool_message["content"]
