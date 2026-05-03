import logging
import os

import google.generativeai as genai
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from auth import get_current_user, User
from utils.admin_settings import speech_chat_enabled_for_user


router = APIRouter(prefix="/speech", tags=["speech"])
logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 12 * 1024 * 1024
# Inline audio must stay under Gemini's ~20 MB per-request limit (we cap uploads at 12 MB).
# Use a model with reliable audio grounding; gemini-3-flash-preview has produced unrelated Q&A text in STT.
DEFAULT_TRANSCRIPTION_MODEL = "models/gemini-2.5-flash"


def _response_text(response) -> str:
    try:
        return (getattr(response, "text", "") or "").strip()
    except Exception:
        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()


def _audio_suffix(filename: str | None, content_type: str | None) -> str:
    name = (filename or "").lower()
    if name.endswith(".m4a"):
        return ".m4a"
    if name.endswith(".mp3"):
        return ".mp3"
    if name.endswith(".wav"):
        return ".wav"
    if name.endswith(".webm"):
        return ".webm"
    if name.endswith(".caf"):
        return ".caf"
    ctype = (content_type or "").lower()
    if "mpeg" in ctype or "mp3" in ctype:
        return ".mp3"
    if "wav" in ctype:
        return ".wav"
    if "webm" in ctype:
        return ".webm"
    return ".m4a"


def _normalized_mime_type(suffix: str, content_type: str | None) -> str:
    """MIME type Gemini expects for inline audio (m4a from iOS is usually audio/mp4)."""
    ct = (content_type or "").strip().lower()
    if "mp4" in ct or "m4a" in ct:
        return "audio/mp4"
    if "3gpp" in ct or "3gp" in ct:
        return "audio/3gpp"
    if "amr" in ct:
        return "audio/amr"
    if "mpeg" in ct or "mp3" in ct:
        return "audio/mpeg"
    if "wav" in ct:
        return "audio/wav"
    if "webm" in ct:
        return "audio/webm"
    if suffix == ".m4a" or suffix == ".mp4":
        return "audio/mp4"
    if suffix == ".3gp":
        return "audio/3gpp"
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".webm":
        return "audio/webm"
    return "audio/mp4"


def _clean_transcript(text: str) -> str:
    def strip_matching_quotes(value: str) -> str:
        cleaned = (value or "").strip()
        if (
            len(cleaned) >= 2
            and cleaned[0] in ("'", '"', "“", "‘")
            and cleaned[-1] in ("'", '"', "”", "’")
        ):
            return cleaned[1:-1].strip()
        return cleaned

    transcript = strip_matching_quotes(" ".join((text or "").split()).strip())
    prefixes = [
        "transcript:",
        "spoken words:",
        "the user said:",
        "user said:",
    ]
    lower = transcript.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            transcript = transcript[len(prefix):].strip()
            break
    return strip_matching_quotes(transcript)


def _normalized_transcription_language(language: str | None) -> str | None:
    raw = (language or "").strip().lower()
    if not raw:
        return None
    if raw.startswith("hi"):
        return "hi"
    if raw.startswith("en"):
        return "en"
    if raw == "hindi":
        return "hi"
    if raw == "english":
        return "en"
    return None


def _looks_like_instruction_following_failure(text: str) -> bool:
    transcript = _clean_transcript(text).lower()
    if not transcript:
        return True
    suspicious_phrases = [
        "what is the capital of france",
        "the capital of france",
        "capital of france is paris",
        "paris is the capital of france",
        "how can i help you",
        "as an ai",
        "i cannot assist",
        "please provide more details",
        "the answer is",
    ]
    return any(phrase in transcript for phrase in suspicious_phrases)


def _transcription_prompt(language: str | None) -> str:
    return (
        "Listen to the attached audio. Task: verbatim speech-to-text only.\n"
        "The audio is the only source of truth. Do not invent speech you do not hear.\n"
        "- Transcribe word-for-word in plain text.\n"
        "- Output ONLY spoken words. No preamble, no quotes, no labels.\n"
        "- Do NOT answer questions, do NOT output unrelated trivia or example sentences.\n"
        "- Do NOT rephrase into a different question or topic.\n"
        "- Most utterances are short astrology app questions such as: describe my behaviour, tell me about my career, how will this month be, what are my traits.\n"
        "- If the speech sounds like a short personal question, preserve it as a short question or phrase rather than turning it into a different sentence.\n"
        "- If inaudible or silent, output exactly: [no speech detected]\n"
        "- If part of a word is unclear, use a phonetic guess or [unclear] for that fragment.\n"
        f"Language hint (may be mixed): {language or 'english'}."
    )


async def _transcribe_with_gemini(
    *,
    data: bytes,
    mime: str,
    language: str | None,
) -> tuple[str, str]:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    model_name = (os.getenv("SPEECH_TRANSCRIPTION_MODEL") or DEFAULT_TRANSCRIPTION_MODEL).strip()
    model = genai.GenerativeModel(
        model_name,
        generation_config=genai.GenerationConfig(
            temperature=0,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
        ),
    )
    audio_part = {"inline_data": {"mime_type": mime, "data": data}}
    prompt = _transcription_prompt(language)
    attempts = ([audio_part, prompt], [prompt, audio_part])
    last_transcript = ""
    for parts in attempts:
        response = await model.generate_content_async(parts)
        raw_llm_text = _response_text(response)
        finish = None
        try:
            cands = getattr(response, "candidates", None) or []
            if cands:
                fr = getattr(cands[0], "finish_reason", None)
                finish = int(fr) if fr is not None else str(fr)
        except Exception:
            finish = None
        logger.info(
            "SPEECH transcribe raw_llm model=%s mime=%s finish=%s chars=%s text=%r",
            model_name,
            mime,
            finish,
            len(raw_llm_text or ""),
            raw_llm_text,
        )
        transcript = _clean_transcript(raw_llm_text)
        last_transcript = transcript
        if transcript and transcript.strip().lower() != "[no speech detected]" and not _looks_like_instruction_following_failure(transcript):
            return transcript, model_name
    return last_transcript, model_name


@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: str = Form("english"),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe a short mobile voice question.
    Raw audio is processed transiently and not stored after the request.
    """
    gemini_api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not gemini_api_key:
        raise HTTPException(status_code=503, detail="Speech transcription is not configured")
    if not speech_chat_enabled_for_user(current_user.userid):
        raise HTTPException(status_code=403, detail="Speech input is disabled")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Audio file is required")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio is too large. Please ask a shorter question.")

    logger.info(
        "SPEECH transcribe request user_id=%s bytes=%s filename=%s content_type=%s language=%s",
        current_user.userid,
        len(data),
        (audio.filename or "").strip() or None,
        (audio.content_type or "").strip() or None,
        (language or "").strip() or "english",
    )

    suffix = _audio_suffix(audio.filename, audio.content_type)
    mime = _normalized_mime_type(suffix, audio.content_type)

    try:
        transcript, model_name = await _transcribe_with_gemini(
            data=data,
            mime=mime,
            language=language,
        )

        transcript = _clean_transcript(transcript)
        if not transcript or transcript.strip().lower() == "[no speech detected]" or _looks_like_instruction_following_failure(transcript):
            logger.info(
                "SPEECH transcribe empty_or_suspicious user_id=%s model=%s transcript=%r",
                current_user.userid,
                model_name,
                transcript,
            )
            raise HTTPException(status_code=422, detail="Could not reliably understand the audio. Please try again.")
        logger.info(
            "SPEECH transcribe cleaned user_id=%s model=%s chars=%s transcript=%r",
            current_user.userid,
            model_name,
            len(transcript),
            transcript,
        )
        return {"transcript": transcript, "model": model_name}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "SPEECH transcribe failed user_id=%s detail=%s",
            current_user.userid,
            exc,
        )
        raise HTTPException(status_code=502, detail=f"Speech transcription failed: {exc}") from exc
