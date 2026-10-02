import json
import unittest
from unittest.mock import patch

import asyncio

from ai.gemini_chat_analyzer import (
    generate_content_rest_v1beta_async_result,
    generate_content_rest_v1beta_async_stream_result,
    generate_content_rest_v1beta_result,
    generate_content_rest_v1beta_stream_result,
)


class _FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return {
            "candidates": [{"content": {"parts": [{"text": '{"monthly_predictions": []}'}]}}],
            "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 3},
        }


class _FakeStreamResponse:
    ok = True
    status_code = 200
    # Requests uses this fallback for text/event-stream when the response has
    # no charset. Production code must override it before decoding Hindi.
    encoding = "ISO-8859-1"
    iter_lines_chunk_size = None

    def iter_lines(self, chunk_size=512, decode_unicode=False):
        self.iter_lines_chunk_size = chunk_size
        events = [
            {
                "candidates": [
                    {"content": {"parts": [{"text": "private reasoning", "thought": True}]}}
                ]
            },
            {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]},
            {
                "candidates": [{"content": {"parts": [{"text": " world"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 7,
                    "candidatesTokenCount": 2,
                    "cachedContentTokenCount": 5,
                    "totalTokenCount": 9,
                },
            },
        ]
        for event in events:
            line = f"data: {json.dumps(event, ensure_ascii=False)}".encode("utf-8")
            yield line.decode(self.encoding) if decode_unicode else line


class GeminiRestStreamTests(unittest.TestCase):
    def test_async_stream_emits_visible_text_and_uses_header_auth(self):
        calls = {}

        class _AsyncStreamResponse:
            is_success = True
            status_code = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def aiter_lines(self):
                events = [
                    {"candidates": [{"content": {"parts": [{"text": "hidden", "thought": True}]}}]},
                    {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]},
                    {
                        "candidates": [{"content": {"parts": [{"text": " world"}]}}],
                        "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 2},
                    },
                ]
                for event in events:
                    yield f"data: {json.dumps(event)}"

        class _AsyncClient:
            def __init__(self, **kwargs):
                calls["client_kwargs"] = kwargs

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            def stream(self, method, url, **kwargs):
                calls.update(method=method, url=url, kwargs=kwargs)
                return _AsyncStreamResponse()

        progress = []
        with patch("httpx.AsyncClient", _AsyncClient):
            result = asyncio.run(
                generate_content_rest_v1beta_async_stream_result(
                    "models/gemini-3-flash-preview",
                    "answer",
                    "secret-test-key",
                    thinking_level="low",
                    on_text_delta=lambda delta, full: progress.append((delta, full)),
                    timeout_s=6,
                )
            )

        self.assertEqual(result["text"], "Hello world")
        self.assertEqual(progress, [("Hello", "Hello"), (" world", "Hello world")])
        self.assertEqual(result["transport"], "genai_rest_async_stream")
        self.assertEqual(calls["kwargs"]["headers"], {"x-goog-api-key": "secret-test-key"})
        self.assertEqual(calls["kwargs"]["params"], {"alt": "sse"})

    def test_async_transport_uses_header_auth_and_returns_usage(self):
        calls = {}

        class _AsyncResponse:
            is_success = True
            status_code = 200

            def json(self):
                return _FakeResponse().json()

        class _AsyncClient:
            def __init__(self, **kwargs):
                calls["client_kwargs"] = kwargs

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, **kwargs):
                calls["url"] = url
                calls["post_kwargs"] = kwargs
                return _AsyncResponse()

        with patch("httpx.AsyncClient", _AsyncClient):
            result = asyncio.run(
                generate_content_rest_v1beta_async_result(
                    "models/gemini-3.1-flash-lite",
                    "route this",
                    "secret-test-key",
                    thinking_level="minimal",
                    response_mime_type="application/json",
                    timeout_s=6,
                )
            )

        self.assertEqual(result["transport"], "genai_rest_async")
        self.assertEqual(result["usage"]["input_tokens"], 4)
        self.assertEqual(calls["post_kwargs"]["headers"], {"x-goog-api-key": "secret-test-key"})
        self.assertNotIn("secret-test-key", calls["url"])
        config = calls["post_kwargs"]["json"]["generationConfig"]
        self.assertEqual(config["thinkingConfig"], {"thinkingLevel": "minimal"})
        self.assertEqual(config["responseMimeType"], "application/json")

    @patch("requests.post")
    def test_non_stream_supports_low_thinking_and_json_output(self, post):
        post.return_value = _FakeResponse()

        result = generate_content_rest_v1beta_result(
            "models/gemini-3-flash-preview",
            "write timeline copy",
            "test-key",
            thinking_level="low",
            response_mime_type="application/json",
            timeout_s=45,
        )

        config = post.call_args.kwargs["json"]["generationConfig"]
        self.assertEqual(config["thinkingConfig"], {"thinkingLevel": "low"})
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertEqual(post.call_args.kwargs["timeout"], 45.0)
        self.assertEqual(result["usage"]["total_tokens"], 0)

    @patch("requests.post")
    def test_stream_emits_only_visible_text_and_returns_usage(self, post):
        post.return_value = _FakeStreamResponse()
        progress = []

        result = generate_content_rest_v1beta_stream_result(
            "gemini-3.1-flash-lite-preview",
            "answer briefly",
            "test-key",
            thinking_level="low",
            system_prompt="stable system rules",
            on_text_delta=lambda delta, full: progress.append((delta, full)),
        )

        self.assertEqual(result["text"], "Hello world")
        self.assertEqual(progress, [("Hello", "Hello"), (" world", "Hello world")])
        self.assertEqual(result["usage"]["input_tokens"], 7)
        self.assertEqual(result["usage"]["output_tokens"], 2)
        self.assertEqual(result["usage"]["cached_tokens"], 5)
        self.assertEqual(result["usage"]["non_cached_input_tokens"], 2)
        self.assertEqual(result["transport"], "genai_rest_stream")
        self.assertTrue(post.call_args.kwargs["stream"])
        self.assertEqual(post.call_args.kwargs["params"]["alt"], "sse")
        self.assertEqual(
            post.call_args.kwargs["json"]["systemInstruction"],
            {"parts": [{"text": "stable system rules"}]},
        )
        self.assertEqual(
            post.call_args.kwargs["json"]["contents"],
            [{"role": "user", "parts": [{"text": "answer briefly"}]}],
        )
        self.assertEqual(post.return_value.iter_lines_chunk_size, 1)
        self.assertEqual(post.return_value.encoding, "utf-8")

    @patch("requests.post")
    def test_stream_rejects_a_response_with_a_dropped_sse_event(self, post):
        class _MalformedResponse(_FakeStreamResponse):
            def iter_lines(self, chunk_size=512, decode_unicode=False):
                self.iter_lines_chunk_size = chunk_size
                lines = [
                    b'data: {"candidates":[{"content":{"parts":[{"text":"first"}]}}]}',
                    b'data: {"candidates": invalid json}',
                    b'data: {"candidates":[{"content":{"parts":[{"text":" last"}]}}]}',
                ]
                for line in lines:
                    yield line.decode(self.encoding) if decode_unicode else line

        post.return_value = _MalformedResponse()

        with self.assertRaisesRegex(RuntimeError, "malformed SSE event"):
            generate_content_rest_v1beta_stream_result(
                "gemini-3-flash-preview",
                "answer in Hindi",
                "test-key",
            )


if __name__ == "__main__":
    unittest.main()
