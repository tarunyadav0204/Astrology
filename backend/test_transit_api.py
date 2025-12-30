#!/usr/bin/env python3
"""
Test the actual transit API endpoint to see what data it returns
"""

import requests
import json
from datetime import datetime

def test_transit_api():
    """Test the transit API endpoint directly"""
    
    # Test data - using a sample birth data
    test_data = {
        'birth_data': {
            'name': 'Test User',
            'date': '1990-01-01',
            'time': '12:00',
            'latitude': 28.6139,  # Delhi
            'longitude': 77.2090,
            'timezone': 'Asia/Kolkata',
            'location': 'Delhi'
        },
        'transit_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    print(f"Testing transit API for date: {test_data['transit_date']}")
    print(f"Birth location: Delhi (28.6139, 77.2090)")
    
    try:
        # Test without authentication first
        response = requests.post(
            'http://localhost:8001/api/calculate-transits', 
            json=test_data, 
            timeout=30
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Transit API working")
            
            if 'planets' in data:
                print("\n" + "="*60)
                print("API RESPONSE - PLANETARY POSITIONS")
                print("="*60)
                
                sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
                
                for planet, planet_data in data['planets'].items():
                    sign_name = sign_names[planet_data['sign']] if planet_data['sign'] < 12 else f"Sign {planet_data['sign']}"
                    retro = " ℞" if planet_data.get('retrograde', False) else ""
                    
                    print(f"{planet:8} | {sign_name:12} | {planet_data['degree']:6.2f}°{retro}")
                
                print("\n" + "="*60)
                print("FULL API RESPONSE:")
                print("="*60)
                print(json.dumps(data, indent=2))
                
            else:
                print("❌ No 'planets' key in response")
                print("Response:", json.dumps(data, indent=2))
                
        elif response.status_code == 403:
            print("❌ Authentication required")
            print("Response:", response.text)
            
            # Try to get a token
            print("\nTrying to authenticate...")
            auth_response = requests.post(
                'http://localhost:8001/api/login',
                json={'phone': 'test_user', 'password': 'test_password'}
            )
            
            if auth_response.status_code == 200:
                token = auth_response.json().get('access_token')
                print("✅ Got authentication token")
                
                # Retry with token
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.post(
                    'http://localhost:8001/api/calculate-transits', 
                    json=test_data, 
                    headers=headers,
                    timeout=30
                )
                
                print(f"Authenticated API Response Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Transit API working with authentication")
                    
                    if 'planets' in data:
                        print("\nPlanets and their signs:")
                        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
                        
                        for planet, planet_data in data['planets'].items():
                            sign_name = sign_names[planet_data['sign']] if planet_data['sign'] < 12 else f"Sign {planet_data['sign']}"
                            print(f"  {planet}: {sign_name} ({planet_data['sign']}) at {planet_data['degree']:.1f}°")
                else:
                    print(f"❌ API Error with auth: {response.text}")
            else:
                print("❌ Authentication failed")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print("Response:", response.text)
            
    except requests.exceptions.ConnectionError:
        print('❌ Server not running on port 8001')
        print('Make sure the backend server is running: python main.py')
    except Exception as e:
        print(f'❌ Test failed: {e}')

if __name__ == "__main__":
    test_transit_api()