# Wealth and Finance knowledge graph

This ontology is the live Instant Chat policy for single-chart financial questions. It covers 20 routes across overall wealth, income, debt, investing, inheritance, windfalls and calculated remedies.

The graph uses D1 as the promise layer and D2 as the mandatory financial confirmation. Route-specific evidence may add D5, D8 or D10, house-lord/nakshatra chains, dignity and Shadbala, operational Dhana yogas, Indu Lagna, Hora Lagna, Arudha gains, KP fructification, dashas and transits. Indu Lagna is sign-only supporting evidence and never overrides D1/D2.

Validate and compile with:

```bash
python3 scripts/validate_wealth_ontology.py
```

The compiler writes `wealth-runtime-preview.json` and `wealth-validation-report.md`. Runtime enforcement is implemented by `backend/instant_chat_v2/wealth_graph_runtime.py` and `backend/instant_chat_v2/graph_live.py`.
