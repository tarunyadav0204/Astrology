"""
Karma AI Integrator - Sends karma context to Gemini for interpretation
"""

import json
import google.generativeai as genai
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calculators.karma_context_builder import KarmaContextBuilder

class KarmaGeminiAnalyzer:
    """Integrates Karma Context with Gemini AI for personalized readings"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-3-pro-preview')
    
    def analyze_karma(self, chart_data: Dict[str, Any], divisional_charts: Dict[str, Any] = None, native_name: str = None, log_request: bool = False) -> Dict[str, Any]:
        """Generate complete karma analysis with AI interpretation"""
        
        # Build karma context
        karma_builder = KarmaContextBuilder(chart_data, divisional_charts)
        karma_context = karma_builder.get_complete_karma_context()
        
        # Generate AI interpretation
        prompt = self._build_karma_prompt(karma_context, native_name)
        
        if log_request:
            print(f"\n{'='*80}")
            print(f"📤 GEMINI REQUEST - Karma Analysis")
            print(f"{'='*80}")
            print(f"Prompt length: {len(prompt)} characters")
            print(f"\nFull Prompt:\n{prompt}")
            print(f"{'='*80}\n")
        
        try:
            response = self.model.generate_content(prompt)
            interpretation = response.text
            
            print(f"\n{'='*80}")
            print(f"📥 GEMINI RESPONSE - Karma Analysis")
            print(f"{'='*80}")
            print(f"Response length: {len(interpretation)} characters")
            print(f"\nFull Response:\n{interpretation}")
            print(f"{'='*80}\n")
            
            return {
                "success": True,
                "karma_context": karma_context,
                "ai_interpretation": interpretation,
                "sections": self._parse_response_sections(interpretation)
            }
        except Exception as e:
            print(f"\n❌ GEMINI ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "karma_context": karma_context
            }
    
    def _build_karma_prompt(self, karma_context: Dict[str, Any], native_name: str = None) -> str:
        """Build comprehensive prompt for Gemini"""
        
        name_instruction = f"\n**IMPORTANT**: Address the native as '{native_name}' throughout the reading. Use their name naturally when providing insights.\n" if native_name else ""
        
        soul_identity = karma_context.get('soul_identity', {})
        soul_desire = karma_context.get('soul_desire', {})
        nakshatra_karma = karma_context.get('nakshatra_karma', {})
        karmic_patterns = karma_context.get('karmic_patterns', [])
        unfinished_debts = karma_context.get('unfinished_debts', [])
        destiny_axis = karma_context.get('destiny_axis', {})
        badhaka = karma_context.get('karmic_obstacles', {})
        gandanta = karma_context.get('soul_junctions', {})
        mrityu = karma_context.get('vulnerable_points', {})
        vargottama = karma_context.get('soul_continuity', {})
        pitru = karma_context.get('ancestral_karma', {})
        matru = karma_context.get('maternal_karma', {})
        poorva_punya = karma_context.get('poorva_punya', {})
        house_8 = karma_context.get('eighth_house_secrets', {})
        bhagya = karma_context.get('bhagya_karma', {})
        house_12 = karma_context.get('moksha_indicators', {})
        timing = karma_context.get('karmic_timing', {})
        
        # Extract raw charts
        d1_chart = karma_context.get('d1_chart', {})
        d9_chart = karma_context.get('d9_navamsa', {})
        d60_chart = karma_context.get('d60_shashtiamsa', {})
        
        prompt = f"""You are an expert Vedic astrologer specializing in past life karma analysis using classical texts (Brihat Parashara Hora Shastra, Jaimini Sutras, Phaladeepika, Saravali). Provide a comprehensive, personalized reading based on the following karmic indicators.{name_instruction}

## CRITICAL ANALYSIS INSTRUCTIONS

### Raw Chart Analysis Protocol
You have access to THREE raw charts for direct analysis:
1. **D1 Chart (Rashi)**: Birth chart showing current life setup - {json.dumps(d1_chart)}
2. **D9 Chart (Navamsa)**: Dharma/marriage/inner strength chart - {json.dumps(d9_chart)}
3. **D60 Chart (Shashtiamsa)**: Past life karma essence chart - {json.dumps(d60_chart)}

**MANDATORY**: Cross-reference calculated insights with raw planetary positions. If you find contradictions or additional patterns in the raw charts, MENTION THEM.

### Classical Text References (MANDATORY)
For EVERY major karmic interpretation, cite the classical source:
- **BPHS (Brihat Parashara Hora Shastra)**: D60 interpretations, retrograde planets, house significations
- **Jaimini Sutras**: Atmakaraka, Chara Karakas, Karkamsa analysis
- **Phaladeepika**: Nakshatra karma, planetary yogas
- **Saravali**: Rahu-Ketu axis, karmic patterns
- **Traditional Texts**: Gandanta, Badhaka, Pitru/Matru Dosha

Format: "According to [Text Name], [interpretation]..."

### D60 Supremacy Rule
**IMPORTANT INTERPRETIVE RULE:** If a planet has high D9 (Navamsa) dignity but a malefic D60 deity (Ghora, Rakshasa, Pishacha, Preta, etc.), prioritize the D60 deity as the 'hidden' karmic reality that will eventually manifest. D60 is the final arbiter of past life karma per BPHS.

## SOUL IDENTITY (D60 Shashtiamsa)
**Lagna Deity:** {soul_identity.get('lagna_deity', 'Unknown')}
**Lagna Nature:** {soul_identity.get('lagna_nature', 'Unknown')}
**Lagna Theme:** {soul_identity.get('lagna_theme', 'Unknown')}
**Atmakaraka Deity:** {soul_identity.get('atmakaraka_deity', 'Unknown')}
**Atmakaraka Nature:** {soul_identity.get('atmakaraka_nature', 'Unknown')}
**Atmakaraka Theme:** {soul_identity.get('atmakaraka_theme', 'Unknown')}
**Atmakaraka D60 Nakshatra:** {soul_identity.get('atmakaraka_d60_nakshatra', 'Unknown')}
**Significance:** {soul_identity.get('significance', '')}

## SOUL'S PRIMARY DESIRE (Atmakaraka)
**Planet:** {soul_desire.get('planet', 'Unknown')}
**House:** {soul_desire.get('house', 'Unknown')}
**Soul Desire:** {soul_desire.get('soul_desire', 'Unknown')}
**Life Purpose:** {soul_desire.get('life_purpose', 'Unknown')}

## NAKSHATRA KARMA (Subconscious Imprints)
**Atmakaraka Nakshatra:** {nakshatra_karma.get('atmakaraka_nakshatra', 'Unknown')}
**Soul Flavor:** {nakshatra_karma.get('soul_flavor', 'Unknown')}
**Ketu Nakshatra:** {nakshatra_karma.get('ketu_nakshatra', 'Unknown')}
**Past Life Expertise:** {nakshatra_karma.get('past_life_expertise', 'Unknown')}
**Moon Nakshatra:** {nakshatra_karma.get('moon_nakshatra', 'Unknown')}
**Emotional Karma:** {nakshatra_karma.get('emotional_karma', 'Unknown')}
**Ganda-Moola (Karmic Knot):** {nakshatra_karma.get('karmic_knot', 'None')}

## KARMIC PATTERNS (Saturn Nadi Links)
{self._format_karmic_patterns(karmic_patterns)}

## UNFINISHED KARMIC DEBTS (Retrograde Planets)
{self._format_retrograde_debts(unfinished_debts)}

## DESTINY AXIS (Rahu-Ketu)
**Ketu (Past Mastery):** House {destiny_axis.get('ketu_house', 'Unknown')} - {destiny_axis.get('ketu_legacy', '')}
**Rahu (Current Mission):** House {destiny_axis.get('rahu_house', 'Unknown')} - {destiny_axis.get('rahu_mission', '')}
**Balance:** {destiny_axis.get('axis_balance', '')}
**🎯 PRE-MASTERED SKILL:** {destiny_axis.get('monetizable_skill', 'Check if Ketu nakshatra lord is in 10th house')}

**CRITICAL INSTRUCTION**: If the "PRE-MASTERED SKILL" field shows a monetizable skill (Ketu nakshatra lord in 10th house), this is a PAST LIFE MASTERY that requires MINIMAL EFFORT in this life. The native can excel in this field with 50% less effort than others. This is NOT a new skill to learn - it's a dormant talent waiting to be reactivated. Prioritize this as the PRIMARY career recommendation.

## KARMIC OBSTACLES (Badhaka)
**Badhaka Lord:** {badhaka.get('badhaka_lord', 'Unknown')}
**House:** {badhaka.get('badhaka_house', 'Unknown')}
**Currently Active:** {badhaka.get('currently_active', False)} {'⚠️ OBSTACLE IS ACTIVE NOW' if badhaka.get('currently_active') else ''}
**Obstacle Type:** {badhaka.get('obstacle_type', 'Unknown')}
**Meaning:** {badhaka.get('karmic_meaning', '')}
**Remedies:** {', '.join(badhaka.get('remedies', []))}

## SOUL JUNCTIONS (Gandanta)
**Planets Affected:** {', '.join(gandanta.get('planets_affected', [])) or 'None'}
**Lagna in Gandanta:** {gandanta.get('lagna_in_gandanta', False)}
**Moon in Gandanta:** {gandanta.get('moon_in_gandanta', False)}
**Significance:** {gandanta.get('significance', '')}

## VULNERABLE KARMIC POINTS (Mrityu Bhaga)
**Planets Affected:** {', '.join(mrityu.get('planets_affected', [])) or 'None'}
**Overall Risk:** {mrityu.get('overall_risk', 'Normal')}
**Significance:** {mrityu.get('significance', '')}

## SOUL CONTINUITY (Vargottama)
**Total Vargottama Planets:** {vargottama.get('total_vargottama_planets', 0)}
**Planets:** {self._format_vargottama(vargottama.get('vargottama_planets', []))}
**Significance:** {vargottama.get('significance', '')}

## ANCESTRAL KARMA (Pitru Dosha)
**Has Ancestral Debt:** {pitru.get('has_ancestral_debt', False)}
**Type:** {pitru.get('type', 'None')}
**Remedy:** {pitru.get('remedy', '')}
**Karmic Meaning:** {pitru.get('karmic_meaning', '')}

## MATERNAL KARMA (Matru Dosha)
**Has Maternal Debt:** {matru.get('has_maternal_debt', False)}
**Type:** {matru.get('type', 'None')}
**Remedy:** {matru.get('remedy', '')}
**Karmic Meaning:** {matru.get('karmic_meaning', '')}

## 5TH HOUSE - POORVA PUNYA (Past Life Merit)
**Planets:** {', '.join(poorva_punya.get('planets', [])) or 'None'}
**Theme:** {poorva_punya.get('theme', '')}
**Karma Type:** {poorva_punya.get('karma_type', '')}
**Past Life Merit:** {poorva_punya.get('past_life_merit', 'Neutral')}
**This Life Blessings:** {poorva_punya.get('this_life_blessings', '')}
**Significance:** {poorva_punya.get('significance', '')}

## 8TH HOUSE - PRARABDHA (Unavoidable Transformation)
**Planets:** {', '.join(house_8.get('planets', [])) or 'None'}
**Theme:** {house_8.get('theme', '')}
**Karma Type:** {house_8.get('karma_type', '')}
**Karmic Debt:** {house_8.get('karmic_debt', '')}
**Occult Potential:** {house_8.get('occult_potential', 'Moderate')}
**Significance:** {house_8.get('significance', '')}

## 9TH HOUSE - BHAGYA (Fortune from Past Dharma)
**Planets:** {', '.join(bhagya.get('planets', [])) or 'None'}
**Theme:** {bhagya.get('theme', '')}
**Karma Type:** {bhagya.get('karma_type', '')}
**Past Dharma:** {bhagya.get('past_dharma', 'Neutral')}
**This Life Luck:** {bhagya.get('this_life_luck', '')}
**Significance:** {bhagya.get('significance', '')}

## MOKSHA INDICATORS (12th House)
**Planets:** {', '.join(house_12.get('planets', [])) or 'None'}
**Moksha Potential:** {house_12.get('moksha_potential', 'Moderate')}
**Theme:** {house_12.get('theme', '')}
**Karmic Indication:** {house_12.get('karmic_indication', '')}

## KARMIC TIMING
**Saturn Dasha:** {timing.get('saturn_dasha', '')}
**Rahu Dasha:** {timing.get('rahu_dasha', '')}
**Ketu Dasha:** {timing.get('ketu_dasha', '')}
**Current Focus:** {timing.get('current_focus', '')}

---

## ANALYSIS REQUIREMENTS

Based on this comprehensive karmic analysis AND the raw charts provided, provide a detailed reading covering:

1. **Past Life Overview**: What karma did this soul bring from previous incarnations? What was their primary role or identity?

2. **Soul's Mission**: What is the primary purpose of this incarnation? What lessons must be learned?

3. **Nakshatra Karma Analysis**: Deep dive into the subconscious karmic patterns revealed by Atmakaraka, Ketu, and Moon nakshatras. What specific past life occupations and skills? How does Ganda-Moola affect the soul's journey?

4. **Karmic Debts**: What specific debts or obligations need resolution? How can they be addressed?

5. **Soul Talents**: What skills, abilities, or wisdom carried forward from past lives? How to leverage them?

6. **Karmic Obstacles**: What challenges or tests will arise? Why are they appearing? How to overcome them?

7. **Ancestral Patterns**: What family karma affects this soul? What ancestral blessings or burdens exist?

8. **Transformation Path**: What major transformations are destined? When and how will they occur?

9. **Spiritual Evolution**: What is the path to moksha/liberation? What spiritual practices are recommended?

10. **Timing of Events**: When will major karmic events manifest? What periods require special attention?

11. **Remedial Measures**: What specific remedies (mantras, charity, practices) can help resolve karma?

Provide a compassionate, insightful, and actionable reading that helps the person understand their karmic journey and soul's evolution.
"""
        
        return prompt
    
    def _format_karmic_patterns(self, patterns: list) -> str:
        """Format karmic patterns for prompt"""
        if not patterns:
            return "No significant Saturn Nadi links found"
        
        formatted = []
        for p in patterns[:5]:  # Top 5
            formatted.append(f"- {p.get('planet', 'Unknown')}: {p.get('description', '')}")
        
        return '\n'.join(formatted)
    
    def _format_retrograde_debts(self, debts: list) -> str:
        """Format retrograde debts for prompt"""
        if not debts:
            return "No retrograde planets - minimal unfinished karma"
        
        formatted = []
        for d in debts:
            formatted.append(f"- {d.get('planet', 'Unknown')}: {d.get('karmic_debt', '')}")
        
        return '\n'.join(formatted)
    
    def _format_vargottama(self, planets: list) -> str:
        """Format vargottama planets"""
        if not planets:
            return "None"
        
        return ', '.join([f"{p.get('planet', 'Unknown')} ({p.get('strength', 'Unknown')})" for p in planets])
    
    def _parse_response_sections(self, response: str) -> Dict[str, str]:
        """Parse AI response into sections"""
        sections = {}
        current_section = None
        current_content = []
        preamble = []
        found_first_section = False
        
        for line in response.split('\n'):
            stripped = line.strip()
            # Check for numbered section headers: ### 1. or ### **1. or ### **1.**
            is_section = False
            if stripped.startswith('###'):
                for i in range(1, 12):
                    if (stripped.startswith(f'### {i}.') or 
                        stripped.startswith(f'### **{i}.') or
                        stripped.startswith(f'### **{i}.**')):
                        is_section = True
                        break
            
            if is_section:
                # Save preamble as Introduction
                if not found_first_section and preamble:
                    sections['Introduction'] = '\n'.join(preamble).strip()
                    preamble = []
                    found_first_section = True
                
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section - clean up formatting
                current_section = stripped.replace('###', '').replace('**', '').strip()
                current_content = []
                found_first_section = True
            else:
                if not found_first_section:
                    preamble.append(line)
                else:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If no sections found, save everything as Introduction
        if not found_first_section and preamble:
            sections['Introduction'] = '\n'.join(preamble).strip()
        
        return sections
