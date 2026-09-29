from pathlib import Path

import pytest

from partner_profile.storage import PartnerPortraitStorage


def test_local_partner_portrait_storage_round_trip_and_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("PARTNER_PORTRAIT_GCS_BUCKET", raising=False)
    monkeypatch.setenv("PARTNER_PORTRAIT_LOCAL_DIR", str(tmp_path))
    storage = PartnerPortraitStorage()

    uri = storage.save(
        user_id=10,
        job_id="job-1",
        kind="portrait",
        content=b"image-bytes",
        content_type="image/jpeg",
    )

    assert uri.endswith("portrait.jpg")
    assert storage.provider_input_uri(uri).startswith("data:image/jpeg;base64,")
    path = Path(uri.removeprefix("file://"))
    assert path.exists()
    storage.delete(uri)
    assert not path.exists()


def test_partner_portrait_requires_private_bucket_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("PARTNER_PORTRAIT_GCS_BUCKET", raising=False)
    with pytest.raises(RuntimeError, match="PARTNER_PORTRAIT_GCS_BUCKET"):
        PartnerPortraitStorage()
