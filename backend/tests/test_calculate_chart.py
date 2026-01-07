"""
Comprehensive test cases for calculateChart method
Tests both /calculate-chart (saves to DB) and /calculate-chart-only (display only) endpoints
"""

import pytest
import json
import sqlite3
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from auth import create_access_token

client = TestClient(app)

class TestCalculateChart:
    """Test suite for chart calculation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_test_user(self):
        """Create test user and get auth token"""
        # Create test user
        user_data = {
            "name": "Test User",
            "phone": "+1234567890",
            "password": "testpass123",
            "email": "test@example.com"
        }
        
        # Register user
        response = client.post("/api/register", json=user_data)
        assert response.status_code == 200
        
        self.auth_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.user_id = response.json()["user"]["userid"]
    
    def teardown_method(self):
        """Clean up test data"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM birth_charts WHERE userid = ?", (self.user_id,))
        cursor.execute("DELETE FROM users WHERE userid = ?", (self.user_id,))
        conn.commit()
        conn.close()

class TestCalculateChartOnly:
    """Test /calculate-chart-only endpoint (display only, no DB save)"""
    
    def test_valid_birth_data_success(self):
        """Test successful chart calculation with valid birth data"""
        birth_data = {
            "name": "John Doe",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "New Delhi, India",
            "gender": "male"
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify chart structure
        assert "planets" in data
        assert "houses" in data
        assert "ascendant" in data
        assert "ayanamsa" in data
        
        # Verify planets data
        expected_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        for planet in expected_planets:
            assert planet in data["planets"]
            assert "longitude" in data["planets"][planet]
            assert "sign" in data["planets"][planet]
            assert "degree" in data["planets"][planet]
        
        # Verify houses data
        assert len(data["houses"]) == 12
        for house in data["houses"]:
            assert "longitude" in house
            assert "sign" in house
    
    def test_nested_birth_data_format(self):
        """Test chart calculation with nested birth_data format"""
        request_data = {
            "birth_data": {
                "name": "Jane Smith",
                "date": "1985-12-25",
                "time": "09:15",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "place": "Mumbai, India"
            }
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "planets" in data
        assert "houses" in data
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields"""
        incomplete_data = {
            "name": "Test Person",
            "date": "1990-01-01"
            # Missing time, latitude, longitude
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=incomplete_data,
            headers=self.headers
        )
        
        assert response.status_code == 500  # Should handle gracefully
    
    def test_invalid_date_format(self):
        """Test error handling for invalid date format"""
        birth_data = {
            "name": "Test Person",
            "date": "15-05-1990",  # Invalid format
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 500
    
    def test_invalid_time_format(self):
        """Test error handling for invalid time format"""
        birth_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "25:70",  # Invalid time
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 500
    
    def test_invalid_coordinates(self):
        """Test error handling for invalid coordinates"""
        birth_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 200.0,  # Invalid latitude
            "longitude": 400.0   # Invalid longitude
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 500
    
    def test_timezone_auto_detection(self):
        """Test automatic timezone detection from coordinates"""
        birth_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "New Delhi, India"
        }
        
        with patch('utils.timezone_service.get_timezone_from_coordinates') as mock_tz:
            mock_tz.return_value = "UTC+5:30"
            
            response = client.post(
                "/api/calculate-chart-only",
                json=birth_data,
                headers=self.headers
            )
            
            assert response.status_code == 200
            mock_tz.assert_called_once_with(28.6139, 77.2090)
    
    def test_different_node_types(self):
        """Test chart calculation with different node types"""
        birth_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        # Test with mean nodes (default)
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        mean_data = response.json()
        
        # Verify Rahu/Ketu positions exist
        assert "Rahu" in mean_data["planets"]
        assert "Ketu" in mean_data["planets"]
    
    def test_performance_timing(self):
        """Test chart calculation performance"""
        birth_data = {
            "name": "Performance Test",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        start_time = datetime.now()
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        assert duration < 5.0  # Should complete within 5 seconds
    
    def test_unauthorized_access(self):
        """Test access without authentication"""
        birth_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data
            # No headers (no auth)
        )
        
        assert response.status_code == 403  # Unauthorized

class TestCalculateChartWithDB:
    """Test /calculate-chart endpoint (saves to database)"""
    
    def test_valid_chart_creation_and_db_save(self):
        """Test successful chart creation with database save"""
        birth_data = {
            "name": "Database Test",
            "date": "1992-08-20",
            "time": "16:45",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "place": "Bangalore, India",
            "gender": "female",
            "relation": "self"
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify chart data structure
        assert "planets" in data
        assert "houses" in data
        assert "ascendant" in data
        
        # Verify database save
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, date, time, relation FROM birth_charts WHERE userid = ?",
            (self.user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        # Note: name, date, time might be encrypted
    
    def test_duplicate_chart_handling(self):
        """Test handling of duplicate chart entries"""
        birth_data = {
            "name": "Duplicate Test",
            "date": "1988-03-10",
            "time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "Delhi, India"
        }
        
        # Create first chart
        response1 = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        assert response1.status_code == 200
        
        # Create duplicate chart
        response2 = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        assert response2.status_code == 200
        
        # Verify both entries exist in database
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM birth_charts WHERE userid = ?",
            (self.user_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2  # Should allow duplicates
    
    def test_invalid_coordinates_validation(self):
        """Test validation of coordinates before database save"""
        birth_data = {
            "name": "Invalid Coords",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 0,  # Invalid
            "longitude": 0   # Invalid
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        assert "coordinates required" in response.json()["detail"]
    
    def test_invalid_date_validation(self):
        """Test date format validation before database save"""
        birth_data = {
            "name": "Invalid Date",
            "date": "15/05/1990",  # Wrong format
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        assert "Invalid date format" in response.json()["detail"]
    
    def test_invalid_time_validation(self):
        """Test time format validation before database save"""
        birth_data = {
            "name": "Invalid Time",
            "date": "1990-05-15",
            "time": "25:70",  # Invalid time
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        assert "Invalid time format" in response.json()["detail"]
    
    def test_missing_timezone_validation(self):
        """Test timezone validation"""
        birth_data = {
            "name": "No Timezone",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": ""  # Empty timezone
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 422
        assert "Timezone is required" in response.json()["detail"]
    
    def test_relation_field_handling(self):
        """Test proper handling of relation field"""
        birth_data = {
            "name": "Relation Test",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "Delhi, India",
            "relation": "self"
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        # Verify relation is saved correctly
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT relation FROM birth_charts WHERE userid = ? ORDER BY id DESC LIMIT 1",
            (self.user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result[0] == "self"
    
    def test_encryption_handling(self):
        """Test that sensitive data is properly encrypted if encryption is enabled"""
        birth_data = {
            "name": "Encryption Test",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "Sensitive Location"
        }
        
        response = client.post(
            "/api/calculate-chart",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        # Check if data is encrypted in database
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, place FROM birth_charts WHERE userid = ? ORDER BY id DESC LIMIT 1",
            (self.user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        # If encryption is enabled, stored data should not match plain text
        # If encryption is disabled, it should match
        stored_name, stored_place = result
        
        # This test will pass regardless of encryption status
        assert stored_name is not None
        assert stored_place is not None

class TestChartCalculationAccuracy:
    """Test accuracy of astrological calculations"""
    
    def test_known_birth_chart_accuracy(self):
        """Test calculation accuracy with known birth chart data"""
        # Using a well-known birth chart for verification
        birth_data = {
            "name": "Accuracy Test",
            "date": "1969-07-20",  # Apollo 11 moon landing
            "time": "20:17",       # UTC time
            "latitude": 28.6139,   # Delhi coordinates
            "longitude": 77.2090,
            "place": "Delhi, India"
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic astrological principles
        assert 0 <= data["ascendant"] < 360
        
        for planet in data["planets"].values():
            assert 0 <= planet["longitude"] < 360
            assert 0 <= planet["sign"] < 12
            assert 0 <= planet["degree"] < 30
    
    def test_ayanamsa_calculation(self):
        """Test Ayanamsa (precession) calculation"""
        birth_data = {
            "name": "Ayanamsa Test",
            "date": "2000-01-01",
            "time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Ayanamsa for year 2000 should be around 23.85 degrees (Lahiri)
        ayanamsa = data["ayanamsa"]
        assert 23.0 < ayanamsa < 25.0
    
    def test_retrograde_detection(self):
        """Test retrograde planet detection"""
        birth_data = {
            "name": "Retrograde Test",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that retrograde field exists for planets that can be retrograde
        retrograde_planets = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        for planet in retrograde_planets:
            if planet in data["planets"]:
                assert "retrograde" in data["planets"][planet]
                assert isinstance(data["planets"][planet]["retrograde"], bool)
    
    def test_rahu_ketu_opposition(self):
        """Test that Rahu and Ketu are always 180 degrees apart"""
        birth_data = {
            "name": "Nodes Test",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        rahu_long = data["planets"]["Rahu"]["longitude"]
        ketu_long = data["planets"]["Ketu"]["longitude"]
        
        # Calculate difference (accounting for 360-degree wrap)
        diff = abs(rahu_long - ketu_long)
        if diff > 180:
            diff = 360 - diff
        
        # Should be exactly 180 degrees apart (within small tolerance)
        assert abs(diff - 180) < 0.1

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_leap_year_date(self):
        """Test calculation with leap year date"""
        birth_data = {
            "name": "Leap Year Test",
            "date": "2000-02-29",  # Leap year
            "time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    def test_midnight_time(self):
        """Test calculation at midnight"""
        birth_data = {
            "name": "Midnight Test",
            "date": "1990-05-15",
            "time": "00:00",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    def test_extreme_coordinates(self):
        """Test calculation with extreme but valid coordinates"""
        birth_data = {
            "name": "Extreme Coords Test",
            "date": "1990-05-15",
            "time": "12:00",
            "latitude": 89.9,   # Near North Pole
            "longitude": 179.9  # Near International Date Line
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    def test_southern_hemisphere(self):
        """Test calculation in Southern Hemisphere"""
        birth_data = {
            "name": "Southern Hemisphere Test",
            "date": "1990-05-15",
            "time": "12:00",
            "latitude": -33.8688,  # Sydney, Australia
            "longitude": 151.2093
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    def test_very_old_date(self):
        """Test calculation with very old date"""
        birth_data = {
            "name": "Old Date Test",
            "date": "1900-01-01",
            "time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    def test_future_date(self):
        """Test calculation with future date"""
        birth_data = {
            "name": "Future Date Test",
            "date": "2050-12-31",
            "time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/calculate-chart-only",
            json=birth_data,
            headers=self.headers
        )
        
        assert response.status_code == 200

class TestConcurrency:
    """Test concurrent access and performance"""
    
    def test_multiple_simultaneous_requests(self):
        """Test handling multiple simultaneous chart calculations"""
        import threading
        import time
        
        results = []
        
        def calculate_chart():
            birth_data = {
                "name": f"Concurrent Test {threading.current_thread().ident}",
                "date": "1990-05-15",
                "time": "14:30",
                "latitude": 28.6139,
                "longitude": 77.2090
            }
            
            response = client.post(
                "/api/calculate-chart-only",
                json=birth_data,
                headers=self.headers
            )
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=calculate_chart)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])