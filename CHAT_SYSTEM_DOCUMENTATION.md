# Gemini Astrology Chat System Documentation

This document outlines the architecture and principles for the astrology chat AI. The system is designed to provide responses that are accurate, trustworthy, transparent, and tailored to the user's specific intent, avoiding a "one-size-fits-all" feeling.

## Core Architecture

The system is built on a three-part architecture:
1.  **Intent Router:** Understands the user's query and assigns a specific `mode`.
2.  **Analysis Engine:** Performs the astrological calculations, guided by the `mode`.
3.  **Template Engine:** Formats the analysis into the appropriate response structure, selected based on the `mode`.

---

## 1. Intent Routing System

The router's primary job is to determine the user's true intent and assign a `mode` from the comprehensive list below. This `mode` dictates the entire analysis and response pipeline.

### Predictive Modes
*(For questions about "When" or "What will happen")*
-   `PREDICT_DAILY`: Handles daily predictions. It has sub-modes: `general_outlook`, `challenges`, `opportunities`, `specific_question`.
-   `PREDICT_PERIOD_OUTLOOK`: For general questions about a specific timeframe (e.g., "How will the next 6 months be for my career?").
-   `PREDICT_EVENT_TIMING`: For "when will X happen?" questions (e.g., "When will I get married?").
-   `PREDICT_EVENTS_FOR_PERIOD`: For listing numerous potential events over a period (e.g., "Tell me all events for this year.").

### Analytical Modes
*(For questions about "Why" or "What is in my chart")*
-   `ANALYZE_TOPIC_POTENTIAL`: Assesses the potential of a life area (e.g., "Tell me about my financial prospects.").
-   `ANALYZE_TOPIC_STRENGTHS_WEAKNESSES`: A focused analysis of a life area (e.g., "What are my career strengths?").
-   `ANALYZE_PERSONALITY`: Describes the user's character based on their chart.
-   `ANALYZE_SPECIFIC_PLACEMENT`: An educational mode for questions like "What does Saturn in my 4th house mean?".
-   `ANALYZE_ROOT_CAUSE`: For deep-seated "why" questions (e.g., "Why do I always struggle with self-confidence?").

### Remedial Modes
*(For questions about "What should I do?")*
-   `RECOMMEND_REMEDY_FOR_PROBLEM`: Suggests remedies for a specific issue (e.g., "I have a lot of anxiety. What can I do?").
-   `RECOMMEND_REMEDY_FOR_PLANET`: Suggests remedies for a specific planet (e.g., "How can I improve my Jupiter?").

### Comparison Modes
*(For questions about "Which one is better?")*
-   `COMPARE_CHOICES`: For "this or that" decisions (e.g., "Should I take Job A or Job B?").
-   `COMPARE_SYNASTRY`: For relationship compatibility analysis.

---

## 2. Astrological Analysis Engine

The analysis engine's logic is guided by the selected `mode`.

### Core Principles
-   **Multi-System Analysis:** All analyses synthesize insights from **Parashari, Jaimini, and Nadi** astrology.
-   **Transparency:** Every prediction must be accompanied by a concise **astrological reason** (e.g., "...because Jupiter is aspecting your 10th house.").
-   **Daily Prediction Focus:** Daily predictions must focus on the transits of **fast-moving planets** (especially the Moon), not the long-term transits of slow-moving planets like Saturn or Jupiter.

### Mode-Driven Analysis Example
For the `PREDICT_EVENTS_FOR_PERIOD` mode, the engine will scan the period for 12+ event triggers, including:
-   Dasha/Antardasha changes.
-   Major transits of Saturn, Jupiter, Rahu, Ketu (sign and nakshatra changes).
-   Conjunctions/aspects from transiting Jupiter and Saturn to natal planets.
-   Saturn/Jupiter "double transits."
-   Planetary stations (retrograde/direct).
-   Eclipses near natal planet degrees.
-   Mercury retrograde cycles.

---

## 3. Response Templates

The `mode` determined by the router is mapped to a specific response template. This ensures the structure of the answer fits the nature of the question.

### Template A: The Deep Dive
This is the most comprehensive template, reserved for broad, analytical questions.
-   **Used for modes:** `ANALYZE_TOPIC_POTENTIAL`, `ANALYZE_ROOT_CAUSE`, `PREDICT_PERIOD_OUTLOOK`, etc.
-   **Structure:**
    1.  `<div class="quick-answer-card">**Quick Answer**: [Comprehensive summary]</div>`
    2.  `### Key Insights: [3-4 bullets]`
    3.  `### Analysis Steps: [A bulleted list of 3-4 key astrological calculation steps]`
    4.  `### Astrological Analysis:`
        -   `#### The Parashari View: [Bulleted list of predictions]`
        -   `#### The Jaimini View: [Paragraph for Chara Dasha, then bulleted list for Karakas]`
        -   `#### Nadi Interpretation: [Bulleted list, one for each planetary combination]`
        -   `#### Timing Synthesis: [Synthesize all dasha systems]`
        -   `#### Triple Perspective (Sudarshana): [Analyze from Lagna, Moon, Sun]`
        -   `#### Divisional Chart Analysis: [Analyze relevant D-chart]`
    5.  `### Nakshatra Insights: [Analysis + Remedies]`
    6.  `### Timing & Guidance: [Actionable roadmap]`
    7.  `<div class="final-thoughts-card">**Final Thoughts**: [Conclusion]</div>`
    8.  `GLOSSARY_START`
        `[JSON block of all <term> definitions]`
        `GLOSSARY_END`
    9.  `<div class="follow-up-questions">[3-4 follow up questions]</div>`

### Template B: Event Prediction Timeline
This template is used exclusively for the `PREDICT_EVENTS_FOR_PERIOD` mode.
-   **Structure:**
    1.  `### Key Themes for [Period]`
        `[Bullet points on main focus areas]`
    2.  `### Timeline of Potential Events`
        `[A chronologically sorted list of events. Each item contains:]`
        -   `🗓️ **[Date or Date Range]**`
        -   `**Potential Event:** [Description of the event]`
        -   `**Astrological Insight:** [The "why" behind the prediction]`
        -   `**Life Area:** [Career, Relationship, Health, etc.]`
    3.  `### Guidance for the Period`
        `[Actionable advice on how to navigate the predicted events]`
    4.  `GLOSSARY_START ... GLOSSARY_END`
    5.  `### Follow-up Questions`
        `[3-4 follow up questions]`

### Template C: Daily Summary
This is a lighter template for all `PREDICT_DAILY_*` modes.
-   **Structure:**
    1.  `<div class="quick-answer-card">**Today's Outlook**: [Brief summary]</div>`
    2.  `### Key Opportunities`
        `[Bulleted list of positive influences and how to use them]`
    3.  `### Potential Challenges`
        `[Bulleted list of obstacles and how to navigate them]`
    4.  `### Guidance for Today`
        `[A final piece of actionable advice]`

### Other Templates
Conceptual templates for `EDUCATIONAL` (direct Q&A), `COMPARISON` (tables/pros & cons), and `REMEDY` (lists) queries also exist to be used as needed, ensuring maximum flexibility.
