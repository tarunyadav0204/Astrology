from calculators.ashtakavarga_transit import AshtakavargaTransitCalculator


class _StubTransitCalculator(AshtakavargaTransitCalculator):
    def __init__(self):
        # No parent init needed because the test stubs the AV outputs directly.
        pass

    def calculate_sarvashtakavarga(self):
        return {
            "sarvashtakavarga": {
                "0": 30,
                "1": 28,
                "2": 26,
                "3": 25,
                "4": 27,
                "5": 29,
                "6": 31,
                "7": 24,
                "8": 27,
                "9": 30,
                "10": 29,
                "11": 31,
            }
        }

    def calculate_transit_ashtakavarga(self, transit_date):
        return {
            "sarvashtakavarga": {
                "0": 32,
                "1": 26,
                "2": 26,
                "3": 23,
                "4": 28,
                "5": 29,
                "6": 29,
                "7": 26,
                "8": 27,
                "9": 30,
                "10": 30,
                "11": 31,
            }
        }


def test_compare_birth_transit_strength_uses_redistribution_not_total_delta():
    calc = _StubTransitCalculator()

    comparison = calc.compare_birth_transit_strength("2026-04-22")
    summary = comparison["summary"]

    assert summary["distribution_shift"] == 6
    assert summary["distribution_percentage"] == 1.8
    assert summary["comparison_basis"] == "redistribution_only"

    assert "total_birth_bindus" not in summary
    assert "total_transit_bindus" not in summary
    assert "overall_change" not in summary
    assert "overall_percentage" not in summary
