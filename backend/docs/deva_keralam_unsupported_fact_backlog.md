# Deva Keralam unsupported-fact backlog

## Result

The three completion ledgers contain **159 passages** classified as `unsupported_fact`. Every one appears exactly once in [unsupported_fact_backlog_v1.json](../classical_rules/deva_keralam/data/unsupported_fact_backlog_v1.json), keyed by its canonical catalogue ordinal and passage key.

This does **not** mean that 159 new calculators are required. The passages reduce to 14 capability families. Most of the high-volume work is a safe adapter task: the backend already calculates the underlying value, but the Deva Keralam fact contract does not expose the normalized predicate required by the source rule.

| Capability family | Passages | Existing implementation to reuse | Recommended action |
|---|---:|---|---|
| Existing structural fact bindings | 54 | `deva_keralam/chart_facts.py` | Add canonical aliases and predicates for already-derived Rashi, house, Navamsa, Nadiamsa, modality and conjunction data. |
| Dynamic house-lord relations | 44 | sign-lord map and current house facts | Emit lord identity, house, Rashi, Navamsa, Nadiamsa and relationship facts generically for Houses 1–12. |
| Relationship quantifiers and aspects | 21 | `chart_facts.py`, `calculators/aspect_calculator.py` | Add reviewed `any`, `all`, relative-house and association predicates without changing the aspect doctrine. |
| Planet nature, strength and condition | 12 | `classical_natural_nature.py`, `planetary_dignities_calculator.py`, strength/Avastha data | Expose the individual classical facts. Do not manufacture a new aggregate strength score. |
| Fine Varga bindings | 6 | divisional-chart calculations, Shadbala/Varga code | Canonically expose D30 lord and D60 Shashtiamsa identity and quality after cross-checking the division formulas. |
| Source-trigger reconstruction | 4 | none | Re-read adjoining pages and, where needed, consult a second witness. These cannot be solved in code alone. |
| Named-yoga bindings | 4 | `classical_core_yogas.py`, `yoga_calculator.py` | Bind only the named Yoga definition actually required by the source clause. |
| Nadiamsa subdivisions beyond halves | 4 | existing 150-Nadi table and precision policy | Add source-defined quarter and one-third subdivisions with stricter precision gating. |
| Timing sequence and transit | 3 | Dasha and transit calculators | Model the book's sequence vocabulary and derived-sign transit relation before promoting these clauses. |
| Birth context and Panchang | 2 | `panchang_calculator.py` | Expose weekday and day/night birth facts. |
| Dispositor relationships | 2 | sign-lord map and aspect/conjunction facts | Emit a planet's sign dispositor and the dispositor's placement and relationships. |
| Arudha and derived Padas | 1 | `jaimini_point_calculator.py` | Expose the reviewed A7/house-Arudha result through the isolated fact contract. |
| Ashtakavarga bindings | 1 | `ashtakavarga.py` | Expose planet BAV bindus for the required house or sign. |
| Pushkara bindings | 1 | `pushkara_calculator.py` | Expose reviewed Pushkara Navamsa status. |
| **Total** | **159** |  |  |

## Highest-yield safe implementation order

### 1. Complete the structural adapter

Implement the 54 structural bindings first. These values are already calculated by the isolated Deva Keralam adapter. Work should be limited to stable canonical keys and tests for sign boundaries, Navamsa boundaries and Nadiamsa precision. This is the lowest-risk batch and immediately makes the largest number of passages eligible for renewed source review.

### 2. Add generic house-lord facts

The next 44 passages use a small repeated grammar: “lord of House N,” its placement, its Varga position, or its relation to another planet. Generate this grammar for all twelve houses from the existing sign-lord map. Avoid one-off facts such as `fifth_lord_in_taurus_navamsa`; use composable facts such as:

- `deva_keralam.house.5.lord_name`
- `deva_keralam.house.5.lord_house`
- `deva_keralam.house.5.lord_navamsa.name`
- `deva_keralam.house.5.lord_conjunct.<Planet>`

This prevents new source chapters from requiring more custom code.

### 3. Finish relationship and dispositor grammar

The 21 relationship passages and two dispositor passages can reuse the current Parashari aspect and conjunction calculations. Add relative-house predicates and explicit quantifiers only where the source requires them. “Association” must remain source-qualified; it should not silently mean conjunction, aspect and exchange simultaneously.

### 4. Bind classical nature and condition

The 12 nature/strength passages can reuse the existing waxing/waning Moon treatment, Mercury association logic, dignity and Avastha calculations. Preserve the underlying facts separately. Terms such as “benefic,” “malefic,” “strong” and “afflicted” must resolve through declared classical policies rather than a hidden score.

Completing stages 1–4 addresses **133 passages**. It should still trigger a source re-review before any passage becomes executable, because calculator availability does not resolve textual ambiguity or guarantee that the extraction captured every premise.

### 5. Connect small, already-implemented calculators

Bind the four named-Yoga passages, two birth-context passages and the single Arudha, Ashtakavarga and Pushkara passages. These are high-value and small, but each needs a source-specific test to ensure that the existing calculator's doctrine matches the book's use of the term.

### 6. Add fine Vargas and finer Nadi divisions

Implement the six D30/D60 bindings only after one canonical Varga formula is selected and regression-tested across existing clients. The four Nadiamsa-quarter/third rules require tighter birth-time precision than the current half-Nadi rules. A result should be unavailable when the uncertainty interval crosses the requested subdivision boundary.

### 7. Keep timing separate

The three timing passages should use the planned source-specific timing layer. Do not reinterpret “third Dasha,” “Janma Dasha,” or transit to a derived Navamsa sign as ordinary Vimshottari timing without textual support.

### 8. Return four passages to textual review

Four passages have no recoverable astrological trigger in their current catalogue unit. More programming cannot make them deterministic. They need adjoining-page reconstruction or a second edition and should remain non-executable until then.

## Reuse assessment

The JSON records the exact extracted fact names per passage as `source_fact:<name>` and the proposed backend reuse target. Reuse means adapting a reviewed output into the isolated Deva Keralam fact contract; it does not mean importing another feature's presentation-oriented result or changing that calculator's public contract.

The main reusable implementations are:

- [chart_facts.py](../classical_rules/deva_keralam/chart_facts.py)
- [aspect_calculator.py](../calculators/aspect_calculator.py)
- [classical_natural_nature.py](../calculators/classical_natural_nature.py)
- [planetary_dignities_calculator.py](../calculators/planetary_dignities_calculator.py)
- [classical_core_yogas.py](../calculators/classical_core_yogas.py)
- [jaimini_point_calculator.py](../calculators/jaimini_point_calculator.py)
- [ashtakavarga.py](../calculators/ashtakavarga.py)
- [pushkara_calculator.py](../calculators/pushkara_calculator.py)
- [panchang_calculator.py](../calculators/panchang_calculator.py)

No ontology, compiler, registry, client or API was changed in this backlog phase.

## Validation contract

The backlog loads through `load_completion_backlog()`. Its 159 `(catalogue_ordinal, passage_key)` pairs are audited against all D, E and F ledger rows by `audit_backlog_against_ledger()`. The audit returns no missing or extra entries.
