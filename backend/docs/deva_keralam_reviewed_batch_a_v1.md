# Deva Keralam reviewed batch A v1

## Scope and decision

Source stream A covers PDF pages 37–110 of the private Volume 1 scan. The
review selected the strongest source-bounded natal units and did not attempt
to turn every verse into a rule. The manifest contains 39 reviewed units:

- 27 approved natal candidates
- 12 explicit rejections
- 0 timing rules
- 0 globally registered rules

The approved set is concentrated in sections where the printed headings and
editorial notes make the inherited context locally recoverable:

- Pisces ascendant, Kundaa Nadiamsa
- Virgo ascendant, Dhanada and Suraa Nadiamsas
- Pisces ascendant, Kamalaa Nadiamsa
- Libra ascendant, Nirmalaa Nadiamsa

Earlier material in the stream contains valuable passages, but much of it
changes ascendant or Nadiamsa context mid-page, depends heavily on timing, or
contains explicit editorial warnings. Those passages were not added simply to
increase coverage.

## Review method

The reviewer used the retained page images as the source of authority and the
two-column OCR as a navigation aid. Page 98 confirms the Kamalaa/Pisces
boundary and verses 778–779. Page 104 confirms the Nirmalaa/Libra boundary,
its exact halves, and verse 860. Page 110 confirms verses 925–932 and the
editorial qualifications around them.

Every approved expression uses only keys accepted by the Deva Keralam fact
ontology. Exact Ascendant Nadiamsa rules fail closed unless birth-time
precision is reliable. The guarded compiler also checked that each Ascendant
Rashi, Navamsa/Nadiamsa name, ordinal and half can coexist at a real sidereal
longitude. Planetary combinations were checked for geometric possibility;
none requires a planet to occupy conflicting signs, houses or Navamsas.

The manifest was loaded with `load_reviewed_manifest()` and compiled with
`compile_reviewed_manifest()`: all 27 approved units compiled, while all 12
rejected units remained blocked.

## Rejection policy

Rejected entries remain in the manifest to make the audit trail visible. Each
has a machine-readable blocker. The main blocker classes are:

- age, dasha or transit timing outside the natal-only compiler
- an explicitly corrupt or editorially disputed passage
- a named yoga without a stated natal outcome
- an anonymous condition such as “two exalted planets” or unspecified
  “malefics,” which cannot be bound to canonical chart facts without invention
- a required relation such as Vargottama or Sakata Yoga that the current
  reviewed fact vocabulary cannot express source-faithfully
- conflicting inherited alternatives or mixed verses

## Limits

This batch is an isolated reviewed manifest. Loading or compiling it does not
publish or register its rules and cannot change chart, chat or prediction
clients. Outcomes retain the traditional source meaning; later product copy
still needs a separate interpretive and safety review, especially for caste,
death, illness, adultery and family-loss language.

Some pages have no clean OCR passage candidate even though their page image is
legible. Such approved units use an exact page-and-verse source key rather
than pretending an OCR candidate exists. Corrected transcription remains a
separate source-catalogue task.
