# Unified Output Schema - Single Source of Truth for Response Formatting

def get_output_schema(premium_analysis=False, analysis_type='birth'):
    """
    Unified output schema for all AI responses.
    Eliminates redundant formatting blocks across the codebase.
    """
    
    # Base schema for all analysis types
    base_schema = """
### 🏛️ RESPONSE STRUCTURE (MANDATORY)
1. <div class="quick-answer-card">**Quick Answer**: [Comprehensive summary of full analysis. Use Jaimini AL/UL as final verdict for status/marriage.]</div>
2. ### Key Insights: [3 Bullets + "The Jaimini Secret" bullet using talents/wealth sutras.]
3. ### Astrological Analysis: [Direct content under header + these #### subsections]:
   - #### The Parashari View | #### Jaimini Sutra Deep-Dive (AL/UL/KL/Yogas)
   - #### Nadi Precision (links) | #### Timing Synthesis (Dasha+Chara+Yogini+Mudda)
   - #### Triple Perspective (Sudarshana) | #### Divisional Chart Analysis
4. ### Nakshatra Insights: [Classical authority analysis + remedies.]
5. ### Timing & Guidance: [Actionableroadmap.]
6. <div class="final-thoughts-card">**Final Thoughts**: [Conclusion.]</div>

### 🚨 FORMATTING RULES
- [HEADERS]: ONLY ### for main; ONLY #### for subs inside Analysis. No # or ##.
- [TECH-TERMS]: Wrap all in <term id="key">Term</term>.
- [GLOSSARY]: End with GLOSSARY_START/END JSON block.
- [FOLLOW-UP]: End with <div class="follow-up-questions"> + 3-4 emoji-led questions in user format (e.g., "Tell me about my health" instead of "Would you like health analysis?").
"""

    # Premium image instructions
    image_instructions = ""
    if premium_analysis:
        image_instructions = """
### 🎨 SUMMARY IMAGE (MANDATORY)
Generate a VISUAL NARRATIVE prompt within SUMMARY_IMAGE_START/END tags.
- [STRUCTURE]: Multi-panel (3-6 organic scenes) representing key themes, predictions, and timing.
- [CONTENT]: Symbolic metaphors only (no literal figures). Map colors: Indigo (Challenge), Gold (Success), Emerald (Growth), Purple (Soul), Orange (Partnership).
- [STYLE]: Professional hand-drawn pencil sketch with watercolor washes. Minimalist and cohesive.
- [LABELS]: Elegant hand-lettered 1-3 word ALL CAPS headers per panel (e.g., "TRANSFORMATION").
- [PROMPT-REQ]: Must describe layout, symbolism, colors, and narrative flow between panels.
"""

    # Analysis-specific overrides
    if analysis_type == 'mundane':
        return """
RESPONSE FORMAT - MUNDANE MODE:
Start with Executive Summary then provide geopolitical analysis:

<div class="quick-answer-card">**Executive Summary**: [Complete risk assessment and market outlook in clear, professional language. Cover major economic, political, and market trends.]</div>

### Key Risk Factors
[Bullet points with specific risks and probabilities]

### Economic & Market Analysis
[Detailed analysis with timing and sectors]

### Geopolitical Outlook
[Political stability, conflicts, policy changes]

<div class="final-thoughts-card">**Strategic Outlook**: [Balanced conclusion with actionable insights]</div>

FOLLOW-UP QUESTIONS - MANDATORY:
Generate 3-4 contextually relevant follow-up questions based on the user's query. Examples for mundane analysis:
<div class="follow-up-questions">
📊 Which sectors will outperform?
⚠️ What are the major risk events?
💱 How will currency markets react?
🌍 What geopolitical shifts are likely?
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