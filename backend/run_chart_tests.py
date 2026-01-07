#!/usr/bin/env python3
"""
Test runner for calculateChart method tests
Handles test database setup and cleanup
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def setup_test_environment():
    """Setup test environment and database"""
    print("🔧 Setting up test environment...")
    
    # Set test environment variables
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['JWT_SECRET'] = 'test_secret_key_for_testing_only'
    os.environ['TEST_DATABASE_PATH'] = 'test_astrology.db'
    
    # Create test database
    test_db_path = 'test_astrology.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Initialize test database with required tables
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            email TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create birth_charts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS birth_charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timezone TEXT NOT NULL,
            place TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            relation TEXT DEFAULT 'other',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userid) REFERENCES users (userid)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Test environment setup complete")

def cleanup_test_environment():
    """Cleanup test environment"""
    print("🧹 Cleaning up test environment...")
    
    test_db_path = 'test_astrology.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("✅ Test environment cleanup complete")

def run_tests():
    """Run the test suite"""
    print("🚀 Running calculateChart method tests...")
    
    # Install required packages if not available
    try:
        import pytest
    except ImportError:
        print("📦 Installing pytest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
    
    try:
        import httpx
    except ImportError:
        print("📦 Installing httpx for FastAPI testing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    
    # Run tests with pytest
    test_file = "tests/test_calculate_chart.py"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    # Run different test categories
    test_categories = [
        ("Unit Tests", "TestCalculateChartOnly"),
        ("Database Integration Tests", "TestCalculateChartWithDB"),
        ("Accuracy Tests", "TestChartCalculationAccuracy"),
        ("Edge Cases", "TestEdgeCases"),
        ("Performance Tests", "TestConcurrency")
    ]
    
    all_passed = True
    
    for category_name, test_class in test_categories:
        print(f"\n📋 Running {category_name}...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"{test_file}::{test_class}",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {category_name} - PASSED")
        else:
            print(f"❌ {category_name} - FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            all_passed = False
    
    return all_passed

def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🎯 Running specific test: {test_name}")
    
    test_file = "tests/test_calculate_chart.py"
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        f"{test_file}::{test_name}",
        "-v", "-s"
    ])
    
    return result.returncode == 0

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run calculateChart method tests")
    parser.add_argument("--test", help="Run specific test class or method")
    parser.add_argument("--setup-only", action="store_true", help="Only setup test environment")
    parser.add_argument("--cleanup-only", action="store_true", help="Only cleanup test environment")
    
    args = parser.parse_args()
    
    if args.cleanup_only:
        cleanup_test_environment()
        return
    
    if args.setup_only:
        setup_test_environment()
        return
    
    try:
        # Setup test environment
        setup_test_environment()
        
        if args.test:
            # Run specific test
            success = run_specific_test(args.test)
        else:
            # Run all tests
            success = run_tests()
        
        if success:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n💥 Some tests failed. Check output above for details.")
            sys.exit(1)
    
    finally:
        # Always cleanup
        cleanup_test_environment()

if __name__ == "__main__":
    main()