"""Pytest configuration and fixtures"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_birth_data():
    """Standard test birth data - Delhi, Jan 1 1990, 12:00 PM"""
    return {
        'name': 'Test User',
        'date': '1990-01-01',
        'time': '12:00',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'place': 'New Delhi, India'
    }
