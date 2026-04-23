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


def _json_for_prompt(value: Any) -> str:
    """Serialize chart payloads for prompts, including datetime/date values."""
    return json.dumps(value, default=str)


def json_dumps_karma_safe(value: Any) -> str:
    """Serialize karma context for persistence, including datetime/date values."""
    return json.dumps(value, default=str)


class KarmaGeminiAnalyzer:
    """Integrates Karma Context with Gemini AI for personalized readings"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        from utils.admin_settings import get_gemini_analysis_model
        self.model = genai.GenerativeModel(get_gemini_analysis_model())
    
    def analyze_karma(self, chart_data: Dict[str, Any], divisional_charts: Dict[str, Any] = None, native_name: str = None, log_request: bool = False) -> Dict[str, Any]:
        """Generate complete karma analysis with AI interpretation"""
        
        # Build karma context. The underlying calculators are verbose, so keep
        # production logs clean unless karma debugging is explicitly enabled.
        karma_builder = KarmaContextBuilder(chart_data, divisional_charts)
        if os.getenv("ASTRO_DEBUG_KARMA") == "1":
            karma_context = karma_builder.get_complete_karma_context()
        else:
            import contextlib
            import io

            with contextlib.redirect_stdout(io.StringIO()):
                karma_context = karma_builder.get_complete_karma_context()
        
        # Generate AI interpretation
        prompt = self._build_karma_prompt(karma_context, native_name)
        
        if log_request:
            print(f"\n{'='*80}")
            print(f"📤 GEMINI REQUEST - Karma Analysis")
            print(f"{'='*80}")
            print(f"Prompt length: {len(prompt)} characters")
            print("Full prompt logging is disabled for privacy. Set ASTRO_DEBUG_AI_PAYLOADS=1 to print sensitive payloads.")
            if os.getenv("ASTRO_DEBUG_AI_PAYLOADS") == "1":
                print(f"\nFull Prompt:\n{prompt}")
            print(f"{'='*80}\n")
        
        try:
            response = self.model.generate_content(prompt)
            interpretation = response.text
            
            if log_request or os.getenv("ASTRO_DEBUG_AI_PAYLOADS") == "1":
                print(f"\n{'='*80}")
                print(f"📥 GEMINI RESPONSE - Karma Analysis")
                print(f"{'='*80}")
                print(f"Response length: {len(interpretation)} characters")
                if os.getenv("ASTRO_DEBUG_AI_PAYLOADS") == "1":
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
        karma_evidence = karma_context.get('karma_evidence', {})
        
        # Extract raw charts
        d1_chart = karma_context.get('d1_chart', {})
        d9_chart = karma_context.get('d9_navamsa', {})
        d60_chart = karma_context.get('d60_shashtiamsa', {})
        
        prompt = f"""You are an expert Vedic astrologer specializing in karma analysis using classical Jyotish principles. Provide a compassionate, evidence-backed reading based on the following karmic indicators.{name_instruction}

## CRITICAL ANALYSIS INSTRUCTIONS

### Trust, Safety, and Certainty Rules
- Treat "past life" language as a symbolic karmic pattern, not a literal factual biography.
- Do NOT use fatalistic, frightening, curse-heavy, or death-predictive language.
- D60 is highly birth-time sensitive. If `karma_evidence.d60_confidence.boundary_risk` is medium/high or birth time is not clearly reliable, downgrade D60 certainty and rely more on D1, D9, Atmakaraka, Karkamsa, Rahu-Ketu, and current dasha.
- Do not invent exact classical citations or verse references. You may say "the classical Parashari/Jaimini principle is..." only when the provided evidence supports it.
- If evidence conflicts, explicitly say which evidence is stronger and which is supportive/weak.
- Remedies must be practical, ethical, and tied to the exact chart evidence. Do not promise guaranteed outcomes.

### Karma Evidence Spine
Use this compact evidence block as the priority spine before raw chart inference:
{_json_for_prompt(karma_evidence)}

### Raw Chart Analysis Protocol
You have access to THREE raw charts for direct analysis:
1. **D1 Chart (Rashi)**: Birth chart showing current life setup - {_json_for_prompt(d1_chart)}
2. **D9 Chart (Navamsa)**: Dharma/marriage/inner strength chart - {_json_for_prompt(d9_chart)}
3. **D60 Chart (Shashtiamsa)**: Past life karma essence chart - {_json_for_prompt(d60_chart)}

**MANDATORY**: Cross-reference calculated insights with raw planetary positions. If you find contradictions or additional patterns in the raw charts, MENTION THEM.

### D60 Handling Rule
D60 refines hidden karmic residue, but it is not a standalone verdict. If D9/D1 show strength and D60 is challenging, describe it as "outer capacity with inner karmic work." If D60 is strong but D1/D9 are weak, describe it as "inner merit requiring current-life discipline." Never say a D60 result must inevitably manifest.

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
**Current Vimshottari:** {_json_for_prompt(timing.get('current_vimshottari', {}))}
**Saturn Dasha:** {timing.get('saturn_dasha', '')}
**Rahu Dasha:** {timing.get('rahu_dasha', '')}
**Ketu Dasha:** {timing.get('ketu_dasha', '')}
**Current Focus:** {timing.get('current_focus', '')}

---

## ANALYSIS REQUIREMENTS

Return the reading using exactly these markdown section headings so the app can render it cleanly:

### 1. Karma Snapshot
Summarize the top 3 karmic themes and state confidence level, especially D60 confidence.

### 2. Static Karma Promise
Use D1 5th/8th/9th/12th houses, Rahu-Ketu axis, Atmakaraka, Karkamsa, D9, and D60 confidence-aware evidence.

### 3. Soul Direction and Lessons
Explain AK, Karkamsa, Rahu mission, and the current-life growth path.

### 4. Gifts and Carried Talents
Describe talents as natural tendencies, not guaranteed success. Include Ketu/nakshatra/Nadi only when supported.

### 5. Karmic Friction and Repeating Patterns
Discuss retrograde planets, Badhaka, Gandanta, ancestral/maternal patterns, and obstacles without fear language.

### 6. Current Activation
Use current Vimshottari MD/AD/PD and active Saturn/Rahu/Ketu themes. Distinguish active now from latent potential.

### 7. Life Domains Affected
Explain how karma may show through career, relationship, family, wealth, health discipline, spirituality, and foreign/inner life, but only as tendencies.

### 8. Transformation Path
State likely transformation themes and broad timing anchors without overclaiming exact events.

### 9. Remedies and Integration Plan
Give specific mantra/charity/seva/behavioral practices tied to chart evidence. Keep remedies realistic and ethical.

### 10. Final Guidance
End with grounded, non-fatalistic advice on how to work with karma consciously.
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
