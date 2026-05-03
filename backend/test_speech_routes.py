import os
import sys
import types

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _stub_module(name: str, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


class _DummyUser:
    userid = 1


_stub_module("auth", get_current_user=lambda: _DummyUser(), User=_DummyUser)
google_mod = _stub_module("google")
genai_mod = _stub_module("google.generativeai")
setattr(google_mod, "generativeai", genai_mod)
_stub_module(
    "fastapi",
    APIRouter=lambda *args, **kwargs: types.SimpleNamespace(post=lambda *a, **k: (lambda fn: fn)),
    Depends=lambda *args, **kwargs: None,
    File=lambda *args, **kwargs: None,
    Form=lambda *args, **kwargs: None,
    HTTPException=Exception,
    UploadFile=object,
)

from speech.routes import _clean_transcript, _looks_like_instruction_following_failure, _normalized_mime_type, _normalized_transcription_language


def test_normalized_transcription_language():
    assert _normalized_transcription_language("english") == "en"
    assert _normalized_transcription_language("hindi") == "hi"
    assert _normalized_transcription_language("en-US") == "en"
    assert _normalized_transcription_language("hi-IN") == "hi"


def test_clean_transcript_strips_labels_and_quotes():
    assert _clean_transcript('Transcript: "Describe my behaviour"') == "Describe my behaviour"


def test_instruction_following_failure_detects_trivia_answer():
    assert _looks_like_instruction_following_failure("What is the capital of France?")
    assert _looks_like_instruction_following_failure("The capital of France is Paris.")
    assert not _looks_like_instruction_following_failure("Describe my behaviour")


def test_normalized_mime_type_keeps_3gpp_audio():
    assert _normalized_mime_type(".3gp", "audio/3gpp") == "audio/3gpp"
    assert _normalized_mime_type(".3gp", "") == "audio/3gpp"


if __name__ == "__main__":
    test_normalized_transcription_language()
    test_clean_transcript_strips_labels_and_quotes()
    test_instruction_following_failure_detects_trivia_answer()
    test_normalized_mime_type_keeps_3gpp_audio()
    print("speech route tests passed")
