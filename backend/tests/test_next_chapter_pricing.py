"""Launch price and Admin override contract, without touching customer credits."""
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from credits.credit_service import CreditService


@pytest.mark.parametrize('row, expected', [
    (None, (49, 49, None)),
    ((79, None), (79, 79, None)),
    ((79, 39), (39, 79, 39)),
    ((0, None), (0, 0, None)),
    ((49, 0), (0, 49, 0)),
])
def test_chapter_admin_price_and_default(monkeypatch, row, expected):
    import db
    monkeypatch.setattr(db, 'get_conn', lambda: nullcontext(object()))

    def execute(conn, sql, params):
        assert params == ('next_chapter_cost',)
        return SimpleNamespace(fetchone=lambda: row)

    monkeypatch.setattr(db, 'execute', execute)
    service = CreditService.__new__(CreditService)
    assert service.get_credit_setting_and_original('next_chapter_cost') == expected
    assert service.get_credit_setting('next_chapter_cost') == expected[0]


def test_chapter_subscription_discount_uses_admin_original(monkeypatch):
    service = CreditService.__new__(CreditService)
    monkeypatch.setattr(service, 'get_subscription_discount_percent', lambda user: 20)
    monkeypatch.setattr(service, 'get_credit_setting_and_original', lambda key: (39, 79, 39))
    assert service.get_effective_cost(1, 39, 'next_chapter_cost') == 63
