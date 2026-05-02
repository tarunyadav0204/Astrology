# Relationship Match Result UX Spec

## Goal

Build a `Marriage & Relationship Match` result experience in `astroroshni_mobile` that:

- feels deeper than commodity kundli matching
- creates trust before monetization
- creates `earned FOMO`, not manipulative lockouts
- works cleanly across `light` and `dark` themes
- works across all app languages
- uses admin-driven pricing instead of hardcoded credit numbers


## Product Principle

The user must get a `real result` for free.

We do **not** charge for:

- basic Ashtakoot score
- basic Manglik result
- high-level verdict
- current timing climate headline
- 1 visible next favorable joint window

We monetize:

- deeper explanation
- contradiction resolution
- premium timing roadmap
- actionable relationship guidance
- follow-up analysis/chat

The UX should make users think:

- `I already got value`
- `There is clearly something more important underneath`
- `I want the full interpretation because this affects a real-life decision`


## Pricing Source Of Truth

Do not hardcode prices in UI.

Use pricing from:

- `GET /api/credits/settings/analysis-pricing`
- `GET /api/credits/settings/my-pricing`

Relevant current pricing keys from backend:

- `marriage_analysis_cost`
- `partnership_analysis_cost`
- `premium_chat_cost`

Current backend pricing behavior is defined in:

- [backend/credits/credit_service.py](/Users/tarunydv/Desktop/Code/AstrologyApp/backend/credits/credit_service.py:918)
- [backend/credits/routes.py](/Users/tarunydv/Desktop/Code/AstrologyApp/backend/credits/routes.py:1317)


## Theme Constraints

Mobile themes already come from:

- [ThemeContext.js](/Users/tarunydv/Desktop/Code/AstrologyApp/astroroshni_mobile/src/context/ThemeContext.js:1)

Do not introduce screen-specific hardcoded palette logic if token reuse is possible.

Use existing semantic colors:

- `colors.text`
- `colors.textSecondary`
- `colors.primary`
- `colors.secondary`
- `colors.success`
- `colors.warning`
- `colors.error`
- `colors.cardBackground`
- `colors.cardBorder`
- `colors.background`
- `colors.backgroundSecondary`

### Theme rules

- Never use only `green/red` to convey meaning.
- Every status needs text labels:
  - `Favorable`
  - `Mixed`
  - `Challenging`
- Premium teaser cards must look premium in both themes without becoming neon-heavy in dark mode.
- Android light mode must respect `androidLightCardFixStyle` and `getCardElevation`.
- Locked sections should not use heavy blur as the only premium cue. Prefer:
  - a visible title
  - 1 unlocked line
  - a soft gradient fade
  - CTA footer


## Localization Constraints

Localization already comes from:

- [i18n.js](/Users/tarunydv/Desktop/Code/AstrologyApp/astroroshni_mobile/src/locales/i18n.js:1)
- locale files in `/astroroshni_mobile/src/locales`

Supported languages in app today:

- English
- Spanish
- Hindi
- Tamil
- Telugu
- Gujarati
- Marathi
- German
- French
- Russian
- Chinese

### Localization rules

- All result labels, CTA copy, paywall lines, and trust copy must use translation keys.
- Primary labels must be short and expansion-safe.
- Avoid long English marketing phrases that become awkward in Indian languages.
- Keep classical terms consistent:
  - `Manglik`
  - `Nadi`
  - `Bhakoot`
  - `Navamsa`
  - `Upapada`
- If a term is retained untranslated, pair it with short helper text.
- Dynamic copy must support interpolation:
  - `{{credits}}`
  - `{{tier}}`
  - `{{date}}`
  - `{{windowStart}}`
  - `{{windowEnd}}`


## Screen Strategy

Treat this as a `decision-support result`, not a score page.

Recommended structure:

1. `Instant Verdict`
2. `Why We Think This`
3. `What Matters Most`
4. `Timing Guidance`
5. `Unlock Deeper Clarity`


## Result Screen Layout

### 1. Hero Summary

Purpose:

- establish trust immediately
- answer the user’s first question fast

Content:

- `Overall Match`
- `Current Timing Climate`
- `Top-line verdict`

Example:

- `Good match with one serious adjustment area`
- `Strong compatibility, but timing is not ideal right now`
- `Low guna score, but deeper chart support improves the picture`

Rules:

- no sales CTA above the fold
- no lock icon in hero
- verdict must be understandable without astrology knowledge


### 2. Trust Spine

Purpose:

- prove that the result is built on real astrology

Display 4 evidence chips/cards:

- `Ashtakoot`
- `Manglik`
- `Marriage Support (D1/D9)`
- `Timing Climate`

Each block must show:

- label
- short verdict
- short status

Examples:

- `Ashtakoot: 24/36`
- `Manglik: balanced at pair level`
- `D1/D9: mature support is strong`
- `Timing: favorable now`

This section should map directly to backend deterministic fields, not AI prose.


### 3. Key Strengths

Purpose:

- create confidence and positive engagement

Free:

- show top 2 strengths fully

Premium teaser:

- show `+ more strengths in full report`

Examples:

- `Emotional compatibility is stronger than the raw score suggests`
- `Both charts support long-term commitment after marriage`


### 4. Key Risks

Purpose:

- create serious intent
- start earned FOMO

Free:

- show top 2 risks fully

Rules:

- risks must sound concrete, not dramatic
- no fearbait like `danger`, `doom`, `never marry`

Examples:

- `Attraction is strong, but emotional rhythm may differ`
- `One chart shows delay pressure during the current period`


### 5. Contradiction Card

Purpose:

- strongest earned-FOMO component

This section should highlight when the result is not surface-level.

Examples:

- `Why this match looks better than the raw score`
- `Why a strong score still does not mean easy marriage`
- `The hidden factor deciding whether this becomes stable`

Free:

- title
- one unlocked summary line

Premium:

- full explanation

This is where the user should feel:

- `I need to know the real story`


### 6. Timing Guidance

Purpose:

- make the product decision-grade

Free:

- `Current Timing Climate`
- `1 best next joint window`

Premium:

- full timing roadmap
- caution windows
- `why now / why later`

Display:

- `Current climate: Favorable / Mixed / Challenging`
- `Best next window: Aug 2027 - Feb 2028`

If premium locked:

- show first window fully
- show `2 more relationship timing windows` locked


### 7. Premium Depth Section

Purpose:

- convert without feeling cheap

Title examples:

- `Unlock Full Relationship Reading`
- `See The Full Marriage Potential`
- `Get The Deeper Compatibility Truth`

Unlocked preview bullets:

- `Who creates the delay pattern`
- `Whether emotional mismatch improves after marriage`
- `Long-term stability vs short-term attraction`
- `Full timing roadmap for the next 24 months`

CTA should be contextual:

- `Unlock for {{credits}} credits`
- `Included in {{tier}}`
- `Use Premium Relationship Reading`


## Earned FOMO Rules

Allowed:

- unresolved contradiction
- hidden cause of mismatch
- timing uncertainty
- premium roadmap
- premium depth label

Not allowed:

- fake countdown
- blocking all useful info
- hiding the score entirely
- generic blur over the whole screen
- manipulative copy like `last chance`, `marry now`, `don’t miss destiny`

Correct FOMO emotion:

- `I need clarity`

Wrong FOMO emotion:

- `this app is withholding obvious info`


## Free vs Paid Boundary

### Free

- overall match %
- overall match grade
- current timing climate
- 1 next favorable joint window
- top 2 strengths
- top 2 risks
- basic Ashtakoot breakdown
- Manglik pair result
- one contradiction teaser

### Paid

- full contradiction explanation
- full timing roadmap
- D1/D9 relationship synthesis detail
- UL/A7-based marriage continuity section
- emotional / physical / practical harmony deep dive
- personalized guidance and next steps
- follow-up premium interpretation / match-specific chat


## Copy Framework

### Headline labels

Use short labels only:

- `Overall Match`
- `Timing Climate`
- `Key Strengths`
- `Key Risks`
- `Hidden Factor`
- `Best Window`
- `Full Reading`

### Trust copy

- `Based on classical compatibility, deeper marriage support, and timing analysis`
- `This result combines score, chart synthesis, and marriage timing`

### Premium CTA copy

- `Unlock deeper relationship clarity`
- `See why this match is stronger than the raw score`
- `Get the full marriage timing roadmap`

### Avoid

- `Unlock secrets`
- `Hidden destiny`
- `Your fate is blocked`
- `Don’t lose this chance`


## Backend Fields To Consume

Primary backend payload now available under compatibility result:

- `compatibility_analysis.overall_score`
- `compatibility_analysis.guna_milan`
- `compatibility_analysis.manglik_analysis`
- `compatibility_analysis.relationship_indicators`
- `compatibility_analysis.timing_overlay`
- `compatibility_analysis.evidence_summary`
- `compatibility_analysis.evidence_objects`
- `compatibility_analysis.recommendation.timing_note`

Top-level route response also exposes:

- `timing_overlay`
- `rule_profile`


## Mobile Component Proposal

Recommended new components:

- `RelationshipResultHero`
- `RelationshipTrustSpine`
- `RelationshipStrengthsCard`
- `RelationshipRisksCard`
- `RelationshipContradictionCard`
- `RelationshipTimingCard`
- `RelationshipPremiumUnlockCard`

Recommended screen:

- `KundliMatchResultScreen`


## Translation Keys Proposal

Suggested namespace:

- `relationshipMatch.*`

Examples:

- `relationshipMatch.overallMatch`
- `relationshipMatch.timingClimate`
- `relationshipMatch.keyStrengths`
- `relationshipMatch.keyRisks`
- `relationshipMatch.hiddenFactor`
- `relationshipMatch.bestWindow`
- `relationshipMatch.unlockFullReading`
- `relationshipMatch.unlockForCredits`
- `relationshipMatch.includedInTier`
- `relationshipMatch.basedOn`
- `relationshipMatch.currentTimingSupportive`
- `relationshipMatch.currentTimingMixed`
- `relationshipMatch.currentTimingChallenging`


## Monetization Mapping

Do not create a paid wall for basic match itself.

Recommended billing behavior:

- `Free`: base result screen
- `Paid full relationship report`: use `marriage_analysis_cost`
- `Premium follow-up chat`: use `partnership_analysis_cost` or `premium_chat_cost`

If later needed, add a dedicated setting like:

- `relationship_match_premium_cost`

But only after the feature proves demand.


## Success Criteria

This UX is successful if users feel:

- `I got a serious answer immediately`
- `The app clearly knows more than generic kundli matching tools`
- `The premium unlock gives me clarity, not recycled fluff`

This UX has failed if users feel:

- `They are charging for what every app gives free`
- `The result is just a score with nicer colors`
- `The paywall is obvious before trust is established`


## Implementation Order

1. Build result screen skeleton with theme-safe cards.
2. Add translation keys for English first, then fan out to other locales.
3. Bind free sections to deterministic backend fields.
4. Add premium teaser sections without hard blur dependency.
5. Bind dynamic pricing from `my-pricing` / `analysis-pricing`.
6. Add unlock CTA behavior.
7. Validate in:
   - dark theme
   - light theme
   - long-language cases like Hindi/Telugu/Tamil

