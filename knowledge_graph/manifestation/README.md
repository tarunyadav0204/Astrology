# AstroRoshni manifestation knowledge graph

This module is the canonical, consumer-neutral model for translating activated
house combinations into bounded real-life manifestation candidates. It is
isolated from Instant Chat, KP, Parashari and the mobile clients. Event Timeline
is the first explicit consumer; its adapter evaluates only patterns carrying
timeline metadata and retains the timeline's independent evidence gates.

## Boundary

The graph owns shared meaning:

```text
activated house roles -> activation pattern -> manifestation candidate
```

It does not decide whether a house is active. Parashari, KP and daily prediction
engines retain their own activation and delivery rules. They will eventually
send a typed activation packet to the resolver.

## Complete combination coverage

The graph uses two layers so coverage does not become fabricated prediction:

1. The semantic lattice contains contextual meanings for all twelve houses and
   thirteen parent-domain lenses. It can interpret every one of the 4,095
   non-empty house sets while preserving alternative meanings.
2. The curated manifestation layer contains specific event candidates with
   explicit house roles, phase restrictions, provenance and review status.

An unmatched combination therefore returns `semantic_only`, with its meanings
and plausible domains, instead of returning an empty success or inventing an
event. `specific_and_semantic` is returned only when a curated manifestation
rule also matches.

`manifestation-ontology.ttl` is the authored source. The validator compiles it
to `manifestation-runtime.json`; the generated JSON must not be hand-edited.
The runtime loads only the compiled bundle and never parses RDF during a request.

## Provenance and review

Every pattern has both a `claimBasis` and `reviewStatus`.

- `classical_direct`: a direct, source-cited classical statement.
- `traditional_derived`: a traditional inference assembled from house roles.
- `modern_mapping`: a modern lived example mapped from traditional meanings.
- `product_heuristic`: an application rule that still needs doctrinal review.

The initial seed is a transparent consolidation of existing AstroRoshni rule
registries. It is not represented as a finished classical edition. Specific
textual citations can be added only after edition-aware scholarly review.

## Build and validate

```bash
backend/.venv/bin/python scripts/validate_manifestation_ontology.py
backend/.venv/bin/python -m pytest \
  backend/tests/test_manifestation_ontology_contract.py \
  backend/tests/test_manifestation_resolver.py -q
```

The release gate checks graph integrity, stable identifiers, house-role
contradictions, provenance, supported enum values and competency cases.

For human review, open `manifestation-review-catalog.md`. It is generated from
the ontology and groups house meanings, domain lenses and manifestation rules
into readable sections. Refer to stable pattern IDs when recording a decision;
the generated catalog itself should not be edited.

## Future integration contract

Each product integration must:

1. construct its own typed activation packet;
2. call the resolver explicitly;
3. store the ontology and calculator versions with its result;
4. fail visibly if the configured ontology version cannot load;
5. run product-specific golden and regression tests;
6. remove its previous mapping only after output parity has been reviewed.

There is no automatic legacy fallback in this module.

## Event Timeline integration

`backend/manifestation_kg/timeline.py` converts only `timelineEnabled` patterns
into Event Timeline definitions. The KG proposes the event structure; Event
Timeline still requires its own anchor permission, manifestation pathway,
transit timing, natal promise, planet delivery, topic varga, KP confirmation and
obstruction evaluation. Qualified cards carry a `manifestation_kg` audit block
with the stable pattern ID, manifestation ID, ontology version, review status,
claim basis, sources and role mapping.

The default integration mode is `review`, which allows the current provisional
patterns to be tested while displaying their review status in the output. Set
`MANIFESTATION_KG_EVENT_TIMELINE=off` for an immediate rollback. Context-gated
patterns are skipped unless the required user fact exists; the top-level
`manifestation_kg.skipped` array records every skipped rule and reason.
