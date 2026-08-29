"""Create timing metadata for the proof video without modifying its source MP3."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
load_dotenv(ROOT / "backend" / ".env")


def main() -> None:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required")
    genai.configure(api_key=api_key)

    context = json.loads((HERE / "context.json").read_text(encoding="utf-8"))
    audio_path = HERE / "episode-82360-original.mp3"
    uploaded = genai.upload_file(path=str(audio_path), display_name="AstroRoshni podcast 82360 proof")
    try:
        while getattr(uploaded.state, "name", str(uploaded.state)) == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)
        if getattr(uploaded.state, "name", str(uploaded.state)) == "FAILED":
            raise RuntimeError("Gemini audio processing failed")

        source_answer = str(context.get("message_content") or "")
        prompt = f"""Analyze this finished AstroRoshni two-host podcast audio. It is the authoritative soundtrack and must not be rewritten.

Return JSON with this exact top-level shape:
{{
  "title": "short title",
  "duration_seconds": 0,
  "turns": [
    {{"start": 0.0, "end": 4.2, "speaker": "ananya", "text": "spoken words"}}
  ],
  "scenes": [
    {{
      "start": 0.0,
      "end": 22.0,
      "type": "opening",
      "headline": "under 48 characters",
      "supporting": "under 100 characters",
      "houses": [],
      "planets": [],
      "dates": [],
      "keywords": []
    }}
  ]
}}

Requirements:
- Identify Ananya as the female host and Arjun as the male host.
- Create a turn for every speaker change. Use timestamps from the audio and transcribe faithfully.
- Create 12 to 18 visual scenes covering the complete audio without gaps and in chronological order.
- Allowed scene types: opening, natal_chart, house_focus, planet_focus, dasha_timeline, date_window, tension, remedy, action_steps, takeaway, closing.
- Use natal_chart/house_focus/planet_focus only when the podcast actually discusses that evidence.
- Use dasha_timeline/date_window only for timing explicitly spoken in the audio.
- Do not invent a planet, house, date, remedy, chart position or conclusion.
- Extract houses, planets and dates only when spoken. Otherwise use empty arrays.
- Use concise cinematic visible copy, not transcript paragraphs.
- duration_seconds, the final turn end, and the final scene end should match the audio duration closely.
- JSON only. No markdown.

The original answer below is supplied only to improve recognition of astrology terms. The audio remains authoritative:

{source_answer[:16000]}
"""
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            [uploaded, prompt],
            generation_config={"response_mime_type": "application/json", "temperature": 0.15},
        )
        if not response or not response.text:
            raise RuntimeError("Gemini returned no transcript metadata")
        payload = json.loads(response.text)
        (HERE / "transcript.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "turns": len(payload.get("turns") or []),
                    "scenes": len(payload.get("scenes") or []),
                    "duration_seconds": payload.get("duration_seconds"),
                }
            )
        )
    finally:
        try:
            genai.delete_file(uploaded.name)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())

