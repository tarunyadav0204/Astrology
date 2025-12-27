#!/usr/bin/env python3
"""
Test script for Blank Chart Context Builder
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculators.blank_chart_context_builder import BlankChartContextBuilder

def test_blank_chart():
    """Test the blank chart context builder"""
    
    # Sample birth data
    birth_data = {
        'date': '1990-05-15',
        'time': '14:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': 'UTC+5:30'
    }
    
    print("🔍 Testing Blank Chart Context Builder...")
    print(f"📅 Birth Data: {birth_data['date']} at {birth_data['time']}")
    
    try:
        # Initialize builder
        builder = BlankChartContextBuilder()
        
        # Build context
        context = builder.build_context(birth_data)
        
        if 'error' in context:
            print(f"❌ Error: {context['error']}")
            return False
        
        print("✅ Context built successfully!")
        
        # Display key insights
        metadata = context.get('metadata', {})
        pillars = context.get('pillars', {})
        stun_factors = context.get('stun_factors', [])
        
        print(f"\n📊 Age: {metadata.get('target_age', 'Unknown')}")
        
        # BCP Activation
        bcp = pillars.get('bcp_activation', {})
        if bcp:
            print(f"🏠 Active House: {bcp.get('activated_house')} - {bcp.get('house_meaning')}")
            print(f"♈ Active Sign: {bcp.get('activated_sign')}")
            if bcp.get('house_occupants'):
                print(f"🪐 Occupants: {', '.join(bcp.get('house_occupants'))}")
        
        # Nakshatra Triggers
        nak_triggers = pillars.get('nakshatra_triggers', {})
        if nak_triggers:
            print(f"⭐ Birth Star: {nak_triggers.get('birth_star')}")
            if nak_triggers.get('is_fated_period'):
                print(f"🎯 FATED PERIOD ACTIVE!")
        
        # Jaimini Markers
        jaimini = pillars.get('jaimini_markers', {})
        if jaimini:
            print(f"🎭 Atmakaraka: {jaimini.get('atmakaraka')}")
            print(f"💼 Amatyakaraka: {jaimini.get('amatyakaraka')}")
        
        # Lal Kitab Debts
        debts = pillars.get('lal_kitab_layer', {}).get('ancestral_debts', [])
        if debts:
            print(f"⚖️ Ancestral Debts: {len(debts)} detected")
            for debt in debts[:2]:  # Show first 2
                print(f"   - {debt}")
        
        # Stun Factors
        if stun_factors:
            print(f"\n⚡ Stun Factors ({len(stun_factors)}):")
            for factor in stun_factors:
                print(f"   - {factor}")
        
        print(f"\n🎪 Total Pillars: {len(pillars)}")
        print("🚀 Blank Chart Context Builder working perfectly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_blank_chart()
    if success:
        print("\n✅ All tests passed! Ready for production.")
    else:
        print("\n❌ Tests failed. Check the errors above.")