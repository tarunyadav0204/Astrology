from datetime import date

from calculators.event_timeline_calibration import calculate_calibration_metrics


def test_calibration_metrics_include_partial_top3_timing_and_false_positives():
    rows = [
        {
            "display_rank": 1, "event_key": "marriage", "support_grade": "A",
            "engine_version": "accuracy_v3", "accuracy_layer": "integrated_v2",
            "forecast_start": date(2030, 1, 10), "forecast_end": date(2030, 1, 20),
            "occurrence": "occurred", "actual_date": date(2030, 1, 18),
        },
        {
            "display_rank": 2, "event_key": "health", "support_grade": "B",
            "engine_version": "accuracy_v3", "accuracy_layer": "integrated_v2",
            "forecast_start": date(2030, 1, 1), "forecast_end": date(2030, 1, 10),
            "occurrence": "partly_occurred", "actual_date": date(2030, 1, 13),
        },
        {
            "display_rank": 4, "event_key": "promotion", "support_grade": "B",
            "engine_version": "accuracy_v3", "accuracy_layer": "delivery_v1",
            "forecast_start": date(2030, 1, 1), "forecast_end": date(2030, 1, 31),
            "occurrence": "did_not_occur", "actual_date": None,
        },
    ]
    result = calculate_calibration_metrics(rows, [{"event_key": "relocation"}])
    assert result["evaluated"] == 3
    assert result["precision_including_partial"] == 0.6667
    assert result["strict_precision"] == 0.3333
    assert result["precision_at_3"] == 1.0
    assert result["mean_absolute_timing_error_days"] == 1.5
    assert result["reported_event_recall"] == 0.6667
    assert result["by_domain"]["promotion"]["false_positive"] == 1
    assert result["by_engine_layer"]["accuracy_v3:integrated_v2"]["evaluated"] == 2
    assert result["by_engine_layer"]["accuracy_v3:delivery_v1"]["strict_precision"] == 0.0
