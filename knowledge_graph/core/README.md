# AstroRoshni shared life-domain ontology

`astroroshni-life-domains.ttl` is the canonical parent-domain layer shared by
all domain-specific knowledge graphs. It contains 13 parent `ar:LifeDomain`
nodes and maps all 46 actual life-topic keys from Instant Chat beneath exactly
one parent.

Muhurat is intentionally modeled as `ar:QuestionOperation`, not as a life
domain. Domain-specific ontologies may keep legacy local domain resources, but
must link them to a canonical parent with `owl:sameAs`. The compiler resolves
that link so runtime evidence trees expose the canonical parent and its topics.

Validate and compile with:

```bash
python3 scripts/validate_life_domain_ontology.py
```

The generated `life-domain-runtime.json` and validation report must not be
hand-edited.
