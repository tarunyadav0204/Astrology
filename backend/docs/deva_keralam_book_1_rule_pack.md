# Deva Keralam Book 1 reviewed rule pack

## Current executable coverage

The opt-in Book 1 pack contains **104 executable, source-linked natal rules**:

- 13 rules from the earlier reviewed pilot slices;
- 27 new rules from PDF pages 37–110;
- 31 new rules from PDF pages 111–185;
- 29 new rules from PDF pages 186–260.
- 4 further rules admitted by the full 878-passage completion audit.

The reviewed manifests retain **37 candidate units as explicit rejections**;
they do not execute.

Every one of the **878 catalogued passages** now also has one completion-ledger
disposition. The unresolved work is no longer an unmeasured remainder:

- 220 timing passages;
- 168 passages with ambiguous inherited context;
- 159 passages requiring facts the current adapter does not calculate;
- 166 mortality passages intentionally excluded from consumer prediction;
- 52 corrupt or disputed passages;
- 15 commentary-only passages;
- 1 duplicate and 1 astronomically impossible passage;
- 92 catalogue passages already represented by earlier reviewed work;
- 4 newly executable passages from the completion pass.

## How it is used

1. Existing sidereal D1 longitudes are converted into canonical facts for
   signs, houses, lords, Navamsha, dignity, conjunctions, Parashari aspects and
   named Nadiamsas.
2. The Book 1 rule pack is loaded only after every manifest passes the strict
   schema and cross-batch audit.
3. The deterministic rule engine compares the chart facts with each reviewed
   source condition.
4. A match returns the traditional result together with its rule key, verse
   range and PDF pages. Non-matches and unavailable precision remain visible.

Exact Ascendant Nadiamsa rules fail closed unless the Ascendant longitude is
known precisely enough to remain within the required Nadiamsa half. No rule is
globally registered by importing or auditing this pack.

## What this does not claim

This is complete disposition coverage, not a claim that every line can or
should be an executable consumer prediction. Deva Keralam frequently carries
context across verses, changes the applicable sign or Nadiamsa mid-section,
gives age or dasha timing, or uses conditions outside the present fact
ontology. The completion ledgers preserve those passages for the relevant
calculator, context-reconstruction or exclusion workflow.

Run the audit with:

```bash
PYTHONPATH=backend backend/.venv/bin/python \
  backend/scripts/audit_deva_keralam_reviewed_rules.py
```

The resulting rule collection can be passed explicitly to
`match_deva_keralam_chart`. It remains separate from production chart, API and
chat contracts until a later integration step is approved and tested.
