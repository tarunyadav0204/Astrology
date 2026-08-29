from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
import base64
import os
import re
import html
import hashlib
from google.cloud import texttospeech
from google.cloud import texttospeech_v1beta1 as texttospeech_beta
import logging
import asyncio
import time
from datetime import datetime
from functools import partial
from pydantic import BaseModel
from types import SimpleNamespace
from typing import Optional, Union

from auth import get_current_user, User
from db import get_conn, execute
from credits.credit_service import CreditService
from credits.routes import _get_play_credentials
from tts.podcast_narrator import (
  PODCAST_BODY_MAX_SPOKEN_WORDS,
  constrain_podcast_script,
  generate_podcast_script,
)
from tts.podcast_cache import get_cached_audio, put_cached_audio
from tts.podcast_visual_cache import get_visual_json, put_visual_json
from tts.podcast_visuals import (
  add_audio_durations_to_source,
  generate_visual_manifest,
  mp3_duration_ms,
  referenced_divisions,
  referenced_houses,
  visual_source,
  visual_source_from_message,
)
from tts import notebook_lm_podcast
from activity.publisher import publish_activity
from utils.env_json import parse_json_from_env
from utils.admin_settings import (
  get_podcast_provider,
  get_podcast_tts_voices,
  get_speech_tts_voice,
  PODCAST_PROVIDER_NOTEBOOK_LM,
)

credit_service = CreditService()
_podcast_history_table_ready = False


def _ensure_podcast_history_table():
    global _podcast_history_table_ready
    if _podcast_history_table_ready:
        return
    with get_conn() as conn:
        execute(conn, """
            CREATE TABLE IF NOT EXISTS podcast_history (
                id SERIAL PRIMARY KEY,
                userid INTEGER NOT NULL,
                message_id TEXT NOT NULL,
                session_id TEXT,
                lang TEXT NOT NULL DEFAULT 'en',
                preview TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(userid, message_id, lang)
            )
        """)
        execute(conn, "ALTER TABLE podcast_history ADD COLUMN IF NOT EXISTS birth_chart_id BIGINT")
        conn.commit()
    _podcast_history_table_ready = True


def _add_podcast_history(userid: int, message_id: str, session_id: Optional[str], lang: str, preview: Optional[str], birth_chart_id: Optional[int] = None):
    if not message_id or not str(message_id).strip():
        return
    _ensure_podcast_history_table()
    preview_trim = (preview or "")[:500].strip() or None
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO podcast_history (userid, message_id, session_id, lang, preview, birth_chart_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT(userid, message_id, lang) DO UPDATE SET
                session_id = COALESCE(EXCLUDED.session_id, podcast_history.session_id),
                preview = COALESCE(EXCLUDED.preview, podcast_history.preview),
                birth_chart_id = COALESCE(EXCLUDED.birth_chart_id, podcast_history.birth_chart_id),
                created_at = CURRENT_TIMESTAMP
            """,
            (userid, str(message_id).strip(), session_id or None, (lang or "en").strip()[:10], preview_trim, birth_chart_id),
        )
        conn.commit()


def _premium_podcast_included(userid: int, message_id: Optional[str]) -> bool:
    """Trust the stored answer tier, never a client-supplied Premium flag."""
    if not message_id:
        return False
    try:
        mid = int(str(message_id).strip())
    except (TypeError, ValueError):
        return False
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT COALESCE(cm.chat_tier, 'standard')
                FROM chat_messages cm
                INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
                WHERE cm.message_id = %s
                  AND cm.sender = 'assistant'
                  AND cs.user_id = %s
                LIMIT 1
                """,
                (mid, userid),
            )
            row = cur.fetchone()
        return bool(row and str(row[0] or '').strip().lower() == 'premium')
    except Exception:
        logger.exception("Podcast: failed to verify Premium inclusion message_id=%s user_id=%s", message_id, userid)
        return False

# TTS credential order: (1) GOOGLE_TTS_SERVICE_ACCOUNT_JSON if set, else (2) GOOGLE_SERVICE_ACCOUNT_KEY
# (inline JSON from tradebest where billing is enabled), else (3) Play credentials. This way the same
# key you use as GOOGLE_SERVICE_ACCOUNT_KEY (tradebest) can drive TTS without a separate env var.
TTS_CREDENTIALS_ENV = "GOOGLE_TTS_SERVICE_ACCOUNT_JSON"
TTS_CREDENTIALS_ENV_ALT = "GOOGLE_SERVICE_ACCOUNT_KEY"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tts", tags=["tts"])
_SPOKEN_TTS_CACHE: dict[str, str] = {}
_FAST_SPEECH_VOICE_EN = os.getenv("SPEECH_TTS_FAST_VOICE_EN", "en-IN-Neural2-A")
_FAST_SPEECH_VOICE_HI = os.getenv("SPEECH_TTS_FAST_VOICE_HI", "hi-IN-Neural2-A")


def _env_flag(name: str, default: bool = False) -> bool:
  raw = os.getenv(name)
  if raw is None:
    return default
  return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_live_speech_voice(lang: str, requested_voice_name: Optional[str] = None) -> str:
  """
  Live speech should honor the admin-selected brand voice by default. If we need
  emergency speed mode, SPEECH_TTS_FAST_VOICE=true swaps Chirp to a faster voice.
  """
  resolved = requested_voice_name or get_speech_tts_voice(lang or "en")
  if requested_voice_name or not _env_flag("SPEECH_TTS_FAST_VOICE", False):
    return resolved
  if "chirp" not in str(resolved or "").lower():
    return resolved
  normalized_lang = str(lang or "en").lower()
  return _FAST_SPEECH_VOICE_HI if normalized_lang.startswith("hi") else _FAST_SPEECH_VOICE_EN


def _build_voice_and_config(lang: str, voice_name: Optional[str] = None):
  lang = (lang or "en").lower()
  resolved_voice_name = voice_name or get_speech_tts_voice(lang)
  if resolved_voice_name:
    parts = resolved_voice_name.split("-")
    language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else ("hi-IN" if lang.startswith("hi") else "en-IN")
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=resolved_voice_name)
  audio_kwargs = {
    "audio_encoding": texttospeech.AudioEncoding.MP3,
  }
  if _voice_family(resolved_voice_name) != "journey":
    audio_kwargs["speaking_rate"] = 0.95
  audio_config = texttospeech.AudioConfig(**audio_kwargs)
  return voice, audio_config


def _build_beta_voice_and_config(lang: str, voice_name: Optional[str] = None):
  lang = (lang or "en").lower()
  resolved_voice_name = voice_name or get_speech_tts_voice(lang)
  if resolved_voice_name:
    parts = resolved_voice_name.split("-")
    language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else ("hi-IN" if lang.startswith("hi") else "en-IN")
    voice = texttospeech_beta.VoiceSelectionParams(language_code=language_code, name=resolved_voice_name)
  audio_config = texttospeech_beta.AudioConfig(
    audio_encoding=texttospeech_beta.AudioEncoding.MP3,
    speaking_rate=0.95,
  )
  return voice, audio_config


def _voice_supports_word_mark_timepoints(voice_name: Optional[str]) -> bool:
  name = str(voice_name or "").lower().strip()
  if not name:
    return True
  # Premium voice families sound worse with per-word SSML marks in speech chat.
  if "chirp" in name or "studio" in name:
    return False
  return True


def _voice_family(voice_name: Optional[str]) -> str:
  name = str(voice_name or "").lower()
  if "journey" in name:
    return "journey"
  if "studio" in name:
    return "studio"
  if "chirp" in name:
    return "chirp"
  if "neural2" in name:
    return "neural2"
  if "wavenet" in name:
    return "wavenet"
  return "standard"


def _is_indic_voice(voice_name: Optional[str]) -> bool:
  parts = str(voice_name or "").split("-")
  return len(parts) >= 2 and parts[1].upper() == "IN"


def _ssml_mode_for_voice(voice_name: Optional[str]) -> str:
  """
  Journey/Studio reject SSML. Chirp3 verbalizes punctuation, so those voices need
  break-only SSML. Neural2/Wavenet (including en-IN) already pause at commas and
  periods — converting punctuation into extra <break> tags stacks silence,
  which is especially obvious on the faster male host.
  """
  family = _voice_family(voice_name)
  if family in ("journey", "studio"):
    return "plain"
  if family == "chirp":
    return "breaks"
  if family in ("neural2", "wavenet") or _is_indic_voice(voice_name):
    return "cues"
  return "full"


def _is_invalid_tts_argument(exc: Exception) -> bool:
  if type(exc).__name__ == "InvalidArgument":
    return True
  msg = str(exc).lower()
  return "invalid argument" in msg or "400" in msg


def _language_code_from_voice_name(voice_name: Optional[str], fallback: str = "en-GB") -> str:
  parts = str(voice_name or "").split("-")
  if len(parts) >= 2 and len(parts[0]) == 2 and parts[1]:
    return f"{parts[0]}-{parts[1]}"
  return fallback


def _podcast_voices(lang: str) -> tuple[str, str, str]:
  """
  Return (female_voice_name, male_voice_name, language_code) for podcast.
  Voices come from admin settings, with Chirp3 HD defaults.
  """
  female, male = get_podcast_tts_voices(lang)
  fallback = "hi-IN" if str(lang or "").lower().startswith("hi") else "en-GB"
  return female, male, _language_code_from_voice_name(female, fallback)


def _podcast_audio_config(role: str, voice_name: Optional[str] = None, *, minimal: bool = False):
  """
  Chirp3 HD honors AudioConfig speaking_rate more reliably than nested SSML <prosody>.
  Journey and some Indic voices 400 if speaking_rate or volume_gain_db is set.
  """
  encoding = texttospeech.AudioEncoding.MP3
  if minimal:
    return texttospeech.AudioConfig(audio_encoding=encoding)
  family = _voice_family(voice_name)
  speaking_rate = 1.15 if role == "male" else 1.0
  if family == "journey":
    return texttospeech.AudioConfig(audio_encoding=encoding)
  if _is_indic_voice(voice_name):
    return texttospeech.AudioConfig(audio_encoding=encoding, speaking_rate=speaking_rate)
  return texttospeech.AudioConfig(
    audio_encoding=encoding,
    speaking_rate=speaking_rate,
    volume_gain_db=10.0,
  )


# Sanskrit/Vedic terms that Google TTS often mispronounces. alias = spelling TTS will speak.
# Order matters: longer phrases first so "Dharma Karma Yoga" is matched before "Dharma".
_PRONUNCIATION_ALIASES: list[tuple[str, str]] = [
  ("Dharma Karma Yoga", "Dhurma Karma Yo-ga"),
  ("Chara Dasha", "Chuh-raa Daa-sha"),
  ("Parashari", "Pa-raa-sha-ree"),
  ("Jaimini", "Jaa-mee-nee"),
  ("Nadi astrology", "Naa-dee astrology"),
  ("Nadi", "Naa-dee"),
  ("Dharma", "Dhurma"),
  ("Karma", "Kar-ma"),
  ("Yoga", "Yo-ga"),
  ("Dasha", "Daa-sha"),
  ("Mahadasha", "Maa-ha-daa-sha"),
  ("Antardasha", "Un-tur-daa-sha"),
  ("Nakshatra", "Nuk-shuh-tra"),
  ("Drishti", "Drish-tee"),
  ("Graha", "Gruh-ha"),
  ("Rashi", "Raa-shee"),
  ("Bhava", "Baa-va"),
  ("Lagna", "Lug-na"),
  ("Panchang", "Pun-chung"),
  ("Sade Sati", "Saa-day Saa-tee"),
  ("Vipat Tara", "Vi-pat Ta-ra")
]


def _strip_literal_punctuation_words(text: str) -> str:
  """
  Gemini and Chirp3 sometimes introduce spoken punctuation ('comma', 'dot').
  Strip those words. Do not strip 'period' — it is used in 'time period'.
  """
  if not text:
    return text
  text = re.sub(
    r"\b(?:question[\s-]*mark|exclamation[\s-]*(?:mark|point)|full[\s-]*stop)s?\b",
    "",
    text,
    flags=re.IGNORECASE,
  )
  text = re.sub(
    r"\b(?:commas?|dots?|semicolons?|colons?)\b",
    "",
    text,
    flags=re.IGNORECASE,
  )
  text = re.sub(r"\s+([,.;:?!।])", r"\1", text)
  text = re.sub(r"\s{2,}", " ", text)
  return text


def _collapse_adjacent_breaks(text: str) -> str:
  def _pick(match: re.Match) -> str:
    times = [int(x) for x in re.findall(r'time="(\d+)ms"', match.group(0))]
    return f'<break time="{max(times) if times else 200}ms"/>'

  return re.sub(r'(?:<break time="\d+ms"/>\s*){2,}', _pick, text)


def _replace_spoken_punctuation_with_breaks(text: str) -> str:
  """
  Chirp3 HD often verbalizes ',', '.', '?', and dashes as 'comma' / 'dot'.
  Turn leftover punctuation into SSML breaks, leaving existing tags alone.
  """
  if not text:
    return text
  parts = re.split(r"(<[^>]+>)", text)
  out: list[str] = []
  for part in parts:
    if part.startswith("<") and part.endswith(">"):
      out.append(part)
      continue
    chunk = part
    chunk = re.sub(r"\.{3,}", '<break time="280ms"/>', chunk)
    chunk = chunk.replace("…", '<break time="280ms"/>')
    chunk = re.sub(r"[.?!।]+", '<break time="380ms"/>', chunk)
    chunk = re.sub(r"[,;:]+", '<break time="160ms"/>', chunk)
    chunk = re.sub(r"\s*[—–]\s*", '<break time="160ms"/>', chunk)
    chunk = re.sub(r"\s+-\s+", '<break time="160ms"/>', chunk)
    out.append(chunk)
  return _collapse_adjacent_breaks("".join(out))


def _escape_ssml_text(text: str) -> str:
  """
  Chirp3 speaks numeric entities like &#x27; as "hash x 27".
  Decode entities first, then escape only XML-significant characters.
  Apostrophes and quotes stay as real characters inside SSML text nodes.
  """
  decoded = html.unescape(str(text or ""))
  return html.escape(decoded, quote=False)


def _apply_pronunciation_ssml(text: str) -> str:
  """Wrap known Sanskrit/astrology terms in <sub alias="..."> so Google TTS pronounces them better."""
  text = _strip_literal_punctuation_words(text)
  for term, alias in _PRONUNCIATION_ALIASES:
    if term in text:
      safe_alias = html.escape(alias, quote=False)
      # Pronounce using alias, but wrap in moderate emphasis so Vedic terms carry a bit more weight
      # and blend better into the surrounding prosody.
      text = text.replace(
        term,
        f'<emphasis level="moderate"><sub alias="{safe_alias}">{term}</sub></emphasis>',
      )
  return text


def _apply_pronunciation_plain(text: str, *, compact_hyphens: bool = False) -> str:
  """Replace terms with phonetic spelling for plain-text TTS (no SSML). Used by /tts/synthesize."""
  text = _strip_literal_punctuation_words(text)
  for term, alias in _PRONUNCIATION_ALIASES:
    spoken = alias.replace("-", "") if compact_hyphens else alias
    text = text.replace(term, spoken)
  return text


def _tighten_male_breaks(text: str, *, extra_short: bool = False) -> str:
  """SSML <break> is wall-clock silence and does not scale with speaking_rate."""
  replacements = [
    ('<break time="1300ms"/>', '<break time="700ms"/>' if extra_short else '<break time="950ms"/>'),
    ('<break time="900ms"/>', '<break time="320ms"/>' if extra_short else '<break time="650ms"/>'),
    ('<break time="420ms"/>', '<break time="160ms"/>' if extra_short else '<break time="220ms"/>'),
    ('<break time="380ms"/>', '<break time="160ms"/>' if extra_short else '<break time="240ms"/>'),
    ('<break time="160ms"/>', '<break time="70ms"/>' if extra_short else '<break time="90ms"/>'),
  ]
  for old, new in replacements:
    text = text.replace(old, new)
  return text


def _strip_followups_block(text: str) -> str:
  raw = str(text or "")
  raw = re.sub(
    r"###FOLLOW_UPS_START###.*?###FOLLOW_UPS_END###",
    " ",
    raw,
    flags=re.DOTALL | re.IGNORECASE,
  )
  return raw


def _fallback_spoken_tts_text(text: str, lang: str) -> str:
  """Cheap cleanup so even fallback TTS sounds less like a report being read aloud."""
  raw = _strip_followups_block(text)
  raw = re.sub(r"<[^>]+>", " ", raw)
  raw = re.sub(r"\*\*(.*?)\*\*", r"\1", raw)
  raw = re.sub(r"\*(.*?)\*", r"\1", raw)
  raw = re.sub(r"^#+\s*", "", raw, flags=re.MULTILINE)
  raw = re.sub(r"[-–—]{2,}", ". ", raw)
  raw = re.sub(r"\n+", " ", raw)
  raw = re.sub(r"\s{2,}", " ", raw).strip()
  if not raw:
    return ""

  spoken = raw
  spoken = re.sub(r"\s*:\s*", ": ", spoken)
  spoken = re.sub(r"\s*;\s*", ". [PAUSE:short] ", spoken)
  spoken = re.sub(r"\s*,\s*", ", [PAUSE:short] ", spoken)
  spoken = re.sub(r"([.?!।])\s+", r"\1 [PAUSE:medium] ", spoken)
  spoken = re.sub(r"\s{2,}", " ", spoken).strip()
  return spoken


def _strip_spoken_control_cues_for_plain_tts(text: str) -> str:
  """Remove pause/emphasis control cues before sending text to non-SSML TTS."""
  cleaned = str(text or "")
  cleaned = re.sub(
    r"\[\s*PAUS[EC]\s*:\s*(?:short|medium|long)\s*\]",
    ". ",
    cleaned,
    flags=re.IGNORECASE,
  )
  cleaned = re.sub(
    r"\bPAUS[EC][\s:_-]+(?:short|medium|long)\b",
    ". ",
    cleaned,
    flags=re.IGNORECASE,
  )
  cleaned = re.sub(
    r"\[\s*(?:EMPHASIS|RISE|FALL|SLOW)\s*:\s*([^\]]+)\]",
    r"\1",
    cleaned,
    flags=re.IGNORECASE,
  )
  cleaned = re.sub(r"\s+([,.?!।])", r"\1", cleaned)
  cleaned = re.sub(r"([,.?!।]){2,}", r"\1", cleaned)
  cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
  return cleaned


def _prepare_spoken_tts_text(text: str, lang: str) -> str:
  """
  Rewrite answer text into a more naturally speakable single-speaker script with pause cues.
  Falls back to deterministic cleanup when Gemini or credentials are unavailable.
  """
  normalized_lang = "hi" if str(lang or "en").lower().startswith("hi") else "en"
  base_text = _fallback_spoken_tts_text(text, normalized_lang)
  if not base_text:
    return ""

  cache_key = hashlib.sha1(f"{normalized_lang}::{base_text}".encode("utf-8")).hexdigest()
  cached = _SPOKEN_TTS_CACHE.get(cache_key)
  if cached:
    return cached

  try:
    from utils.admin_settings import CHAT_LLM_DEEPSEEK, get_analysis_llm_vendor

    if get_analysis_llm_vendor() == CHAT_LLM_DEEPSEEK:
      if not os.getenv("DEEPSEEK_API_KEY"):
        return base_text
      from ai.analysis_llm_backend import build_analysis_llm_model

      model, _, _ = build_analysis_llm_model()
    else:
      import google.generativeai as genai
      from utils.admin_settings import get_gemini_analysis_model

      api_key = os.getenv("GEMINI_API_KEY")
      if not api_key:
        return base_text

      genai.configure(api_key=api_key)
      model_name = os.getenv("GEMINI_SPEECH_TTS_MODEL") or os.getenv("GEMINI_PODCAST_MODEL") or get_gemini_analysis_model()
      model = genai.GenerativeModel(model_name)

    language_instruction = (
      "Write the ENTIRE response in natural spoken Hindi (Devanagari), warm and conversational, "
      "like a trusted guide speaking aloud. Avoid stiff bookish phrasing."
      if normalized_lang == "hi"
      else "Write in natural spoken English, warm and conversational, like a trusted guide speaking aloud."
    )

    prompt = f"""Rewrite the following assistant answer so it sounds natural when spoken aloud by ONE person.

Rules:
- Preserve the exact meaning, facts, timing, names, and recommendations. Do not add or remove facts.
- Make it sound spoken, not read from a report.
- Prefer shorter spoken sentences and natural transitions.
- Insert pause cues where helpful: [PAUSE:short], [PAUSE:medium], [PAUSE:long].
- Use pause cues sparingly but deliberately so the voice can breathe.
- Do NOT add speaker labels, markdown, bullets, JSON, or explanations.
- Return only the rewritten script.

{language_instruction}

Original answer:
{base_text}
"""

    response = model.generate_content(prompt)
    shaped = str(getattr(response, "text", "") or "").strip()
    if not shaped:
      return base_text
    shaped = _strip_followups_block(shaped)
    shaped = re.sub(r"\s{2,}", " ", shaped).strip()
    if not shaped:
      return base_text
    _SPOKEN_TTS_CACHE[cache_key] = shaped
    if len(_SPOKEN_TTS_CACHE) > 128:
      _SPOKEN_TTS_CACHE.pop(next(iter(_SPOKEN_TTS_CACHE)))
    logger.info("TTS: prepared spoken script via Gemini (lang=%s, in_chars=%s, out_chars=%s)", normalized_lang, len(base_text), len(shaped))
    return shaped
  except Exception as e:
    logger.warning("TTS: spoken script shaping fallback due to error: %s", e)
    return base_text


def _segment_text_to_plain(segment_text: str) -> str:
  text = html.unescape(str(segment_text or ""))
  text = _strip_literal_punctuation_words(text)
  text = _apply_pronunciation_plain(text)
  text = re.sub(r"\[PAUSE:(?:short|medium|long)\]", ". ", text, flags=re.IGNORECASE)
  text = re.sub(r"\[(?:EMPHASIS|RISE|FALL|SLOW):([^\]]+)\]", r"\1", text, flags=re.IGNORECASE)
  return _strip_spoken_control_cues_for_plain_tts(text)


def _segment_text_to_ssml(segment_text: str, role: str = "female", ssml_mode: str = "full") -> str:
  """
  Convert segment text with cues to SSML for Google TTS.
  Cues: [PAUSE:*], [EMPHASIS:...], [RISE:...], [FALL:...], [SLOW:...].
  Wraps in <prosody> so female and male sound distinct.
  Applies pronunciation aliases for Sanskrit/Vedic terms (Parashari, Jaimini, Nadi, etc.).
  """
  if not segment_text or not segment_text.strip():
    return "<speak></speak>"
  # Simple deterministic hash so prosody variation is stable per segment but not identical everywhere
  base_hash = sum(ord(ch) for ch in segment_text)

  # Escape XML in the text so we can safely insert SSML tags
  text = _escape_ssml_text(_strip_literal_punctuation_words(segment_text.strip()))
  if ssml_mode in ("breaks", "cues"):
    # Neural2 treats "Daa-sha" hyphens as extra pauses; compact those aliases.
    text = _apply_pronunciation_plain(text, compact_hyphens=(ssml_mode == "cues"))
  else:
    # Improve pronunciation of Sanskrit/astrology terms via SSML <sub alias="...">
    text = _apply_pronunciation_ssml(text)
  # Pauses — defaults; we will further tighten them for the male host below so he sounds less choppy.
  text = re.sub(r"\[PAUSE:short\]", '<break time="420ms"/>', text, flags=re.IGNORECASE)
  text = re.sub(r"\[PAUSE:medium\]", '<break time="900ms"/>', text, flags=re.IGNORECASE)
  text = re.sub(r"\[PAUSE:long\]", '<break time="1300ms"/>', text, flags=re.IGNORECASE)
  if ssml_mode in ("breaks", "cues"):
    text = re.sub(r"\[(?:EMPHASIS|RISE|FALL|SLOW):([^\]]+)\]", r"\1", text, flags=re.IGNORECASE)
    if ssml_mode == "breaks":
      text = _replace_spoken_punctuation_with_breaks(text)
    if role == "male":
      text = _tighten_male_breaks(text, extra_short=(ssml_mode == "cues"))
    return f"<speak>{text}</speak>"

  # Emphasis — strong so it stands out from neutral tone
  text = re.sub(
    r"\[EMPHASIS:([^\]]+)\]",
    r'<emphasis level="strong">\1</emphasis>',
    text,
    flags=re.IGNORECASE,
  )

  # Intonation — add small deterministic variation so questions don't all sound identical
  def _rise_repl(match: re.Match) -> str:
    phrase = match.group(1)
    local = (base_hash + sum(ord(c) for c in phrase)) % 3
    # Slightly different upward pitches / rates
    if local == 0:
      pitch, rate = "+0.8st", "100%"
    elif local == 1:
      pitch, rate = "+1.2st", "103%"
    else:
      pitch, rate = "+1.5st", "98%"
    return f'<prosody pitch="{pitch}" rate="{rate}">{phrase}</prosody>'

  def _fall_repl(match: re.Match) -> str:
    phrase = match.group(1)
    local = (base_hash + sum(ord(c) for c in phrase) * 3) % 3
    if role == "male":
      if local == 0:
        pitch, rate = "-0.4st", "102%"
      elif local == 1:
        pitch, rate = "-0.7st", "100%"
      else:
        pitch, rate = "-1.0st", "98%"
    elif local == 0:
      pitch, rate = "-0.6st", "97%"
    elif local == 1:
      pitch, rate = "-1.0st", "94%"
    else:
      pitch, rate = "-1.4st", "92%"
    return f'<prosody pitch="{pitch}" rate="{rate}">{phrase}</prosody>'

  def _slow_repl(match: re.Match) -> str:
    phrase = match.group(1)
    local = (base_hash + len(phrase)) % 3
    # Female host can slow down more; male host stays closer to normal so he doesn't feel dragged.
    if role == "male":
      if local == 0:
        rate = "104%"
      elif local == 1:
        rate = "102%"
      else:
        rate = "106%"
    else:
      if local == 0:
        rate = "92%"
      elif local == 1:
        rate = "88%"
      else:
        rate = "95%"
    return f'<prosody rate="{rate}" pitch="0st">{phrase}</prosody>'

  text = re.sub(r"\[RISE:([^\]]+)\]", _rise_repl, text, flags=re.IGNORECASE)
  text = re.sub(r"\[FALL:([^\]]+)\]", _fall_repl, text, flags=re.IGNORECASE)
  text = re.sub(r"\[SLOW:([^\]]+)\]", _slow_repl, text, flags=re.IGNORECASE)

  # Interjections — wrap short exclamations so Google TTS treats them as expressive
  def _interjection_repl(match: re.Match) -> str:
    word = match.group(1)
    punct = match.group(2) or ""
    return f'<say-as interpret-as="interjection">{word}</say-as>{punct}'

  text = re.sub(r"(?<![\w>])(Wow|Oh|Great|Nice|Exactly|Right)([!?,\.])", _interjection_repl, text)
  # Chirp3 HD reads leftover punctuation aloud; convert to pauses after cues are applied.
  text = _replace_spoken_punctuation_with_breaks(text)

  # For the male host, further tighten pauses so his delivery feels more continuous.
  if role == "male":
    text = _tighten_male_breaks(text)

  # Base prosody per host — keep consistent so clearly 2 people (Gacrux vs Algenib).
  # Chirp3 often ignores nested SSML rate; AudioConfig speaking_rate is the reliable knob.
  if role == "male":
    prosody = '<prosody rate="118%" pitch="-0.2st">'
  else:
    prosody = '<prosody rate="100%" pitch="+0.2st">'
  return f"<speak>{prosody}{text}</prosody></speak>"


def _parse_podcast_script(script: str) -> list[tuple[str, str]]:
  """
  Parse script with FEMALE: / MALE: lines into segments (role, text).
  Role is 'female' or 'male'. Consecutive lines with same role are merged.
  Lines without a prefix are merged into the previous segment (or FEMALE if first).
  """
  segments: list[tuple[str, str]] = []
  current_role: str | None = None
  current_text: list[str] = []

  def flush():
    if current_role and current_text:
      segments.append((current_role, " ".join(current_text).strip()))
    current_text.clear()

  for raw_line in script.splitlines():
    line = raw_line.strip()
    if not line:
      continue
    line_upper = line.upper()
    if line_upper.startswith("FEMALE:"):
      if current_role is not None:
        flush()
      current_role = "female"
      current_text.append(line[7:].strip())
    elif line_upper.startswith("MALE:"):
      if current_role is not None:
        flush()
      current_role = "male"
      current_text.append(line[5:].strip())
    else:
      if current_role is None:
        current_role = "female"
      current_text.append(line)

  flush()
  if not segments and script.strip():
    segments.append(("female", script.strip()))
  # Ensure only "female" and "male" — no stray roles (so only 2 voices ever used)
  return [(r if r in ("female", "male") else "female", t) for r, t in segments]


async def _chunk_and_synthesize(client, voice, audio_config, text: str) -> bytes:
  """Chunk text for Google TTS limit and synthesize in parallel; return concatenated MP3 bytes."""
  encoded = text.encode("utf-8")
  max_bytes = 2000
  chunks = []
  start = 0
  while start < len(encoded):
    end = min(start + max_bytes, len(encoded))
    while end < len(encoded) and (encoded[end] & 0xC0) == 0x80:
      end -= 1
    if end <= start:
      end = min(start + max_bytes, len(encoded))
    chunks.append(encoded[start:end].decode("utf-8", errors="ignore"))
    start = end

  async def synthesize_chunk(idx: int, chunk_text: str) -> bytes:
    chunk_text = _apply_pronunciation_plain(chunk_text)
    synthesis_input = texttospeech.SynthesisInput(text=chunk_text)
    logger.info("TTS: synthesizing chunk %s/%s (%s bytes)", idx + 1, len(chunks), len(chunk_text.encode("utf-8")))
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
      None,
      partial(
        client.synthesize_speech,
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
      ),
    )
    return response.audio_content

  audio_segments = await asyncio.gather(
    *[synthesize_chunk(i, chunk) for i, chunk in enumerate(chunks)]
  )
  return b"".join(audio_segments)


# Max input size for Google TTS (SSML or text) is 5000 bytes
_TTS_INPUT_MAX_BYTES = 5000
_TTS_TIMING_SAFETY_BYTES = 400
_SINGLE_WORD_ALIAS_MAP = {
  term.lower(): alias
  for term, alias in _PRONUNCIATION_ALIASES
  if " " not in term.strip()
}
_MARKED_SSML_PREFIX = '<speak><prosody rate="100%" pitch="+0.15st">'
_MARKED_SSML_SUFFIX = '</prosody></speak>'
_SPOKEN_WORD_PATTERN = r"[A-Za-z0-9\u00c0-\u024f\u0900-\u097f]+(?:['’][A-Za-z0-9\u00c0-\u024f\u0900-\u097f]+)?"
_SPOKEN_TOKEN_RE = re.compile(
  rf"\[PAUSE:(?:short|medium|long)\]|{_SPOKEN_WORD_PATTERN}|[^\sA-Za-z0-9\u00c0-\u024f\u0900-\u097f]+|\s+",
  flags=re.IGNORECASE,
)


def _pause_tag_to_ssml(token: str) -> str:
  value = str(token or "").lower()
  if value == "[pause:short]":
    return '<break time="260ms"/>'
  if value == "[pause:medium]":
    return '<break time="620ms"/>'
  return '<break time="960ms"/>'


def _iter_spoken_tokens(text: str):
  for match in _SPOKEN_TOKEN_RE.finditer(str(text or "")):
    token = match.group(0)
    if not token:
      continue
    lowered = token.lower()
    if lowered in ("[pause:short]", "[pause:medium]", "[pause:long]"):
      yield ("pause", lowered)
    elif re.fullmatch(_SPOKEN_WORD_PATTERN, token, flags=re.IGNORECASE):
      yield ("word", token)
    else:
      yield ("separator", token)


def _estimate_syllables(word: str) -> int:
  cleaned = re.sub(r"[^a-z0-9\u00c0-\u024f\u0900-\u097f]", "", (word or "").lower())
  if not cleaned:
    return 1
  matches = re.findall(r"[aeiouy\u0904-\u094c\u0962\u0963]+", cleaned)
  return max(1, min(len(matches) or 1, 5))


def _word_intensity(word: str) -> int:
  syllables = _estimate_syllables(word)
  letters = len(re.sub(r"[^\w]", "", word or "", flags=re.UNICODE)) or len(word or "")
  if syllables >= 3 or letters >= 7 or re.search(r"\d", word or ""):
    return 3
  if syllables >= 2 or letters >= 4:
    return 2
  return 1


def _estimated_word_ms(word: str) -> int:
  syllables = _estimate_syllables(word)
  letters = len(re.sub(r"[^\w]", "", word or "", flags=re.UNICODE)) or len(word or "")
  strong = syllables >= 3 or letters >= 7 or re.search(r"\d", word or "")
  medium = (not strong) and (syllables >= 2 or letters >= 4)
  return max(
    120,
    min(
      300,
      110 + letters * 14 + syllables * 34 + (32 if strong else 18 if medium else 0),
    ),
  )


def _word_token_to_ssml(token: str) -> str:
  alias = _SINGLE_WORD_ALIAS_MAP.get((token or "").lower().strip())
  escaped_token = html.escape(token, quote=False)
  if alias:
    safe_alias = html.escape(alias, quote=True)
    return f'<sub alias="{safe_alias}">{escaped_token}</sub>'
  return escaped_token


def _wrap_marked_ssml(content_parts: list[str]) -> str:
  return _MARKED_SSML_PREFIX + "".join(content_parts) + _MARKED_SSML_SUFFIX


def _build_marked_ssml_chunks_and_timeline(text: str) -> list[dict]:
  raw = _strip_literal_punctuation_words(text or "").strip()
  if not raw:
    return []

  chunks: list[dict] = []
  content_parts: list[str] = []
  timeline: list[dict] = []
  word_index = 0

  def flush_chunk() -> None:
    nonlocal content_parts, timeline
    if not content_parts or not timeline:
      content_parts = []
      timeline = []
      return
    chunks.append({
      "ssml": _wrap_marked_ssml(content_parts),
      "timeline_template": timeline,
    })
    content_parts = []
    timeline = []

  for token_type, token in _iter_spoken_tokens(raw):
    if token_type == "word":
      mark_name = f"w{word_index}"
      rendered = f'<mark name="{mark_name}"/>{_word_token_to_ssml(token)}'
      row = {
        "mark_name": mark_name,
        "word_index": word_index,
        "word": token,
        "intensity": _word_intensity(token),
        "estimated_word_ms": _estimated_word_ms(token),
      }
      candidate_parts = content_parts + [rendered]
      candidate_timeline = timeline + [row]
      if timeline and len(_wrap_marked_ssml(candidate_parts).encode("utf-8")) > (_TTS_INPUT_MAX_BYTES - _TTS_TIMING_SAFETY_BYTES):
        flush_chunk()
      content_parts.append(rendered)
      timeline.append(row)
      word_index += 1
    elif token_type == "pause":
      rendered = _pause_tag_to_ssml(token)
      candidate_parts = content_parts + [rendered]
      if timeline and len(_wrap_marked_ssml(candidate_parts).encode("utf-8")) > (_TTS_INPUT_MAX_BYTES - _TTS_TIMING_SAFETY_BYTES):
        flush_chunk()
      content_parts.append(rendered)
    else:
      rendered = html.escape(token, quote=False)
      candidate_parts = content_parts + [rendered]
      if timeline and len(_wrap_marked_ssml(candidate_parts).encode("utf-8")) > (_TTS_INPUT_MAX_BYTES - _TTS_TIMING_SAFETY_BYTES):
        flush_chunk()
      content_parts.append(rendered)

  flush_chunk()
  return chunks


def _strip_mark_tags(ssml: str) -> str:
  return re.sub(r'<mark name="[^"]+"\s*/>', "", ssml or "")


async def _synthesize_ssml(client, voice, audio_config, ssml: str) -> bytes:
  """Synthesize a single SSML string (under 5000 bytes)."""
  encoded = ssml.encode("utf-8")
  if len(encoded) > _TTS_INPUT_MAX_BYTES:
    # Fallback: strip SSML and use plain text chunking (loses pauses/emphasis for this segment)
    plain = re.sub(r"<[^>]+>", " ", ssml)
    plain = re.sub(r"\s+", " ", plain).strip()
    return await _chunk_and_synthesize(client, voice, audio_config, plain)
  synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
  loop = asyncio.get_running_loop()
  try:
    response = await loop.run_in_executor(
      None,
      partial(
        client.synthesize_speech,
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
      ),
    )
  except Exception as e:
    if not _is_invalid_tts_argument(e):
      raise
    logger.warning("TTS: SSML rejected (%s); retrying as plain text", e)
    plain = re.sub(r"<[^>]+>", " ", ssml)
    plain = re.sub(r"\s+", " ", plain).strip()
    return await _chunk_and_synthesize(client, voice, audio_config, plain)
  return response.audio_content


async def _synthesize_podcast_segment(client, voice_name: str, role: str, segment_text: str, language_code: str) -> bytes:
  voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
  audio_config = _podcast_audio_config(role, voice_name)
  mode = _ssml_mode_for_voice(voice_name)
  try:
    if mode == "plain":
      return await _chunk_and_synthesize(client, voice, audio_config, _segment_text_to_plain(segment_text))
    ssml = _segment_text_to_ssml(segment_text, role, ssml_mode=mode)
    return await _synthesize_ssml(client, voice, audio_config, ssml)
  except Exception as e:
    if not _is_invalid_tts_argument(e):
      raise
    logger.warning("TTS: voice %s rejected podcast audio (%s); retrying minimal plain text", voice_name, e)
    minimal = _podcast_audio_config(role, voice_name, minimal=True)
    return await _chunk_and_synthesize(client, voice, minimal, _segment_text_to_plain(segment_text))


async def _synthesize_ssml_with_timepoints(client, voice, audio_config, ssml: str) -> tuple[bytes, list]:
  synthesis_input = texttospeech_beta.SynthesisInput(ssml=ssml)
  request = texttospeech_beta.SynthesizeSpeechRequest(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config,
    enable_time_pointing=[
      texttospeech_beta.SynthesizeSpeechRequest.TimepointType.SSML_MARK,
    ],
  )
  loop = asyncio.get_running_loop()
  response = await loop.run_in_executor(
    None,
    partial(
      client.synthesize_speech,
      request=request,
    ),
  )
  return response.audio_content, list(getattr(response, "timepoints", []) or [])


def _merge_mark_timeline(timepoints: list, timeline_template: list[dict], offset_ms: int = 0) -> list[dict]:
  if not timepoints or not timeline_template:
    return []

  marks = {}
  for tp in timepoints:
    mark_name = getattr(tp, "mark_name", None) or getattr(tp, "markName", None)
    seconds = getattr(tp, "time_seconds", None)
    if seconds is None:
      seconds = getattr(tp, "timeSeconds", None)
    if mark_name is None or seconds is None:
      continue
    try:
      marks[str(mark_name)] = float(seconds)
    except (TypeError, ValueError):
      continue

  merged = []
  for row in timeline_template:
    mark_name = row.get("mark_name")
    if mark_name not in marks:
      continue
    merged.append({
      **row,
      "start_ms": offset_ms + int(round(marks[mark_name] * 1000)),
    })
  return merged


def _estimate_timeline_end_ms(merged_timeline: list[dict]) -> int:
  if not merged_timeline:
    return 0
  last = merged_timeline[-1]
  last_start = int(last.get("start_ms") or 0)
  last_word_ms = int(last.get("estimated_word_ms") or 180)
  return last_start + max(140, min(last_word_ms + 80, 420))


def _get_tts_credentials_only():
  """
  Load credentials from GOOGLE_TTS_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY (inline JSON
  or file path). Used for TTS so it can use the tradebest key and billing project. Returns None if not set.
  """
  raw = os.environ.get(TTS_CREDENTIALS_ENV) or os.environ.get(TTS_CREDENTIALS_ENV_ALT)
  if not raw or not str(raw).strip():
    return None
  raw = str(raw).strip()
  from google.oauth2 import service_account
  scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  # Inline JSON (e.g. GOOGLE_SERVICE_ACCOUNT_KEY with full JSON)
  info = parse_json_from_env(raw)
  if info and isinstance(info, dict):
    try:
      return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except (ValueError, TypeError):
      return None
  if os.path.isfile(raw):
    try:
      return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
    except Exception:
      return None
  return None


def _get_google_credentials():
  """
  Use for TTS: (1) GOOGLE_TTS_SERVICE_ACCOUNT_JSON, or (2) GOOGLE_SERVICE_ACCOUNT_KEY (e.g. tradebest
  JSON so billing is on the right project), else (3) Play credentials with cloud scope.
  """
  try:
    tts_creds = _get_tts_credentials_only()
    if tts_creds is not None:
      return tts_creds
    base_creds = _get_play_credentials()
    if not base_creds:
      logger.error("TTS: Google credentials not available (set GOOGLE_SERVICE_ACCOUNT_KEY or GOOGLE_PLAY_SERVICE_ACCOUNT_JSON)")
      raise HTTPException(
        status_code=503,
        detail="Google service account credentials not available (GOOGLE_SERVICE_ACCOUNT_KEY or GOOGLE_PLAY_SERVICE_ACCOUNT_JSON).",
      )
    return base_creds.with_scopes(
      ["https://www.googleapis.com/auth/cloud-platform"]
    )
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: Failed to build Google credentials")
    raise HTTPException(status_code=503, detail=f"Failed to build Google credentials: {e}")


@router.get("/voices")
async def list_voices():
  """
  Return available Google TTS voices so admin can audition/select speech-chat voices.
  """
  try:
    creds = _get_google_credentials()
    client = texttospeech.TextToSpeechClient(credentials=creds)
    response = client.list_voices()
  except Exception as e:
    logger.exception("TTS: list_voices failed")
    raise HTTPException(status_code=500, detail=f"TTS voices fetch failed: {e}")

  voices = []
  for v in response.voices:
    voices.append({
      "name": v.name,
      "language_codes": list(v.language_codes),
      "ssml_gender": texttospeech.SsmlVoiceGender(v.ssml_gender).name if isinstance(v.ssml_gender, int) else str(v.ssml_gender),
      "natural_sample_rate_hertz": v.natural_sample_rate_hertz,
    })
  voices.sort(key=lambda item: (item["name"], ",".join(item["language_codes"])))
  return {"voices": voices}


class VoicePreviewRequest(BaseModel):
  text: str
  voice_name: str
  lang: str = "en"
  mode: str = "podcast"  # podcast | speech
  role: str = "female"  # female | male (podcast hosts)


def _require_tts_preview_admin(current_user: User = Depends(get_current_user)) -> User:
  if getattr(current_user, "role", None) != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
  return current_user


@router.post("/voice-preview")
async def voice_preview(
  request: VoicePreviewRequest,
  current_user: User = Depends(_require_tts_preview_admin),
):
  """
  Admin-only audition of a Google TTS voice using the exact typed sample.
  Podcast mode uses the same SSML + rate path as generated episodes.
  """
  sample = str(request.text or "").strip()
  voice_name = str(request.voice_name or "").strip()
  if not sample:
    raise HTTPException(status_code=400, detail="Text is required")
  if not voice_name:
    raise HTTPException(status_code=400, detail="voice_name is required")
  if len(sample) > 400:
    sample = sample[:400]

  lang = "hi" if str(request.lang or "en").lower().startswith("hi") else "en"
  role = "male" if str(request.role or "").lower().startswith("m") else "female"
  mode = str(request.mode or "podcast").strip().lower()
  language_code = _language_code_from_voice_name(
    voice_name,
    "hi-IN" if lang == "hi" else "en-GB",
  )

  try:
    creds = _get_google_credentials()
    client = texttospeech.TextToSpeechClient(credentials=creds)
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: voice-preview client init failed")
    raise HTTPException(status_code=503, detail=f"TTS client initialization failed: {e}")

  try:
    if mode == "speech":
      voice, audio_config = _build_voice_and_config(lang, voice_name)
      spoken = _strip_spoken_control_cues_for_plain_tts(sample)
      try:
        audio_bytes = await _chunk_and_synthesize(client, voice, audio_config, spoken)
      except Exception as e:
        if not _is_invalid_tts_argument(e):
          raise
        logger.warning("TTS: speech preview rejected for %s (%s); retrying minimal config", voice_name, e)
        minimal = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        audio_bytes = await _chunk_and_synthesize(client, voice, minimal, spoken)
    else:
      audio_bytes = await _synthesize_podcast_segment(
        client,
        voice_name,
        role,
        sample,
        language_code,
      )
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: voice-preview failed voice=%s mode=%s", voice_name, mode)
    raise HTTPException(status_code=500, detail=f"Voice preview failed: {e}")

  if not audio_bytes:
    raise HTTPException(status_code=500, detail="Voice preview produced no audio")
  return JSONResponse({"audio": base64.b64encode(audio_bytes).decode("ascii"), "voice_name": voice_name})


@router.post("/synthesize")
async def synthesize(
  text: str,
  lang: str = "en",
  voice_name: Optional[str] = None,
  include_timepoints: bool = Query(default=False),
  prepare_spoken: bool = False,
):
  """
  Google Cloud Text-to-Speech with Indian voices.
  - lang='en' -> en-IN Neural voice
  - lang='hi' -> hi-IN Neural voice
  """
  if not text or not text.strip():
    raise HTTPException(status_code=400, detail="Text is required")

  try:
    creds = _get_google_credentials()
    client = texttospeech.TextToSpeechClient(credentials=creds)
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: Error initializing TextToSpeechClient")
    raise HTTPException(status_code=503, detail=f"TTS client initialization failed: {e}")

  resolved_voice_name = _resolve_live_speech_voice(lang or "en", voice_name)
  voice, audio_config = _build_voice_and_config(lang or "en", resolved_voice_name)
  try:
    tts_total_started = time.perf_counter()
    timing_mode_used = False
    timing_disabled_reason: str | None = None
    timepoints_payload: list[dict] = []
    timeline_payload: list[dict] = []
    prep_started = time.perf_counter()
    spoken_text = (
      _prepare_spoken_tts_text(text, lang or "en")
      if prepare_spoken
      else _fallback_spoken_tts_text(text, lang or "en")
    )
    prep_ms = (time.perf_counter() - prep_started) * 1000.0
    allow_word_mark_timing = _voice_supports_word_mark_timepoints(resolved_voice_name)
    logger.info(
      "TTS: synthesize request prepared spoken text (lang=%s, include_timepoints=%s, prepare_spoken=%s, prep_ms=%.1f, src_chars=%s, spoken_chars=%s, voice=%s, allow_word_mark_timing=%s)",
      lang,
      include_timepoints,
      prepare_spoken,
      prep_ms,
      len(str(text or "")),
      len(spoken_text),
      resolved_voice_name,
      allow_word_mark_timing,
    )

    synth_started = time.perf_counter()
    if include_timepoints and allow_word_mark_timing:
      marked_chunks = _build_marked_ssml_chunks_and_timeline(spoken_text)
      if marked_chunks:
        beta_client = texttospeech_beta.TextToSpeechClient(credentials=creds)
        beta_voice, beta_audio_config = _build_beta_voice_and_config(lang or "en", resolved_voice_name)
        audio_parts: list[bytes] = []
        offset_ms = 0
        for chunk_index, chunk in enumerate(marked_chunks):
          chunk_audio, timepoints = await _synthesize_ssml_with_timepoints(
            beta_client,
            beta_voice,
            beta_audio_config,
            chunk["ssml"],
          )
          audio_parts.append(chunk_audio)
          chunk_timepoints_payload = [
            {
              "mark_name": getattr(tp, "mark_name", None) or getattr(tp, "markName", None),
              "time_seconds": float(getattr(tp, "time_seconds", None) or getattr(tp, "timeSeconds", 0.0) or 0.0),
              "chunk_index": chunk_index,
            }
            for tp in timepoints
            if (getattr(tp, "mark_name", None) or getattr(tp, "markName", None)) is not None
          ]
          timepoints_payload.extend(chunk_timepoints_payload)
          chunk_timeline = _merge_mark_timeline(timepoints, chunk["timeline_template"], offset_ms=offset_ms)
          timeline_payload.extend(chunk_timeline)
          offset_ms = _estimate_timeline_end_ms(chunk_timeline) if chunk_timeline else offset_ms
        audio_bytes = b"".join(audio_parts)
        timing_mode_used = bool(timeline_payload)
      else:
        audio_bytes = await _chunk_and_synthesize(client, voice, audio_config, spoken_text)
    else:
      if include_timepoints and not allow_word_mark_timing:
        timing_disabled_reason = "voice_family_prefers_smooth_audio"
      audio_bytes = await _chunk_and_synthesize(
        client,
        voice,
        audio_config,
        _strip_spoken_control_cues_for_plain_tts(spoken_text),
      )
    synth_ms = (time.perf_counter() - synth_started) * 1000.0
    total_ms = (time.perf_counter() - tts_total_started) * 1000.0
    logger.info(
      "TTS_PERF synthesize_complete lang=%s prepare_spoken=%s include_timepoints=%s prep_ms=%.1f synth_ms=%.1f total_ms=%.1f audio_bytes=%s",
      lang,
      prepare_spoken,
      include_timepoints,
      prep_ms,
      synth_ms,
      total_ms,
      len(audio_bytes or b""),
    )
  except Exception as e:
    logger.exception("TTS: synthesize_speech failed")
    raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")

  audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
  response = {"audio": audio_b64}
  if include_timepoints:
    response["timing_mode_used"] = timing_mode_used
    response["timepoints"] = timepoints_payload
    response["timeline"] = timeline_payload
    if timing_disabled_reason:
      response["timing_disabled_reason"] = timing_disabled_reason
  return JSONResponse(response)


class PodcastRequest(BaseModel):
  message_content: str
  language: str = "en"
  message_id: Optional[Union[str, int]] = None  # optional: if provided, use GCS cache; client may send int (e.g. 2329)
  session_id: Optional[str] = None  # optional: for podcast history and opening conversation
  preview: Optional[str] = None  # optional: first ~150 chars for history list
  native_name: Optional[str] = None  # optional: birth chart / native name for personalized intro
  birth_chart_id: Optional[int] = None  # selected owned chart for factual visual enrichment
  prepare_only: bool = False  # generate/cache a Premium podcast without returning or autoplaying audio


def _podcast_cache_lang(lang: str) -> str:
  """Normalize language to cache key so store and lookup match (client may send 'en' or 'english')."""
  if not lang or not str(lang).strip():
    return "en"
  l = str(lang).lower().strip()
  return "hi" if l.startswith("hi") else "en"


def _podcast_lang_aliases(lang: str) -> tuple[str, ...]:
  return ("hi", "hindi") if _podcast_cache_lang(lang) == "hi" else ("en", "english")


def _message_id_aliases(message_id: str) -> list[str]:
  raw = str(message_id or "").strip()
  ids = [raw] if raw else []
  try:
    as_int = str(int(raw))
    if as_int not in ids:
      ids.append(as_int)
  except (TypeError, ValueError):
    pass
  return ids


def _find_podcast_history(userid: int, message_id: str, cache_lang: str):
  ids = _message_id_aliases(message_id)
  if not ids:
    return None
  langs = _podcast_lang_aliases(cache_lang)
  id_ph = ",".join("?" for _ in ids)
  lang_ph = ",".join("?" for _ in langs)
  with get_conn() as conn:
    cursor = execute(
      conn,
      f"""
      SELECT message_id, session_id, lang, preview, birth_chart_id
      FROM podcast_history
      WHERE userid = ?
        AND message_id IN ({id_ph})
        AND LOWER(TRIM(lang)) IN ({lang_ph})
      ORDER BY created_at DESC
      LIMIT 1
      """,
      (userid, *ids, *langs),
    )
    row = cursor.fetchone()
    if row:
      return row
    cursor = execute(
      conn,
      f"""
      SELECT message_id, session_id, lang, preview, birth_chart_id
      FROM podcast_history
      WHERE userid = ?
        AND message_id IN ({id_ph})
      ORDER BY created_at DESC
      LIMIT 1
      """,
      (userid, *ids),
    )
    return cursor.fetchone()


def _podcast_history_languages(userid: int, message_id: str) -> list[str]:
  """Return languages this user has already generated for one message.

  Podcast history is the entitlement record. A missing cache object can be
  restored by the stream endpoint without charging again, so a status check
  must not download MP3 data merely to decide whether the user owns it.
  """
  ids = _message_id_aliases(message_id)
  if not ids:
    return []
  _ensure_podcast_history_table()
  id_ph = ",".join("?" for _ in ids)
  with get_conn() as conn:
    cursor = execute(
      conn,
      f"""
      SELECT lang
      FROM podcast_history
      WHERE userid = ?
        AND message_id IN ({id_ph})
      ORDER BY created_at DESC
      """,
      (userid, *ids),
    )
    rows = cursor.fetchall()
  languages: list[str] = []
  for row in rows:
    value = row[0] if not isinstance(row, dict) else row.get("lang")
    lang = _podcast_cache_lang(value or "en")
    if lang not in languages:
      languages.append(lang)
  return languages


def _cached_podcast_bytes(message_id: str, cache_lang: str):
  for mid in _message_id_aliases(message_id):
    for alias in _podcast_lang_aliases(cache_lang):
      cached = get_cached_audio(mid, alias)
      if cached:
        return cached
  return None


def _load_assistant_message_content(userid: int, message_id: str, session_id: Optional[str] = None):
  mid_int = None
  try:
    mid_int = int(str(message_id).strip())
  except (TypeError, ValueError):
    mid_int = None
  with get_conn() as conn:
    if mid_int is not None:
      cursor = execute(
        conn,
        """
        SELECT cm.content, cm.session_id
        FROM chat_messages cm
        INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.message_id = ?
          AND cs.user_id = ?
          AND cm.sender = 'assistant'
        LIMIT 1
        """,
        (mid_int, userid),
      )
      row = cursor.fetchone()
      if row and str(row[0] or "").strip():
        return str(row[0]).strip(), row[1]
    if session_id:
      cursor = execute(
        conn,
        """
        SELECT cm.content, cm.session_id
        FROM chat_messages cm
        INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.session_id = ?
          AND cs.user_id = ?
          AND cm.sender = 'assistant'
          AND CAST(cm.message_id AS TEXT) = ?
        LIMIT 1
        """,
        (session_id, userid, str(message_id).strip()),
      )
      row = cursor.fetchone()
      if row and str(row[0] or "").strip():
        return str(row[0]).strip(), row[1]
  return None, None


def _podcast_ashtakavarga_visual(birth, chart: dict) -> dict:
  """Return the compact house-indexed SAV/BAV matrix used by video cards."""
  from calculators.ashtakavarga import AshtakavargaCalculator

  calculated = AshtakavargaCalculator(birth, chart).calculate_sarvashtakavarga()
  sav = calculated.get("sarvashtakavarga") or {}
  individual = calculated.get("individual_charts") or {}
  av_planets = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
  ascendant_sign = int(float(chart.get("ascendant") or 0.0) / 30) % 12
  rows = []
  for house in range(1, 13):
    sign = (ascendant_sign + house - 1) % 12
    rows.append({
      "house": house,
      "sign": sign,
      "sav": int(sav.get(str(sign), sav.get(sign, 0)) or 0),
      "bav": {
        planet: int(
          ((individual.get(planet) or {}).get("bindus") or {}).get(
            str(sign),
            ((individual.get(planet) or {}).get("bindus") or {}).get(sign, 0),
          ) or 0
        )
        for planet in av_planets
      },
    })
  return {
    "rows": rows,
    "total_bindus": int(calculated.get("total_bindus") or sum(row["sav"] for row in rows)),
  }


def _compact_podcast_chart(chart: dict) -> dict:
  planets = []
  for name, raw in (chart.get("planets") or {}).items():
    if not isinstance(raw, dict):
      continue
    longitude = float(raw.get("longitude") or 0.0)
    planets.append({
      "name": str(name),
      "house": int(raw.get("house") or 0),
      "sign": raw.get("sign"),
      "longitude": round(longitude, 4),
      "degree": round(float(raw.get("degree") or raw.get("degrees") or longitude % 30), 2),
      "retrograde": bool(raw.get("retrograde") or raw.get("is_retrograde")),
    })
  ascendant = round(float(chart.get("ascendant") or 0.0), 4)
  ascendant_sign = chart.get("ascendant_sign")
  if not isinstance(ascendant_sign, (int, float)):
    ascendant_sign = int(ascendant / 30) % 12
  return {
    "ascendant": ascendant,
    "ascendant_sign": int(ascendant_sign) % 12,
    "planets": planets,
  }


def _podcast_dasha_visual(birth_data: dict) -> dict:
  """Return real current Vimshottari periods without retaining birth details."""
  from shared.dasha_calculator import DashaCalculator

  now = datetime.now()
  calculated = DashaCalculator().calculate_current_dashas(birth_data, current_date=now, strict=True)
  level_specs = (
    ("maha", "mahadasha"),
    ("antar", "antardasha"),
    ("pratyantar", "pratyantardasha"),
  )
  levels = []
  for kind, key in level_specs:
    raw = calculated.get(key) or {}
    if raw.get("planet"):
      levels.append({
        "kind": kind,
        "planet": str(raw["planet"]),
        "start": raw.get("start"),
        "end": raw.get("end"),
      })
  mahadashas = []
  for raw in calculated.get("maha_dashas") or []:
    start = raw.get("start")
    end = raw.get("end")
    mahadashas.append({
      "planet": str(raw.get("planet") or ""),
      "start": start.strftime("%Y-%m-%d") if hasattr(start, "strftime") else str(start or ""),
      "end": (end.replace(microsecond=0).strftime("%Y-%m-%d") if hasattr(end, "strftime") else str(end or "")),
      "current": bool(start and end and start <= now <= end),
    })
  return {"as_of": now.strftime("%Y-%m-%d"), "levels": levels, "mahadashas": mahadashas}


def _podcast_house_activation_visual(
  birth,
  chart: dict,
  dasha: dict,
  ashtakavarga: dict,
  focus_houses: Optional[list[int]] = None,
) -> dict:
  """Build a compact four-layer activation ledger for the visual player."""
  from calculators.badhaka_calculator import BadhakaCalculator
  from calculators.transit_calculator import TransitCalculator
  from calculators.vedic_graha_drishti import get_aspect_houses_for_planet

  def aspects(planet: str, house: int) -> set[int]:
    aspect_numbers = (7,) if planet in {"Rahu", "Ketu"} else get_aspect_houses_for_planet(planet)
    return {
      ((int(house) + int(number) - 2) % 12) + 1
      for number in aspect_numbers
      if int(number) != 1
    }

  ascendant_sign = int(float(chart.get("ascendant") or 0.0) / 30.0) % 12
  dasha_planets = []
  for level in dasha.get("levels") or []:
    planet = str(level.get("planet") or "")
    if planet and planet not in dasha_planets:
      dasha_planets.append(planet)

  dasha_houses: set[int] = set()
  dasha_by_house: dict[int, list[str]] = {house: [] for house in range(1, 13)}
  natal_portfolio: dict[str, set[int]] = {}
  for planet in dasha_planets:
    raw = (chart.get("planets") or {}).get(planet) or {}
    if not raw:
      continue
    occupied = int(raw.get("house") or 0)
    ruled = {
      house for house in range(1, 13)
      if BadhakaCalculator.SIGN_LORDS[(ascendant_sign + house - 1) % 12] == planet
    }
    portfolio = ruled | ({occupied} if occupied else set()) | aspects(planet, occupied)
    natal_portfolio[planet] = portfolio
    dasha_houses.update(portfolio)
    for house in portfolio:
      if planet not in dasha_by_house[house]:
        dasha_by_house[house].append(planet)

  transit_by_house: dict[int, list[str]] = {house: [] for house in range(1, 13)}
  transits = TransitCalculator(chart).calculate_transits(birth, datetime.now().strftime("%Y-%m-%d"))
  for planet in dasha_planets:
    raw = (transits.get("planets") or {}).get(planet) or {}
    if not raw or planet not in natal_portfolio:
      continue
    transit_house = ((int(raw.get("sign") or 0) - ascendant_sign) % 12) + 1
    contacts = ({transit_house} | aspects(planet, transit_house)) & natal_portfolio[planet]
    for house in contacts:
      if planet not in transit_by_house[house]:
        transit_by_house[house].append(planet)

  sav_by_house = {
    int(row.get("house") or 0): int(row.get("sav") or 0)
    for row in (ashtakavarga.get("rows") or [])
    if int(row.get("house") or 0) in range(1, 13)
  }
  natal_houses = {int(house) for house in (focus_houses or []) if int(house) in range(1, 13)}
  rows = []
  for house in range(1, 13):
    sav = sav_by_house.get(house)
    rows.append({
      "house": house,
      "natal_promise": house in natal_houses,
      "dasha_activation": house in dasha_houses,
      "transit_activation": bool(transit_by_house[house]),
      "ashtakavarga_support": sav is not None and sav >= 30,
      "sav": sav,
      "dasha_planets": dasha_by_house[house],
      "transit_planets": transit_by_house[house],
    })
  return {
    "as_of": datetime.now().strftime("%Y-%m-%d"),
    "sav_support_threshold": 30,
    "rows": rows,
  }


def _podcast_chart_visual(
  userid: int,
  message_id: str,
  session_id: Optional[str] = None,
  division_numbers: Optional[list[int]] = None,
  focus_houses: Optional[list[int]] = None,
  birth_chart_id: Optional[int] = None,
  native_name_hint: Optional[str] = None,
):
  """Calculate a privacy-minimised D1 chart for the visual companion.

  Only chart geometry is returned to the authenticated owner. Birth date,
  time, place, coordinates and the native's name never enter the manifest.
  A missing/deleted chart is non-fatal: the podcast remains fully playable.
  """
  row = None
  try:
    mid_int = int(str(message_id).strip())
  except (TypeError, ValueError):
    mid_int = None
  try:
    with get_conn() as conn:
      if birth_chart_id:
        cursor = execute(
          conn,
          """
          SELECT id, name, date, time, latitude, longitude,
                 timezone, place, gender
          FROM birth_charts
          WHERE id = %s AND userid = %s
          LIMIT 1
          """,
          (birth_chart_id, userid),
        )
        row = cursor.fetchone()
      if not row and session_id:
        cursor = execute(
          conn,
          """
          SELECT bc.id, bc.name, bc.date, bc.time, bc.latitude, bc.longitude,
                 bc.timezone, bc.place, bc.gender
          FROM chat_sessions cs
          INNER JOIN birth_charts bc ON bc.id = cs.birth_chart_id
          WHERE cs.session_id = %s AND cs.user_id = %s AND bc.userid = %s
          LIMIT 1
          """,
          (session_id, userid, userid),
        )
        row = cursor.fetchone()
      if not row and mid_int is not None:
        cursor = execute(
          conn,
          """
          SELECT bc.id, bc.name, bc.date, bc.time, bc.latitude, bc.longitude,
                 bc.timezone, bc.place, bc.gender
          FROM chat_messages cm
          INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
          INNER JOIN birth_charts bc ON bc.id = cs.birth_chart_id
          WHERE cm.message_id = %s AND cm.sender = 'assistant'
            AND cs.user_id = %s AND bc.userid = %s
          LIMIT 1
          """,
          (mid_int, userid, userid),
        )
        row = cursor.fetchone()
      if not row and str(native_name_hint or "").strip():
        # Some instant/day chat sessions predate chart-id persistence. The
        # fixed podcast intro still names the selected saved profile, allowing
        # an exact owner-scoped recovery without exposing that name in the
        # returned visual manifest.
        cursor = execute(
          conn,
          """
          SELECT id, name, date, time, latitude, longitude,
                 timezone, place, gender
          FROM birth_charts
          WHERE userid = %s
          ORDER BY id DESC
          """,
          (userid,),
        )
        candidates = cursor.fetchall()
        from encryption_utils import EncryptionManager

        decryptor = EncryptionManager()
        expected_name = re.sub(r"\s+", " ", str(native_name_hint)).strip().casefold()
        for candidate in candidates:
          try:
            candidate_name = decryptor.decrypt(candidate[1])
          except Exception:
            candidate_name = str(candidate[1] or "")
          if re.sub(r"\s+", " ", str(candidate_name)).strip().casefold() == expected_name:
            row = candidate
            break
    if not row:
      return None

    from calculators.chart_calculator import ChartCalculator
    from encryption_utils import EncryptionManager

    try:
      decryptor = EncryptionManager()
      decrypted = {
        "name": decryptor.decrypt(row[1]),
        "date": decryptor.decrypt(row[2]),
        "time": decryptor.decrypt(row[3]),
        "latitude": float(decryptor.decrypt(str(row[4]))),
        "longitude": float(decryptor.decrypt(str(row[5]))),
        "place": decryptor.decrypt(row[7] or ""),
      }
    except Exception:
      decrypted = {
        "name": str(row[1] or ""),
        "date": str(row[2] or ""),
        "time": str(row[3] or ""),
        "latitude": float(row[4]),
        "longitude": float(row[5]),
        "place": str(row[7] or ""),
      }
    birth = SimpleNamespace(
      **decrypted,
      timezone=row[6] or "UTC",
      gender=row[8] or "",
    )
    chart = ChartCalculator({}).calculate_chart(birth)
    payload = _compact_podcast_chart(chart)
    requested_divisions = [
      number for number in (division_numbers or [])
      if number in {2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}
    ]
    if requested_divisions:
      from calculators.divisional_chart_calculator import DivisionalChartCalculator

      calculator = DivisionalChartCalculator(chart)
      payload["divisional_charts"] = {}
      for number in dict.fromkeys(requested_divisions):
        try:
          result = calculator.calculate_divisional_chart(number)
          compact = _compact_podcast_chart(result.get("divisional_chart") or {})
          compact["label"] = calculator.get_chart_name(number)
          payload["divisional_charts"][f"D{number}"] = compact
        except Exception as div_exc:
          logger.warning("Podcast visuals: D%s unavailable: %s", number, div_exc)
    try:
      payload["ashtakavarga"] = _podcast_ashtakavarga_visual(birth, chart)
    except Exception as av_exc:
      logger.warning(
        "Podcast visuals: Ashtakavarga unavailable for message_id=%s user_id=%s: %s",
        message_id,
        userid,
        av_exc,
      )
    try:
      payload["dasha"] = _podcast_dasha_visual({
        **decrypted,
        "timezone": row[6] or "UTC",
        "gender": row[8] or "",
      })
    except Exception as dasha_exc:
      logger.warning(
        "Podcast visuals: dasha unavailable for message_id=%s user_id=%s: %s",
        message_id,
        userid,
        dasha_exc,
      )
    if payload.get("dasha") and payload.get("ashtakavarga"):
      try:
        payload["house_activation"] = _podcast_house_activation_visual(
          birth,
          chart,
          payload["dasha"],
          payload["ashtakavarga"],
          focus_houses,
        )
      except Exception as activation_exc:
        logger.warning(
          "Podcast visuals: house activation unavailable for message_id=%s user_id=%s: %s",
          message_id,
          userid,
          activation_exc,
        )
    return payload
  except Exception as exc:
    logger.warning(
      "Podcast visuals: chart unavailable for message_id=%s user_id=%s: %s",
      message_id,
      userid,
      exc,
    )
    return None


def _podcast_native_name_hint(source: dict) -> str:
  """Recover only the profile name spoken in the application's fixed intro."""
  segments = source.get("segments") if isinstance(source, dict) else []
  opening = " ".join(
    str(item.get("text") or "") for item in (segments or [])[:3] if isinstance(item, dict)
  )
  opening = re.sub(r"\[(?:PAUSE|EMPHASIS|RISE|FALL|SLOW):([^\]]*)\]", r"\1", opening, flags=re.IGNORECASE)
  patterns = (
    r"today(?:'|’)s\s+personal\s+reading\s+is\s+for\s+([^.!?]+)",
    r"आज\s+की\s+यह\s+व्यक्तिगत\s+रीडिंग\s+(.+?)\s+के\s+लिए\s+है",
  )
  for pattern in patterns:
    match = re.search(pattern, opening, flags=re.IGNORECASE)
    if match:
      return re.sub(r"\s+", " ", match.group(1)).strip()[:120]
  return ""


async def _synthesize_podcast_mp3(text: str, lang: str, native_name: str = "") -> bytes:
  loop = asyncio.get_running_loop()
  script = await loop.run_in_executor(None, partial(generate_podcast_script, text, lang))
  if not script or not script.strip():
    raise HTTPException(status_code=500, detail="Podcast script generation produced empty output")
  intro = _podcast_intro_line(native_name or "", lang)
  outro = _podcast_outro_lines(lang)
  script = (
    intro
    + constrain_podcast_script(script, PODCAST_BODY_MAX_SPOKEN_WORDS)
    + "\n"
    + outro
  )
  script = _normalize_hindi_ordinals(script, lang)
  script = constrain_podcast_script(script)
  segments = _parse_podcast_script(script)
  if not segments:
    raise HTTPException(status_code=500, detail="Podcast script had no parseable FEMALE:/MALE: lines")
  try:
    creds = _get_google_credentials()
    client = texttospeech.TextToSpeechClient(credentials=creds)
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: Error initializing TextToSpeechClient for podcast")
    raise HTTPException(status_code=503, detail=f"TTS client initialization failed: {e}")
  female_name, male_name, language_code = _podcast_voices(lang)
  audio_parts: list[bytes] = []
  try:
    for role, segment_text in segments:
      if not segment_text or not segment_text.strip():
        continue
      voice_name = female_name if role == "female" else male_name
      audio_parts.append(
        await _synthesize_podcast_segment(
          client,
          voice_name,
          role,
          segment_text,
          _language_code_from_voice_name(voice_name, language_code),
        )
      )
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("TTS: podcast synthesis failed")
    raise HTTPException(status_code=500, detail=f"Podcast TTS failed: {e}")
  audio_bytes = b"".join(audio_parts)
  if not audio_bytes:
    raise HTTPException(status_code=500, detail="Podcast produced no audio")
  return audio_bytes


def _podcast_intro_line(native_name: str, lang: str) -> str:
  """Return the consistent two-host AstroRoshni programme opening."""
  name = (native_name or "").strip()
  use_hindi = lang and str(lang).lower().startswith("hi")
  if use_hindi:
    listener = f"आज की यह व्यक्तिगत रीडिंग {name} के लिए है" if name else "आज हम आपकी व्यक्तिग रीडिंग लेकर आए हैं"
    return (
      f"FEMALE: [RISE:नमस्ते!] [PAUSE:short] AstroRoshni Podcast में आपका स्वागत है। "
      f"मैं हूँ अनन्या, और {listener}।\n"
      "MALE: और मैं हूँ अर्जुन। [PAUSE:short] आइए चार्ट के संकेतों को आपकी रोज़मर्रा की ज़िंदगी के मायने में समझते हैं।\n"
    )
  listener = f"today's personal reading is for {name}" if name else "today we're opening your personal reading"
  return (
    "FEMALE: [RISE:Welcome to the AstroRoshni Podcast.] [PAUSE:short] "
    f"I'm Ananya, and {listener}.\n"
    "MALE: And I'm Arjun. [PAUSE:short] Let's turn the chart's strongest signals into what they may mean in real life.\n"
  )


def _podcast_outro_lines(lang: str) -> str:
  """Return a warm, consistent two-host closing without generic AI phrasing."""
  use_hindi = lang and str(lang).lower().startswith("hi")
  if use_hindi:
    return (
      "FEMALE: [FALL:आज के लिए बस इतना ही।] [PAUSE:short] अपने लिए सबसे ज़रूरी संकेत को साथ लेकर जाइए।\n"
      "MALE: सुनने के लिए धन्यवाद। [PAUSE:short] मैं अर्जुन—\n"
      "FEMALE: और मैं अनन्या। [FALL:फिर मिलेंगे AstroRoshni Podcast पर।]\n"
    )
  return (
    "FEMALE: [FALL:That's our reading for today.] [PAUSE:short] Keep the one insight that felt most useful, and let it guide your next step.\n"
    "MALE: Thank you for listening. [PAUSE:short] I'm Arjun—\n"
    "FEMALE: And I'm Ananya. [FALL:We'll meet you again on the AstroRoshni Podcast.]\n"
  )


def _normalize_hindi_ordinals(script: str, lang: str) -> str:
  """
  Gemini sometimes writes mixed Hindi/English ordinals like "8wa", "8 wa", "12wa house".
  For Hindi podcasts, normalize the most common patterns so TTS sounds more natural.
  """
  if not lang or not str(lang).lower().startswith("hi"):
    return script

  # 8wa / 8 wa → 8वाँ, and "8वाँ house" → "8वाँ भाव"
  script = re.sub(r"\b8\s*wa\b", "8वाँ", script, flags=re.IGNORECASE)
  script = re.sub(r"\b8\s*वा\b", "8वाँ", script, flags=re.IGNORECASE)
  script = re.sub(r"\b8वाँ\s+house\b", "8वाँ भाव", script, flags=re.IGNORECASE)

  # 12wa / 12 wa → 12वाँ, and "12वाँ house" → "12वाँ भाव"
  script = re.sub(r"\b12\s*wa\b", "12वाँ", script, flags=re.IGNORECASE)
  script = re.sub(r"\b12\s*वा\b", "12वाँ", script, flags=re.IGNORECASE)
  script = re.sub(r"\b12वाँ\s+house\b", "12वाँ भाव", script, flags=re.IGNORECASE)

  # Generic "(\d+) wa/वा house" → "<num>वाँ भाव" as a fallback
  script = re.sub(r"\b(\d+)\s*(wa|वा)\s+house\b", r"\1वाँ भाव", script, flags=re.IGNORECASE)
  return script


@router.get("/podcast/check-cache")
async def podcast_check_cache(
  message_id: Union[str, int],
  lang: str = "en",
  current_user: User = Depends(get_current_user),
):
  """
  Return the languages this user has already generated for the message.
  History is intentionally used instead of downloading GCS audio: the stream
  route can restore a missing object without charging the user again.
  """
  raw_id = message_id
  mid = str(raw_id).strip() if raw_id is not None else None
  if not mid:
    return JSONResponse({"cached": False, "ready": False, "languages": []})
  cache_lang = _podcast_cache_lang(lang)
  languages = _podcast_history_languages(current_user.userid, mid)
  return JSONResponse({
    "cached": cache_lang in languages,
    "ready": bool(languages),
    "languages": languages,
  })


@router.post("/podcast")
async def podcast(request: PodcastRequest, current_user: User = Depends(get_current_user)):
  """
  Generate a podcast from a chat message: Gemini produces a two-host (FEMALE/MALE) script,
  then each segment is synthesized with the matching voice and concatenated.
  If message_id is provided and PODCAST_CACHE_BUCKET is set, cached audio is returned when available;
  on first generation the audio is stored in GCS and credits are deducted.
  """
  try:
    text = (request.message_content or "").strip()
    if not text:
      raise HTTPException(status_code=400, detail="message_content is required")

    lang = (request.language or "en").lower()
    raw_id = request.message_id
    message_id = str(raw_id).strip() if raw_id is not None else None
    cache_lang = _podcast_cache_lang(lang)
    premium_included = _premium_podcast_included(current_user.userid, message_id)

    # Auto-prepare was removed: podcasts generate only from the Listen CTA.
    if request.prepare_only:
      raise HTTPException(
        status_code=403,
        detail="Automatic podcast preparation is disabled. Generate from the Listen CTA.",
      )

    if message_id:
      loop = asyncio.get_running_loop()
      cached = await loop.run_in_executor(None, lambda: get_cached_audio(message_id, cache_lang))
      if not cached and cache_lang == "en":
        cached = await loop.run_in_executor(None, lambda: get_cached_audio(message_id, "english"))
      if cached:
        logger.info("Podcast: cache hit, message_id=%s (no generation)", message_id)
        _add_podcast_history(
          current_user.userid,
          message_id,
          request.session_id,
          cache_lang,
          request.preview,
          request.birth_chart_id,
        )
        if request.prepare_only:
          return JSONResponse({"ready": True, "cached": True, "included_with_premium": premium_included})
        audio_b64 = base64.b64encode(cached).decode("ascii")
        return JSONResponse({"audio": audio_b64, "cached": True, "included_with_premium": premium_included})

    # Cache miss: will generate and deduct. Check balance first.
    base_cost = credit_service.get_credit_setting("podcast_cost")
    effective_cost = 0 if premium_included else credit_service.get_effective_cost(
      current_user.userid, base_cost or 2, "podcast_cost"
    )
    effective_cost = 0 if premium_included else (max(1, int(effective_cost)) if effective_cost else 2)
    balance = credit_service.get_user_credits(current_user.userid)
    if effective_cost > 0 and balance < effective_cost:
      raise HTTPException(
        status_code=402,
        detail=f"Insufficient credits. Need {effective_cost}, have {balance}.",
      )

    provider = get_podcast_provider()
    loop = asyncio.get_running_loop()
    logger.info("Podcast: using provider=%s, message_id=%s (cache miss)", provider, message_id)

    use_tts = provider != PODCAST_PROVIDER_NOTEBOOK_LM
    audio_bytes = None
    visual_source_payload = None
    if provider == PODCAST_PROVIDER_NOTEBOOK_LM:
      # NotebookLM (Discovery Engine) Podcast API: full message as context, no script step
      try:
        audio_bytes = await loop.run_in_executor(
          None,
          partial(
            notebook_lm_podcast.generate_podcast_mp3,
            text,
            lang,
            title="AstroRoshni Podcast",
            description="Generated from your astrological reading.",
            length="SHORT",
          ),
        )
        logger.info("Podcast: generated via Notebook LM (Discovery Engine), audio_bytes=%d", len(audio_bytes))
      except Exception as e:
        err_str = str(e)
        if "404" in err_str or "Method not found" in err_str:
          logger.warning(
            "Podcast: Notebook LM returned 404 (method not found / limited availability), falling back to Google TTS. Error: %s",
            err_str[:200],
          )
          use_tts = True
        else:
          logger.exception("NotebookLM podcast failed: %s", e)
          raise HTTPException(
            status_code=500,
            detail="Podcast generation failed (NotebookLM). Check server logs and Discovery Engine setup.",
          )
    if use_tts:
      # TTS flow: Gemini script then Google TTS synthesis
      logger.info("Podcast: generating via Google TTS (Gemini script + synthesis)")
      script = await loop.run_in_executor(None, partial(generate_podcast_script, text, lang))
      if not script or not script.strip():
        raise HTTPException(status_code=500, detail="Podcast script generation produced empty output")

      # Frame the generated discussion as a consistent, named AstroRoshni show.
      intro = _podcast_intro_line(request.native_name or "", lang)
      outro = _podcast_outro_lines(lang)
      script = (
        intro
        + constrain_podcast_script(script, PODCAST_BODY_MAX_SPOKEN_WORDS)
        + "\n"
        + outro
      )

      # Clean up common Hindi ordinal patterns (8wa house → 8वाँ भाव etc.) before we parse segments.
      script = _normalize_hindi_ordinals(script, lang)
      # Enforce the final budget after adding the personalized intro. This is a
      # safety net for models that ignore the requested duration.
      script = constrain_podcast_script(script)

      segments = _parse_podcast_script(script)
      if not segments:
        raise HTTPException(status_code=500, detail="Podcast script had no parseable FEMALE:/MALE: lines")

      script_chars = len(script)
      script_words = len(script.split())
      logger.info(
        "Podcast script size: chars=%d words=%d segments=%d (TTS billed by character; ~₹2,490/1M chars after free tier)",
        script_chars,
        script_words,
        len(segments),
      )

      try:
        creds = _get_google_credentials()
        client = texttospeech.TextToSpeechClient(credentials=creds)
      except HTTPException:
        raise
      except Exception as e:
        logger.exception("TTS: Error initializing TextToSpeechClient for podcast")
        raise HTTPException(status_code=503, detail=f"TTS client initialization failed: {e}")

      female_name, male_name, language_code = _podcast_voices(lang)
      audio_parts: list[bytes] = []
      try:
        for role, segment_text in segments:
          if not segment_text or not segment_text.strip():
            continue
          voice_name = female_name if role == "female" else male_name
          segment_bytes = await _synthesize_podcast_segment(
            client,
            voice_name,
            role,
            segment_text,
            _language_code_from_voice_name(voice_name, language_code),
          )
          audio_parts.append(segment_bytes)
      except Exception as e:
        logger.exception("TTS: podcast synthesis failed")
        raise HTTPException(status_code=500, detail=f"Podcast TTS failed: {e}")

      audio_bytes = b"".join(audio_parts)
      if not audio_bytes:
        raise HTTPException(status_code=500, detail="Podcast produced no audio")
      # Capture visual-only timing metadata after synthesis. Reading the
      # already-generated segment sizes does not alter voices, bytes, order,
      # speed or any other podcast-audio behaviour.
      visual_source_payload = visual_source(
        script,
        segments,
        text,
        segment_audio_sizes=[len(part) for part in audio_parts],
        segment_audio_durations_ms=[mp3_duration_ms(part) for part in audio_parts],
        birth_chart_id=request.birth_chart_id,
      )
      logger.info("Podcast: generated via Google TTS, audio_bytes=%d", len(audio_bytes))

    if message_id:
      await loop.run_in_executor(None, partial(put_cached_audio, message_id, cache_lang, audio_bytes))
      if visual_source_payload:
        await loop.run_in_executor(
          None,
          partial(put_visual_json, message_id, cache_lang, "source", visual_source_payload),
        )

    # Deduct (we already checked balance above)
    if effective_cost > 0:
      success = credit_service.spend_credits(
        current_user.userid,
        effective_cost,
        "podcast",
        f"Podcast for message {message_id or 'chat'}",
      )
      if not success:
        logger.warning("Podcast: credit deduction failed (insufficient balance?) for user %s", current_user.userid)

    publish_activity(
      "podcast_generated",
      user_id=current_user.userid,
      user_phone=current_user.phone,
      user_name=current_user.name,
      resource_type="message",
      resource_id=message_id,
      metadata={"cached": False, "included_with_premium": premium_included, "credits_charged": effective_cost},
    )
    if message_id:
      _add_podcast_history(
        current_user.userid,
        message_id,
        request.session_id,
        cache_lang,
        request.preview,
        request.birth_chart_id,
      )
    if request.prepare_only:
      return JSONResponse({"ready": True, "cached": False, "included_with_premium": premium_included})
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    return JSONResponse({"audio": audio_b64, "cached": False, "included_with_premium": premium_included})

  except HTTPException:
    raise
  except Exception as e:
    logger.exception("Podcast endpoint unexpected error: %s", e)
    raise HTTPException(
      status_code=500,
      detail="Podcast generation failed. Check server logs for details.",
    )


@router.get("/podcast/visuals")
async def podcast_visuals(
  message_id: str = Query(..., description="Message ID of an owned podcast"),
  lang: str = Query("en", description="Language code"),
  birth_chart_id: Optional[int] = Query(None, description="Selected owned chart for visual enrichment"),
  current_user: User = Depends(get_current_user),
):
  """Return a cached or newly planned visual companion for an owned podcast."""
  raw_id = str(message_id or "").strip()
  if not raw_id:
    raise HTTPException(status_code=400, detail="message_id required")
  cache_lang = _podcast_cache_lang(lang)
  history = _find_podcast_history(current_user.userid, raw_id, cache_lang)
  if not history:
    raise HTTPException(status_code=404, detail="Podcast not found or access denied")
  history_id = str(history[0] or raw_id).strip()
  history_session = history[1]
  history_lang = _podcast_cache_lang(history[2] or cache_lang)
  history_birth_chart_id = history[4] if len(history) > 4 else None
  effective_birth_chart_id = birth_chart_id or history_birth_chart_id
  loop = asyncio.get_running_loop()

  manifest = await loop.run_in_executor(
    None,
    partial(get_visual_json, history_id, history_lang, "manifest"),
  )
  if manifest:
    if not manifest.get("chart") and effective_birth_chart_id:
      scene_divisions = referenced_divisions(" ".join(
        str(scene.get("division") or "") for scene in (manifest.get("scenes") or []) if isinstance(scene, dict)
      ))
      scene_houses = sorted({
        int(house)
        for scene in (manifest.get("scenes") or []) if isinstance(scene, dict)
        for house in (scene.get("houses") or [])
        if str(house).isdigit() and 1 <= int(house) <= 12
      })
      chart = await loop.run_in_executor(
        None,
        partial(
          _podcast_chart_visual,
          current_user.userid,
          history_id,
          history_session,
          scene_divisions,
          scene_houses,
          effective_birth_chart_id,
          None,
        ),
      )
      if chart:
        manifest["chart"] = chart
        await loop.run_in_executor(
          None,
          partial(put_visual_json, history_id, history_lang, "manifest", manifest),
        )
    return JSONResponse({"manifest": manifest, "cached": True})

  source = await loop.run_in_executor(
    None,
    partial(get_visual_json, history_id, history_lang, "source"),
  )
  if not source:
    content, _ = _load_assistant_message_content(
      current_user.userid,
      history_id,
      history_session,
    )
    if not content:
      raise HTTPException(status_code=404, detail="Podcast source message not found")
    source = visual_source_from_message(content)
  elif any(
    isinstance(item, dict)
    and int(item.get("audio_weight") or 0) > 0
    and int(item.get("audio_duration_ms") or 0) <= 0
    for item in (source.get("segments") or [])
  ):
    cached_audio = await loop.run_in_executor(
      None,
      partial(_cached_podcast_bytes, history_id, history_lang),
    )
    if cached_audio:
      upgraded_source = add_audio_durations_to_source(source, cached_audio)
      if upgraded_source is not source:
        source = upgraded_source
        await loop.run_in_executor(
          None,
          partial(put_visual_json, history_id, history_lang, "source", source),
        )

  manifest = await loop.run_in_executor(
    None,
    partial(generate_visual_manifest, source, history_lang),
  )
  spoken_source = " ".join(
    str(item.get("text") or "")
    for item in (source.get("segments") or [])
    if isinstance(item, dict)
  ) or str(source.get("message_content") or "")
  chart = await loop.run_in_executor(
    None,
    partial(
      _podcast_chart_visual,
      current_user.userid,
      history_id,
      history_session,
      referenced_divisions(spoken_source),
      referenced_houses(spoken_source),
      effective_birth_chart_id or (source.get("birth_chart_id") if isinstance(source, dict) else None),
      _podcast_native_name_hint(source),
    ),
  )
  if chart:
    manifest["chart"] = chart
  manifest["visual_style"] = "cinematic_v3"
  await loop.run_in_executor(
    None,
    partial(put_visual_json, history_id, history_lang, "manifest", manifest),
  )
  return JSONResponse({"manifest": manifest, "cached": False})


@router.get("/podcast/history")
async def podcast_history(current_user: User = Depends(get_current_user)):
  """
  Return list of podcasts the current user has generated or played (cached).
  Each item includes message_id, session_id, lang, preview, created_at.
  App builds play URL as GET /tts/podcast/stream?message_id=...&lang=...
  """
  _ensure_podcast_history_table()
  with get_conn() as conn:
    cursor = execute(
      conn,
      """
      SELECT message_id, session_id, lang, preview, created_at, birth_chart_id
      FROM podcast_history
      WHERE userid = ?
      ORDER BY created_at DESC
      LIMIT 200
      """,
      (current_user.userid,),
    )
    rows = cursor.fetchall()
  return JSONResponse({
    "podcasts": [
      {
        "message_id": r[0],
        "session_id": r[1],
        "lang": _podcast_cache_lang(r[2] or "en"),
        "preview": r[3],
        "created_at": (r[4].isoformat() if hasattr(r[4], "isoformat") else (str(r[4]) if r[4] is not None else None)),
        "birth_chart_id": r[5],
      }
      for r in rows
    ],
  })


@router.get("/podcast/stream")
async def podcast_stream(
  message_id: str = Query(..., description="Message ID of the cached podcast"),
  lang: str = Query("en", description="Language code"),
  current_user: User = Depends(get_current_user),
):
  """
  Stream cached podcast audio. Only allowed if this user has the podcast in their history.
  If the MP3 is missing from cache (common on local/emulator after a backend restart),
  rebuild it from the original chat message without charging again.
  """
  raw_id = str(message_id).strip() if message_id else None
  if not raw_id:
    raise HTTPException(status_code=400, detail="message_id required")
  cache_lang = _podcast_cache_lang(lang)
  _ensure_podcast_history_table()
  history = _find_podcast_history(current_user.userid, raw_id, cache_lang)
  if not history:
    logger.warning(
      "Podcast stream: no history row user=%s message_id=%s lang=%s",
      current_user.userid,
      raw_id,
      cache_lang,
    )
    raise HTTPException(status_code=404, detail="Podcast not found or access denied")
  history_id = str(history[0] or raw_id).strip()
  history_session = history[1]
  history_lang = _podcast_cache_lang(history[2] or cache_lang)
  audio_bytes = _cached_podcast_bytes(history_id, history_lang) or _cached_podcast_bytes(raw_id, cache_lang)
  if audio_bytes:
    return Response(content=audio_bytes, media_type="audio/mpeg")

  logger.warning(
    "Podcast stream cache miss; rebuilding user=%s message_id=%s lang=%s",
    current_user.userid,
    history_id,
    history_lang,
  )
  content, session_id = _load_assistant_message_content(
    current_user.userid,
    history_id,
    history_session,
  )
  if not content:
    raise HTTPException(status_code=404, detail="Podcast audio not in cache")
  audio_bytes = await _synthesize_podcast_mp3(content, history_lang)
  loop = asyncio.get_running_loop()
  await loop.run_in_executor(None, partial(put_cached_audio, history_id, history_lang, audio_bytes))
  _add_podcast_history(
    current_user.userid,
    history_id,
    session_id or history_session,
    history_lang,
    history[3],
    history[4] if len(history) > 4 else None,
  )
  return Response(content=audio_bytes, media_type="audio/mpeg")
