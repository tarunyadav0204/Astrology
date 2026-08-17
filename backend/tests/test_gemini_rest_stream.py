import json
import unittest
from unittest.mock import patch

from ai.gemini_chat_analyzer import generate_content_rest_v1beta_stream_result


class _FakeStreamResponse:
    ok = True
    status_code = 200
    encoding = None
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
                    "totalTokenCount": 9,
                },
            },
        ]
        for event in events:
            line = f"data: {json.dumps(event)}"
            yield line if decode_unicode else line.encode("utf-8")


class GeminiRestStreamTests(unittest.TestCase):
    @patch("requests.post")
    def test_stream_emits_only_visible_text_and_returns_usage(self, post):
        post.return_value = _FakeStreamResponse()
        progress = []

        result = generate_content_rest_v1beta_stream_result(
            "gemini-3.1-flash-lite-preview",
            "answer briefly",
            "test-key",
            thinking_level="low",
            on_text_delta=lambda delta, full: progress.append((delta, full)),
        )

        self.assertEqual(result["text"], "Hello world")
        self.assertEqual(progress, [("Hello", "Hello"), (" world", "Hello world")])
        self.assertEqual(result["usage"]["input_tokens"], 7)
        self.assertEqual(result["usage"]["output_tokens"], 2)
        self.assertEqual(result["transport"], "genai_rest_stream")
        self.assertTrue(post.call_args.kwargs["stream"])
        self.assertEqual(post.call_args.kwargs["params"]["alt"], "sse")
        self.assertEqual(post.return_value.iter_lines_chunk_size, 1)


if __name__ == "__main__":
    unittest.main()
