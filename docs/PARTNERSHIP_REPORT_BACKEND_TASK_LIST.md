# Partnership Report Backend Task List

This task list is the execution companion to `PARTNERSHIP_REPORT_BACKEND_SPEC.md`.
Use it to implement the new report framework in small, testable steps.

## Milestone 1: Report Framework Skeleton

- [ ] Create `backend/reports/` package
- [ ] Add `backend/reports/__init__.py`
- [ ] Add `backend/reports/models.py`
- [ ] Add `backend/reports/constants.py`
- [ ] Add `backend/reports/report_types.py`
- [ ] Add `backend/reports/report_registry.py`
- [ ] Add `backend/reports/routes.py`
- [ ] Add `backend/reports/orchestrator.py`
- [ ] Add `backend/reports/cache/report_hash.py`
- [ ] Add `backend/reports/cache/report_cache_service.py`
- [ ] Add `backend/reports/cache/report_storage.py`

## Milestone 2: Base Context Assembly

- [ ] Add `backend/reports/context/base_context_builder.py`
- [ ] Add `backend/reports/context/chart_context_builder.py`
- [ ] Add `backend/reports/context/timing_context_builder.py`
- [ ] Add `backend/reports/context/remedy_context_builder.py`
- [ ] Add `backend/reports/context/house_context_builder.py`
- [ ] Add `backend/reports/context/shared_branch_context.py`
- [ ] Implement `build_base_context(request)`
- [ ] Implement `collect_birth_data(request)`
- [ ] Implement `collect_chart_payloads(request)`
- [ ] Implement `collect_divisional_charts(request)`
- [ ] Implement `collect_timing_payload(request)`
- [ ] Implement `collect_remedy_payload(request)`
- [ ] Implement `collect_house_payload(request)`

## Milestone 3: Branch Extractors

- [ ] Add `backend/reports/context/kp_context_builder.py`
- [ ] Add `backend/reports/context/jaimini_context_builder.py`
- [ ] Add `backend/reports/context/nadi_context_builder.py`
- [ ] Add `backend/reports/context/nakshatra_context_builder.py`
- [ ] Add `backend/reports/context/d60_context_builder.py`
- [ ] Implement `collect_kp_context(...)`
- [ ] Implement `collect_jaimini_context(...)`
- [ ] Implement `collect_nadi_context(...)`
- [ ] Implement `collect_nakshatra_context(...)`
- [ ] Implement `collect_d60_context(...)`
- [ ] Implement `build_kp_branch_context(...)`
- [ ] Implement `build_jaimini_branch_context(...)`
- [ ] Implement `build_nadi_branch_context(...)`
- [ ] Implement `build_nakshatra_branch_context(...)`
- [ ] Implement `build_d60_branch_context(...)`

## Milestone 4: Partnership Report Context

- [ ] Add `backend/reports/context/partnership_context_builder.py`
- [ ] Implement `build_partnership_report_context(request)`
- [ ] Implement `build_partnership_evidence_spine(...)`
- [ ] Implement `build_partnership_score_summary(...)`
- [ ] Implement `build_partnership_chart_blocks(...)`
- [ ] Implement `build_partnership_timing_blocks(...)`
- [ ] Implement `build_partnership_remedy_blocks(...)`
- [ ] Implement `build_partnership_faq_seed(...)`
- [ ] Decide the exact 20-page JSON shape for partnership reports

## Milestone 5: LLM Layer

- [ ] Add `backend/reports/llm/report_prompt_builder.py`
- [ ] Add `backend/reports/llm/report_llm_service.py`
- [ ] Add `backend/reports/llm/report_response_validator.py`
- [ ] Implement `build_system_prompt(report_type, language)`
- [ ] Implement `build_partnership_prompt(context, language)`
- [ ] Implement `build_page_instructions(report_type)`
- [ ] Implement `build_llm_context_excerpt(context)`
- [ ] Implement `generate_report_narrative(report_type, context, language)`
- [ ] Implement `call_structured_llm(prompt, context, language)`
- [ ] Implement `merge_llm_sections(static_report, ai_payload)`
- [ ] Implement `validate_report_json(payload)`

## Milestone 6: Page Assembly

- [ ] Add `backend/reports/assembly/page_builders.py`
- [ ] Add `backend/reports/assembly/page_assembler.py`
- [ ] Add `backend/reports/assembly/pdf_manifest_builder.py`
- [ ] Implement `assemble_report_document(report_type, context, ai_payload)`
- [ ] Implement `assemble_partnership_pages(...)`
- [ ] Implement `build_cover_page(...)`
- [ ] Implement `build_executive_summary_page(...)`
- [ ] Implement `build_compatibility_breakdown_page(...)`
- [ ] Implement `build_d1_overlay_pages(...)`
- [ ] Implement `build_d9_pages(...)`
- [ ] Implement `build_dasha_pages(...)`
- [ ] Implement `build_guna_page(...)`
- [ ] Implement `build_strengths_page(...)`
- [ ] Implement `build_challenges_page(...)`
- [ ] Implement `build_remedies_page(...)`
- [ ] Implement `build_timing_page(...)`
- [ ] Implement `build_future_analysis_page(...)`
- [ ] Implement `build_d60_page(...)`
- [ ] Implement `build_house_synthesis_page(...)`
- [ ] Implement `build_faq_page(...)`
- [ ] Implement `build_next_steps_page(...)`
- [ ] Implement `build_pdf_manifest(...)`

## Milestone 7: Routes and Orchestration

- [ ] Expose `backend/reports/routes.py` through `backend/main.py`
- [ ] Implement `create_report(...)`
- [ ] Implement `get_report_status(...)`
- [ ] Implement `get_report(...)`
- [ ] Implement `regenerate_report(...)`
- [ ] Implement `list_report_types(...)`
- [ ] Implement `start_report_generation(...)`
- [ ] Implement `process_report_job(...)`
- [ ] Implement `build_and_cache_report(...)`
- [ ] Implement `get_report_result(...)`
- [ ] Implement `regenerate_report(...)`
- [ ] Ensure all report endpoints accept `language`

## Milestone 8: Caching

- [ ] Implement `normalize_birth_data(data)`
- [ ] Implement `normalize_report_request(request)`
- [ ] Implement `build_report_cache_key(request)`
- [ ] Implement `build_pair_hash(person_a, person_b, report_type, language)`
- [ ] Implement `save_report(report_id, payload)`
- [ ] Implement `load_report(report_id)`
- [ ] Implement `upsert_report_cache(...)`
- [ ] Implement `get_cached_report(...)`
- [ ] Define cache invalidation rules by report version

## Milestone 9: Reuse Existing Calculators Correctly

- [ ] Reuse `backend/calculators/divisional_chart_calculator.py`
- [ ] Reuse `backend/calculators/jaimini_point_calculator.py`
- [ ] Reuse `backend/calculators/nadi_linkage_calculator.py`
- [ ] Reuse `backend/calculators/nakshatra_calculator.py`
- [ ] Reuse `backend/calculators/remedy_engine.py`
- [ ] Reuse `backend/calculators/karma_context_builder.py`
- [ ] Reuse `backend/app/kp/services/chart_service.py`
- [ ] Confirm D1 and D9 data shapes match the report layer contract
- [ ] Confirm D60 fields are available for the karmic page

## Milestone 10: Future Report Types

- [ ] Add report type registry entries for `career`
- [ ] Add report type registry entries for `progeny`
- [ ] Add report type registry entries for `wealth`
- [ ] Add report type registry entries for `health`
- [ ] Create report templates for each new report type
- [ ] Reuse the same context, LLM, and assembly pipeline

## Implementation Order

1. Build the report framework skeleton
2. Add the base context builder
3. Add branch extractors for KP, Jaimini, Nadi, Nakshatra, and D60
4. Build the partnership context
5. Add the single-call LLM enrichment layer
6. Assemble the 20-page document structure
7. Wire the routes and cache
8. Connect the backend report payload to the mobile/web PDF renderer
9. Add the next report types using the same framework

## Acceptance Criteria

- The backend can generate one partnership report end to end
- The report uses one LLM call per report
- The report accepts language from the client
- The report returns structured page data, not only prose
- KP, Jaimini, Nadi, Nakshatra, and D60 are placed in the correct report sections
- The design can be reused for career, progeny, wealth, and health reports later

