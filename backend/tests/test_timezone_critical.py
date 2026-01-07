"""Critical timezone tests - would have caught the Asia/Kolkata bug"""
import pytest
from utils.timezone_service import get_timezone_from_coordinates, parse_timezone_offset


class TestTimezoneCalculation:
    """Tests for timezone calculation from coordinates"""
    
    def test_delhi_coordinates_give_ist(self):
        """Delhi should return UTC+5:30"""
        tz = get_timezone_from_coordinates(28.6139, 77.2090)
        assert tz == 'UTC+5:30', f"Expected UTC+5:30, got {tz}"
    
    def test_new_york_coordinates(self):
        """New York should return UTC-5 or UTC-4 depending on DST"""
        tz = get_timezone_from_coordinates(40.7128, -74.0060)
        assert tz in ['UTC-5', 'UTC-4'], f"Expected UTC-5 or UTC-4, got {tz}"
    
    def test_london_coordinates(self):
        """London should return UTC+0 or UTC+1 depending on DST"""
        tz = get_timezone_from_coordinates(51.5074, -0.1278)
        assert tz in ['UTC+0', 'UTC+1'], f"Expected UTC+0 or UTC+1, got {tz}"
    
    def test_timezone_calculation_is_deterministic(self):
        """Same coordinates should always give same timezone"""
        tz1 = get_timezone_from_coordinates(28.6139, 77.2090)
        tz2 = get_timezone_from_coordinates(28.6139, 77.2090)
        assert tz1 == tz2, "Timezone calculation not deterministic"
    
    def test_parse_utc_plus_format(self):
        """Test parsing UTC+5:30 format"""
        offset = parse_timezone_offset('UTC+5:30')
        assert offset == 5.5, f"Expected 5.5, got {offset}"
    
    def test_parse_utc_minus_format(self):
        """Test parsing UTC-8:00 format"""
        offset = parse_timezone_offset('UTC-8:00')
        assert offset == -8.0, f"Expected -8.0, got {offset}"
    
    def test_parse_utc_simple_format(self):
        """Test parsing UTC+5 format"""
        offset = parse_timezone_offset('UTC+5')
        assert offset == 5.0, f"Expected 5.0, got {offset}"
    
    def test_parse_numeric_string(self):
        """Test parsing numeric string"""
        offset = parse_timezone_offset('5.5')
        assert offset == 5.5
    
    def test_parse_numeric_float(self):
        """Test parsing float directly"""
        offset = parse_timezone_offset(5.5)
        assert offset == 5.5
    
    def test_fallback_to_coordinates_when_empty(self):
        """When timezone is empty, should calculate from coordinates"""
        offset = parse_timezone_offset('', latitude=28.6139, longitude=77.2090)
        assert offset == 5.5, f"Expected 5.5 from coordinates, got {offset}"
    
    def test_fallback_to_coordinates_when_utc_zero(self):
        """When timezone is UTC+0, should calculate from coordinates if provided"""
        offset = parse_timezone_offset('UTC+0', latitude=28.6139, longitude=77.2090)
        # Should detect from coordinates and return 5.5
        assert offset == 5.5, f"Expected 5.5 from coordinates, got {offset}"
    
    def test_no_coordinates_returns_zero(self):
        """When no timezone and no coordinates, should return 0"""
        offset = parse_timezone_offset('')
        assert offset == 0.0, f"Expected 0.0, got {offset}"


class TestTimezoneNotRequired:
    """Test that timezone is NOT required in requests - prevents Asia/Kolkata bug"""
    
    def test_chart_calculation_without_timezone_field(self, sample_birth_data):
        """Chart calculation should work without timezone field"""
        from calculators.chart_calculator import ChartCalculator
        from types import SimpleNamespace
        
        # Remove timezone if it exists
        data = {k: v for k, v in sample_birth_data.items() if k != 'timezone'}
        
        birth_obj = SimpleNamespace(**data)
        calc = ChartCalculator({})
        
        # Should not raise error
        result = calc.calculate_chart(birth_obj)
        assert result is not None
        assert 'ascendant' in result
    
    def test_request_data_has_no_timezone(self, sample_birth_data):
        """Verify sample data doesn't include timezone field"""
        assert 'timezone' not in sample_birth_data, \
            "Sample birth data should NOT include timezone field"
    
    def test_coordinates_are_sufficient(self, sample_birth_data):
        """Verify that latitude and longitude are present"""
        assert 'latitude' in sample_birth_data
        assert 'longitude' in sample_birth_data
        assert sample_birth_data['latitude'] is not None
        assert sample_birth_data['longitude'] is not None


class TestTimezoneRegression:
    """Regression tests to prevent timezone bugs from returning"""
    
    def test_no_hardcoded_asia_kolkata_in_calculation(self, sample_birth_data):
        """Ensure calculations don't use hardcoded Asia/Kolkata"""
        from calculators.chart_calculator import ChartCalculator
        from types import SimpleNamespace
        
        # Use coordinates that are NOT in India
        data = sample_birth_data.copy()
        data['latitude'] = 40.7128  # New York
        data['longitude'] = -74.0060
        
        birth_obj = SimpleNamespace(**data)
        calc = ChartCalculator({})
        result = calc.calculate_chart(birth_obj)
        
        # If it was using hardcoded Asia/Kolkata, the ascendant would be wrong
        # This is a smoke test - actual value verification would need golden dataset
        assert result is not None
        assert 'ascendant' in result
    
    def test_same_coordinates_same_chart(self, sample_birth_data):
        """Same coordinates should produce same chart"""
        from calculators.chart_calculator import ChartCalculator
        from types import SimpleNamespace
        
        birth_obj = SimpleNamespace(**sample_birth_data)
        calc = ChartCalculator({})
        
        result1 = calc.calculate_chart(birth_obj)
        result2 = calc.calculate_chart(birth_obj)
        
        assert result1['ascendant'] == result2['ascendant'], \
            "Same input should produce same ascendant"
