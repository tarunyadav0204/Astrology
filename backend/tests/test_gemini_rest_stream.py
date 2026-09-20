import json
import unittest
from unittest.mock import patch

from ai.gemini_chat_analyzer import (
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
