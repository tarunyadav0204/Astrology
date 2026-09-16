# Event Timeline Accuracy V3

V3 is a reversible deterministic event resolver. It preserves V2's requested-year dasha and transit calculations while replacing LLM-selected single-house stories with a multi-house activation graph.

## Natal promise and delivery layer (V3.7)

V3.7 adds a second deterministic judgment after an event combination passes the activation graph:

- D1 natal promise checks event-house lords, relevant karakas, occupation/aspect, conjunction, exchange, dispositor links, and repetition from the Moon.
- MD/AD/PD delivery checks each active carrier's occupation, lordship, aspect, dignity, dispositor, conjunctions, retrogression, and the Rahu/Ketu dispositor–nakshatra chain when those inputs exist.
- Event activation is separated from obstruction, outcome, permanence, and completion. An active topic is therefore not automatically described as a favourable completed event.
- KP inspects cusp sub-lord permission and the active carrier's planet→star→sub→sub-sub significator chain. The relevant varga checks its own ascendant, house lords, carriers, karakas, dignity, and D1 repetition.
- Candidate timing is split at the day boundaries already present in dasha and transit evidence. It is explicitly labelled sign/nakshatra/pada-level until exact applying/exact/separating contacts and stations are exposed upstream.

## Integrated calculator layer (V3.8)

The default is now `EVENT_TIMELINE_V3_ACCURACY_LAYER=integrated_v2`. It retains V3.7's natal-promise and carrier-delivery judgments and additionally uses:

- daily longitude contacts to natal event lords/karakas, Lagna, Moon, and KP anchor cusps, with applying/exact/separating phase, retrograde passes, and direction-change stations;
- planet-specific Prastara Bhinnashtakavarga and Kakshya bindus as ease/timing modifiers only;
- Chara, Yogini, Kalachakra, Sudarshana, and the available Varshaphal subset as capped comparison groups;
- birth-time provenance and a boundary sensitivity run for Lagna, Moon nakshatra, relevant varga ascendants, KP cusp sub-lords, and the Vimshottari stack.

These systems cannot open an event by themselves. Correlated systems are grouped and counted once, the combined supporting-system adjustment is capped, and exact contacts use daily samples rather than claiming an intraday root.

Set the accuracy layer to `delivery_v1` to roll back to V3.7, or `legacy_v3_6` to roll back again to V3.6. The selected layer remains part of the cache fingerprint. The repository's current Varshphal calculator supplies a solar-return chart, Muntha, a year-lord field, and Mudda Dasha; it does not supply Panchavargiya Bala, independently selected Varshesha, Sahams, or Tajika aspects, so V3.8 labels it `solar_return_subset` rather than presenting it as complete Tajika judgment.

Weak natal promise restricts wording to a broad theme; unavailable D1 data does not fabricate denial. Grade A/B now requires usable natal promise and non-obstructed active-planet delivery in addition to the earlier dasha/KP/varga criteria. These are internal astrological support grades, not empirical probabilities.

## Engine selection and rollback

- Default: `accuracy_v3`
- Previous conservative engine: `EVENT_TIMELINE_ENGINE_VERSION=accuracy_v2`
- Original engine: `EVENT_TIMELINE_ENGINE_VERSION=legacy_v1`
- Unknown values fail safely to `legacy_v1`.
- Timeline caches are separated by engine version.
- V3 result caches are additionally separated by user facts, explanation contract, pipeline, and narrator mode.
- V3 result caches are also separated by publication mode and the V3.7 accuracy layer.

## Fast deterministic pipeline

The default V3 runtime is now:

- `EVENT_TIMELINE_V3_PIPELINE=optimized`
- `EVENT_TIMELINE_V3_NARRATOR=deterministic`

The optimized builder calculates only D1, classical house lordships, D2/D4/D7/D9/D10/D24/D30, D1 Sarvashtakavarga, requested-period Vimshottari/transits, and KP. It does not build the general chat context or serialize that unused payload. A monthly deep dive scans only its selected month.

Natal D1/vargas/SAV and KP are cached independently in each backend process by hashed calculation inputs. Running another year for the same birth chart reuses them and recalculates the year-specific dasha and transit evidence. Defaults are a 12-hour TTL and 128 entries; `EVENT_TIMELINE_V3_NATAL_CACHE_TTL_S` and `EVENT_TIMELINE_V3_NATAL_CACHE_MAX_ENTRIES` can override them.

Deterministic narration returns the resolver's curated prediction, explanation, scenarios, dates, and grades directly and does not initialize or call an LLM. To compare or roll back independently:

- Full previous context path: `EVENT_TIMELINE_V3_PIPELINE=legacy_context`
- LLM wording layer: `EVENT_TIMELINE_V3_NARRATOR=llm`

Pipeline and narrator modes are included in the V3 cache fingerprint. In a cold local January parity run, the optimized calculation took 0.81 seconds versus 20.24 seconds for the corrected full-context path, reduced the unused serialized context from about 802 KB to 117 bytes, and produced identical activation graphs and candidate fields. This is a development benchmark, not a production latency guarantee.

## Candidate ranking and publication (V3.3)

V3.3 keeps qualification and presentation separate:

- `qualified_candidates` retains every event family that passes the anchor, transition, and transit gates. Nothing is removed merely to make the screen shorter.
- `publishable_candidates` defaults to the strongest distinct life areas: up to five within twelve ranking points of the monthly leader, with at least three when at least three qualify.
- `background_candidates` carries the complete deterministic prediction, explanation, scenarios, timing, grade, and evidence for qualified events that were not shown as primary cards. Mobile keeps this section collapsed until requested.
- Closely related events compete within a life area on the primary screen, but remain separate in the qualified set.

The ranking is deterministic and auditable. Direct natal lordship/placement of an event's anchor weighs more than an aspect-only anchor. Transition activation, direct transit timing, outcome activation, a carrier bridging anchor and transition, multiple core dasha levels, KP, and the relevant varga add support. The ranking score orders candidates; it is not a probability.

Deterministic copy now changes with the activated transition route, outcome phase, relevant transit carriers, KP/varga confirmation, and Desh-Kaal-Patra label. This avoids repeating one generic template while retaining restrained, non-certain wording.

The annual `macro_trends` field is a separate whole-year synthesis, not a list of event-family labels. It ranks distinct life domains by recurrence and monthly strength, identifies genuine peak months only when the evidence is concentrated, describes result-producing versus developmental periods, and notes independent KP/varga support. Closely related cards contribute at most once per domain per month, preventing duplicate work or property events from dominating the year's summary.

## Deterministic languages (V3.6)

The mobile client sends its active interface language with generation and cache requests. Hindi (`hindi`, `hi`, or a `hi-*` locale) uses deterministic Hindi event labels, predictions, annual themes, scenarios, and astrological explanations. English remains the fallback for every other language. Language is part of the V3 cache fingerprint, so English and Hindi results for the same chart and period cannot overwrite or masquerade as one another. Translation changes presentation only; candidate IDs, calculations, ranking, timing, houses, grades, KP, and varga evidence remain identical.

Set `EVENT_TIMELINE_V3_PUBLICATION_MODE=exhaustive` to publish every qualified candidate exactly as the earlier V3 behavior did. The full qualified set remains available in both modes.

Exhaustive mode also bypasses V3.11's persistent-permission peak demotion. It is intended for debugging and comparison. Prioritized mode remains the product default.

## Calculation order

1. Calculate the target-year MD/AD/PD/Sookshma stacks and daily boundaries.
2. Calculate daily-scanned target-month transit segments.
3. For each active dasha planet, record natal lordship, natal occupation, natal aspect, transit occupation, and transit aspect channels.
4. Aggregate those channels into one graph for H1-H12. Preserve every planet, dasha level, mechanism, date range, and evidence ID.
5. Evaluate the existing Instant `EventDefinition` registry plus eligible subject-relative definitions. Natal MD/AD/PD channels normally open the anchor. In integrated V3.11, direct transit occupation by an active MD/AD/PD lord may supply persistent anchor permission when natal channels do not, but that same slow channel cannot time its own event.
6. Require a separate PD/Sookshma or faster-transit timing channel in transition/outcome houses whenever persistent transit permission was needed. Test actual date overlap, not merely presence somewhere in the same month.
7. Judge D1 natal promise and the delivery/pressure of the active MD/AD/PD planets.
8. Use the relevant divisional chart as an independent confirmation when available.
9. Use KP Placidus cusp sub-lords and planet significator chains as a separate event-family confirmation. Do not merge KP house coordinates into the Parashari graph.
10. Separate initiation, obstruction, result, permanence, and completion; split timing at evidence boundaries.
11. Apply Desh-Kaal-Patra to manifestation eligibility and wording.
12. Rank all qualified event families. Preserve recurring permission as background, keep only its strongest one- or two-month corridor eligible for primary display, and merge adjacent instances under one cross-month window ID.
13. Ask the LLM only to narrate the deterministic candidates. The validator restores omitted candidates and overwrites LLM dates, grades, evidence, and event-family labels with deterministic values.

## Explanation contract (V3.1)

- `Why` names the active MD/AD/PD stack, then lists the event-relevant houses each planet activates by natal lordship, natal placement, natal aspect, transit placement, and transit aspect.
- It explains how the anchor, transition, and outcome houses combine instead of exposing shorthand such as `dasha-open anchor H9`.
- It reports KP and relevant-varga confirmation honestly, including when either is unavailable or does not confirm.
- Possible scenarios are two distinct, curated real-life alternatives. Each reason names the houses, dasha levels, and transit planets supporting that alternative; it does not repeat the event title.
- Scenarios remain constrained by Desh-Kaal-Patra facts.

Set `EVENT_TIMELINE_V3_EXPLANATION_VERSION=legacy_v1` to restore the original compact V3 explanation layer. The explanation version is included in the cache fingerprint, so changing this flag does not reuse results generated under the other contract.

## Plain-language presentation contract (V3.13)

The visible event label, prediction, and scenario title are written for a general reader rather than an astrologer. They use short sentences and common words. Planet names, dasha levels, transits, house notation, KP, varga names, Ashtakavarga, scoring, and internal verdict labels are excluded from the prediction and retained inside the collapsed Why/evidence section.

Phase language is also translated into ordinary outcomes: a result window says there is a better chance of a clear result; a developing window says the matter may move forward but take more time; a preparatory window recommends planning; and obstruction is described as possible delay or difficulty. When a manifestation channel is not isolated, the card says that more than one event is possible instead of mentioning bhava or confidence machinery.

The same rule applies to People Around You. Relative cards say plainly whose event it is and use familiar phrases such as doctor visit, care at home, buying a vehicle, moving home, or making a relationship decision. The optional LLM narrator is validated against a technical-term filter; if it inserts astrology terminology into the visible prediction, the deterministic wording is restored. Full technical reasoning remains unchanged and auditable under Why.

## Prediction-strength presentation contract (V3.14)

The monthly screen no longer uses “Other qualified events” as a catch-all. In prioritized integrated V3, Grade A/B candidates selected for the month appear as **Main possibilities**. They are the clearest supported possibilities for that month, but the screen explicitly says they are not guaranteed outcomes. Grade C candidates do not become main cards.

Every omitted candidate receives one deterministic display tier and reason:

- **Also possible**: a Grade A/B event that remains credible but ranks below a clearer event, either because another event in the same life area is stronger or because it falls outside the month's primary set.
- **Ongoing theme**: a Grade A/B event continuing immediately before or after its independently timed peak.
- **Annual background**: broader Grade A/B permission outside a distinctive monthly peak. It remains auditable but is not repeated on monthly cards.
- **Weak signal**: a Grade C combination with incomplete or mixed confirmation. The UI explicitly tells the user not to treat it as a prediction.

The API exposes `display_tier`, `display_reason`, `display_explanation`, `display_tier_label`, and `support_label` on every rendered event. It also returns separate native and people-relative arrays for the secondary tiers. The earlier `background_candidates` and `people_background_candidates` fields remain as compatibility unions, carrying the same metadata, so older clients and frozen-forecast calibration continue to work without a schema migration.

User-facing support labels are **Strong indication**, **Moderate indication**, **Background indication**, and **Weak indication**, with Hindi equivalents. The internal A/B/C grade remains in the audit payload and frozen forecast but is no longer the primary language shown to users. All technical explanations remain collapsed under Why.

## Monthly timing lift and recurrence control (V3.15)

Static evidence answers whether an event is permitted during the broader period; it does not independently make the event a prediction in every month. Natal promise, MD/AD activation, KP, varga, and slow-transit permission therefore form the annual baseline. Monthly promotion requires finer timing evidence: an overlapping PD/Sookshma or independent fast-transit channel plus a close, event-specific Sun, Moon, Mars, Mercury, or Venus contact. Contact quality is scored from phase, orb, speed, and target relevance; only the strongest two contacts contribute materially, preventing a large noisy contact count from dominating.

Each subject/event family is compared with itself across the requested year. The strongest month becomes a peak. A second, non-adjacent peak is allowed only when its timing score is close and its fine-timing signature differs. Adjacent qualified months are labelled continuations and are not counted as new events. Other months retain annual permission in `annual_context_candidates` for audit and annual synthesis but are omitted from monthly cards and chips.

Prioritized mode no longer forces three events into every month. It may return a quiet month, and a peak month shows at most four distinct native life domains. Relative events use the same rule independently and remain grouped by person. Primary dates are narrowed to the strongest retained event-specific contact window. `exhaustive` mode and earlier accuracy layers bypass this display policy for rollback and comparison.

## Desh-Kaal-Patra and user facts

V3 reads facts extracted from normal chat for the selected, user-owned birth chart. Facts are user statements, not assistant predictions.

Facts may constrain:

- Employment expression: employed, self-employed, homemaker, student, unemployed, retired, or unknown.
- Relationship expression: single, partnered, engaged, married, divorced/separated, widowed, or unknown.
- Parenthood expression: has children, explicitly no children, or unknown.
- Age/life stage.

Examples:

- A homemaker's H10/H11 activation becomes household, community, or independent responsibility—not a promotion.
- An unemployed native receives career-opening/work-transition language—not promotion language.
- A student's status activation becomes academic responsibility or recognition.
- A married native's H7 combination becomes an existing partnership development rather than a new wedding prediction.
- Unknown parenthood produces children-or-creative-responsibility language and cannot be narrowed to pregnancy or childbirth.

User facts never create astrological evidence. They only permit a person-specific definition and constrain its wording. Since stored facts arrive newest first, the newest explicit state wins; older conflicting statements remain visible in `fact_basis` for audit.

## Subject-relative health timing (V3.9)

When a current user fact establishes a spouse, child, parent, or sibling, V3 may rotate houses from that person's reference house. For a spouse (native H7), spouse H6/H8/H12 map to native H12/H2/H6. The same rotation works for every supported relative instead of hard-coding one chart or one medical question.

A relative-health candidate uses the relative's reference house only as the ascendant from which H6/H8/H12 are rotated into the native chart. The reference house itself does not need activation. At least two derived medical houses must activate, at least one must have a dasha connection, and at least one must receive a transit trigger. D30, KP, exact contacts, and health karakas provide confirmation. The user-facing result remains a broad medical-attention, treatment, rest, recovery, or care-logistics window. A possible procedure is mentioned only when derived H8, derived H6 or H12, and Mars coincide; the engine does not diagnose a condition, identify a body part, or claim surgery is certain.

Integrated V3 reads all fast-planet transit segments before testing date overlap. V2 and legacy rollback paths retain their historical eight-segment behavior so model comparisons remain reproducible.

## Subject-relative event registry (V3.10)

V3.20 applies the same relative-house transformation to every applicable source event: work transition, recognition/responsibility, health, property decisions and gains, relocation, relationship development, long-distance travel, children/caregiving, education, and income/resources. The relative's reference house establishes the rotated lagna but is not an activation gate. The rotated source definition must independently pass its own anchor, transition, outcome, and transit gates. Event-specific karakas, KP rules, obstruction houses, varga selection, and exact-contact analysis are retained in the relative frame.

Relative events never compete with the native's primary cards. The API publishes them as `people_candidates` and `people_background_candidates`; mobile combines these into a collapsed “People around you” navigator. Its first level shows one clearly bounded accordion per person with that person's event count and top-theme preview. Expanding a person reveals only that person's events, with every Why still collapsed. Spouse-relative marriage and children definitions are folded out because they overlap the native's shared marriage/family events and could otherwise imply an unrelated spouse event.

## Persistent permission and peak timing (V3.11)

The same activation contract now applies to every house and to both native and subject-relative definitions. A core dasha lord directly occupying a required house in transit can open that house even when its natal lordship, placement, and aspect channels do not. This is recorded separately from natal dasha permission.

A long Saturn, Jupiter, Rahu, or Ketu transit is permission, not repeated event timing. When such permission is needed to pass an anchor or relative-subject gate, the event also needs an independent channel in its transition or outcome houses: PD/Sookshma activation or a faster-planet transit from a different timing source. The permission and trigger must overlap at the ledger's date boundaries. The direct slow transit cannot satisfy both jobs by itself.

Qualified long-running themes remain auditable as background. For primary presentation, each native-or-relative event family keeps only its strongest month and, when present, the stronger adjacent month. Adjacent monthly instances share an `event_window` identifier so a November-to-December activation is represented as one continuing window rather than two unrelated predictions. `delivery_v1` and `legacy_v3_6` retain the previous natal-only gate for rollback comparisons.

## Bhava-to-manifestation discrimination (V3.12)

An activated house identifies a life department, not a unique event. Every native and subject-relative candidate therefore carries an H1-H12 `bhava_disambiguation` audit. It lists the anchor house's competing classical threads, the configured companion houses actually active, the expected and active natural karakas, the topic-specific varga, and one of three specificity levels: `channel_distinguished`, `channel_supported_but_ranked`, or `bhava_level_ranked`. When the selected channel is not distinguished, deterministic copy explicitly describes it as a ranked possibility.

H4 demonstrates the general rule. Mother/family line is separated through the Moon, the fourth lord, D12, and a subject-relative event combination. Land/home property uses Mars and Moon, D4, and acquisition houses. Vehicle acquisition uses Venus with Moon/Mars, D16, H2 resources, and H11 acquisition. Residence change uses Moon/Mars/Rahu, D4, and H3/H12 movement. Education uses Mercury/Jupiter and D24. The engine applies the same companion-house + karaka + relevant-varga method to every event anchor; none of these channels is inferred from H4 alone.

For people around the native, subject identity and event type are two separate questions. D3 confirms sibling framing, D7 child framing, D9 spouse framing, and D12 parent framing. The source event still uses its own varga—for example, a mother's health event uses D12 for “mother” and D30 for “health.” Neither chart creates an event without the rotated D1 house combination and timing gates.

A concrete property-purchase candidate now requires H4, H11, and at least one funding/outlay route through H2 or H8. H4 with H2/H8 but without H11 may describe budgeting, family resources, financing, home concerns, or another fourth-house thread, but it is not labelled as a purchase. Vehicle acquisition is a separate D16 definition requiring H4 + H2 + H11 and no longer borrows property wording.

## Node and house-system doctrine

- Rahu and Ketu receive no direct classical house lordship.
- Nodes contribute through occupation, their dispositor/conjunction chain when available, KP significations, and seventh aspect only.
- Parashari activation uses whole-sign houses.
- KP uses Placidus cusps as independent confirmation.

## Support grades

- Grade A: usable natal promise, supportive active-planet delivery, no dominant obstruction, cooperative dasha levels, supportive KP, and relevant varga confirmation.
- Grade B: usable natal promise, supportive or mixed delivery, no dominant obstruction, cooperative dasha levels, plus KP or varga support.
- Grade C: the core event combination passes, but independent confirmation is incomplete.

Grades describe internal astrological support. They are not empirical probabilities.

## Known limitations before calibration

- Stored facts are free text and do not yet have explicit superseded/valid-from/valid-to fields.
- Combustion, planetary war, Shadbala, and verified planet-specific BAV/Kakshya are not supplied by the minimal context and are reported unavailable rather than inferred.
- Transit segmentation is day-level rather than exact ingress/aspect root solving; applying/separating status and station repeat passes are not yet available.
- Birth-time source and uncertainty are not yet stored, so KP cusp and sensitive-varga boundary confidence cannot yet be adjusted automatically.
- Grade thresholds require prospective outcome calibration.
- Health candidates remain broad and must never be treated as diagnosis.
