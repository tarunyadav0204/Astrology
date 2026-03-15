from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import base64
import os
import re
import html
from google.cloud import texttospeech
import logging
import asyncio
from functools import partial
from pydantic import BaseModel

from auth import get_current_user, User
from credits.credit_service import CreditService
from credits.routes import _get_play_credentials
from tts.podcast_narrator import generate_podcast_script
from tts.podcast_cache import get_cached_audio, put_cached_audio
from tts import notebook_lm_podcast
from activity.publisher import publish_activity
from utils.env_json import parse_json_from_env
from utils.admin_settings import get_podcast_provider, PODCAST_PROVIDER_NOTEBOOK_LM

credit_service = CreditService()

# TTS credential order: (1) GOOGLE_TTS_SERVICE_ACCOUNT_JSON if set, else (2) GOOGLE_SERVICE_ACCOUNT_KEY
# (inline JSON from tradebest where billing is enabled), else (3) Play credentials. This way the same
# key you use as GOOGLE_SERVICE_ACCOUNT_KEY (tradebest) can drive TTS without a separate env var.
TTS_CREDENTIALS_ENV = "GOOGLE_TTS_SERVICE_ACCOUNT_JSON"
TTS_CREDENTIALS_ENV_ALT = "GOOGLE_SERVICE_ACCOUNT_KEY"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tts", tags=["tts"])


def _build_voice_and_config(lang: str, voice_name: str | None = None):
  lang = (lang or "en").lower()
  if voice_name:
    parts = voice_name.split("-")
    language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else ("hi-IN" if lang.startswith("hi") else "en-IN")
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
  else:
    if lang.startswith("hi"):
      voice = texttospeech.VoiceSelectionParams(language_code="hi-IN", name="hi-IN-Neural2-C")
    else:
      voice = texttospeech.VoiceSelectionParams(language_code="en-IN", name="en-IN-Neural2-A")
  audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.95,
  )
  return voice, audio_config


def _podcast_voices(_lang: str) -> tuple[str, str]:
  """Return (female_voice_name, male_voice_name) for podcast. UK English Chirp3-HD."""
  return ("en-GB-Chirp3-HD-Gacrux", "en-GB-Chirp3-HD-Algenib")


def _segment_text_to_ssml(segment_text: str, role: str = "female") -> str:
  """
  Convert segment text with cues to SSML for Google TTS.
  Cues: [PAUSE:*], [EMPHASIS:...], [RISE:...], [FALL:...], [SLOW:...].
  Wraps in <prosody> so female and male sound distinct.
  """
  if not segment_text or not segment_text.strip():
    return "<speak></speak>"
  # Escape XML in the text so we can safely insert SSML tags
  text = html.escape(segment_text.strip(), quote=True)
  # Pauses — use longer, audible breaks so it doesn't sound like one run-on announcement
  text = re.sub(r"\[PAUSE:short\]", '<break time="500ms"/>', text, flags=re.IGNORECASE)
  text = re.sub(r"\[PAUSE:medium\]", '<break time="1s"/>', text, flags=re.IGNORECASE)
  text = re.sub(r"\[PAUSE:long\]", '<break time="1.5s"/>', text, flags=re.IGNORECASE)
  # Emphasis — strong so it stands out from neutral tone
  text = re.sub(
    r"\[EMPHASIS:([^\]]+)\]",
    r'<emphasis level="strong">\1</emphasis>',
    text,
    flags=re.IGNORECASE,
  )
  # Intonation — subtle so the same 2 voices stay recognizable (avoid sounding like 3–4 people)
  text = re.sub(
    r"\[RISE:([^\]]+)\]",
    r'<prosody pitch="+1st" rate="100%">\1</prosody>',
    text,
    flags=re.IGNORECASE,
  )
  text = re.sub(
    r"\[FALL:([^\]]+)\]",
    r'<prosody pitch="-0.8st" rate="97%">\1</prosody>',
    text,
    flags=re.IGNORECASE,
  )
  text = re.sub(
    r"\[SLOW:([^\]]+)\]",
    r'<prosody rate="92%" pitch="0st">\1</prosody>',
    text,
    flags=re.IGNORECASE,
  )
  # Base prosody per host — keep consistent so clearly 2 people (Gacrux vs Algenib)
  if role == "male":
    prosody = '<prosody rate="100%" pitch="-0.2st">'
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
  Return available Indian voices (en-IN, hi-IN) from Google TTS.
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
    # Filter to Indian English and Hindi
    if not any(code.startswith(("en-IN", "hi-IN")) for code in v.language_codes):
      continue
    voices.append({
      "name": v.name,
      "language_codes": list(v.language_codes),
      "ssml_gender": texttospeech.SsmlVoiceGender(v.ssml_gender).name if isinstance(v.ssml_gender, int) else str(v.ssml_gender),
      "natural_sample_rate_hertz": v.natural_sample_rate_hertz,
    })

  return {"voices": voices}


@router.post("/synthesize")
async def synthesize(text: str, lang: str = "en", voice_name: str | None = None):
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

  voice, audio_config = _build_voice_and_config(lang or "en", voice_name)
  try:
    audio_bytes = await _chunk_and_synthesize(client, voice, audio_config, text)
  except Exception as e:
    logger.exception("TTS: synthesize_speech failed")
    raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")

  audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
  return JSONResponse({"audio": audio_b64})


class PodcastRequest(BaseModel):
  message_content: str
  language: str = "en"
  message_id: str | int | None = None  # optional: if provided, use GCS cache; client may send int (e.g. 2329)


def _podcast_cache_lang(lang: str) -> str:
  """Normalize language to cache key so store and lookup match (client may send 'en' or 'english')."""
  if not lang or not str(lang).strip():
    return "en"
  l = str(lang).lower().strip()
  return "hi" if l.startswith("hi") else "en"


@router.get("/podcast/check-cache")
async def podcast_check_cache(
  message_id: str | int,
  lang: str = "en",
  current_user: User = Depends(get_current_user),
):
  """
  Check if a podcast for this message is already cached (no credits will be charged on play).
  Used by the app to skip the credit confirmation modal when replaying.
  """
  raw_id = message_id
  mid = str(raw_id).strip() if raw_id is not None else None
  if not mid:
    return JSONResponse({"cached": False})
  cache_lang = _podcast_cache_lang(lang)
  cached = get_cached_audio(mid, cache_lang)
  if not cached and cache_lang == "en":
    cached = get_cached_audio(mid, "english")  # backward compat: old cache used "english"
  return JSONResponse({"cached": bool(cached)})


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

    if message_id:
      loop = asyncio.get_running_loop()
      cached = await loop.run_in_executor(None, lambda: get_cached_audio(message_id, cache_lang))
      if not cached and cache_lang == "en":
        cached = await loop.run_in_executor(None, lambda: get_cached_audio(message_id, "english"))
      if cached:
        logger.info("Podcast: cache hit, message_id=%s (no generation)", message_id)
        audio_b64 = base64.b64encode(cached).decode("ascii")
        return JSONResponse({"audio": audio_b64, "cached": True})

    # Cache miss: will generate and deduct. Check balance first.
    base_cost = credit_service.get_credit_setting("podcast_cost")
    effective_cost = credit_service.get_effective_cost(
      current_user.userid, base_cost or 2, "podcast_cost"
    )
    effective_cost = max(1, int(effective_cost)) if effective_cost else 2
    balance = credit_service.get_user_credits(current_user.userid)
    if balance < effective_cost:
      raise HTTPException(
        status_code=402,
        detail=f"Insufficient credits. Need {effective_cost}, have {balance}.",
      )

    provider = get_podcast_provider()
    loop = asyncio.get_running_loop()
    logger.info("Podcast: using provider=%s, message_id=%s (cache miss)", provider, message_id)

    use_tts = provider != PODCAST_PROVIDER_NOTEBOOK_LM
    audio_bytes = None
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
            length="STANDARD",
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

      female_name, male_name = _podcast_voices(lang)
      language_code = "en-GB"  # Podcast uses UK English Chirp3-HD (Gacrux, Algenib)
      audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.95,
        volume_gain_db=10.0,  # +10 dB max recommended; makes podcast clearly audible
      )
      audio_parts: list[bytes] = []
      try:
        for role, segment_text in segments:
          if not segment_text or not segment_text.strip():
            continue
          voice_name = female_name if role == "female" else male_name
          voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
          ssml = _segment_text_to_ssml(segment_text, role)
          segment_bytes = await _synthesize_ssml(client, voice, audio_config, ssml)
          audio_parts.append(segment_bytes)
      except Exception as e:
        logger.exception("TTS: podcast synthesis failed")
        raise HTTPException(status_code=500, detail=f"Podcast TTS failed: {e}")

      audio_bytes = b"".join(audio_parts)
      if not audio_bytes:
        raise HTTPException(status_code=500, detail="Podcast produced no audio")
      logger.info("Podcast: generated via Google TTS, audio_bytes=%d", len(audio_bytes))

    if message_id:
      await loop.run_in_executor(None, partial(put_cached_audio, message_id, cache_lang, audio_bytes))

    # Deduct (we already checked balance above)
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
      metadata={"cached": False},
    )
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    return JSONResponse({"audio": audio_b64, "cached": False})

  except HTTPException:
    raise
  except Exception as e:
    logger.exception("Podcast endpoint unexpected error: %s", e)
    raise HTTPException(
      status_code=500,
      detail="Podcast generation failed. Check server logs for details.",
    )

