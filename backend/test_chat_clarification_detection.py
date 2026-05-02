import os
import sys
import types

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    import google.generativeai  # noqa: F401
except ModuleNotFoundError:
    google_mod = sys.modules.setdefault("google", types.ModuleType("google"))
    genai_mod = types.ModuleType("google.generativeai")

    class _StubGenerativeModel:
        def __init__(self, *args, **kwargs):
            self._model_name = "stub-model"

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

try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:
    fastapi_mod = types.ModuleType("fastapi")

    class _StubAPIRouter:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def post(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def delete(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    class _StubHTTPException(Exception):
        pass

    class _StubBackgroundTasks:
        pass

    def _stub_depends(*args, **kwargs):
        return None

    fastapi_mod.APIRouter = _StubAPIRouter
    fastapi_mod.HTTPException = _StubHTTPException
    fastapi_mod.BackgroundTasks = _StubBackgroundTasks
    fastapi_mod.Depends = _stub_depends
    sys.modules["fastapi"] = fastapi_mod

if "auth" not in sys.modules:
    auth_mod = types.ModuleType("auth")
    auth_mod.get_current_user = lambda *args, **kwargs: None
    sys.modules["auth"] = auth_mod

if "db" not in sys.modules:
    db_mod = types.ModuleType("db")
    db_mod.get_conn = lambda *args, **kwargs: None
    db_mod.execute = lambda *args, **kwargs: None
    sys.modules["db"] = db_mod

from chat_history.routes import _looks_like_clarification_reply


def test_short_topic_reply_counts_as_clarification():
    assert _looks_like_clarification_reply("career") is True
    assert _looks_like_clarification_reply("both") is True
    assert _looks_like_clarification_reply("option b") is True


def test_brief_scoped_reply_counts_as_clarification():
    assert _looks_like_clarification_reply("about my marriage") is True
    assert _looks_like_clarification_reply("focus on career timing") is True


def test_fresh_question_does_not_count_as_clarification():
    assert _looks_like_clarification_reply("how are you today?") is False
    assert _looks_like_clarification_reply("what about tomorrow") is False
    assert _looks_like_clarification_reply("will today be good for me") is False


if __name__ == "__main__":
    test_short_topic_reply_counts_as_clarification()
    test_brief_scoped_reply_counts_as_clarification()
    test_fresh_question_does_not_count_as_clarification()
    print("chat clarification detection tests passed")
