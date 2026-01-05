#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from ai.gemini_chat_analyzer import GeminiChatAnalyzer

async def test_image_integration():
    print("🧪 Testing Gemini Image Integration...")
    
    # Test response with image tags
    test_response = '''
<div class="quick-answer-card">**Quick Answer**: Your Jupiter placement shows excellent career potential in teaching and advisory roles.</div>

### Key Insights
Your <image id="jupiter_power">Jupiter in Sagittarius brings wisdom and expansion</image> to your career sector.

### Astrological Analysis  
This creates <image id="career_growth">excellent opportunities for growth in education and consulting</image> fields.

### Final Thoughts
Focus on sharing knowledge and wisdom with others.

GLOSSARY_START
{"jupiter": "Jupiter - Planet of wisdom, expansion, and higher learning"}
GLOSSARY_END

IMAGE_PROMPTS_START
{"jupiter_power": "mystical Jupiter planet symbol glowing golden in Sagittarius constellation, vedic astrology cosmic art", "career_growth": "ascending staircase of success with books and teaching symbols, golden cosmic light"}
IMAGE_PROMPTS_END
'''
    
    try:
        analyzer = GeminiChatAnalyzer()
        
        # Test image prompt extraction
        image_prompts = analyzer._extract_image_prompts(test_response)
        print(f"✅ Extracted {len(image_prompts)} image prompts:")
        for img_id, prompt in image_prompts.items():
            print(f"  {img_id}: {prompt}")
        
        # Test image generation if Flux service is available
        if analyzer.flux_service:
            print(f"\n🎨 Testing image generation...")
            for img_id, prompt in image_prompts.items():
                try:
                    image_url = await analyzer.flux_service.generate_image(prompt)
                    if image_url:
                        print(f"  ✅ Generated {img_id}: {image_url[:100]}...")
                    else:
                        print(f"  ❌ Failed to generate {img_id}")
                except Exception as e:
                    print(f"  ⚠️ Error generating {img_id}: {e}")
        else:
            print(f"⚠️ Flux service not available")
        
        print(f"\n🎉 Image integration test complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_integration())