#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')

try:
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    print("Trying to initialize GeminiChatAnalyzer...")
    analyzer = GeminiChatAnalyzer()
    print("GeminiChatAnalyzer initialized successfully")
except Exception as e:
    print(f"Error initializing GeminiChatAnalyzer:")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error message: {str(e)}")
    print(f"  Contains 'GEMINI_API_KEY': {'GEMINI_API_KEY' in str(e)}")
    print(f"  Contains 'api key': {'api key' in str(e).lower()}")
    print(f"  Contains 'not set': {'not set' in str(e).lower()}")
    
    import traceback
    traceback.print_exc()