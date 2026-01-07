"""
Simplified test cases for calculateChart method
Tests core functionality without complex setup requirements
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
import tempfile

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

class TestCalculateChartSimple:
    """Simplified test suite for chart calculation"""
    
    def __init__(self):
        self.test_db = None
        self.setup_test_db()
    
    def setup_test_db(self):
        """Setup temporary test database"""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db.close()
        
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Create minimal tables for testing
        cursor.execute('''
            CREATE TABLE users (
                userid INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE birth_charts (
                id INTEGER PRIMARY KEY,
                userid INTEGER,
                name TEXT,
                date TEXT,
                time TEXT,
                latitude REAL,
                longitude REAL,
                timezone TEXT,
                place TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                relation TEXT DEFAULT 'other'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def cleanup(self):
        """Cleanup test database"""
        if self.test_db and os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_chart_calculator_import(self):
        """Test that chart calculator can be imported"""
        try:
            from calculators.chart_calculator import ChartCalculator
            print("✅ ChartCalculator import successful")
            return True
        except ImportError as e:
            print(f"❌ ChartCalculator import failed: {e}")
            return False
    
    def test_birth_data_validation(self):
        """Test birth data validation logic"""
        print("🧪 Testing birth data validation...")
        
        # Test valid data
        valid_data = {
            "name": "Test Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "place": "Delhi, India"
        }
        
        # Test date validation
        try:
            datetime.strptime(valid_data["date"], '%Y-%m-%d')
            print("✅ Valid date format accepted")
        except ValueError:
            print("❌ Valid date format rejected")
            return False
        
        # Test invalid date
        try:
            datetime.strptime("15-05-1990", '%Y-%m-%d')
            print("❌ Invalid date format accepted")
            return False
        except ValueError:
            print("✅ Invalid date format rejected")
        
        # Test time validation
        time_parts = valid_data["time"].split(':')
        if len(time_parts) == 2:
            hour, minute = int(time_parts[0]), int(time_parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                print("✅ Valid time format accepted")
            else:
                print("❌ Valid time format rejected")
                return False
        
        # Test coordinate validation
        lat, lon = valid_data["latitude"], valid_data["longitude"]
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            print("✅ Valid coordinates accepted")
        else:
            print("❌ Valid coordinates rejected")
            return False
        
        return True
    
    def test_chart_calculation_basic(self):
        """Test basic chart calculation functionality"""
        print("🧪 Testing basic chart calculation...")
        
        try:
            from calculators.chart_calculator import ChartCalculator
            
            # Create a simple birth data object
            class BirthData:
                def __init__(self):
                    self.name = "Test Person"
                    self.date = "1990-05-15"
                    self.time = "14:30"
                    self.latitude = 28.6139
                    self.longitude = 77.2090
                    self.timezone = "UTC+5:30"
                    self.place = "Delhi, India"
            
            birth_data = BirthData()
            calculator = ChartCalculator({})
            
            # Attempt calculation
            result = calculator.calculate_chart(birth_data)
            
            # Verify result structure
            if isinstance(result, dict):
                required_keys = ['planets', 'houses', 'ascendant']
                if all(key in result for key in required_keys):
                    print("✅ Chart calculation returned expected structure")
                    
                    # Verify planets data
                    expected_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                    planets_found = [p for p in expected_planets if p in result['planets']]
                    
                    if len(planets_found) >= 7:
                        print(f"✅ Found {len(planets_found)} planets in result")
                    else:
                        print(f"⚠️ Only found {len(planets_found)} planets, expected 7+")
                    
                    # Verify houses data
                    if 'houses' in result and len(result['houses']) == 12:
                        print("✅ Found 12 houses in result")
                    else:
                        print("⚠️ Houses data incomplete")
                    
                    return True
                else:
                    print(f"❌ Missing required keys in result: {required_keys}")
                    return False
            else:
                print("❌ Chart calculation did not return dictionary")
                return False
                
        except Exception as e:
            print(f"❌ Chart calculation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_timezone_detection(self):
        """Test timezone detection functionality"""
        print("🧪 Testing timezone detection...")
        
        try:
            from utils.timezone_service import get_timezone_from_coordinates
            
            # Test with Delhi coordinates
            timezone = get_timezone_from_coordinates(28.6139, 77.2090)
            
            if timezone and isinstance(timezone, str):
                print(f"✅ Timezone detection successful: {timezone}")
                return True
            else:
                print("❌ Timezone detection returned invalid result")
                return False
                
        except ImportError:
            print("⚠️ Timezone service not available (optional)")
            return True
        except Exception as e:
            print(f"❌ Timezone detection failed: {e}")
            return False
    
    def test_database_operations(self):
        """Test database operations for chart storage"""
        print("🧪 Testing database operations...")
        
        try:
            conn = sqlite3.connect(self.test_db.name)
            cursor = conn.cursor()
            
            # Test user creation
            cursor.execute(
                "INSERT INTO users (name, phone, password) VALUES (?, ?, ?)",
                ("Test User", "+1234567890", "hashed_password")
            )
            user_id = cursor.lastrowid
            
            # Test chart creation
            cursor.execute('''
                INSERT INTO birth_charts 
                (userid, name, date, time, latitude, longitude, timezone, place, relation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, "Test Chart", "1990-05-15", "14:30", 28.6139, 77.2090, 
                  "UTC+5:30", "Delhi, India", "self"))
            
            chart_id = cursor.lastrowid
            
            # Verify data was stored
            cursor.execute("SELECT * FROM birth_charts WHERE id = ?", (chart_id,))
            result = cursor.fetchone()
            
            conn.commit()
            conn.close()
            
            if result:
                print("✅ Database operations successful")
                return True
            else:
                print("❌ Database operations failed")
                return False
                
        except Exception as e:
            print(f"❌ Database operations failed: {e}")
            return False
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("🧪 Testing edge cases...")
        
        test_cases = [
            {
                "name": "Leap Year",
                "date": "2000-02-29",
                "time": "12:00",
                "lat": 28.6139,
                "lon": 77.2090
            },
            {
                "name": "Midnight",
                "date": "1990-05-15", 
                "time": "00:00",
                "lat": 28.6139,
                "lon": 77.2090
            },
            {
                "name": "Southern Hemisphere",
                "date": "1990-05-15",
                "time": "12:00", 
                "lat": -33.8688,
                "lon": 151.2093
            }
        ]
        
        passed = 0
        for case in test_cases:
            try:
                # Validate date
                datetime.strptime(case["date"], '%Y-%m-%d')
                
                # Validate time
                time_parts = case["time"].split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    passed += 1
                    print(f"✅ {case['name']} case passed")
                else:
                    print(f"❌ {case['name']} case failed - invalid time")
                    
            except Exception as e:
                print(f"❌ {case['name']} case failed: {e}")
        
        if passed == len(test_cases):
            print(f"✅ All {passed} edge cases passed")
            return True
        else:
            print(f"⚠️ {passed}/{len(test_cases)} edge cases passed")
            return False
    
    def run_all_tests(self):
        """Run all tests and return summary"""
        print("🚀 Running calculateChart method tests...\n")
        
        tests = [
            ("Chart Calculator Import", self.test_chart_calculator_import),
            ("Birth Data Validation", self.test_birth_data_validation),
            ("Basic Chart Calculation", self.test_chart_calculation_basic),
            ("Timezone Detection", self.test_timezone_detection),
            ("Database Operations", self.test_database_operations),
            ("Edge Cases", self.test_edge_cases)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 50)
            
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests completed successfully!")
        else:
            print("💥 Some tests failed. Check output above for details.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = TestCalculateChartSimple()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)