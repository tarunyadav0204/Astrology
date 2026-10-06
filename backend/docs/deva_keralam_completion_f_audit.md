# Deva Keralam completion stream F audit

## Scope

Stream F owns catalogue ordinals **587–878**, the final 292 records in the
canonical `(PDF page, passage key)` order. These records span PDF pages
198–258 and verses 2002–2718. The machine-readable disposition ledger is
`completion_ledger_f_v1.json`.

Every assigned catalogue record appears exactly once and in order. Earlier
work is not counted again: overlaps with reviewed batch C and the verses
2497–2498 Book 1 pilot are marked `already_reviewed` with their existing rule
or rejection keys.

## Disposition totals

| Disposition | Count | Meaning |
|---|---:|---|
| `executable` | 2 | Complete natal condition and result verified on the rendered source page and expressible with canonical facts |
| `already_reviewed` | 21 | Already represented by batch C or the Book 1 pilot |
| `unsupported_fact` | 76 | A plausible natal rule requires facts or subdivisions outside the current canonical ontology |
| `timing_pending` | 71 | Requires dasha, transit, age, or life-stage execution beyond the natal-only reviewed compiler |
| `ambiguous_context` | 56 | Inherited sign, Nadiamsa, subject, or conditional boundaries are not independently secure |
| `mortality_excluded` | 46 | Literal death, lifespan, or survival judgment excluded from this product rule pack |
| `corrupt_or_disputed` | 20 | The supplied edition flags corruption, incompleteness, disputed wording, or an unstable reading |
| **Total** | **292** | Complete stream coverage |

`duplicate`, `commentary_only`, and `impossible_geometry` have zero entries in
this stream. Zero is a reviewed result; passages were not forced into every
available category.

## New executable rules

### Verse 2062 — sibling indication

The rendered PDF page 202 (printed page 185) gives a complete natal condition:
an immovable Ascendant, Saturn as the Moon-sign lord, Saturn exalted, and
Jupiter viewing Saturn. The rule retains the direction of the Sanskrit
`guru-nirikshite` as Jupiter's aspect to Saturn. “Immovable Ascendant” is
represented explicitly by Taurus, Leo, Scorpio, or Aquarius, avoiding a new
parallel modality calculator.

Rule key:
`DK.F.2062.IMMOVABLE_ASC_SATURN_EXALTED_JUPITER_ASPECT`

Reviewed image evidence:
`page-0202-e9290c78b150.jpg`, SHA-256
`e9290c78b150c4fb06725f1ba1423e6bc031964fbe3057384ca9c73c8472e778`.

### Verse 2605 — relationship/conduct indication

The rendered PDF page 249 (printed page 232) explicitly requires seventh-lord
Mars in the Ascendant with another malefic and Saturn either aspecting or
joining Mars. Mars does not satisfy the separate “with a malefic” clause in
the implementation. The additional occupant is limited to Sun, Saturn, Rahu,
or Ketu. The Sanskrit construction makes Mars the object, so Mars merely
aspecting Saturn does not satisfy this rule.

Rule key:
`DK.F.2605.SEVENTH_LORD_MARS_ASC_SATURN_MALEFIC`

The outcome is sensitive. Its rule metadata states that it must never be
presented as proof of conduct or as a factual accusation.

Reviewed image evidence:
`page-0249-39505bcf3a4c.jpg`, SHA-256
`39505bcf3a4cc1fe7189d9c05091c7d9cd367e050e82e8ff7d0b754de8f45a9d`.

## Review policy

- Draft AI extraction was used only as a navigation aid.
- A new executable entry required inspection of the rendered page image and
  its neighboring context.
- OCR-only evidence could support a conservative non-executable disposition,
  but never a new executable rule.
- Existing reviewed work was linked rather than duplicated.
- A passage containing both natal and timed results was retained as
  `timing_pending` unless a separate, source-safe natal clause could be
  isolated without changing the source boundary.
- Mortality statements remain catalogued and traceable but are deliberately
  unavailable to runtime matching.

## Validation

The strict completion-ledger loader accepts all 292 rows with exact ordinal
coverage. The strict reviewed-manifest loader accepts both new candidates, and
the guarded compiler compiles both without lint findings. Loading these files
does not publish or globally register any rule and does not alter client or API
contracts.
