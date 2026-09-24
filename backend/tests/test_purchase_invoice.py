"""Purchase invoices keep payment amounts and omit gateway secrets."""
import json
from contextlib import contextmanager

import db
from credits.credit_service import CreditService
from credits.invoice_service import purchase_invoice_document


def test_inr_purchase_invoice_includes_gst_and_hides_the_payment_token():
    metadata = {
        "purchase_token": "secret-play-token",
        "product_id": "credits_50",
        "order_id": "GPA.1234",
        "price_amount_micros": 99000000,
        "price_currency": "INR",
    }
    document = purchase_invoice_document(
        credits=50,
        source="google_play",
        reference_id="GPA.1234",
        metadata=json.dumps(metadata),
        amount_inr=99,
        issued_at="2026-09-22T06:00:00+00:00",
        buyer={"name": "Asha", "phone": "9999999999", "email": ""},
    )

    assert document["credits"] == 50
    assert document["product_id"] == "credits_50"
    assert document["order_id"] == "GPA.1234"
    assert document["payment_method"] == "google_play"
    assert document["buyer"] == {"name": "Asha", "phone": "9999999999"}
    assert document["seller"]["name"] == "APEIRON LOGIC LLP"
    assert document["seller"]["gstin"] == "06ACNFA1124G1ZS"
    assert "Gurgaon- 122004" in document["seller"]["address"]
    assert document["money"]["currency"] == "INR"
    assert document["money"]["amount_paid"] == 99
    assert document["money"]["tax_included"] is True
    assert document["money"]["tax_amount"] > 0
    dumped = json.dumps(document)
    assert "secret-play-token" not in dumped
    assert "purchase_token" not in dumped


def test_pack_without_a_stored_price_still_invoices_the_list_price_and_gst():
    document = purchase_invoice_document(
        credits=50,
        source="google_play",
        reference_id="GPA.50",
        metadata={"product_id": "credits_50", "order_id": "GPA.50"},
        amount_inr=None,
        issued_at="2026-09-22T06:00:00+00:00",
        buyer={"name": "Asha"},
    )
    assert document["money"]["currency"] == "INR"
    assert document["money"]["amount_paid"] == 99
    assert document["money"]["tax_included"] is True
    assert document["money"]["tax_amount"] > 0
    assert round(document["money"]["pretax_amount"] + document["money"]["tax_amount"], 2) == 99


def test_non_inr_invoice_has_no_gst_and_bonus_rows_are_not_invoices():
    document = purchase_invoice_document(
        credits=50,
        source="google_play",
        reference_id="GPA.9",
        metadata={"price_amount_micros": 1990000, "price_currency": "USD", "product_id": "credits_50"},
        amount_inr=None,
        issued_at="2026-09-22T06:00:00+00:00",
        buyer={"name": "Sam"},
    )
    assert document["money"]["currency"] == "USD"
    assert "tax_amount" not in document["money"]

    assert purchase_invoice_document(
        credits=10,
        source="first_purchase_bonus",
        reference_id="GPA.9",
        metadata={},
        amount_inr=None,
        issued_at="2026-09-22T06:00:00+00:00",
        buyer={},
    ) is None


def test_invoice_failure_does_not_report_a_committed_credit_grant_as_failed(monkeypatch):
    class Connection:
        committed = False

        def commit(self):
            self.committed = True

    connection = Connection()

    @contextmanager
    def fake_connection():
        yield connection

    monkeypatch.setattr(db, "get_conn", fake_connection)
    monkeypatch.setattr(db, "execute", lambda *_args, **_kwargs: None)

    service = CreditService()
    monkeypatch.setattr(service, "get_user_credits", lambda *_args, **_kwargs: 5)
    monkeypatch.setattr(service, "_upsert_user_credits", lambda *_args, **_kwargs: None)

    import credits.invoice_service as invoice_service

    def fail_invoice(*_args, **_kwargs):
        raise RuntimeError("invoice storage unavailable")

    monkeypatch.setattr(invoice_service, "ensure_purchase_invoice_for_reference", fail_invoice)

    assert service.add_credits(22081, 24, "google_play", reference_id="GPA.test") is True
    assert connection.committed is True
