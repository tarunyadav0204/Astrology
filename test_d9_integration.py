#!/usr/bin/env python3
"""
Test script for D9 Navamsa integration in marriage analysis
"""

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from marriage_analysis.marriage_analyzer import MarriageAnalyzer

def test_d9_integration():
    """Test D9 integration with sample birth data"""
    
    # Sample birth data
    birth_details = {
        'name': 'Test Person',
        'date': '1990-05-15',
        'time': '14:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': 'UTC+5:30'
    }
    
    # Sample chart data (simplified)
    chart_data = {
        'planets': {
            'Sun': {'longitude': 54.5, 'sign': 1, 'degree': 24.5},
            'Moon': {'longitude': 120.3, 'sign': 4, 'degree': 0.3},
            'Mars': {'longitude': 200.7, 'sign': 6, 'degree': 20.7},
            'Mercury': {'longitude': 45.2, 'sign': 1, 'degree': 15.2},
            'Jupiter': {'longitude': 95.8, 'sign': 3, 'degree': 5.8},
            'Venus': {'longitude': 75.4, 'sign': 2, 'degree': 15.4},
            'Saturn': {'longitude': 280.1, 'sign': 9, 'degree': 10.1},
            'Rahu': {'longitude': 310.5, 'sign': 10, 'degree': 10.5},
            'Ketu': {'longitude': 130.5, 'sign': 4, 'degree': 10.5}
        },
        'houses': [
            {'sign': 0, 'longitude': 30.0},
            {'sign': 1, 'longitude': 60.0},
            {'sign': 2, 'longitude': 90.0},
            {'sign': 3, 'longitude': 120.0},
            {'sign': 4, 'longitude': 150.0},
            {'sign': 5, 'longitude': 180.0},
            {'sign': 6, 'longitude': 210.0},
            {'sign': 7, 'longitude': 240.0},
            {'sign': 8, 'longitude': 270.0},
            {'sign': 9, 'longitude': 300.0},
            {'sign': 10, 'longitude': 330.0},
            {'sign': 11, 'longitude': 360.0}
        ],
        'ayanamsa': 24.1,
        'ascendant': 30.0
    }
    
    print("🌟 Testing D9 Navamsa Integration for Marriage Analysis")
    print("=" * 60)
    
    try:
        # Initialize marriage analyzer
        analyzer = MarriageAnalyzer()
        
        # Perform analysis
        print("📊 Running marriage analysis with D9 integration...")
        result = analyzer.analyze_single_chart(chart_data, birth_details)
        
        # Display results
        print("\n✅ Analysis completed successfully!")
        print(f"Overall Score: {result.get('overall_score', {}).get('score', 'N/A')}/10")
        print(f"Grade: {result.get('overall_score', {}).get('grade', 'N/A')}")
        
        # Check D9 analysis
        d9_analysis = result.get('d9_analysis', {})
        if d9_analysis and not d9_analysis.get('error'):
            print("\n🌟 D9 Navamsa Analysis:")
            print(f"  Overall D9 Strength: {d9_analysis.get('overall_strength', 'N/A')}/10")
            print(f"  7th House D9: {d9_analysis.get('seventh_house_d9', {}).get('sign_name', 'N/A')} (Strength: {d9_analysis.get('seventh_house_d9', {}).get('strength', 'N/A')}/10)")
            print(f"  Venus D9: {d9_analysis.get('venus_d9', {}).get('sign_name', 'N/A')} ({d9_analysis.get('venus_d9', {}).get('dignity', 'N/A')})")
            print(f"  Jupiter D9: {d9_analysis.get('jupiter_d9', {}).get('sign_name', 'N/A')} ({d9_analysis.get('jupiter_d9', {}).get('dignity', 'N/A')})")
            print(f"  Interpretation: {d9_analysis.get('interpretation', 'N/A')}")
        elif d9_analysis.get('error'):
            print(f"\n⚠️ D9 Analysis Error: {d9_analysis.get('error')}")
        else:
            print("\n❌ No D9 analysis found")
        
        # Score breakdown
        components = result.get('overall_score', {}).get('components', {})
        if components:
            print("\n📊 Score Breakdown:")
            print(f"  D1 Total: {components.get('d1_total', 'N/A')}/7.0 (70%)")
            print(f"  D9 Total: {components.get('d9_total', 'N/A')}/3.0 (30%)")
            print(f"  Manglik Penalty: {components.get('manglik_penalty', 'N/A')}")
        
        print("\n🎉 D9 integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_d9_integration()
    sys.exit(0 if success else 1)