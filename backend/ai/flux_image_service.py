import replicate
import os
from typing import Optional, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FluxImageService:
    def __init__(self):
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable not set")
        self.client = replicate.Client(api_token=api_token)
    
    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> Optional[str]:
        """Generate image using Flux model"""
        try:
            output = self.client.run(
                "black-forest-labs/flux-dev:6e4a938f85952bdabcc15aa329178c4d681c52bf25a0342403287dc26944661d",
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "webp",
                    "output_quality": 80
                }
            )
            return output[0] if output else None
        except Exception as e:
            logger.error(f"Flux image generation failed: {e}")
            return None

    def create_astrological_prompts(self, context: dict) -> List[str]:
        """Generate contextual image prompts based on astrological data"""
        prompts = []
        
        # Planet-based images
        if "dominant_planets" in context:
            for planet in context["dominant_planets"][:2]:
                prompts.append(f"mystical {planet} planet symbol glowing in cosmic space, vedic astrology art style, golden and purple colors")
        
        # House-based images  
        if "strong_houses" in context:
            house_themes = {
                1: "person meditating with glowing aura",
                2: "golden coins and jewels floating in cosmic light", 
                4: "peaceful home with spiritual energy",
                5: "creative arts and learning symbols",
                7: "two souls connecting under starlight",
                9: "ancient temple with divine light",
                10: "mountain peak with success symbols"
            }
            for house in context["strong_houses"][:1]:
                if house in house_themes:
                    prompts.append(f"{house_themes[house]}, vedic astrology mystical art, cosmic background")
        
        # Dasha-based images
        if "current_dasha" in context:
            dasha_planet = context["current_dasha"]
            prompts.append(f"{dasha_planet} dasha period cosmic energy, vedic astrology symbols, mystical aura")
        
        return prompts[:3]  # Max 3 images