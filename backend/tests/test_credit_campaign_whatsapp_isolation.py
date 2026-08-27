import os
from unittest.mock import patch

import pytest

from nudge_engine.connections import assert_explicit_isolated_database_configuration
from nudge_engine.credit_campaign_whatsapp import _retryable_provider_error
from nudge_engine.task_queue import _queue_name


def test_credit_campaign_send_requires_explicit_isolated_databases():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="Explicit notification database"):
            assert_explicit_isolated_database_configuration()


def test_credit_campaign_send_rejects_database_aliasing():
    values = {
        "POSTGRES_DSN": "postgresql://primary",
        "NUDGE_AUDIENCE_DATABASE_URL": "postgresql://replica",
        "NUDGE_NOTIFICATION_DATABASE_URL": "postgresql://primary",
    }
    with patch.dict(os.environ, values, clear=True):
        with pytest.raises(RuntimeError, match="must not equal the application primary"):
            assert_explicit_isolated_database_configuration()


def test_credit_campaign_whatsapp_uses_dedicated_queue():
    with patch.dict(os.environ, {}, clear=True):
        assert _queue_name("credit-campaign-whatsapp-batch") == "nudge-whatsapp-campaign-queue"


@pytest.mark.parametrize("error", ["Meta 429: busy", "Meta 503: unavailable", "connection timed out"])
def test_transient_meta_errors_are_retryable(error):
    assert _retryable_provider_error(error)


def test_permanent_meta_validation_error_is_not_retryable():
    assert not _retryable_provider_error("Meta 400: template parameter invalid")
