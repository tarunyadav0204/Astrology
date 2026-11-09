# Your Next Chapter

The prediction engine now has a customer-facing interactive reading on mobile and
web, alongside the admin-only preview. Neither event-timeline version is replaced.

## Customer experience

Next Chapter uses Gemini 3 Flash independently of the monthly/yearly timeline model
setting, with no fallback to Pro. Coverage batches start as soon as their own PD
plans finish; they do not wait for unrelated planners. Chapter-spectrum generation
runs alongside section writing. The event-quality review and first factual-review
batches run together. Section repairs remain parallel, followed by review of the
repaired draft. Cross-chapter editing still waits for all plans, and corrections
still wait for review findings. Audit records distinguish provider time from time
waiting for a concurrency slot. The model change applies to newly started workers;
an already running generation keeps its existing model instance.

Web route: `/next-chapter`. Mobile route: `NextChapter`. Entry points include
Profile, Ask Tara and home/readings navigation. Users select an owned birth chart
and English or Hindi, preview the upcoming Antardasha dates, then confirm the
displayed credit price. The default is 49 credits; Admin's `next_chapter_cost`
and existing discount rules take precedence. Reopening a purchased chapter is free.

The reading includes an overview, nine selectable Pratyantardasha phases,
specific possibilities, timing windows, expandable reasoning and a saved library.
Progress reflects processing stages and explains that users can leave and return.
The screens inherit the active native instead of asking users to choose again.
Mobile uses the existing NativeSelectorChip and SelectNative screen; web uses the
shared navigation header's native picker. Purchase confirmation immediately opens
the progress view. Percentages are weighted completed planning/writing/review work,
not estimated time remaining, and reach 100 only when the saved report is complete.
Status polling is sequential and uncached, refreshes on return, and shows a
connection warning when status cannot be obtained. Failure/refund replaces progress.
Failed jobs refund their charged credits. Mobile interface copy covers all eleven
supported locales; report generation supports English and Hindi. Web uses the
existing theme modal and mobile uses ConfirmCreditsModal.

Completed chapters now offer a translated Create a chapter reel entry on mobile and web.
It reuses Reel Studio language/style selection, Admin credit pricing, confirmation,
progress, saved playback/recreation, and reel history. A stable owned negative source
ID links each chapter to the existing reel cache without creating chat messages.
The planner receives the complete report and period calendar and creates a concise
summary across the chapter, preserving uncertainty. An edited birth chart requires
a refreshed chapter before generating a new reel. Reel generation is charged separately. Per the user's request, the
latest UI changes have not been run through UI tests or builds, pushed or deployed.

## Selection and timing

1. Use the shared Vimshottari calculator and bundled Swiss Ephemeris under Lahiri/mean-node settings.
2. Find the currently running AD at the requested timezone-aware instant. Select the **next scheduled AD**, even when it begins more than a year away. Do not silently substitute the current AD or a generic 90-day forecast.
3. Use the MD that contains that next AD. A new MD is selected only when the next AD crosses the current MD boundary. There is no invented “soon” cutoff.
4. Include all nine PDs, preserving the app’s date conventions. Intervals are half-open. The final AD closes at its parent MD transition and the final PD closes at its parent AD boundary because the shared calculator mixes calendar-year MDs and 365.25-day subdivisions. Any AD correction is exposed as `parent_boundary_adjustment_seconds`; mismatches larger than one day fail rather than being hidden.
5. Keep the MD background, AD themes and changing PD emphasis separate.

## Natal foundation

`charts.house_insight_service.build_natal_insight_bundle` shares the same house and planet worksheets used by the ChartScreen drawer. One HouseAnalyzer instance supplies all twelve houses and nine dasha planets.

The dossier retains dignity and functional nature, Shadbala/components, friendship, combustion and its distance/threshold, retrograde motion, Neecha Bhanga conditions, aspects, Gandanta, special lordships, Yogi/Avayogi and other points, SAV/BAV, Argala/Virodha, natural/Chara karakas and the drawer’s related divisional-chart worksheets. Current-day drawer activation is excluded from future prediction evidence. Nodes have no classical Shadbala value, rather than a misleading zero.

The implementation also fixes the drawer’s SAV/BAV adapter: calculator bindus are indexed by sign and must be mapped into houses. SAV sums the seven planetary BAVs; Lagna BAV is kept separately. Missing required SAV/BAV or strength evidence fails calculation instead of supplying invented values.

## Activation and multiple possible outcomes

Each MD/AD/PD exposes occupation, lordship and natal graha drishti as direct links. Sign-dispositor and nakshatra-lord links remain explicitly indirect. Pairwise dasha relationships include conjunction, directed aspects, dispositorship, exchange and the same lord operating at multiple levels.

House significations and combinations come from the existing prediction-engine catalog. They are examples, not a gate selecting one predetermined event. The LLM may explain several plausible manifestations, tied to the calculated house/planet evidence and any known life context. There is no forced event quota, probability score or “all these events will happen” claim. The report must explain what changes in each PD instead of repeating the same AD-wide predictions.

The model packet retains catalog labels, house meanings and combination mappings but removes
the catalog's prewritten `possibilities` phrases. Live review showed those fragments being
copied into multiple periods. The complete original catalog remains in the calculation
dossier; the planner must derive concrete conditional possibilities from the evidence.

## Transit engine

For each PD, inspect MD/AD/PD lords plus Sun, Jupiter, Saturn and the lunar nodes. Retain:

- Natal-house occupancy and whole-sign aspects, with sign/nakshatra boundaries refined from six-hour screening.
- Relations to the natal signs and nakshatras of the active dasha planets.
- Exact conjunction and graha-drishti degree contacts to active natal lords, including each lord’s own return and Sun triggers.
- A declared ±1° orb; the orb is an interpretive convention, not a calibrated probability.
- Station-aware refinement, preserving direct/retrograde repeat crossings and in-orb approaches without falsely labelling them exact crossings.
- Windows clipped to the PD. Boundary-clipping flags distinguish them from a complete orb entry/exit.
- Overlapping contacts from different transiting planets as reinforcement windows. Two contacts from the same planet do not become two independent votes.

Numerical roots are refined to one second. That is astronomical calculation precision, not life-event certainty. Next Chapter uses the classical planet aspect table with an explicit node override: Rahu/Ketu have only the seventh aspect; conjunction is separate. The override applies to natal activation, received aspects in the shared worksheets, transit house aspects and exact contacts. Other ChartScreen consumers retain their existing default convention. KP cusp timing, Chara Dasha and Nadi-specific timing are not calculated in this version and must not be claimed by narration.

## Run locally

From `backend`, provide a JSON file containing `name`, `date`, `time`, `latitude`, `longitude`, `timezone` and optionally `gender`/`place`:

```sh
.venv/bin/python -m next_chapter.preview \
  --birth-json /absolute/path/birth.json \
  --as-of 2026-11-08T12:00:00+05:30 \
  --out storage/next_chapter/my-preview
```

This writes `evidence.json` and `preview.html`, with no provider call. Add `--narrate --language en` or `--narrate --language hi` to call Gemini 3 Flash (`models/gemini-3-flash-preview`), the dedicated Next Chapter model. That writes `report.json` and includes its interpretation in the HTML. Provider charges apply; returned usage records the actual model/vendor/input/output tokens. Preview artifacts are ignored by Git.

The narration contains an overview, MD context, structured AD-wide event possibilities, complete MD/AD transit sequences, and all nine PDs with changing emphasis, possible manifestations, explanations and practical guidance. Code validates coverage and evidence references and attaches dates from the dossier. It does not apply the newer timeline’s restrictive event-selection rules. No fabricated fallback narrative is returned on calculation or generation failure.

## API preview

`POST /api/next-chapter/preview`, with the normal bearer token of an admin:

```json
{
  "birth_chart_id": 123,
  "as_of": "2026-11-08T12:00:00+05:30",
  "language": "en",
  "narrate": false,
  "life_context": "Optional facts supplied by the native"
}
```

The saved chart must belong to that admin. Default requests calculate evidence only. One preview is admitted per worker; additional concurrent requests receive 429. This route does not spend customer feature credits or expose the preview to non-admin users.

## Review before customer rollout

Review actual report breadth, redundant themes, dasha conventions, node-aspect/orb conventions, and factual grounding on several charts. After that review, add the customer UI, pricing/credit lifecycle, persisted report cache/history and reel conversion. The preview has no claim of empirically validated event probabilities.

## Validation notes

The focused Next Chapter pipeline/calculation, house-insight, transit-return, aspect and functional-nature suite currently passes 80 tests. A separate legacy cascading-dasha date test has an existing order-dependent one-day discrepancy: it passes alone but fails after the existing house-insight tests initialize the bundled ephemeris. This also reproduces without any next-chapter tests. Next Chapter explicitly initializes the bundled ephemeris before dasha calculation, and its regression test checks that dates remain the same before and after chart calculation. The older shared calculator's global initialization behavior remains a separate issue.

An earlier real-chart review found a second inconsistency: `PlanetAnalyzer` used node aspects 3/11 while ChartScreen used 5/7/9. Next Chapter now explicitly selects seventh-only nodes as described above. It now delegates to the canonical aspect table and excludes display-only outer planets from its classical aspect analysis. This removes contradictory aspect testimony from the shared planet worksheets.

Narration now receives an explicit natal summary (including degree separation of same-sign companions), merged slow-planet house intervals, and timestamps already converted into the birth location's timezone. Detailed nakshatra intervals and raw UTC contacts remain in the calculation dossier. Merging preserves all sign transitions, including retrograde returns; it only removes repeated nakshatra splits within the same sign. This addresses drafts that ignored slow-planet house changes or used UTC dates in local narration.

Local real-chart review artifacts are under the ignored `backend/storage/next_chapter/` directory. A review-only calculation audit checks placements, lordships, shared aspect agreement, dasha proportions, Ashtakavarga sums, transit occupancy and exact contact residuals through direct Swiss Ephemeris calls and separately expressed formulas. This checks implementation consistency; it is not an independent ephemeris vendor or a validation of future event accuracy. That initial manually edited artifact remains preserved for comparison. The staged runtime below now performs its own editorial and factual reviews; its delivered output is not manually rewritten.

A real generation placed its existing closing paragraph inside a tenth singleton `periods` entry. The response adapter now relocates only that exact shape, preserving the text and all nine periods. It does not invent missing content or discard an extra period. A regression test covers both relocation and rejection of ambiguous shapes.

## Staged generation (v3)

The admin narration entry point now uses `next_chapter.pipeline`. It builds fact packets
from the shared house drawer calculations, excluding the drawer's canned predictions,
heuristic effect scores and duplicate aspect geometry. Planet aspects and separations
come from the canonical natal chart. SAV, individual planet BAV contributions, divisional
house worksheets and their domain limits remain explicit.

1. Nine planning requests each cover one PD and can run together, with up to ten model requests per report. Plans
   include concrete alternative manifestations, circumstances, support/counter-evidence,
   timing references and explicit AV/divisional assessments.
2. A chapter editor sees all nine plans, separates recurring MD/AD themes from changing PD
   emphasis and gives specific revision instructions. It does not impose an event quota.
3. Three concurrent writing requests produce the customer prose. Dates and evidence links
   are attached by code; source references cannot cross into another PD's contacts.
4. A dedicated event-writing review checks the full report for vague topic fragments,
   missing supported branches and statements that cannot be compared with observable events.
   Its notes feed the same targeted repairs; it does not assert which events will occur.
5. Three focused model reviews cover the chapter introduction and all nine PDs, checking natal facts, local dates, contact types,
   SAV/BAV mapping, varga scope, unsupported certainty, assumed circumstances and language.
   Each reported factual defect must quote existing text. Material quality findings receive at most two targeted editorial passes; remaining subjective observations are advisory.
6. Only affected PDs/chapter fields are repaired, followed by another complete set of focused reviews.
   At most two section-repair rounds and one structural repair per call are allowed. If
   factual issues remain, one final quote-only patch may replace exactly the reviewer-cited
   spans, followed by a complete factual review; it cannot rewrite unrelated prose. An
   unresolved factual error still prevents release; there is no fabricated fallback narrative.

This is **model-assisted factual review, not a mathematical guarantee of prose accuracy or
an empirical validation of predicted events**. The feature remains admin-only. The existing
monthly/yearly timeline selection and customer credit flows are unchanged.

The local CLI writes `generation-audit.json` incrementally, including failed responses,
repair calls, provider usage (including thinking/total when supplied), stage durations,
prompt hashes, plans and review findings. Unknown usage stays unknown, not zero. Concurrent
requests are all awaited on failure so paid calls are not silently abandoned. These artifacts
contain private birth/report data and stay under ignored `storage/next_chapter/`.

Before customer launch, run blinded historical reports using only context known at the
forecast cutoff, obtain actual dated outcomes separately, and record misses as well as hits.
Assess factual correctness, distinguishability of PDs, readable Hindi/English, and usefulness
across different ascendants, life circumstances and MD changes. Do not infer an event-hit
rate from an impressive sample or convert astrological strength into probabilities.

Local review can resume with `--resume-audit path/to/generation-audit.json`. Only responses
whose model, vendor, stage and exact prompt hash match are reused, and current validators
run again. Reused stages record zero *new* provider usage and retain source usage separately;
this must not be interpreted as free original generation. Different chart data, language or
prompts cause fresh requests. Complete alternate JSON wrappers and correctly identified
background timing references are relocated without inventing facts or discarding sections.

The model output budget includes room for reasoning as well as JSON. Finish reasons and raw
responses are recorded so a truncated response is distinguishable from invalid references.
Neither malformed nor unresolved factual output is exposed as a finished customer report.

Each batch foregrounds the active MD/AD/PD conditions and the PD planet's own BAV contributions at its directly activated houses. This keeps mixed lordship, special roles and received aspects visible alongside strength, without inventing a favorability score.

Divisional reference IDs use the source natal house number, not the divisional chart number.
Writers must read the worksheet's explicit name and house: for example, a ninth-house
reference may contain D20 evidence, not D9. A single worksheet cannot establish the verdict
of an entire divisional chart. The writer retains relevant numeric evidence and qualifications
while explaining it in ordinary language; low scores must not become diagnoses or instructions
to make financial decisions.

Successful audits preserve the reviewed report as a checkpoint. Review-only policy changes can resume from that corrected text only when all planning/editing/writing stages match their exact model and prompt hashes and the current report contract validates. A changed chart, language or upstream prompt invalidates the checkpoint. This prevents a new review from resurrecting defects in the original draft.

The earlier staged-v2 local English review covered all nine PDs with no manual prose edits. It passed 917 calculation-consistency checks and the final model review reported no factual issues, with one advisory wording note retained in its audit. It has no verbatim repeated possibility sentences; this is not a semantic-uniqueness or event-accuracy score. A full cold generation took about 6.5 minutes on the configured model during this review, including targeted repairs. Live Hindi output and multi-native historical outcome validation are not established by that English sample.

## Event spectrum and transit revision (staged_v3)

The model receives full house significations, separate body correspondences, and specific
nonfinancial vocabulary such as occult studies, astrology, investigation and insurance payouts.
These are candidate domains to assess, not predetermined outcomes or a quota to fill.
Prewritten catalog prediction sentences remain excluded. Each PD includes a house-coverage
packet with natal links and explicit transit references, including transit-only activated houses.

The first writer receives all nine plans to produce `antardasha_events` before the PD breakdown.
Each event group contains circumstances, observable alternatives, supporting/counter-evidence,
and broad timing. `antardasha_transits` must explain every merged AD-lord sign/house interval;
`transit_story` must cover that lord's segments within each PD. Natal relationships are attached
to the transit facts so a broad seventh aspect to a natal position is not lost merely because
no exact degree crossing occurs in that PD. House number and aspect number remain distinct.
All structured chapter fields participate in review, targeted repair and resume validation.

The preview renders the AD event spectrum and transit sequence ahead of the nine PDs, with
a separate AD-lord transit explanation inside each PD. Original review artifacts remain intact.
The node convention is a declared interpretation choice, not a claim of classical consensus.
Body-part significations never establish a diagnosis or a need for treatment; low point scores
alone must not generate medical predictions. Financial possibilities do not justify investment
or debt directives. Broad event lists still require real-outcome feedback; breadth is not accuracy.


## Concurrent combination synthesis (staged_v4)

`next_chapter/synthesis.py` constructs half-open windows at every active MD/AD/PD
lord's sign/house transition. Each window exposes simultaneous natal occupation,
lordship and aspect sources and transit occupation/aspect sources. Dispositor and
nakshatra links retain their indirect status. Repeated roles of one planet share one
physical transit; other slow movers remain separate background evidence.

All co-active house pairs and triples are enumerated as a search space, without using
the legacy event catalogue as a whitelist. The model assesses those, coherent larger
clusters and single-house branches. Meaningful alternatives must state which
significations combine, their activation sources and concurrent windows, a selected/
merged/unsupported decision, and supporting or limiting reasons. Every planned theme
maps to a selected or merged route. This ledger is preserved in the generation audit.
Mechanical permutations are not predictions and no event count is imposed.

Plans explicitly assess natal and transit evidence at each MD/AD/PD level. Validation
rejects routes with unknown sources, unsupported house membership or nonconcurrent
transit sources. The chapter packet includes both MD and AD transit sequences; each
PD's transit explanation covers all active lords (brief fast-planet cycles may be grouped).
The whole-report event review checks for selected routes lost during writing, repetitive
AD themes and missing supported branches beyond money and work.

Structural coverage is auditable; it does not prove that an LLM has exhausted every
semantic possibility or that any predicted event will occur. Review outcomes separately.

A separate coverage editor reviews the nine initial plans in three batches before prose.
It revisits unjustified exclusions and explicitly prevents treating MD/AD natal aspects as
indirect or requiring a PD-specific activation for every event. Continuing MD/AD-supported
possibilities remain available to the AD spectrum; new PD timing still needs its own evidence.
Only model-produced plan fields are revised, with source/concurrency validation reapplied.

Known activation-source citations resolve to their canonical planet facts. If an exploration
route omits a citation for a listed house, code can attach only calculated direct period-lord
sources available throughout every cited window, preserving `resolved_source_ids` and the
original model response. A house without such support, unknown source or nonconcurrent
transit still fails. This resolves references; it does not create events or change prose.
Exact successful structural repairs can be reused on resume using the original prompt hash,
with revalidation and original usage retained; failed or interrupted call costs remain visible
or explicitly unknown rather than being counted as free.

A dedicated whole-AD writer then receives all nine reviewed plans and supplies an explicit
map from every selected PD event family to its AD overview group. This avoids allowing the
first three PDs to dominate the introduction. Materially distinct branches survive grouping;
PD-specific possibilities retain their phase qualification.

Each preview PD includes expandable natal and transit evidence tables for all active
MD/AD/PD lords, including occupation, lordship, aspects, signs and local date intervals.
A resume may preserve corrected prose from either a completed checkpoint or an unreleased
review, but only after every upstream prompt matches and the current contract validates.
Unreleased prose still undergoes the complete review before release.

Review addresses that name an existing chapter field resolve to the chapter section before
validation. Exact quotations, evidence references and full review coverage remain mandatory;
unknown addresses or invented quotations still fail. This avoids paid repair calls for an
unambiguous field-versus-parent naming difference.


## Curated Reel Studio entry

Mobile `ReelStudio` and web `/reel-studio` offer six launch topics, filtered collections,
a featured relationship story and the saved reel library. They use the active chart
and the existing reel setup/credit confirmation; no generation is charged on a card tap.
Five evergreen topics prepare a dedicated chart-grounded reading inside the metered
reel planning session (`studio_reading`). My Next Chapter opens the existing chapter
experience, followed by its reel conversion. Its report and reel prices are shown
separately. Prices come from the existing Admin reel and next-chapter settings.

Studio sources reserve IDs below -1,000,000,000, separate from positive chat message
IDs and the existing negative chapter IDs. The owned chart fingerprint and topic
identify a stable cached source. Edited charts create new sources; stale sources
cannot create new reels. Model reading usage, image, speech, presenter and render
usage remain in the existing reel cost ledger. New catalogue copy covers all eleven
app locales, while reel output remains Hindi/English. No builds or generation tests
were run for this addition, at the user's request.
