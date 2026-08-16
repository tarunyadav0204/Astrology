from __future__ import annotations

from credits.credit_service import CreditService
from utils import admin_settings


def _configured_service(monkeypatch, *, balance: int, used: bool = False) -> CreditService:
    service = CreditService()
    monkeypatch.setattr(admin_settings, "is_free_question_enabled", lambda: True)
    monkeypatch.setattr(service, "get_user_credits", lambda userid: balance)
    monkeypatch.setattr(service, "get_free_chat_question_used", lambda userid: used)
    monkeypatch.setattr(
        service,
        "notification_opt_in_satisfied_for_free_question",
        lambda userid: True,
    )
    return service


def test_free_question_is_hidden_when_user_has_credits(monkeypatch):
    service = _configured_service(monkeypatch, balance=20)

    assert service.is_free_standard_chat_question_available(123) is False


def test_free_question_remains_available_for_zero_balance_user(monkeypatch):
    service = _configured_service(monkeypatch, balance=0)

    assert service.is_free_standard_chat_question_available(123) is True


def test_used_free_question_stays_unavailable_at_zero_balance(monkeypatch):
    service = _configured_service(monkeypatch, balance=0, used=True)

    assert service.is_free_standard_chat_question_available(123) is False
