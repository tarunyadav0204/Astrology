import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from chat import feedback_routes as routes


def test_feedback_accepts_reasons_and_legacy_ratings():
    for reason in ['unclear', 'wrong_personal_detail', 'contradicts_earlier_answer', 'helpful', None]:
        assert routes.FeedbackRequest(message_id=1, rating=2, reason=reason).reason == reason
    with pytest.raises(ValidationError):
        routes.FeedbackRequest(message_id=1, rating=2, reason='unknown')


def test_user_feedback_is_scoped_to_owner(monkeypatch):
    queries = []
    class Cursor:
        def fetchall(self):
            return [(7, 5, '', '2026-10-08', 'helpful')]
    class Conn:
        def commit(self):
            pass
    @contextmanager
    def connection():
        yield Conn()
    def execute(conn, query, params):
        queries.append((query, params))
        return Cursor()
    monkeypatch.setattr(routes, 'get_conn', connection)
    monkeypatch.setattr(routes, 'execute', execute)
    result = asyncio.run(routes.get_user_feedback(SimpleNamespace(userid=42)))
    assert result['feedback'][0]['reason'] == 'helpful'
    query, params = queries[-1]
    assert 'WHERE cs.user_id = %s' in query
    assert params == (42,)
