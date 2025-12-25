#!/usr/bin/env python3
"""
Test script to verify divisional chart detection in Intent Router
"""

import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from ai.intent_router import IntentRouter

async def test_divisional_chart_detection():
    """Test divisional chart detection for various question types"""
    
    router = IntentRouter()
    
    test_cases = [
        {
            "question": "When will I get married?",
            "expected_charts": ["D1", "D9", "D7"]
        },
        {
            "question": "How is my career in 2025?",
            "expected_charts": ["D1", "D9", "D10"]
        },
        {
            "question": "Tell me about my siblings",
            "expected_charts": ["D1", "D3", "D9"]
        },
        {
            "question": "Property purchase timing?",
            "expected_charts": ["D1", "D4", "D9", "D12"]
        },
        {
            "question": "How is my health?",
            "expected_charts": ["D1", "D9", "D30"]
        },
        {
            "question": "Children prospects?",
            "expected_charts": ["D1", "D7", "D9"]
        },
        {
            "question": "Education opportunities?",
            "expected_charts": ["D1", "D9", "D24"]
        },
        {
            "question": "Spiritual growth?",
            "expected_charts": ["D1", "D9", "D20"]
        }
    ]
    
    print("🧪 Testing Divisional Chart Detection in Intent Router")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected = test_case["expected_charts"]
        
        print(f"\n{i}. Question: '{question}'")
        print(f"   Expected charts: {expected}")
        
        try:
            result = await router.classify_intent(question)
            actual_charts = result.get('divisional_charts', [])
            
            print(f"   Actual charts: {actual_charts}")
            
            # Check if all expected charts are present
            missing_charts = [chart for chart in expected if chart not in actual_charts]
            extra_charts = [chart for chart in actual_charts if chart not in expected]
            
            if not missing_charts and not extra_charts:
                print(f"   ✅ PASS - Perfect match")
            elif not missing_charts:
                print(f"   ⚠️  PARTIAL - Extra charts: {extra_charts}")
            else:
                print(f"   ❌ FAIL - Missing: {missing_charts}, Extra: {extra_charts}")
                
            print(f"   Status: {result.get('status')}")
            print(f"   Mode: {result.get('mode')}")
            print(f"   Category: {result.get('category')}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Divisional Chart Detection Test Complete")

if __name__ == "__main__":
    asyncio.run(test_divisional_chart_detection())