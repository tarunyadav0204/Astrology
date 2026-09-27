# Classical Pitṛ-śāpa calculation

## Selected source and scope

AstroRoshni uses the eleven combinations stated in *Bṛhat Parāśara Horā
Śāstra*, chapter incipit `atha pūrvajanmaśāpadyotanādhyāyaḥ`, verses 20–30.
The Chaukhamba/Devachandra Jha arrangement numbers these BPHS 83.20–30.
Other editions can number the chapter differently, so the chapter title,
verse range and incipits are stored with the result.

The repeated result in the verses is `suta-kṣaya` or `santati-nāśana`:
loss or absence of progeny. The calculator therefore does not turn the rule
into a generic diagnosis of ancestral trouble in career, money, health,
marriage or every area of life.

Primary Sanskrit text:

- <https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par8190.html>
- <https://vedicpupil.in/library/books/brihat-parashara-hora-shastra/chapter-83>

## Rules evaluated

Every verse is represented by a separate rule ID, `BPHS-PS-20` through
`BPHS-PS-30`. A rule matches only when every clause in that verse matches.
The API returns every evaluated clause, the actual chart fact and the matched
state. No score or Low/Medium/High grade is added.

The following do not form Pitṛ-śāpa by themselves:

- Sun joined Rahu
- Sun joined Saturn
- Rahu, Ketu or Saturn in House 9
- an afflicted ninth lord

Those facts can be assessed separately as father, Sun or ninth-house strain,
but they are never relabelled as Pitṛ-śāpa.

## Conservative textual decisions

- Verse 20 `mandāṃśa` is evaluated specifically as a Saturn-ruled navāṃśa.
- Verse 23 `durbala` is matched only when the ascendant lord is debilitated;
  the calculator does not invent a numeric weakness threshold.
- Verse 26 `pāparāśi` is evaluated as a sign ruled by the natural malefics
  Sun, Mars or Saturn.
- Verse 30 reads `kāraka` as Jupiter, the progeny significator in this chapter.
- Generic `pāpa-dṛṣṭi` does not introduce the debated fifth and ninth aspects
  of Rahu and Ketu. Nodes are applied where a verse names them explicitly.

These decisions are returned under `interpretive_notes` so they are not hidden
from astrologers or downstream clients.

## Contract compatibility

The existing `major_doshas.pitra_dosha` key remains in place. Its contents are
now the canonical BPHS result and include:

- `method`, `available`, `status`, `present`
- `display_name`, `scope`, `classical_result`
- `matched_rules`, `matched_rule_ids`, `evaluated_rules`
- `corroborating_factors`, `protective_factors`, `excluded_shortcuts`
- `source` and `interpretive_notes`

The Karma context retains old field names needed by existing clients, but their
values come from this result and explicitly forbid a broad ancestral-debt claim.

## Remedies in the source

BPHS 83.31–33 follows these combinations with Gayā Śrāddha, feeding Brahmins,
kanyādāna and godāna. These are reported as the text's prescriptions only
after a complete verse combination matches. They are not generated from a
standalone solar or ninth-house affliction.
