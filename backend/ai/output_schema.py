# Unified Output Schema - Single Source of Truth for Response Formatting

def get_output_schema(premium_analysis=False, analysis_type='birth'):
    """
    Unified output schema for all AI responses.
    Eliminates redundant formatting blocks across the codebase.
    """
    
    # Base schema for all analysis types
    base_schema = """
### 🏛️ RESPONSE STRUCTURE (MANDATORY)
Your response MUST follow this exact sequence:
1. <div class="quick-answer-card">**Quick Answer**: [Comprehensive summary]</div>
2. ### Key Insights: [3-4 bullets]
3. ### Analysis Steps: [A bulleted list of 3-4 key astrological calculation steps taken to generate the response, e.g., "- Analyzing Dasha periods", "- Calculating planetary dignities", "- Cross-referencing Navamsa chart".]
4. ### Astrological Analysis: [Use #### for all subsections below]
   - #### The Parashari View: [Bulleted list of predictions]
   - #### The Jaimini View: [Paragraph for Chara Dasha (MD & AD), then bulleted list for Karakas]
   - #### Nadi Interpretation: [Bulleted list, one for each planetary combination]
   - #### Timing Synthesis: [Synthesize all dasha systems]
   - #### Triple Perspective (Sudarshana): [Analyze from Lagna, Moon, Sun]
   - #### Divisional Chart Analysis: [Analyze relevant D-chart]
5. ### Nakshatra Insights: [Analysis + Remedies]
6. ### Timing & Guidance: [Actionable roadmap]
7. <div class="final-thoughts-card">**Final Thoughts**: [Conclusion]</div>
8. GLOSSARY_START
   [JSON block of all <term> definitions]
   GLOSSARY_END
9. <div class="follow-up-questions">[3-4 emoji-led questions]</div>

### 🚨 FORMATTING RULES
- [HEADERS]: Use ### for main headers, #### for subsections.
- [TECH-TERMS]: Wrap all in <term id="key">Term</term>.
"""

    # Premium image instructions
    image_instructions = ""
    if premium_analysis:
        image_instructions = """
9. SUMMARY_IMAGE_START
   [A multi-panel visual narrative prompt for an image generation model.]
   SUMMARY_IMAGE_END
"""

    # Analysis-specific overrides
    if analysis_type == 'mundane':
        return """
RESPONSE FORMAT - MUNDANE MODE:
<div class="quick-answer-card">**Executive Summary**: [Risk assessment & market outlook]</div>
### Key Risk Factors
[Bullet points]
### Economic & Market Analysis
[Detailed analysis]
### Geopolitical Outlook
[Political stability, conflicts]
<div class="final-thoughts-card">**Strategic Outlook**: [Conclusion]</div>
GLOSSARY_START
[JSON block of definitions]
GLOSSARY_END
<div class="follow-up-questions">
[4 relevant questions]
</div>
"""
    
    return base_schema + "\n" + image_instructions


# Legacy compatibility - maps old RESPONSE_SKELETON to new schema
RESPONSE_SKELETON = """
[QUICK ANSWER CARD]: Comprehensive summary answering user's specific question decisively. Synthesize Parashari lords, Jaimini status, and Dasha timing into single verdict.
### Key Insights: 3 specific wins and 1 specific challenge.
### Astrological Analysis:
#### [Protocol] View: (Parashari, Jaimini, or Nadi results). For Parashari "Provide a Technically Exhaustive analysis. For the Parashari View, go into deep detail for every dasha level. Do not summarize; explain the 'why' behind every prediction using house significations."
#### Timing Synthesis: (Synthesize Vimshottari MD/AD/PD + Chara Sign + Yogini Lord)
#### Triple Perspective: Compare house strength from Lagna, Moon, and Sun.
### Nakshatra Insights: Star Shakti + Biological (Vriksha) remedy.
### Timing & Guidance: Specific monthly roadmap for next 6-12 months.
[FINAL THOUGHTS CARD]: Outlook anchored in classical text authority (cite BPHS, Saravali, or Phaladeepika).
"""