# Partnership Report Backend Spec

This document is the backend source of truth for the new partnership PDF report system.
It explains what exists today, what must be built, how the report should be assembled, where each astrology branch belongs, and how to keep the design extensible for future reports such as career, progeny, wealth, and health.

## 1. Goal

Build a premium PDF report system that can generate a high-value partnership report first, then reuse the same backend for other report types later.

The report must:
- Use deterministic calculator outputs as the factual base
- Call the LLM once per report for premium narrative generation
- Support multiple languages
- Render a 20-page PDF template
- Reuse existing chart and compatibility infrastructure
- Stay generic enough to support future report types without rewriting the backend

## 2. Current State

The backend already has the important building blocks.

### Existing partnership / marriage stack

- `backend/marriage/marriage_routes.py`
  - Background marriage AI job flow
  - Cache lookup
  - Credit checks
  - Current request model already includes `language`

- `backend/marriage/marriage_analysis_execute.py`
  - Builds marriage AI context
  - Attaches compact evidence from Parashari, Jaimini, and Nadi branch payloads
  - Uses one structured LLM call through `StructuredAnalysisAnalyzer`

- `backend/ai/structured_analyzer.py`
  - Single-call JSON-only LLM analyzer
  - Takes a prompt, context, and language
  - Parses and validates structured JSON output

- `backend/marriage_matching/engine.py`
  - Deterministic compatibility engine
  - Produces:
    - overall score
    - D1/D9 profiles
    - evidence summary
    - timing overlay
    - recommendation
    - legacy payload

- `backend/marriage_matching/premium_report.py`
  - Best current template for the future report architecture
  - Builds a static report first
  - Calls the LLM once
  - Merges AI output into structured sections
  - Caches the final report

### Existing calculators and branch sources

- `backend/calculators/divisional_chart_calculator.py`
  - D1 through D60 support
  - Includes divisional chart generation and raw D60 arc tracking

- `backend/calculators/jaimini_point_calculator.py`
  - Arudha Lagna
  - Darapada / A7
  - Upapada Lagna / UL
  - Karkamsa
  - Swamsa
  - Hora Lagna
  - Ghatika Lagna

- `backend/calculators/nakshatra_calculator.py`
  - Nakshatra name, lord, deity, pada, and compatibility helpers

- `backend/calculators/nadi_linkage_calculator.py`
  - Nadi-style planetary linkage and exchange logic

- `backend/calculators/remedy_engine.py`
  - Structured remedies
  - Behavioral, ritual, charity, mantra, gemstone, and timing guidance

- `backend/calculators/karma_context_builder.py`
  - D60 and karmic context
  - Strong candidate for Page 16

- `backend/app/kp/services/chart_service.py`
  - KP chart calculation
  - House cusps
  - Cusp lords
  - Significators

### Existing mobile PDF path

- `astroroshni_mobile/src/utils/pdfGenerator.js`
  - Already contains `generateRelationshipReportPDF`
  - Already shares PDF files

- `astroroshni_mobile/src/components/Relationship/RelationshipMatchScreen.js`
  - Already fetches compatibility analysis
  - Already unlocks premium report
  - Already exports a PDF

## 3. Architecture Decision

The backend should be built as a **generic report framework** with report-type plug-ins.

### Why this architecture

- Future reports will share the same structure
- Calculators stay independent from presentation
- PDF rendering can remain generic
- LLM usage stays controlled and cheap
- Caching is easier when each report type uses a common contract

### Core rule

Do not create one-off report code paths for each topic.
Instead, create:

- a shared report orchestrator
- a shared context builder
- a shared LLM enrichment service
- a shared page assembler
- report-type templates

## 4. LLM Strategy

Use **one LLM call per report**, not 20 calls.

### Why one call is better

- Lower latency
- Lower cost
- Better consistency
- Easier cache behavior
- Less retry complexity
- Less chance of contradictory page-to-page output

### When to use more than one call

Only if a report becomes too large for the model context window.

If that ever happens, split it into at most 2-3 calls:
- core interpretation
- remedies / timing / FAQ
- optional recovery pass

But the default should remain a single call.

### LLM responsibility

The LLM should:
- interpret deterministic facts
- write premium narrative text
- adapt language to the user-selected language
- fill the human-facing sections of the report

The LLM should not:
- invent unsupported chart facts
- recompute astrology from scratch
- replace deterministic scores
- override calculator outputs without explicit evidence

## 5. Where Each Branch Belongs

This is the most important placement rule for the report.

### Jaimini

Use Jaimini for:
- relationship manifestation
- formal alliance
- spouse nature
- public expression of the bond
- soul-level maturity

Recommended pages:
- Page 4-5: D1 overlay
- Page 6-7: D9 depth
- Page 14-15: timing / manifestation support

Key outputs:
- `AL` = public image
- `A7` = lived partnership manifestation
- `UL` = formal marriage / alliance
- `Karkamsa` = soul direction
- `Swamsa` = inner path after commitment

### Nadi

Use Nadi for:
- karmic repetition
- hidden relationship patterns
- continuity
- unfinished emotional loops

Recommended pages:
- Page 12: challenges
- Page 16: karmic layer
- Page 17: synthesis

### KP

Use KP for:
- event materialization
- timing confirmation
- yes/no style support for the event
- cusp-level proof of delivery

Recommended pages:
- Page 2: executive summary
- Page 8-9: timing comparison
- Page 14: best timing
- Page 19: FAQ / certainty questions

KP should be treated as the materialization verifier, not a side note.

### Nakshatra

Use Nakshatra for:
- emotional rhythm
- instinctive chemistry
- lunar compatibility
- star-lord tone

Recommended pages:
- Page 3: compatibility breakdown
- Page 10: Guna Milan + AI score
- Page 11: strengths
- Page 12-13: friction and remedies

### D60

Use D60 for:
- karmic residue
- hidden legacy patterns
- deep explanation layer

Recommended page:
- Page 16 only, or mostly Page 16

## 6. Chart Image Strategy

The frontend already has North Indian and South Indian chart widgets, and those should be reused for chart pictures in the PDF.

### Backend role

The backend should not become a chart drawing engine.
Instead, it should:
- specify which charts are required
- specify which chart image slots are needed
- provide chart data for the renderer
- let mobile/web export chart images into the PDF

### Recommended image placement

- Pages 4-5: D1 chart images
- Pages 6-7: D9 chart images
- Optional: Page 16 mini D60 visual or badge

### Chart image manifest

The backend should return a manifest like:
- `d1_north`
- `d1_south`
- `d9_north`
- `d9_south`
- `d60_summary`

## 7. Language Handling

The report endpoint must accept `language`.

### Requirements

- Default to the app-provided language
- Allow the user to change it before generation
- Pass it into the LLM prompt
- Use it for page text, FAQ wording, and remedies

### Behavior

- If `language` is present, use it
- If missing, fall back to English
- Keep the report output language consistent end to end

This matches the current pattern already used in the marriage AI pipeline.

## 8. Recommended Backend File Layout

Create a new backend report framework under:

- `backend/reports/`
- `backend/reports/templates/`
- `backend/reports/context/`
- `backend/reports/llm/`
- `backend/reports/cache/`
- `backend/reports/assembly/`
- `backend/reports/branch_extractors/`

### Initial files

- `backend/reports/__init__.py`
- `backend/reports/models.py`
- `backend/reports/constants.py`
- `backend/reports/report_registry.py`
- `backend/reports/report_types.py`
- `backend/reports/routes.py`
- `backend/reports/orchestrator.py`
- `backend/reports/cache/report_cache_service.py`
- `backend/reports/cache/report_hash.py`
- `backend/reports/cache/report_storage.py`
- `backend/reports/context/base_context_builder.py`
- `backend/reports/context/partnership_context_builder.py`
- `backend/reports/context/shared_branch_context.py`
- `backend/reports/context/chart_context_builder.py`
- `backend/reports/context/timing_context_builder.py`
- `backend/reports/context/remedy_context_builder.py`
- `backend/reports/context/house_context_builder.py`
- `backend/reports/context/kp_context_builder.py`
- `backend/reports/context/jaimini_context_builder.py`
- `backend/reports/context/nadi_context_builder.py`
- `backend/reports/context/nakshatra_context_builder.py`
- `backend/reports/context/d60_context_builder.py`
- `backend/reports/llm/report_prompt_builder.py`
- `backend/reports/llm/report_llm_service.py`
- `backend/reports/llm/report_response_validator.py`
- `backend/reports/assembly/page_assembler.py`
- `backend/reports/assembly/page_builders.py`
- `backend/reports/assembly/pdf_manifest_builder.py`
- `backend/reports/templates/partnership/template.py`
- `backend/reports/templates/partnership/page_outline.py`
- `backend/reports/templates/partnership/section_map.py`
- `backend/reports/templates/partnership/faq_bank.py`
- `backend/reports/templates/partnership/cta_copy.py`

### Later report templates

- `backend/reports/templates/career/`
- `backend/reports/templates/progeny/`
- `backend/reports/templates/wealth/`
- `backend/reports/templates/health/`

## 9. Methods To Implement

### Registry methods

- `get_report_config(report_type)`
- `list_supported_report_types()`
- `get_required_calculators(report_type)`
- `get_required_branches(report_type)`

### Hash / cache methods

- `normalize_birth_data(data)`
- `normalize_report_request(request)`
- `build_report_cache_key(request)`
- `build_pair_hash(person_a, person_b, report_type, language)`

### Context builders

- `build_base_context(request)`
- `collect_birth_data(request)`
- `collect_chart_payloads(request)`
- `collect_divisional_charts(request)`
- `collect_timing_payload(request)`
- `collect_remedy_payload(request)`
- `collect_house_payload(request)`

- `build_partnership_report_context(request)`
- `build_partnership_evidence_spine(...)`
- `build_partnership_score_summary(...)`
- `build_partnership_chart_blocks(...)`
- `build_partnership_timing_blocks(...)`
- `build_partnership_remedy_blocks(...)`
- `build_partnership_faq_seed(...)`

- `collect_jaimini_context(...)`
- `collect_nadi_context(...)`
- `collect_kp_context(...)`
- `collect_nakshatra_context(...)`
- `collect_d60_context(...)`
- `collect_d1_context(...)`
- `collect_d9_context(...)`

### Chart / image methods

- `build_chart_image_manifest(...)`
- `build_north_chart_slot(...)`
- `build_south_chart_slot(...)`
- `build_divisional_chart_slot(...)`

### Timing methods

- `build_timing_context(...)`
- `build_joint_timing_windows(...)`
- `build_best_periods(...)`
- `build_avoid_periods(...)`

### Remedy methods

- `build_remedy_context(...)`
- `select_top_remedies(...)`
- `map_remedies_to_challenges(...)`

### House synthesis methods

- `build_house_wise_synthesis(...)`
- `build_house_summary_rows(...)`

### Branch-specific methods

#### KP
- `build_kp_branch_context(...)`
- `build_cusp_analysis(...)`
- `build_materialization_summary(...)`

#### Jaimini
- `build_jaimini_branch_context(...)`
- `build_a7_analysis(...)`
- `build_ul_analysis(...)`
- `build_al_analysis(...)`
- `build_karkamsa_analysis(...)`

#### Nadi
- `build_nadi_branch_context(...)`
- `build_pattern_repeat_analysis(...)`
- `build_karmic_continuity_analysis(...)`

#### Nakshatra
- `build_nakshatra_branch_context(...)`
- `build_emotional_compatibility_analysis(...)`
- `build_lunar_rhythm_analysis(...)`

#### D60
- `build_d60_branch_context(...)`
- `build_past_life_summary(...)`
- `build_hidden_karma_summary(...)`

### LLM methods

- `build_system_prompt(report_type, language)`
- `build_partnership_prompt(context, language)`
- `build_page_instructions(report_type)`
- `build_llm_context_excerpt(context)`
- `generate_report_narrative(report_type, context, language)`
- `call_structured_llm(prompt, context, language)`
- `merge_llm_sections(static_report, ai_payload)`
- `validate_report_json(payload)`

### Page assembly methods

- `assemble_report_document(report_type, context, ai_payload)`
- `assemble_partnership_pages(...)`
- `build_cover_page(...)`
- `build_executive_summary_page(...)`
- `build_compatibility_breakdown_page(...)`
- `build_d1_overlay_pages(...)`
- `build_d9_pages(...)`
- `build_dasha_pages(...)`
- `build_guna_page(...)`
- `build_strengths_page(...)`
- `build_challenges_page(...)`
- `build_remedies_page(...)`
- `build_timing_page(...)`
- `build_future_analysis_page(...)`
- `build_d60_page(...)`
- `build_house_synthesis_page(...)`
- `build_faq_page(...)`
- `build_next_steps_page(...)`
- `build_pdf_manifest(...)`

### Storage / cache methods

- `save_report(report_id, payload)`
- `load_report(report_id)`
- `upsert_report_cache(...)`
- `get_cached_report(...)`

### Orchestrator methods

- `start_report_generation(...)`
- `process_report_job(...)`
- `build_and_cache_report(...)`
- `get_report_result(...)`
- `regenerate_report(...)`

### Routes

- `create_report(...)`
- `get_report_status(...)`
- `get_report(...)`
- `regenerate_report(...)`
- `list_report_types(...)`

## 10. 20-Page Content Map

### Page 1: Cover
- Report title
- Report type
- Person A and Person B names
- Birth summary
- Overall score
- Verdict
- Brand and tagline

### Page 2: Executive Summary
- Green flag
- Yellow flag
- Red flag
- One-line decision
- Timing window summary
- Proceed / wait / caution conclusion

### Page 3: Compatibility Breakdown
- Radar chart or score bars
- Emotional
- Communication
- Financial
- Physical / intimacy
- Values / goals
- Karma / destiny

### Pages 4-5: D1 Overlay
- North and South chart images
- Cross-house placements
- Planet-to-house relationship text
- Key conjunctions and aspects

### Pages 6-7: D9 Navamsa
- D9 chart images
- Marriage depth
- Long-term maturity
- Emotional bond after commitment

### Pages 8-9: Dasha Comparison
- 2026-2035 timeline
- Joint favorable windows
- Joint challenging windows
- Best times for action

### Page 10: Guna Milan + AI Score
- Traditional score
- Effective score
- Exceptions
- AI interpretation

### Page 11: Strengths
- Five strong positives
- Each with astrological reason and real-life meaning

### Page 12: Challenges
- Three main friction points
- Why they happen
- How they may show up

### Page 13: Solutions / Remedies
- Practical remedies
- Traditional remedies
- One remedy per challenge

### Page 14: Timing
- Best months
- Avoid months
- Timing logic
- Action windows

### Page 15: Future Analysis
- Marriage: child / family expansion
- Business: growth / revenue peak
- Parent-child: bond development
- Custom: long-term evolution

### Page 16: D60
- Past-life theme
- Karmic connection
- Hidden residue
- Confidence note

### Page 17: House-wise Synthesis
- 1st through 12th house summary
- Strong / mixed / needs work
- One-line interpretation each

### Page 18: Remedies Summary
- Three strongest remedies
- Custom to the chart
- Keep it short and useful

### Page 19: FAQ
- Common objections
- Score interpretation
- Timing questions
- Remedy questions
- D60 / KP confidence questions

### Page 20: Next Steps
- App download CTA
- Consult CTA
- Upsell CTA
- QR code / WhatsApp support

## 11. Report Type Adaptation

The 20-page skeleton should stay stable, but some pages should adapt by report type.

### Partnership
- D1 / D9 / KP / Nadi / D60 all matter strongly

### Career
- D10, D24, Dasha, KP materialization, profession yogas

### Progeny
- 5th house, D7, Jupiter, Moon, timing, family growth

### Wealth
- 2nd, 11th, 5th, 9th houses, D2, D20, gain timing

### Health
- 1st, 6th, 8th, 12th houses, vitality, strain, recovery windows

This means the framework must support report-specific page content while preserving the same rendering pipeline.

## 12. Data Contract Recommendation

The report API should return a single structured object with:

- `report_type`
- `language`
- `generated_at`
- `input_summary`
- `score_summary`
- `branch_payloads`
- `pages`
- `faq`
- `cta`
- `chart_manifest`
- `cached`

Each page should be represented as structured data, not raw prose only.

Recommended page fields:
- `page_number`
- `title`
- `subtitle`
- `summary`
- `bullets`
- `metrics`
- `chart_refs`
- `tables`
- `notes`
- `cta`

## 13. Caching Strategy

Cache by:
- user id
- report type
- pair hash or subject hash
- language
- version

### Cache rules

- Cache the final structured report
- Allow cache hits even if current credits are low, if the report already exists
- Invalidate when the template version changes
- Keep a version string in the report payload

## 14. How The Backend Should Work End To End

1. Request arrives with report type, people, language, and options
2. Backend normalizes input
3. Backend calculates deterministic evidence
4. Backend builds branch payloads
5. Backend builds a compact report context
6. Backend calls the LLM once
7. Backend merges AI narrative with static facts
8. Backend assembles 20 page objects
9. Backend caches the final result
10. Mobile/web renders and exports PDF

## 15. What Not To Do

- Do not make 20 separate LLM calls for 20 pages
- Do not move astrology logic into the PDF renderer
- Do not let the LLM invent chart facts
- Do not hardcode partnership logic in a way that blocks future report types
- Do not mix chart calculation, narrative generation, and PDF rendering in one module
- Do not hide language handling in the frontend only; the backend must accept it

## 16. Implementation Order

Recommended order:

1. Create the report framework skeleton
2. Build partnership context assembly
3. Add branch extractors for Jaimini, Nadi, KP, Nakshatra, and D60
4. Build the one-call LLM enrichment flow
5. Define the 20-page JSON schema
6. Wire caching
7. Connect the API route
8. Let mobile/web render the PDF from the report payload
9. Add future report types using the same framework

## 17. Files To Reuse As Source Of Truth

These files should remain the main technical references:

- [`backend/marriage_matching/engine.py`](/Users/macbookpro/Astrology/backend/marriage_matching/engine.py)
- [`backend/marriage_matching/premium_report.py`](/Users/macbookpro/Astrology/backend/marriage_matching/premium_report.py)
- [`backend/marriage/marriage_analysis_execute.py`](/Users/macbookpro/Astrology/backend/marriage/marriage_analysis_execute.py)
- [`backend/ai/structured_analyzer.py`](/Users/macbookpro/Astrology/backend/ai/structured_analyzer.py)
- [`backend/calculators/divisional_chart_calculator.py`](/Users/macbookpro/Astrology/backend/calculators/divisional_chart_calculator.py)
- [`backend/calculators/jaimini_point_calculator.py`](/Users/macbookpro/Astrology/backend/calculators/jaimini_point_calculator.py)
- [`backend/calculators/nadi_linkage_calculator.py`](/Users/macbookpro/Astrology/backend/calculators/nadi_linkage_calculator.py)
- [`backend/calculators/nakshatra_calculator.py`](/Users/macbookpro/Astrology/backend/calculators/nakshatra_calculator.py)
- [`backend/calculators/remedy_engine.py`](/Users/macbookpro/Astrology/backend/calculators/remedy_engine.py)
- [`backend/calculators/karma_context_builder.py`](/Users/macbookpro/Astrology/backend/calculators/karma_context_builder.py)
- [`backend/app/kp/services/chart_service.py`](/Users/macbookpro/Astrology/backend/app/kp/services/chart_service.py)
- [`astroroshni_mobile/src/utils/pdfGenerator.js`](/Users/macbookpro/Astrology/astroroshni_mobile/src/utils/pdfGenerator.js)
- [`astroroshni_mobile/src/components/Relationship/RelationshipMatchScreen.js`](/Users/macbookpro/Astrology/astroroshni_mobile/src/components/Relationship/RelationshipMatchScreen.js)

## 18. Final Backend Principle

The backend should become a report platform, not a one-time feature.

The partnership report is the first report built on that platform.
The design should make later report types feel like configuration and content changes, not like new systems.

