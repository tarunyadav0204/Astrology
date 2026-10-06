# Deva Keralam reviewed rule compiler

The reviewed compiler is the boundary between AI-assisted extraction and an executable classical rule. It does not read the extraction-candidate table, update `classical_rule_versions`, or register a rule pack. A reviewer must construct a `ReviewedRuleCandidate` with a verified passage key, context-block key, pinned source pages, canonical fact expression, explicit precision policy and a source-resolved outcome.

The compiler rejects a candidate when any of these conditions is present:

- the candidate or its context has not been reviewed;
- a qualified context has not been explicitly acknowledged;
- a fact key is outside the versioned Deva Keralam ontology;
- exact conditions conflict, have impossible ranges, or pair a Nadiamsa name with the wrong ordinal;
- an exact Nadiamsa rule lacks the birth-time precision gate;
- an inherited pronoun or premise remains ambiguous;
- the edition records competing readings or missing source text;
- the outcome depends on dasha, transit, age, death timing or another timing grammar that this compiler release does not support.

Successful compilation creates a source-linked `ClassicalRule` that can run through the existing deterministic matcher. The rule remains isolated from the global registry, so compilation is not publication.

## First vertical slice

The first complete review slice is Deva Keralam Book I, Abala/Prabhaa Nadiamsa, verses 54-96, PDF pages 32-36 and printed pages 7-11 of the supplied scan. The source reconstruction defines four contexts:

1. verses 54-60: Abala outcomes qualified by the edition as applying to fixed Ascendants;
2. verses 61-75: Taurus-specific parallel branches: Aries Navamsa for the opening prosperity statement, and Abala Nadiamsa for the following clauses;
3. verses 76-87: return to the fixed-Ascendant context;
4. verses 88-96: Aquarius Ascendant.

The edition identifies Abala with Prabha. The reviewed alias maps this spelling exactly to Table 1 `Prabhaa`, ordinal 16. There is no fuzzy spelling repair.

The slice contains **27 reviewed candidate units**. **12 compile** to exact natal rules and **15 are rejected** with machine-readable reasons. The rejected group includes all timing-dependent passages, recorded textual alternatives, missing original text, conditions outside the current fact ontology, and clauses whose inherited premise cannot be proved. Each compiled rule has one positive and one negative fixture, and missing birth-time precision produces `unavailable` rather than a negative match.

The implementation is in:

- `classical_rules/deva_keralam/review_compiler.py`
- `classical_rules/deva_keralam/abala_prabhaa_slice.py`
- `tests/test_deva_keralam_review_compiler.py`

Future sections should add reviewed candidate manifests and reuse the compiler. They should not add section-specific matching code or query AI drafts at runtime.

