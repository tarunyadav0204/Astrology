# Deva Keralam ambiguous-context backlog

## Coverage and purpose

The completion ledgers D, E, and F contain **168** passages classified as
`ambiguous_context`. The accompanying
`ambiguous_context_backlog_v1.json` accounts for every one of those passages
exactly once. It does not promote, compile, or publish any rule.

The backlog distinguishes ambiguity that can probably be settled by reviewing
neighboring pages in the supplied edition from ambiguity that requires an
independent textual witness. This prevents a missing section heading from
being treated in the same way as a corrupt or disputed reading.

## Ambiguity groups

| Group | Count | Resolution approach |
|---|---:|---|
| Section or Nadi identity | 57 | Recover the active heading, named Nadiamsa, half, quarter, or degree boundary from adjacent pages and the supplied edition's table |
| OCR or source dispute | 40 | Compare with a separately sourced edition or manuscript witness before deciding the reading |
| Ascendant scope | 20 | Determine whether the verse is general or inherits a sign/Ascendant heading |
| Technical-term definition | 16 | Resolve a named Yoga, Kala, Avastha, benefic/malefic class, or other source-specific technical term |
| Pronoun or inherited planet | 15 | Trace “it,” “the said lord,” “the last-mentioned relative,” or an unnamed planet to its antecedent |
| Relationship or reference point | 9 | Fix aspect direction, the house/sign counted from, or the relevant chart point |
| Clause boundary | 7 | Decide which conditions and outcomes form one rule and where a continuation ends |
| Outcome or subject interpretation | 4 | Identify the subject or the exact traditional result without adding a modern inference |
| **Total** | **168** | Complete ambiguity backlog |

## What this edition can resolve

After the first 30 page reviews, **90 passages** remain assigned to
`source_review`. Their problem is local
context: a heading on the preceding page, a continuation on the following
page, an editorial note, or a Nadiamsa identity available elsewhere in this
same volume. Each entry records a page-centered review window and requires
section-boundary reconstruction.

**48 passages** are assigned to `second_witness`. These contain OCR damage,
conflicting readings, explicit editorial doubt, broken syntax, missing text,
or competing interpretations that nearby pages cannot settle reliably. Their
required evidence includes an independently sourced edition or manuscript and
a Sanskrit/translation comparison. They remain low priority until that
evidence is available.

The two routes are conservative. Reviewing adjacent pages may still conclude
that a passage is commentary-only, unsupported, or corrupt. A “source review”
route means the evidence is locally available; it does not assume the passage
will become executable.

## First resolution set — completed

The first set contained **30 high-confidence local-context cases**, balanced
across the three completion streams. They were selected because their stated
problem is usually a recoverable section/Nadi identity or inherited subject,
without requiring textual emendation. It produced **7 implementable rules**
and **23 explicit exclusions**. The source decisions and validation evidence
are recorded in `deva_keralam_ambiguous_context_resolution_g_audit.md`.

| Catalogue ordinal | Stream | PDF page | Verses | Primary task |
|---:|:---:|---:|---:|---|
| 52 | D | 38 | 110 | Recover Nadiamsa half and active Ascendant scope |
| 56 | D | 38 | 115–118 | Recover the Agada section and half |
| 78 | D | 45 | 190–191 | Resolve Varuna boundaries from the section notes/table |
| 88 | D | 48 | 214 | Carry the Varuna section identity safely |
| 90 | D | 48 | 216 | Separate the Varuna natal clause from its continuation |
| 140 | D | 65 | 388–390 | Identify the active Nadiamsa heading |
| 148 | D | 66 | 401 | Identify the inherited Nadiamsa and half |
| 207 | D | 89 | 656–658 | Recover Kunda section scope |
| 246 | D | 105 | 867 | Resolve “last-mentioned uncle” from preceding prose |
| 248 | D | 105 | 870–871 | Recover Nirmalaa section and half |
| 349 | E | 137 | 1248 | Resolve Guhamsa identity from local heading/notes |
| 354 | E | 138 | 1256–1257 | Recover Guha section and second part |
| 364 | E | 139 | 1272–1274 | Preserve Guha section scope across the continuation |
| 382 | E | 144 | 1336 | Apply the supplied Kanthaa half-boundary note |
| 393 | E | 147 | 1370–1371 | Recover Kanthaa section identity |
| 426 | E | 154 | 1451–1452 | Resolve Champaka/Kanthaa section transition |
| 468 | E | 167 | 1639 | Recover Trailokya section identity |
| 472 | E | 169 | 1662 | Resolve first-part versus second-half boundary |
| 489 | E | 173 | 1713 | Carry Trailokya identity from neighboring text |
| 528 | E | 182 | 1840 | Recover Seethala section identity |
| 590 | F | 199 | 2013–2014 | Recover Leo/Champaka section scope |
| 598 | F | 200 | 2033–2034 | Resolve Champaka half and degree boundary |
| 609 | F | 202 | 2068 | Carry the Gadaa section identity into the dasha clause |
| 649 | F | 211 | 2159–2161 | Resolve Gadaa and Vipra Kala boundaries |
| 669 | F | 216 | 2216–2219 | Recover the former-half Mangala section |
| 700 | F | 223 | 2298–2299 | Resolve former-half Uraga scope |
| 714 | F | 226 | 2326–2328 | Separate Uraga former/latter-half clauses |
| 728 | F | 229 | 2369 | Recover Sumathi section identity |
| 781 | F | 240 | 2499–2500 | Identify the Capricorn Nadiamsa inherited after Kaalaa |
| 790 | F | 241 | 2510 | Identify the active Nadiamsa from adjacent verses |

Each first-set review inspected the page image, the declared neighboring page
window, and the relevant section/table note. Every executable candidate passed
the reviewed-manifest schema, canonical fact ontology, geometry checks,
precision policy, and guarded compiler.

## Machine-readable contract

The JSON file uses `deva-keralam-completion-backlog/1.0.0` and the shared
`completion_backlog.py` loader. Entries contain the catalogue ordinal, passage
key, primary ambiguity category, concise evidence note, required capabilities,
resolution route, and priority.

Validation compares its 168 `(catalogue_ordinal, passage_key)` pairs with all
`ambiguous_context` rows in completion ledgers D, E, and F. Missing entries,
extra entries, or duplicates fail the audit.
