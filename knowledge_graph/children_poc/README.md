# Children, Parenthood and Progeny graph

This ontology is the authoritative Instant policy for children questions. It
separates promise, conception, childbirth, child order, delay, assisted and
adoption pathways, relationship questions, timing, remedies and specialist
safety handoffs. Static routes never inherit incidental timing, and a parent's
chart is never used as the child's own chart.

Validate and compile:

```bash
python3 scripts/validate_children_ontology.py
```

The generated runtime bundle is `children-runtime-preview.json`.
