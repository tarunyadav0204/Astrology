# Deva Keralam ambiguous-context resolution — batch G

Batch G reviews the 30 high-priority rows selected from the 168-entry ambiguous-context backlog. Every selected passage was checked on its rendered PDF page together with the immediately adjacent section material. The review does not use an inferred second witness and does not register rules globally.

## Result

- 30 source passages reviewed
- 7 source-secure natal rules compiled
- 23 source-checked candidates retained as explicit fail-closed rejections
- 168 backlog rows still represented exactly once
- selected backlog rows now resolve to `implementable_now` or `excluded`; none remain labelled `source_review`

The executable rules cover verses 656–658, 1336, 1639, 1713, 1840, 2033–2034 and 2216–2219. They add Pisces–Kundaa maternal-relative indications, the exact Capricorn–Kanthaa former-half profile, two Capricorn–Trailokya indications, a Taurus–Seethala spiritual indication, a Leo–Chambaka birth profile, and the Aries–Mangala father indication.

## Source decisions

| Catalogue ordinal | Verses | Decision | Resolution |
|---:|---:|---|---|
| 52 | 110 | Rejected | Agada has no secure ordinal in the pinned table. |
| 56 | 115–118 | Rejected | Agada is unmapped; mortality and remedies are also mixed into the result. |
| 78 | 190–191 | Rejected | The edition's Varuna/Varuni note conflicts with the pinned table. |
| 88 | 214 | Rejected | Varuna/Varuni remains unmapped despite clear local section context. |
| 90 | 216 | Rejected | The extraction joined verse 216 timing with verse 217 planetary conditions. |
| 140 | 388–390 | Rejected | Uraga is unmapped and the passage contains separate half-specific clauses. |
| 148 | 401 | Rejected | The inherited label is Uraga, which remains unmapped. |
| 207 | 656–658 | Approved | The preceding heading fixes Pisces Ascendant; the note fixes Mercury in Kundaa and the page states Saturn's conjunction. |
| 246 | 867 | Rejected | The relative is recoverable, but the verse contains no chart condition. |
| 248 | 870–871 | Rejected | Nirmalaa and Saturn are clear; widowhood and deprivation of named relatives remain excluded. |
| 349 | 1248 | Rejected | Guha is unmapped and the result is a longevity claim with remedy. |
| 354 | 1256–1257 | Rejected | The editor calls the subdivision reconstruction assumptive and the verses mixed. |
| 364 | 1272–1274 | Rejected | Guha's local half is clear, but its canonical ordinal is not. |
| 382 | 1336 | Approved | The page supplies exact Kanthaa degree bounds, resolving canonical ordinal 31. |
| 393 | 1370–1371 | Rejected | Kanthaa is recoverable, but sibling-destruction claims keep the complete result excluded. |
| 426 | 1451–1452 | Rejected | The Sun's Kanta/Kanthaa placement cannot be assigned between the duplicate table names. |
| 468 | 1639 | Approved | The uninterrupted Capricorn section and prior reviewed mapping identify Trailokya-mohankari ordinal 75. |
| 472 | 1662 | Rejected | The rule directly contrasts maternal longevity and early loss. |
| 489 | 1713 | Approved | The Capricorn–Trailokya latter-half scope carries continuously into the verse. |
| 528 | 1840 | Approved | Taurus–Seethala context, Sun in House 2 and Pisces Navamsa are explicit and expressible. |
| 590 | 2013–2014 | Rejected | Leo–Champaka and Venus–Jupiter are clear, but the complete outcome predicts sibling destruction. |
| 598 | 2033–2034 | Approved | The page explicitly restarts Leo–Champaka and states the former-half condition. |
| 609 | 2068 | Rejected | The required “adverse sub-period” is undefined and belongs to timing work. |
| 649 | 2159–2161 | Rejected | The rule needs a quarter/Vipra-Kala subdivision that the current fact contract does not expose. |
| 669 | 2216–2219 | Approved | Saturn tenth from Sun and the eighth lord in House 6 map directly to canonical relative-house and house-lord facts. |
| 700 | 2298–2299 | Rejected | Uraga is locally explicit but absent from the pinned canonical table. |
| 714 | 2326–2328 | Rejected | Uraga is unmapped and the passage mixes natal, mortality and incomplete transit clauses. |
| 728 | 2369 | Rejected | Sumathi has no secure canonical ordinal in the pinned table. |
| 781 | 2499–2500 | Rejected | Kaalaa ordinal 32 is resolved, but the result predicts loss and widowhood of siblings. |
| 790 | 2510 | Rejected | “In old age” is an unbounded life-stage trigger and cannot be compiled as natal timing. |

## Guardrails and validation

Executable Ascendant-Nadiamsa rules require `deva_keralam.precision.ascendant.reliable = true`. Approved entries record `source_check = page_image_context`. Rejected entries preserve the exact blocker and use a deliberately non-operative placeholder expression; the guarded compiler rejects them before rule construction.

Tests verify manifest decision/compiler parity, positive and negative matching for every approved expression, exact 30-row backlog resolution, full 168-row backlog coverage, and the absence of unresolved Agada, Varuna, Guha, Uraga and Sumathi aliases from executable expressions.
