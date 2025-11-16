#!/usr/bin/env python3

# Simple test to verify the event periods feature works
import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from chat.chat_context_builder import ChatContextBuilder

# Test birth data
birth_data = {
    'name': 'Test User',
    'date': '1990-01-15',
    'time': '10:30',
    'place': 'New Delhi',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'timezone': 'UTC+5:30',
    'gender': 'male'
}

def test_event_periods():
    try:
        print("Testing Event Periods Feature...")
        
        # Initialize context builder
        context_builder = ChatContextBuilder()
        
        # Test getting high-significance periods
        print("Getting high-significance periods...")
        periods = context_builder.get_high_significance_periods(birth_data, years_ahead=2)
        
        print(f"Found {len(periods)} high-significance periods:")
        for i, period in enumerate(periods[:5]):  # Show first 5
            print(f"{i+1}. {period['label']} - Significance: {period['significance']}")
        
        # Test selected period functionality
        if periods:
            print("\nTesting selected period context...")
            context_builder.set_selected_period(periods[0]['period_data'])
            
            context = context_builder.build_complete_context(
                birth_data, 
                "Predict events for this period", 
                None, 
                None
            )
            
            if 'selected_period_focus' in context:
                print("✅ Selected period focus instructions added successfully")
            else:
                print("❌ Selected period focus instructions missing")
        
        print("\n✅ Event Periods Feature Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_event_periods()