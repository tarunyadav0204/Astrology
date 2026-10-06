# Deva Keralam inherited-context reconstruction

Deva Keralam often states a heading, ascendant, Nadiamsa half or planetary
premise once and carries it across several later verses. A verse-by-verse OCR
extractor therefore cannot safely create chart logic on its own. This layer
records those inherited premises as source scholarship before any rule is
authored.

## Safety boundary

`classical_context_blocks`, `classical_context_spans` and
`classical_context_premises` are not executable rule tables. No chart or chat
client reads them. The reconstruction schema has no release membership or
automatic promotion path. AI proposals are saved separately as `draft` and a
reviewer must compare every boundary and premise with the page image.

## Deterministic boundaries

Each context block has an explicit first and last verse and page. Its spans
must be ordered, non-overlapping and cover every verse exactly once. Each
premise has a bounded verse range, structured value and page-based provenance.
The installer rejects gaps, overlaps, inverted ranges and missing provenance.

## Pilot: Abala / Prabhaa

The first pilot covers PDF pages 32–36 and verses 54–96. Verse 97 begins the
next `Virgo Navamsa` section and is the deterministic end boundary.

The source distinctions are preserved:

1. Verses 54–60: Abala context for immovable ascendants, with a Taurus heading
   retained as a qualification.
2. Verses 61–75: Taurus-specific parallel branches. The opening prosperity statement uses Aries Navamsa; the following independently worded statements use Abala Nadiamsa. These conditions are not cumulative.
3. Verses 76–87: general immovable-sign context with local planetary premises.
4. Verses 88–96: explicitly Aquarius from the edition note.

The source name `Abala` and table name `Prabhaa` are both retained. For fixed
signs this is ordinal 16 and physical division 135, spanning 26°48′–27°00′;
the former and latter six-minute halves are stored explicitly.

Install after runtime migrations:

```bash
cd backend
python scripts/install_deva_keralam_context_pilot.py
```

The fixture is versioned at
`classical_sources/data/deva_keralam_context_pilot_abala_prabha_v1.json`.
