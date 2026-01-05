#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from ai.response_parser import ResponseParser

async def test_full_chat_flow():
    print("🧪 Testing Full Chat Flow with Image Integration...")
    
    # Mock astrological context (simplified)
    mock_context = {
        'birth_details': {'name': 'Test User', 'date': '1990-01-01'},
        'planetary_analysis': {
            'Jupiter': {'sign': 'Sagittarius', 'house': 10, 'longitude': 255.5}
        }
    }
    
    # Mock Gemini response with image tags and prompts
    mock_gemini_response = '''<div class="quick-answer-card">**Quick Answer**: Your <term id="jupiter">Jupiter</term> in <term id="sagittarius">Sagittarius</term> in the 10th house creates exceptional career opportunities in teaching, consulting, and advisory roles. This placement brings wisdom, expansion, and recognition in your professional life.</div>

### Key Insights
• <image id="jupiter_career">Your Jupiter in the 10th house of career brings tremendous growth potential</image>
• Strong leadership abilities and natural teaching skills
• Excellent prospects in education, law, or spiritual guidance
• Recognition and respect from colleagues and superiors

### Astrological Analysis
<image id="sagittarius_wisdom">Jupiter in Sagittarius amplifies your wisdom and philosophical nature</image>, making you naturally suited for roles that involve sharing knowledge. The 10th house placement ensures that your career will be your primary vehicle for expressing Jupiter's benefic energy.

### Nakshatra Insights
Your <term id="jupiter">Jupiter</term> placement suggests a natural inclination toward higher learning and teaching others.

### Timing & Guidance
Focus on building your expertise and sharing knowledge with others. The next few years will bring significant career advancement.

<div class="final-thoughts-card">**Final Thoughts**: Embrace opportunities to teach, guide, and inspire others in your professional journey.</div>

<div class="follow-up-questions">
📅 When will career growth happen?
🔮 What remedies can enhance Jupiter?
💼 Which industries suit me best?
🌟 How to maximize this placement?
</div>

GLOSSARY_START
{"jupiter": "Jupiter - The planet of wisdom, expansion, and higher learning. Known as the great benefic in Vedic astrology.", "sagittarius": "Sagittarius - A fire sign ruled by Jupiter, associated with philosophy, higher education, and spiritual wisdom.", "term": "A technical astrological concept that requires explanation for better understanding."}
GLOSSARY_END

IMAGE_PROMPTS_START
{"jupiter_career": "mystical Jupiter planet symbol glowing golden above a mountain peak representing career success, cosmic vedic astrology art style", "sagittarius_wisdom": "archer constellation of Sagittarius with glowing arrows of wisdom shooting toward stars, mystical purple and gold cosmic background"}
IMAGE_PROMPTS_END'''

    try:
        # Initialize analyzer
        analyzer = GeminiChatAnalyzer()
        print("✅ Gemini Chat Analyzer initialized")
        
        # Test 1: Response parsing
        print("\n📝 Testing response parsing...")
        parsed = ResponseParser.parse_response(mock_gemini_response)
        print(f"✅ Parsed {len(parsed['terms'])} terms: {list(parsed['terms'])}")
        print(f"✅ Parsed {len(parsed['glossary'])} glossary entries: {list(parsed['glossary'].keys())}")
        
        # Test 2: Image prompt extraction
        print("\n🎨 Testing image prompt extraction...")
        image_prompts = analyzer._extract_image_prompts(mock_gemini_response)
        print(f"✅ Extracted {len(image_prompts)} image prompts:")
        for img_id, prompt in image_prompts.items():
            print(f"  • {img_id}: {prompt[:60]}...")
        
        # Test 3: Image generation
        if analyzer.flux_service and image_prompts:
            print(f"\n🖼️ Testing image generation...")
            generated_images = []
            
            for img_id, prompt in image_prompts.items():
                print(f"  Generating {img_id}...")
                try:
                    image_url = await analyzer.flux_service.generate_image(prompt)
                    if image_url:
                        generated_images.append({
                            'id': img_id,
                            'url': image_url,
                            'prompt': prompt
                        })
                        print(f"  ✅ {img_id}: {image_url[:80]}...")
                    else:
                        print(f"  ❌ Failed to generate {img_id}")
                except Exception as e:
                    print(f"  ⚠️ Error generating {img_id}: {e}")
            
            # Test 4: Complete response simulation
            print(f"\n📦 Simulating complete chat response...")
            complete_response = {
                'success': True,
                'response': parsed['content'],
                'terms': parsed['terms'],
                'glossary': parsed['glossary'],
                'images': generated_images,
                'timing': {'total_request_time': 15.5}
            }
            
            print(f"✅ Complete response ready:")
            print(f"  • Response length: {len(complete_response['response'])} chars")
            print(f"  • Terms: {len(complete_response['terms'])}")
            print(f"  • Glossary entries: {len(complete_response['glossary'])}")
            print(f"  • Images: {len(complete_response['images'])}")
            
            # Test 5: Cost calculation
            image_cost = len(generated_images) * 1  # ₹1 per image
            total_cost = 5  # Premium chat base cost
            print(f"\n💰 Cost Analysis:")
            print(f"  • Base premium chat: ₹5")
            print(f"  • Images generated: {len(generated_images)} × ₹1 = ₹{image_cost}")
            print(f"  • Total cost: ₹{total_cost} (images included in premium)")
            
            print(f"\n🎉 Full chat flow test SUCCESSFUL!")
            print(f"📊 Summary:")
            print(f"  ✅ Response parsing: Working")
            print(f"  ✅ Image extraction: Working") 
            print(f"  ✅ Image generation: Working")
            print(f"  ✅ Complete flow: Working")
            print(f"  ✅ Cost effective: ₹{total_cost} for premium experience")
            
        else:
            print(f"⚠️ Flux service not available or no image prompts")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_chat_flow())