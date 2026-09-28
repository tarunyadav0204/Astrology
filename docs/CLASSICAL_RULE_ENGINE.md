# AstroRoshni Classical Rule Engine

The engine turns a pinned classical passage into deterministic, reviewable
chart evidence. It does not generate free-form predictions and is not connected
to chat. Certified natal judgments can be rendered directly from rule evidence.

## Publication contract

Every chapter must satisfy all of these conditions before it is certified:

1. A source profile pins the work, edition/witness, numbering and source policy.
2. Every verse belongs to exactly one passage group; gaps and overlaps fail tests.
3. Narrative, descriptive, computational and interpretive passages remain distinct.
4. An executable rule names its exact source verses and canonical calculator binding.
5. Explicitly missing astronomical inputs produce `unavailable`; no fallback or inferred value is allowed. Calculator and programming errors propagate instead of being disguised as missing data.
6. Rule evidence contains calculated facts, never LLM-authored conclusions.
7. Later conventions are excluded unless they have a separate, named source profile.
8. A rule-set version is immutable once promoted to a release.

## Source text policy

The first pinned transcription permits personal study and research but restricts
commercial republication. The repository therefore stores our operational
summaries, verse locations and source links, not copied Sanskrit or translation
text. Full text may be added after a suitable public-domain or licensed witness
has been approved.

## Coverage

| Work | Chapter | Verses | Catalogued | Executable groups | Status |
|---|---:|---:|---:|---:|---|
| BPHS | 3, Graha-guna-svarupa | 74 | 74 | 9 | Certified backend pack |
| BPHS | 24, Effects of house lords | 145 | 145 | 144 placements + 1 control | Certified natal-judgment pack |
| BPHS | 34, Yoga Karakas and lordships | 46 | 46 | 16 published rules | Certified dependency and natal-reading pack |

Chapter 3 currently publishes deterministic evidence for:

- natural benefic/malefic nature, including phase-dependent Moon and associated Mercury;
- exaltation, debilitation and Moolatrikona;
- natural, temporary and fivefold friendship for the seven visible grahas;
- solar upagrahas;
- time upagrahas and Gulika;
- Pranapada.

Planetary significations, appearance, temperament, tissues, objects, seasons,
tastes and other correspondences are catalogued doctrine. They are not falsely
presented as chart-matching rules merely because they occur in the chapter.

Chapter 24 publishes all 144 house-lord-in-house placements. A D1 chart matches
exactly twelve: one for each house lord. Verse 145 is implemented as a mandatory
interpretive control, so the response includes the relevant lord's dignity,
combustion, motion, conjunctions and visible-graha aspects. It does not present
the placement verse as an unconditional certainty.

Chapter 34 publishes the general functional-lordship doctrine and all twelve
ascendant-specific catalogues through the existing canonical functional-nature
calculator. It keeps four ideas distinct: natural nature, functional role,
single-planet Yoga Karaka ownership, and qualified yoga or Maraka statements in
the Lagna-specific passage. Its fact compiler lets later chapters consume each
role with its exact rule and verse provenance. The relationship rule tests only
the relationships named in verses 11–12: exchange, conjunction, one lord in the
other's sign, and full mutual aspect. The node rule applies verses 16–17 through
occupied house, conjunction and the stated Kendra/Trikona lord contact; it does
not invent independent node lordship or a universal node friendship table.

The authenticated `POST /api/classical-natal-promise` endpoint remains intact
for existing clients. New clients use `POST /api/classical-reading`, which
evaluates every published reading-capable pack and returns one versioned,
chapter-independent contract grouped by life area and subject. The mobile
professional positions screen consumes this aggregate contract under `Life`.

## Scalable reading contract

A chapter pack declares its capabilities beside the chapter module. The
registry discovers `CHAPTER_*` objects automatically; it has no chapter import
list or evaluation switch. Calculation and doctrine packs set
`contributes_reading_insights` to false. Interpretive packs set it to true and
return normalized `insights` from their evaluator.

Every insight must provide:

- a stable insight id and author-declared semantic deduplication key;
- life-area and subject taxonomy;
- translation-ready statement keys with reviewed fallback text;
- separate support and pressure testimony;
- generic display evidence plus preserved raw evidence;
- exact rule, verse, witness and calculator provenance;
- any interpretive controls that qualify the result.

The aggregator validates this contract and fails loudly when a published pack
is malformed. It merges only insights whose authors deliberately share a
deduplication key. It never resolves contradictory classical testimony using an
arbitrary score. The UI renders one life area at a time and expands every
contributing rule under Classical basis.

To publish another chapter, implement its source coverage, rules, evaluator and
normalized insights in the chapter module. No API route, registry switch or
mobile chapter component is added.

## Code entry points

- `backend/classical_rules/models.py`: source, passage, rule and result contracts.
- `backend/classical_rules/engine.py`: deterministic evaluator.
- `backend/classical_rules/facts.py`: canonical source-carrying chart facts and Boolean rule expressions.
- `backend/classical_rules/registry.py`: certified pack registry.
- `backend/classical_rules/reading.py`: normalized insight validation,
  deduplication and life-area aggregation.
- `backend/classical_rules/bphs/chapter_03.py`: Chapter 3 coverage and rules.
- `backend/classical_rules/bphs/chapter_24.py`: 144 natal placement judgments and the verse 145 strength control.
- `backend/classical_rules/bphs/chapter_34.py`: functional lordship, Yoga Karaka and twelve Lagna catalogues.
- `backend/migrations/create_classical_rule_engine.sql`: versioned persistence model.

The legacy `sutra_rules` table remains untouched for compatibility. It must not
become a production authority until its authored records are migrated into
versioned source passages and certified rule releases.
