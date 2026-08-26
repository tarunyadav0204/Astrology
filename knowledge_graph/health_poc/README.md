# AstroRoshni Health ontology proof of concept

The canonical source is `astroroshni-health-poc.ttl`. Version `0.1.0` mirrors
the existing Instant Health implementation as ten graph routes: constitutional
and time-bound variants of overall health, mental wellbeing, surgery, accident,
and recovery. The legacy `disease` category resolves to overall Health.

Every question type expands through decision stages to required astrology
factors. The graph describes policy and calculator requirements; it does not
diagnose, prescribe treatment, calculate charts, or write the final answer.

The authored safety invariants include emergency triage before astrology, no
medical diagnosis, no unsupported body-part claims, no treatment decisions,
no surgery certainty, no accident prediction, and no recovery promise. Static
questions exclude timing. Time-bound questions require a natal vulnerability,
matching dasha activation, and dated transit confirmation inside the requested
horizon.

Validate and compile locally:

```bash
python3 scripts/validate_health_ontology.py
backend/.venv/bin/python -m pytest backend/tests/test_health_ontology_contract.py -q
```

The compiler generates `health-runtime-preview.json` and
`health-validation-report.md`; neither generated file should be hand-edited.
Instant Chat loads the compiled bundle locally and enforces it before answer
generation through `knowledge_graph_policy`, `knowledge_graph_routes`, and
`health_graph_route`.
