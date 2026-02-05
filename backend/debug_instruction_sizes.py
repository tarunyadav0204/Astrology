#!/usr/bin/env python3
"""
Debug script to identify why system instructions are still large
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.optimized_instruction_builder import CategoryInstructionInjector
from chat.system_instruction_loader import SystemInstructionLoader

def debug_instruction_sizes():
    """Debug instruction sizes to find the issue"""
    
    print("🔍 DEBUGGING INSTRUCTION SIZES")
    print("=" * 60)
    
    # Test optimized system
    print("\n1. OPTIMIZED INSTRUCTION SYSTEM:")
    injector = CategoryInstructionInjector()
    
    categories = ['career', 'wealth', 'health', 'marriage', 'education', 'general']
    
    for category in categories:
        instructions = injector.get_instructions_for_intent(category, 'normal')
        print(f"   {category:10}: {len(instructions):,} characters")
    
    # Test old system
    print("\n2. OLD INSTRUCTION SYSTEM:")
    loader = SystemInstructionLoader()
    
    for category in categories:
        try:
            instructions = loader.get_instructions_for_category(category, 'normal')
            print(f"   {category:10}: {len(instructions):,} characters")
        except Exception as e:
            print(f"   {category:10}: ERROR - {e}")
    
    # Test what happens when we simulate the Gemini analyzer context
    print("\n3. SIMULATED GEMINI CONTEXT:")
    
    # Simulate context with optimized instructions
    mock_context = {
        'intent_category': 'career',
        'tier_key': 'normal',
        'optimized_system_instructions': injector.get_instructions_for_intent('career', 'normal'),
        'instruction_metadata': {
            'category': 'career',
            'tier': 'normal',
            'size_reduction': '~94%',
            'character_count': len(injector.get_instructions_for_intent('career', 'normal'))
        }
    }
    
    # Check if optimized instructions are in context
    if 'optimized_system_instructions' in mock_context:
        system_instruction = mock_context['optimized_system_instructions']
        print(f"   Using optimized: {len(system_instruction):,} characters")
    else:
        # Fallback
        system_instruction = loader.get_instructions_for_category('career', 'normal')
        print(f"   Using fallback: {len(system_instruction):,} characters")
    
    print(f"\n4. INSTRUCTION PREVIEW:")
    print(f"   First 500 chars: {system_instruction[:500]}")
    print(f"   ...")
    print(f"   Last 200 chars: {system_instruction[-200:]}")

if __name__ == "__main__":
    debug_instruction_sizes()