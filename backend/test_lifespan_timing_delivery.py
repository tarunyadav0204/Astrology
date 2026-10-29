from chat.lifespan_timing_delivery import ensure_complete_ranked_lifespan_windows


PACK = {
    "candidate_windows": [
        {
            "rank": 1,
            "start": "2029-11-09",
            "end": "2032-07-10",
            "execution_start": "2029-11-10",
            "execution_end": "2029-12-31",
            "dasha_chain": "Jupiter-Venus-Venus",
            "double_transit": "full",
            "why": ["Venus occupies the main topic house"],
        },
        {
            "rank": 2,
            "start": "2026-08-28",
            "end": "2028-12-03",
            "execution_start": "2027-02-11",
            "execution_end": "2027-06-28",
            "dasha_chain": "Jupiter-Mercury-Venus",
            "double_transit": "partial",
            "why": ["Mercury rules a supportive topic house"],
        },
    ]
}


def test_appends_omitted_secondary_viable_window():
    answer = """### Ranked Potential Windows
- **Window 1**: 2029-11-09 – 2032-07-10, Jupiter-Venus-Venus."""

    repaired = ensure_complete_ranked_lifespan_windows(answer, PACK)

    assert "Additional calculated timing window" in repaired
    assert "Window 2" in repaired
    assert "2026-08-28 – 2028-12-03" in repaired
    assert "Jupiter-Mercury-Venus" in repaired
    assert "preparation only" in repaired


def test_does_not_duplicate_windows_already_present_in_rank_order():
    answer = """### Ranked Potential Windows
- **Window 1**: 2029-11-09 – 2032-07-10, Jupiter-Venus-Venus.
- **Window 2**: 2026-08-28 – 2028-12-03, Jupiter-Mercury-Venus."""

    assert ensure_complete_ranked_lifespan_windows(answer, PACK) == answer
