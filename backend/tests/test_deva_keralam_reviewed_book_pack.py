from pathlib import Path

from classical_rules.deva_keralam.reviewed_batches import (
    audit_reviewed_manifests,
    discover_reviewed_manifests,
    load_book_1_reviewed_rule_pack,
    load_reviewed_rule_pack,
)
from classical_rules.deva_keralam.service import match_deva_keralam_chart


DATA_DIR = Path(__file__).resolve().parents[1] / "classical_rules" / "deva_keralam" / "data"


def _manifest_paths():
    return discover_reviewed_manifests(DATA_DIR)


def test_reviewed_book_batches_have_decision_compiler_parity():
    paths = _manifest_paths()
    assert [path.name for path in paths] == [
        "reviewed_batch_a_v1.json",
        "reviewed_batch_b_v1.json",
        "reviewed_batch_c_v1.json",
        "reviewed_batch_d_v1.json",
        "reviewed_batch_e_v1.json",
        "reviewed_batch_f_v1.json",
        "reviewed_batch_g_v1.json",
    ]
    audit = audit_reviewed_manifests(paths)
    assert audit.valid, audit.issues
    assert audit.reviewed_candidates == 158
    assert audit.approved_candidates == 98
    assert audit.rejected_candidates == 60
    assert audit.compiled_rules == 98
    book_pack = load_book_1_reviewed_rule_pack(paths)
    assert book_pack.included_existing_rule_count == 13
    assert len(book_pack.rules) == 111


def test_real_longitudes_flow_through_adapter_and_match_each_review_stream():
    pack = load_reviewed_rule_pack(_manifest_paths())

    # Virgo 9°48′18″: Dhanada ordinal 125, former half.
    batch_a = match_deva_keralam_chart(
        {"ascendant": 159.805, "planets": {}},
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 1},
        rules=pack.rules,
    )
    assert "DK1.A.V0738_DHANADA_FORMER" in batch_a["summary"]["matched_rule_keys"]

    # Libra Ascendant with Mars in Gemini gives Mars in natal House 9.
    batch_b = match_deva_keralam_chart(
        {"ascendant": 190.0, "planets": {"Mars": {"longitude": 70.0}}},
        rules=pack.rules,
    )
    assert "DK.B.1030_LIBRA_MARS_NINTH" in batch_b["summary"]["matched_rule_keys"]

    # Aquarius 16°24′18″: Nirmalaa ordinal 68, former half.
    batch_c = match_deva_keralam_chart(
        {"ascendant": 316.405, "planets": {}},
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 1},
        rules=pack.rules,
    )
    assert "DK.C.1901-1904.AQUARIUS_NIRMALAA_FORMER" in batch_c["summary"]["matched_rule_keys"]
