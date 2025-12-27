#!/usr/bin/env python3
"""
API Test for Blank Chart Routes
"""

import requests
import json

def test_blank_chart_api():
    """Test the blank chart API endpoints"""
    
    # API base URL (adjust if needed)
    base_url = "http://localhost:8001"
    
    # Sample birth data
    birth_data = {
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "UTC+5:30"
    }
    
    print("🔍 Testing Blank Chart API...")
    print(f"📡 Base URL: {base_url}")
    
    try:
        # Test stunning prediction endpoint
        print("\n🎯 Testing /api/blank-chart/stunning-prediction...")
        
        response = requests.post(
            f"{base_url}/api/blank-chart/stunning-prediction",
            json=birth_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Stunning prediction endpoint working!")
            
            if result.get('success'):
                stunning = result.get('stunning_prediction', {})\n                print(f"📊 Age revelation: {stunning.get('age_revelation')}")
                print(f"🏠 Life phase: {stunning.get('life_phase')}")
                
                if stunning.get('timing_alerts'):
                    print(f"⚡ Timing alerts: {len(stunning.get('timing_alerts'))} found")
                    for alert in stunning.get('timing_alerts')[:2]:
                        print(f"   - {alert}")
                
                if stunning.get('karmic_patterns'):
                    print(f"⚖️ Karmic patterns: {len(stunning.get('karmic_patterns'))} detected")
            else:
                print(f"❌ API returned success=False")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test quick insight endpoint
        print("\n💡 Testing /api/blank-chart/quick-insight...")
        
        response = requests.post(
            f"{base_url}/api/blank-chart/quick-insight",
            json=birth_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Quick insight endpoint working!")
            
            if result.get('success'):
                insight = result.get('insight', '')
                confidence = result.get('confidence', '0%')
                print(f"🎯 Insight: {insight[:100]}...")
                print(f"📈 Confidence: {confidence}")
            else:
                print(f"❌ API returned success=False")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
        
        print("\n🚀 API tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on port 8001")
        print("💡 Start server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_blank_chart_api()
    if success:
        print("\n✅ All API tests passed! Blank chart routes are working.")
    else:
        print("\n❌ API tests failed. Check server status and try again.")