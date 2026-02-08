# calculateChart Method Test Suite

## Overview

This test suite provides comprehensive testing for the `calculateChart` method in the AstroRoshni backend. The method is responsible for calculating Vedic astrological charts using Swiss Ephemeris with Lahiri Ayanamsa.

## Test Files

### 1. `test_calculate_chart.py` - Full Test Suite
Comprehensive test suite using pytest and FastAPI TestClient.

**Test Categories:**
- **TestCalculateChartOnly**: Tests `/calculate-chart-only` endpoint (display only)
- **TestCalculateChartWithDB**: Tests `/calculate-chart` endpoint (saves to database)
- **TestChartCalculationAccuracy**: Tests astrological calculation accuracy
- **TestEdgeCases**: Tests boundary conditions and edge cases
- **TestConcurrency**: Tests performance and concurrent access

### 2. `test_chart_simple.py` - Simplified Test Suite
Lightweight test suite that can run without complex dependencies.

**Test Functions:**
- `test_chart_calculator_import()`: Verifies calculator imports
- `test_birth_data_validation()`: Tests input validation
- `test_chart_calculation_basic()`: Tests core calculation logic
- `test_timezone_detection()`: Tests timezone auto-detection
- `test_database_operations()`: Tests database storage
- `test_edge_cases()`: Tests boundary conditions

## Test Execution

### Quick Test (Recommended)
```bash
cd backend
python test_chart_simple.py
```

### Full Test Suite
```bash
cd backend
python run_chart_tests.py
```

### Specific Test Categories
```bash
# Run only accuracy tests
python run_chart_tests.py --test TestChartCalculationAccuracy

# Run only database tests  
python run_chart_tests.py --test TestCalculateChartWithDB
```

## Test Coverage

### 1. Input Validation Tests
- **Valid Data**: Proper birth data format and structure
- **Invalid Dates**: Wrong date formats (DD-MM-YYYY vs YYYY-MM-DD)
- **Invalid Times**: Out of range hours/minutes (25:70)
- **Invalid Coordinates**: Out of range latitude/longitude
- **Missing Fields**: Required field validation
- **Timezone Validation**: Proper timezone format checking

### 2. API Endpoint Tests

#### `/calculate-chart-only` (Display Only)
- ✅ Valid birth data processing
- ✅ Nested vs flat data format handling
- ✅ Error handling for invalid inputs
- ✅ Performance timing (< 5 seconds)
- ✅ Authentication requirement
- ✅ Response structure validation

#### `/calculate-chart` (Database Save)
- ✅ Chart creation with database save
- ✅ Duplicate chart handling
- ✅ Input validation before save
- ✅ Relation field handling ('self', 'other')
- ✅ Encryption handling (if enabled)
- ✅ Database integrity verification

### 3. Astrological Accuracy Tests
- **Known Chart Verification**: Test with documented birth charts
- **Ayanamsa Calculation**: Verify Lahiri Ayanamsa accuracy (~23.85° for year 2000)
- **Retrograde Detection**: Verify retrograde planet identification
- **Rahu-Ketu Opposition**: Verify nodes are exactly 180° apart
- **Coordinate Range Validation**: Longitude 0-360°, Sign 0-11, Degree 0-30°

### 4. Edge Case Tests
- **Leap Year Dates**: February 29th in leap years
- **Midnight Times**: 00:00 time handling
- **Extreme Coordinates**: Near poles and date line
- **Southern Hemisphere**: Negative latitude calculations
- **Historical Dates**: Very old dates (1900s)
- **Future Dates**: Calculations for future years

### 5. Performance Tests
- **Response Time**: Chart calculation under 5 seconds
- **Concurrent Requests**: Multiple simultaneous calculations
- **Memory Usage**: No memory leaks during calculations
- **Database Performance**: Efficient storage and retrieval

## Expected Test Results

### Successful Test Output
```
🚀 Running calculateChart method tests...

📋 Chart Calculator Import
--------------------------------------------------
✅ ChartCalculator import successful

📋 Birth Data Validation  
--------------------------------------------------
✅ Valid date format accepted
✅ Invalid date format rejected
✅ Valid time format accepted
✅ Valid coordinates accepted

📋 Basic Chart Calculation
--------------------------------------------------
✅ Chart calculation returned expected structure
✅ Found 7 planets in result
✅ Found 12 houses in result

📋 Timezone Detection
--------------------------------------------------
✅ Timezone detection successful: UTC+5:30

📋 Database Operations
--------------------------------------------------
✅ Database operations successful

📋 Edge Cases
--------------------------------------------------
✅ Leap Year case passed
✅ Midnight case passed  
✅ Southern Hemisphere case passed
✅ All 3 edge cases passed

============================================================
📊 TEST SUMMARY
============================================================
✅ PASS - Chart Calculator Import
✅ PASS - Birth Data Validation
✅ PASS - Basic Chart Calculation
✅ PASS - Timezone Detection
✅ PASS - Database Operations
✅ PASS - Edge Cases

🎯 Results: 6/6 tests passed
🎉 All tests completed successfully!
```

## Test Data Examples

### Valid Birth Data
```json
{
    "name": "Test Person",
    "date": "1990-05-15",
    "time": "14:30", 
    "latitude": 28.6139,
    "longitude": 77.2090,
    "place": "New Delhi, India",
    "gender": "male",
    "relation": "self"
}
```

### Expected Chart Response Structure
```json
{
    "planets": {
        "Sun": {
            "longitude": 54.23,
            "sign": 1,
            "degree": 24.23,
            "retrograde": false
        },
        "Moon": { ... },
        // ... other planets
    },
    "houses": [
        {
            "longitude": 120.45,
            "sign": 4
        },
        // ... 11 more houses
    ],
    "ascendant": 120.45,
    "ayanamsa": 23.85
}
```

## Common Test Failures and Solutions

### 1. Import Errors
**Error**: `ModuleNotFoundError: No module named 'calculators'`
**Solution**: Ensure you're running tests from the backend directory

### 2. Database Errors  
**Error**: `sqlite3.OperationalError: no such table: users`
**Solution**: Run test setup to create required database tables

### 3. Swiss Ephemeris Errors
**Error**: `swisseph not found`
**Solution**: Install Swiss Ephemeris: `pip install pyswisseph`

### 4. Authentication Errors
**Error**: `403 Forbidden`
**Solution**: Ensure JWT_SECRET is set in test environment

### 5. Timezone Errors
**Error**: `Timezone detection failed`
**Solution**: Install timezone libraries: `pip install timezonefinder`

## Performance Benchmarks

### Expected Performance Metrics
- **Chart Calculation**: < 2 seconds
- **Database Save**: < 0.5 seconds  
- **Timezone Detection**: < 0.1 seconds
- **Total Request**: < 5 seconds
- **Concurrent Requests**: 5 simultaneous requests should complete successfully

### Memory Usage
- **Base Memory**: ~50MB
- **Per Calculation**: +2-5MB
- **Peak Memory**: Should not exceed 200MB during tests

## Test Environment Setup

### Required Dependencies
```bash
pip install pytest
pip install httpx  # For FastAPI testing
pip install pyswisseph  # Swiss Ephemeris
pip install timezonefinder  # Timezone detection
```

### Environment Variables
```bash
export ENVIRONMENT=test
export JWT_SECRET=test_secret_key
export TEST_DATABASE_PATH=test_astrology.db
```

### Database Schema
The test suite automatically creates required tables:
- `users`: User authentication data
- `birth_charts`: Stored birth chart data

## Continuous Integration

### GitHub Actions Example
```yaml
name: Chart Calculation Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest httpx
      - name: Run tests
        run: |
          cd backend
          python test_chart_simple.py
```

## Troubleshooting Guide

### Test Failures
1. **Check Dependencies**: Ensure all required packages are installed
2. **Verify Environment**: Confirm test environment variables are set
3. **Database Access**: Ensure write permissions for test database
4. **Swiss Ephemeris**: Verify ephemeris data files are accessible
5. **Network Access**: Some tests may require internet for timezone detection

### Debug Mode
Run tests with verbose output:
```bash
python test_chart_simple.py --verbose
```

### Manual Testing
Test individual components:
```python
from calculators.chart_calculator import ChartCalculator

# Test basic calculation
calculator = ChartCalculator({})
# ... test specific functionality
```

## Contributing

### Adding New Tests
1. Follow existing test naming conventions
2. Include both positive and negative test cases
3. Add performance benchmarks for new features
4. Update documentation with new test coverage

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing  
- **Accuracy Tests**: Astrological calculation verification
- **Performance Tests**: Speed and memory benchmarks
- **Edge Case Tests**: Boundary condition handling

This comprehensive test suite ensures the reliability, accuracy, and performance of the calculateChart method across all supported use cases and edge conditions.