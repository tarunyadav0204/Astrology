# Parashari Prediction Engine Checklist

This is the working implementation tracker for the reusable deterministic prediction platform and its first consumer: homepage event-teaser cards for app and PWA.

The checklist deliberately separates astrological facts, prediction policy, presentation, and delivery. A phase is complete only when its exit gate is satisfied.

## Status and ownership

- Overall status: House-first deterministic core implemented; manual classical validation remains open
- Initial prediction profile: `parashari_fomo_v1`
- Initial horizon: Next 90 days, configurable
- Initial subjects: Self, mother, father, spouse
- Initial consumers: Authenticated app/PWA homepage and click-through chat
- Deployment decision: Separate domain service inside the existing backend; extraction-ready, not a separately deployed microservice yet

## Locked architectural decisions

- [x] Use only Parashari logic for the initial profile.
- [x] Keep deterministic calculation and event selection free of LLM calls.
- [x] Use the LLM only after a user opens a teaser and asks for its explanation.
- [x] Build a reusable prediction domain service, not feature-specific homepage calculations.
- [x] Keep the engine stateless and independent of authentication, UI, chat routes, and campaign code.
- [x] Represent every astrological factor as traceable evidence.
- [x] Keep activation strength separate from supportive/challenging outcome tone.
- [x] Use server-owned teaser IDs for click-to-chat; never trust astrological evidence supplied by the client.
- [x] Make calculation providers and prediction profiles independently versioned.
- [x] Make future factors such as Bhrigu Bindu addable without modifying the core engine.

## Phase 0 — Existing-system audit and baseline

- [x] Trace Event Timeline from UI through API, chart-context generation, LLM generation, caching, and credit handling.
- [x] Confirm that Event Timeline calculations are reusable but its event selection is LLM-driven.
- [x] Review the older `ParashariEventPredictor` and `DashaHouseGate` implementations.
- [x] Identify the older predictor's mixed Jaimini/Nadi dependencies, stale dignity call, silent fallbacks, and simplified scoring.
- [x] Inventory canonical dasha, transit, aspect, dignity, friendship, Badhaka, Yogi/Avayogi, Gandanta, Dagdha Rashi, and Tithi Shunya calculators.
- [x] Trace existing relative-house rotation for self and relatives.
- [x] Trace homepage prompt arbitration and chat `query_context` handling.
- [x] Identify the incorrect exact-ascendant transit-house shortcut in `ChatContextBuilder`.
- [x] Identify incomplete transit connection logic that does not use all planet-specific Parashari aspects.
- [x] Record baseline execution time for a 90-day calculation on representative charts.
- [ ] Record peak memory for a 90-day calculation on representative charts.
- [ ] Save representative baseline outputs from current Event Timeline and instant-chat timing for later regression comparison.

### Phase 0 exit gate

- [ ] Baseline performance and comparison fixtures are committed and reproducible.

## Phase 1 — Package boundary and public contracts

- [x] Create `backend/prediction_engine/` as an isolated domain package.
- [x] Define a serializable, validated `PredictionRequest` contract.
- [x] Define a versioned `PredictionResult` contract.
- [x] Define the normalized `Evidence` contract.
- [x] Define `PredictionCandidate`, `PredictionWindow`, `ActivationAssessment`, and `OutcomeAssessment` contracts.
- [x] Define explicit `evaluated`, `not_applicable`, `not_available`, and `calculation_error` states.
- [x] Define a public `PredictionService.generate(request)` interface.
- [ ] Ensure callers cannot import provider internals through the public package API.
- [x] Keep user authentication and chart ownership checks outside the engine.
- [x] Pass normalized/decrypted chart input into the engine; do not query user tables from calculation code.
- [ ] Define repository interfaces for snapshots, funnel events, and optional calculation caches.
- [x] Add schema-version fields to every persisted and returned contract.
- [x] Add structured error types instead of broad exception swallowing.
- [x] Document timezone, ayanamsha, zodiac, node, house-system, and ephemeris conventions.

### Phase 1 exit gate

- [ ] Contract tests can serialize and deserialize a request, evidence ledger, candidates, and final result without application globals or database access.

## Phase 2 — Canonical calculation primitives

- [x] Establish one canonical source for whole-sign house calculation.
- [x] Replace or bypass the exact-ascendant longitude shortcut for transit houses.
- [x] Establish one canonical source for Parashari graha drishti.
- [x] Remove duplicated aspect tables from the new prediction path.
- [x] Expose MD–AD–PD periods and exact boundaries through a stable adapter around the shared dasha calculator.
- [x] Normalize natal and transit planet names, signs, longitudes, houses, speeds, and retrograde flags.
- [ ] Expose conjunction detection with configurable orbs and explicit exactness.
- [x] Expose transit-to-natal conjunction and full Parashari aspect relations.
- [x] Expose dasha-planet-to-dasha-planet natal and transit relationships.
- [x] Expose natal lordship, occupation, dispositors, and house aspects.
- [x] Expose natural and functional benefic/malefic classifications separately.
- [x] Expose dignity without collapsing all dignity states into a single opaque score.
- [x] Expose compound friendship with the relevant sign/house lord.
- [x] Expose natal and transit combustion with configurable thresholds.
- [x] Expose natal and transit retrogression where applicable.
- [x] Expose benefic/malefic conjunction and aspect associations.
- [ ] Expose Gandanta through a stable public function for any evaluated longitude.
- [x] Expose Badhaka status and relationships.
- [x] Expose Yogi and Avayogi status.
- [x] Expose Dagdha Rashi and Tithi Shunya status.
- [x] Preserve raw calculation facts alongside normalized values.
- [ ] Add deterministic unit tests for sign boundaries, house boundaries, aspects, conjunction orbs, combustion, and retrograde transitions.
- [ ] Add tests around midnight, timezone changes, leap years, dasha boundaries, and transit sign changes.

### Phase 2 exit gate

- [ ] The same chart/date input produces identical normalized facts across repeated runs and no new prediction code depends on duplicated or private calculation logic.

## Phase 3 — Provider registry and evidence ledger

- [x] Add declared provider dependencies and supported-profile constraints to the implemented provider ID/version/evaluate interface.
- [x] Create a provider registry with dependency validation and deterministic execution order.
- [x] Reject incompatible provider versions and duplicate provider IDs.
- [x] Implement `DashaActivationProvider`.
- [x] Implement the independent twelve-house natal/dasha connection ledger (supersedes family-scoped `NatalHousePromiseProvider`).
- [x] Implement `TransitHouseProvider` as an independently switchable provider.
- [x] Implement `TransitNatalRelationProvider` as an independently switchable provider.
- [x] Implement `DashaPlanetRelationshipProvider`.
- [x] Implement `PlanetConditionProvider`.
- [x] Implement `FunctionalNatureProvider` as an independently switchable provider.
- [x] Implement `FriendshipProvider`.
- [x] Implement `BeneficMaleficAssociationProvider`.
- [x] Implement `BadhakaProvider`.
- [x] Implement `YogiAvayogiProvider`.
- [x] Implement `GandantaProvider`.
- [x] Implement `DagdhaRashiProvider`.
- [x] Implement `TithiShunyaProvider`.
- [x] Require every evidence record to include provider version, rule ID, source facts, subject, domain, window, polarity, and contributions.
- [x] Preserve independent supporting and challenging evidence rather than cancelling it prematurely.
- [x] Add an evidence trace mode for developers and internal admin inspection.
- [x] Add provider contract tests that run without APIs, databases, or LLMs.

### Phase 3 exit gate

- [x] Providers can be enabled, disabled, or added through a registry/profile change without editing the core engine.

## Phase 4 — Subjects, domains, and relative-house frames

- [x] Add an explicit version to the implemented subject registry.
- [x] Implement self with first-house anchor.
- [x] Implement mother with fourth-house anchor.
- [x] Implement father with ninth-house anchor.
- [x] Implement spouse with seventh-house anchor.
- [x] Use one tested relative-house rotation function everywhere.
- [x] Add an explicit version to the implemented event-domain and event-family registry.
- [x] Add conflicting-house mappings to the implemented primary-house, supporting-house, and karaka mappings.
- [x] Cover career/authority, money/gains, partnership/marriage, home/property, children/education, travel, health/workload, family responsibility, and communication/decisions.
- [x] Define minimum natal-promise evidence for every event family.
- [x] Define minimum timing evidence for every event family.
- [x] Prevent one activation from producing several near-duplicate event labels.
- [ ] Phrase relative predictions as themes involving the relative, not facts derived from an independent chart.
- [ ] Add rotation tests for every subject/domain combination.

### Phase 4 exit gate

- [x] Every supported candidate can show exactly which native and rotated houses produced it.

## Phase 5 — Window construction and prediction policy

- [x] Construct the configurable horizon from exact MD–AD–PD segments.
- [x] Split windows at relevant dasha boundaries.
- [x] Split windows at relevant transit sign changes.
- [x] Split windows at retrograde/direct changes.
- [x] Split windows at combustion entry/exit.
- [ ] Split windows at validated exact conjunction/aspect orb changes; current v7 windows use whole-sign relations.
- [x] Merge adjacent windows only when their evidence signatures are materially equivalent.
- [x] Define activation contributions for lordship, occupation, natal aspect, dispositor, karaka, and transit reinforcement.
- [x] Require independent confirmations rather than counting duplicated evidence twice.
- [x] Require transit reinforcement before assigning the strongest activation band.
- [x] Calculate supportive and challenging contributions independently.
- [x] Produce weighted `supportive`, `mixed`, `challenging`, and explicit `neutral/insufficient evidence` tone bands from transparent policy rules.
- [x] Do not expose raw scores as statistical probability or certainty.
- [x] Define configurable minimum activation and evidence-quality thresholds.
- [x] Add explicit consumer-relevance ranking to the implemented strength, evidence-diversity, duration, and recency ranking.
- [x] Deduplicate candidates across subjects, domains, and overlapping windows.
- [x] Add deterministic tie-breaking so output order is stable.
- [x] Store policy version and rule contributions with every candidate.

### Phase 5 exit gate

- [x] A candidate's activation band, tone, timing window, and ranking can all be reproduced from its evidence ledger.

## Phase 6 — Profiles and extensibility

- [x] Define `parashari_fomo_v1` as configuration rather than hard-coded conditionals.
- [x] Add safety policy configuration to the implemented horizon, subject, domain, provider, threshold, and candidate-limit profile configuration.
- [x] Validate unknown providers and invalid profile combinations at startup/test time.
- [x] Include profile and provider versions in cache signatures.
- [ ] Support request-level include/exclude provider overrides for internal testing only.
- [ ] Prevent public clients from selecting unsafe or unvalidated profiles.
- [ ] Define a profile migration policy so old snapshots remain explainable.
- [ ] Document the steps for adding a provider such as Bhrigu Bindu.
- [ ] Create a disabled placeholder/profile experiment for Bhrigu Bindu without inventing its scoring rules prematurely.

### Phase 6 exit gate

- [ ] A dummy provider can be added and exercised by a test profile without changing engine orchestration code.

## Phase 6A — Event resolution from combinations

- [x] Add a separately versioned event-signature registry beneath the broad event-family taxonomy.
- [x] Define required, supporting, and conflicting house combinations for each initial event signature.
- [x] Require complete D1 required-house coverage from direct dasha lordship or occupation.
- [x] Require an active AD/PD carrier; MD-only activation cannot resolve an event.
- [x] Replace the incorrect same-carrier requirement with traceable cooperative MD–AD–PD delivery through natal sambandha.
- [x] Use divisional charts only after D1/dasha/transit locks pass; a varga cannot create an event.
- [x] Calculate D2, D4, D7, D9, D10, D12, and D24 once per request through the existing canonical calculator.
- [x] Inspect the domain varga for self, plus D12 for parent themes or D9 for spouse themes, as corroboration rather than an event-existence gate.
- [x] Classify D1–dasha–transit events as `core_event` and upgrade to `corroborated_event` only when supporting houses and all relevant vargas agree.
- [x] Record varga chart, carrier, house, and relation in the resolution trace.
- [x] Add optional explicit real-life eligibility context without chart-based inference or hidden defaults.
- [x] Use broader labels when eligibility is unknown and reject explicitly impossible signatures.
- [x] Keep equal fully locked signatures ambiguous instead of choosing one by an opaque score.
- [x] Preserve simultaneous self/relative meanings when one native house maps to several derived-house frames.
- [x] Group one delivered native-house activation into subject-relevant bounded interpretation alternatives.
- [x] Add a versioned, complete 1–12 house-signification registry independent of event families.
- [x] Rotate every activated native house into every requested subject frame before selecting an event label.
- [x] Keep standalone house meanings broad; do not reduce the eleventh house to money or the sixth house to work.
- [x] Add a separate house-combination registry and require every house in a named combination to be activated.
- [x] Resolve named combinations only when every required house is simultaneously dasha-deliverable and transit-activated.
- [x] Return structured native-house and relative-house bases for every interpretation alternative.
- [x] Separate neutral house significations from supportive, mixed, challenging, and neutral outcome wording.
- [x] Attach tone, independent factor counts, carrier-based outcome rule, and tone-conditioned interpretation to every alternative.
- [x] Derive one de-duplicated carrier-based outcome for a shared activation cluster without family-specific conflict evidence leaking across frames.
- [x] Preserve shared activation polarity through every self/relative rotation; derived-house identity cannot flip the tone.
- [x] Separate sixth-house health/workload/debt/dispute meanings rather than defaulting to work pressure.
- [x] Add financial-pressure/obligation separately from income/gains.
- [x] Add a safety-limited eighth-house shared-resource/change interpretation without death or lifespan claims.
- [x] Reject unresolved candidates in `parashari_fomo_v1`; never fill the requested quota with weaker themes.
- [x] Include resolution, signature-registry, taxonomy, profile, and schema versions in reproducibility signatures.
- [x] Add tests proving that vargas cannot create events, carriers cannot be mixed, missing vargas do not veto core events, and equal locks remain ambiguous.
- [x] Add a regression test for one native second-house activation resolving to self-finance, spouse-eighth, and father-sixth alternatives.
- [x] Extend that regression to mother-eleventh meanings and verify gains, goals, recognition, networks, and elder-sibling possibilities remain available.
- [x] Add a test proving 2+11 financial accumulation is not emitted when only house 2 is active.
- [x] Add regressions proving mixed/challenging eleventh-house activation cannot emit unconditional positive-income wording.
- [ ] Obtain manual astrologer sign-off on each registered signature and its divisional convention.
- [ ] Add manually verified golden charts for every event signature.

### Phase 6A exit gate

- [ ] Every displayed candidate resolves through natal house connection, cooperative MD–AD–PD delivery, and a relevant transit trigger; all strength, varga, yoga, and manifestation rules have manual sign-off and golden-chart coverage.

## Phase 6B — Whole-chart manifestation resolver

- [x] Add a reusable `ChartManifestationResolver` behind an explicit versioned contract.
- [x] Match only registry-defined multi-house signatures; do not enumerate arbitrary signification permutations.
- [x] Require every core house to be dasha-deliverable and transit-activated in an overlapping MD–AD–PD window.
- [x] Derive direct carriers independently for every required house.
- [x] Accept a combination only when the houses share a direct carrier or their direct carriers have a declared natal sambandha.
- [x] Reject unrelated carrier unions.
- [x] Rotate signature houses through self, mother, father, and spouse frames while preserving native-house identity.
- [x] Require a relative's native anchor house or natural karaka to join the same delivery chain before emitting a mother, father, or spouse manifestation.
- [x] Treat the event-defining house as the weakest link so its challenging tone cannot be averaged into a supportive result.
- [x] Merge repeated planet factors without counting friendship or correlated special conditions as independent votes.
- [x] Rank deterministically by current timing, carrier coherence, activation reinforcement, and registry priority.
- [x] Dominance-prune repeated adjacent windows and retain one strongest card per subject/signature.
- [x] Return bounded alternatives, house roles, timing, carriers, coherence, factors, and reproducible rationale.
- [x] Expose named synthesis-evidence bands rather than a percentage or statistical probability.
- [x] Add focused tests for shared carriers, connected carriers, unrelated carriers, subject rotation, tone protection, and deterministic IDs.
- [x] Add House Activations and Chart Manifestations tabs to web, app, and PWA.
- [ ] Obtain manual astrologer sign-off on every chart-manifestation signature and role definition.
- [ ] Add golden-chart fixtures for every subject/signature combination.

### Phase 6B exit gate

- [ ] Every shown chart manifestation has a manually validated signature and golden-chart example in addition to its deterministic carrier and timing proof.

## Phase 7 — Deterministic teaser presentation

- [ ] Create a presentation adapter separate from calculation and policy.
- [ ] Define deterministic templates by subject, event family, tone band, and time band.
- [ ] Generate a title, teaser, date band, and suggested editable question without an LLM.
- [ ] Keep the unrevealed outcome out of the teaser.
- [ ] Avoid exact promises and certainty language.
- [ ] Avoid fear, threats, coercion, and loss-framed conversion tactics.
- [ ] Support localization without changing prediction evidence.
- [ ] Return fallback copy when a translation is unavailable.
- [ ] Add snapshot tests for every template family and supported language.
- [ ] Review copy for clarity, repetition, and inappropriate specificity.

### Phase 7 exit gate

- [ ] Every eligible candidate produces safe, deterministic, localized teaser content with no LLM call.

## Phase 8 — Persistence, caching, and APIs

- [ ] Add a `parashari_prediction_snapshots` migration.
- [ ] Store user, chart, calculation/profile versions, horizon, evidence signature, candidates, creation time, and expiry.
- [ ] Add ownership-preserving birth-chart deletion behavior.
- [ ] Add retention rules for expired snapshots and large evidence payloads.
- [ ] Add a `parashari_prediction_funnel_events` migration.
- [ ] Support idempotent `shown`, `opened`, `dismissed`, `question_prefilled`, `question_sent`, and `answer_completed` events.
- [ ] Add `credits_purchased` attribution only if product policy later requires it.
- [ ] Add repository implementations using the existing database abstraction.
- [ ] Add an authenticated endpoint to fetch eligible homepage teasers.
- [ ] Add authenticated impression, open, dismiss, and question-send endpoints.
- [ ] Verify user and birth-chart ownership on every endpoint.
- [ ] Never return the complete private evidence ledger to the homepage client.
- [ ] Cache by chart hash, as-of date, horizon, profile version, provider versions, and ephemeris settings.
- [ ] Invalidate cache when birth data, calculation version, profile, or relevant timing boundary changes.
- [ ] Add request timeouts, payload limits, structured logs, and metrics.
- [ ] Make the API return quickly from cache and support background generation on a miss.

### Phase 8 exit gate

- [ ] API authorization, caching, invalidation, idempotency, deletion, and failure-path integration tests pass.

## Phase 9 — Trusted click-to-chat explanation

- [ ] Extend normalized `query_context` to preserve a server-issued teaser/candidate ID.
- [ ] Open chat with the candidate's suggested question prefilled and editable.
- [ ] Keep the selected candidate ID until that question is sent or abandoned.
- [ ] Resolve the candidate ID server-side and verify user/chart ownership and expiry.
- [ ] Load the original deterministic evidence snapshot on the backend.
- [ ] Feed the verified evidence into the existing Parashari chat pipeline.
- [ ] Instruct the LLM to explain the supplied candidate rather than invent a new event.
- [ ] Prevent the LLM from naming unsupported dasha chains, aspects, houses, or dates.
- [ ] Handle an expired or invalid candidate by recalculating or giving a clear recoverable response.
- [ ] Record question-sent and answer-completed funnel events idempotently.
- [ ] Add tests for altered client context, another user's candidate ID, deleted charts, expired snapshots, retries, and duplicate sends.

### Phase 9 exit gate

- [ ] A clicked teaser always resolves to the same server-owned evidence and produces an evidence-grounded chat request.

## Phase 10 — Homepage app/PWA experience

- [ ] Add the event teaser to the existing one-prompt-per-home-visit arbiter.
- [ ] Confirm priority after critical notices and the first-free-question prompt.
- [ ] Do not independently open a modal that competes with existing home prompts.
- [ ] Add a bottom sheet with up to three ranked, non-duplicative tiles.
- [ ] Show loading only when useful; never block homepage interaction while calculating.
- [ ] Add empty, unavailable, stale, and calculation-error states.
- [ ] Add “Not now” and “Don't show these” controls.
- [ ] Apply a configurable 5–7 day display cooldown.
- [ ] Allow an earlier display only when the evidence signature changes materially.
- [ ] Record an impression only when the sheet/tile was actually visible.
- [ ] Open standard chat and prefill the suggested question when a tile is selected.
- [ ] Preserve first-free-question Standard-mode behavior.
- [ ] Verify responsive layout, scrolling, safe areas, dark mode, accessibility labels, and keyboard navigation.
- [ ] Add localization keys for every visible string.
- [ ] Test Android app and installed PWA separately.

### Phase 10 exit gate

- [ ] End-to-end tests cover eligibility, cooldown, display, dismissal, tile click, question editing, send, and returned answer on app and PWA.

## Phase 11 — Safety and product policy

- [ ] Block death and lifespan teasers.
- [ ] Block accident, violence, crime, and legal-ruin teasers.
- [ ] Block severe illness and medical-outcome teasers.
- [ ] Block pregnancy, miscarriage, and fetal-sex teasers.
- [ ] Block guaranteed financial gain/loss and financial-ruin teasers.
- [ ] Block infidelity and factual accusations about relatives.
- [ ] Block deterministic certainty and exact-outcome claims.
- [ ] Add safe redirection rules for blocked candidate families.
- [ ] Add a user-level opt-out that is honored across devices.
- [ ] Add admin kill switches for the feature, profile, subject, domain, and individual provider.
- [ ] Log policy suppression without storing unnecessary sensitive copy.
- [ ] Review the final copy and interaction for manipulative dark patterns.

### Phase 11 exit gate

- [ ] Automated prohibited-domain tests and a manual safety review pass before any external rollout.

## Phase 12 — Validation and calibration

- [ ] Create golden-chart fixtures with manually verified natal facts.
- [x] Create fixed synthetic calibration fixtures with deterministic output and candidate-density invariants.
- [ ] Create boundary fixtures for dasha and transit changes.
- [ ] Validate relative-house rotations independently.
- [ ] Validate every provider's evidence against source calculator output.
- [x] Validate that a non-carrier adverse factor does not change event tone or activation.
- [x] Validate that repeated evidence is not double-counted.
- [x] Validate stable output ordering and signatures.
- [ ] Add performance benchmarks for cold and cached generation.
- [x] Add candidate invariants for dates, primary houses, carriers, diversity, and strong transit reinforcement.
- [ ] Create an internal trace viewer or structured admin output.
- [ ] Run shadow predictions without displaying them to users.
- [ ] Manually review a diverse chart set and record false-positive patterns.
- [ ] Compare engine candidates with current Event Timeline and chat timing outputs without treating LLM agreement as ground truth.
- [ ] Calibrate thresholds only from recorded evidence and review results.
- [ ] Freeze `parashari_fomo_v1` rules before rollout.

### Phase 12 exit gate

- [ ] Accuracy, stability, latency, safety, and explainability thresholds are documented and approved for rollout.

## Phase 13 — Observability and operations

- [ ] Add metrics for generation attempts, duration, cache hits, failures, empty results, and provider errors.
- [ ] Add funnel metrics for eligible users, impressions, opens, dismissals, questions sent, answers completed, and opt-outs.
- [ ] Segment metrics by profile version, platform, language, subject, and event family without exposing private chart facts.
- [ ] Add alerts for error-rate, latency, empty-result, and funnel anomalies.
- [ ] Add structured trace IDs linking snapshot, candidate, API request, and chat request.
- [ ] Add snapshot/profile version visibility to admin diagnostics.
- [ ] Add cleanup monitoring for expired snapshots and funnel retention.
- [ ] Document rollback, kill-switch, and cache-purge procedures.
- [ ] Ensure prediction generation cannot degrade core chat availability.

### Phase 13 exit gate

- [ ] Operators can identify, disable, and diagnose a faulty provider/profile without redeploying unrelated features where practical.

## Phase 14 — Rollout

- [ ] Add backend and frontend feature flags.
- [ ] Enable only for internal users first.
- [ ] Run internal app/PWA smoke tests with several charts and languages.
- [ ] Review traces for every internally opened teaser.
- [ ] Roll out to a small cohort.
- [ ] Compare question-send rate against dismiss, opt-out, and complaint signals.
- [ ] Confirm no measurable regression in homepage or chat latency.
- [ ] Increase cohort gradually only after safety and reliability checks.
- [ ] Record the deployed engine, profile, provider, frontend, and API versions.
- [ ] Add the user-facing feature to the appropriate release tracker only when the release version is selected.

### Phase 14 exit gate

- [ ] The feature is generally available with acceptable reliability, safety, performance, and funnel quality.

## Phase 15 — Additional consumers

- [ ] Create an Event Timeline presentation adapter backed by deterministic candidates.
- [ ] Evaluate replacing or supplementing LLM-generated Event Timeline selection.
- [ ] Create a push-notification eligibility adapter with stricter frequency and safety rules.
- [ ] Create daily/monthly prediction adapters.
- [ ] Create reusable report context.
- [ ] Create admin preview/debug tooling.
- [ ] Keep consumer wording and disclosure policy outside the prediction engine.
- [ ] Verify all consumers reference the same candidate/evidence contracts.

## Checklist for every future evidence provider

- [ ] Document the classical rule and intended interpretation.
- [ ] Assign a stable provider ID and semantic version.
- [ ] Declare required primitive inputs.
- [ ] Return normalized evidence rather than final prose.
- [ ] Keep activation and tone contributions separate.
- [ ] Define `not_available` behavior.
- [ ] Add deterministic unit and boundary tests.
- [ ] Add golden-chart verification cases.
- [ ] Add the provider only to an experimental profile first.
- [ ] Include it in cache and evidence signatures.
- [ ] Run shadow comparisons before changing a production profile.
- [ ] Version the production profile when enabling it.
- [ ] Document rollback and compatibility implications.

## Bhrigu Bindu future-provider checklist

- [ ] Confirm the exact Bhrigu Bindu calculation convention to support.
- [ ] Implement it as a calculation primitive with boundary tests.
- [ ] Define natal and transit relations that qualify as evidence.
- [ ] Decide whether it contributes to activation, tone, timing, or more than one dimension.
- [ ] Prevent overlap with already-counted Rahu/Moon evidence.
- [ ] Add `BhriguBinduProvider` behind an experimental profile.
- [ ] Validate on golden charts before enabling it in a production profile.

## Final definition of done

- [ ] The core engine produces deterministic, reproducible and traceable candidates without an LLM.
- [ ] Every candidate explains its houses, planets, timing window, activation strength, and outcome tone.
- [ ] New providers can be added without modifying engine orchestration.
- [ ] Homepage teasers reveal curiosity-oriented copy but not unsupported outcomes.
- [ ] Chat explanations use the exact trusted evidence behind the clicked teaser.
- [ ] App/PWA funnel, opt-out, safety, performance, and operational controls are live.
- [ ] Documentation, tests, migrations, monitoring, rollout record, and rollback procedure are complete.
