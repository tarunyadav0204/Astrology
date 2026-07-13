"""Tests for admin-managed credit pack visibility (Play + Razorpay)."""
from unittest.mock import MagicMock, patch

import pytest


def test_list_active_credit_amounts_filters_inactive():
    from credits.credit_service import CreditService

    svc = CreditService.__new__(CreditService)

    def _list(active_only=False):
        all_rows = [
            {"product_id": "credits_50", "credits": 50, "is_active": True, "sort_order": 1},
            {"product_id": "credits_100", "credits": 100, "is_active": False, "sort_order": 2},
            {"product_id": "credits_250", "credits": 250, "is_active": True, "sort_order": 3},
        ]
        if active_only:
            return [r for r in all_rows if r["is_active"]]
        return all_rows

    with patch.object(svc, "list_credit_products", side_effect=_list):
        assert svc.list_active_credit_amounts() == [50, 250]
        assert svc.is_credit_pack_sellable(credits=50) is True
        assert svc.is_credit_pack_sellable(product_id="credits_100") is False
        assert svc.is_credit_pack_sellable(product_id="credits_999") is False

def test_razorpay_catalog_respects_active_packs():
    from credits import razorpay_routes as rz

    with patch.object(rz.credit_service, "list_active_credit_amounts", return_value=[50, 250]):
        packs = rz.get_razorpay_credit_packs()
    assert [p["credits"] for p in packs] == [50, 250]
    assert all(p["product_id"] == f"credits_{p['credits']}" for p in packs)
