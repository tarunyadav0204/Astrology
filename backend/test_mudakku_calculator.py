import os
import sys


backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)


def test_mudakku_calculator_import():
    from calculators.mudakku_calculator import MudakkuCalculator

    calc = MudakkuCalculator(
        {
            "planets": {
                "Sun": {
                    "longitude": 15.0,  # Bharani
                }
            }
        }
    )

    result = calc.calculate()

    assert result["sun_nakshatra"]["name"] == "Bharani"
    assert result["count_to_mula"] == 18
    assert result["mudakku_nakshatra"]["name"] == "Magha"
    assert result["mudakku_rashi"] == "Leo"
    assert result["mudakku_rashi_lord"] == "Sun"
    assert result["is_split_nakshatra"] is False
    assert result["mudakku_point"]["sign_name"] == "Leo"
    assert result["mudakku_point"]["longitude"] > 0


def test_mudakku_summary():
    from calculators.mudakku_calculator import MudakkuCalculator

    calc = MudakkuCalculator(
        {
            "planets": {
                "Sun": {
                    "longitude": 335.0,  # Revati
                }
            }
        }
    )

    summary = calc.get_mudakku_summary()

    assert summary["sun_nakshatra"] == "Uttara Bhadrapada"
    assert summary["mudakku_nakshatra"] == "Hasta"
    assert summary["mudakku_rashi"] == "Virgo"
    assert summary["mudakku_rashi_lord"] == "Mercury"
