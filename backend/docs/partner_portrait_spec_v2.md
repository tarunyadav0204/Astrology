# AstroRoshni Partner Portrait Spec v2

Status: **specification only** — not yet implemented. Current runtime remains `bphs-partner-portrait/1.5.1` in `backend/partner_profile/`.

## Aims

1. Stay faithful to classical Jyotish.
2. Still generate a realistic human portrait prompt.

Classics often give symbolic colour/shape language (“blood-red”, “green”, “tawny”, “variegated”). A real portrait engine cannot literally draw a green spouse because Mercury dominates. This spec therefore separates:

- **Classical evidence**
- **Modern portrait inference**

---

## 1) Core principle

The engine must produce an **approximate spouse archetype**, not a literal real-world identity.

It should answer:

- likely complexion range
- face shape
- build / body type
- height tendency
- hair texture / density
- eye quality
- overall visual impression
- temperament / vibe

It should **not** claim:

- exact resemblance
- exact ethnicity / caste / community
- exact facial identity

---

## 2) Classical base to use

Primary classical sources:

| Source | Role |
|---|---|
| BPHS Ch. 3 | Graha nature and bodily form |
| BPHS Ch. 4 | Rashi nature and bodily form |
| BPHS Ch. 7 | Navamsha importance |
| BPHS Ch. 18 | 7th house matters |
| BPHS Ch. 32 | Chara karakas |
| Brihat Jataka | Spouse description through 7th sign / Navamsha |
| Saravali / Phaladeepika | Refinement, strength, condition, spouse significations |

---

## 3) Two-layer model

### Layer A — Classical evidence layer

Identifies which grahas/signs are describing the spouse.

### Layer B — Portrait inference layer

Converts classical descriptions into modern realistic portrait attributes.

Examples:

| Classical | Portrait inference |
|---|---|
| Mercury = greenish | olive / neutral-wheatish undertone, youthful look |
| Venus = variegated, beautiful | clear skin, attractive symmetry, soft pleasant features |

---

## 4) Evidence channels

Do not treat every signal as fully independent. Use **evidence groups**.

### A. Primary spouse-definition channels

| Channel | Role | Base strength |
|---|---|---|
| D1 7th sign | body form / visual field / general spouse type | 1.00 |
| D1 7th lord | core spouse graha | 1.00 |
| Planet occupying D1 7th | strong direct modifier | 0.95 |
| Planet strongly aspecting D1 7th | important modifier | 0.75 |
| Planet conjoining 7th lord | modifier of spouse form | 0.75 |
| Planet aspecting 7th lord | secondary modifier | 0.60 |

### B. Navamsha confirmation channels

| Channel | Role | Base strength |
|---|---|---|
| D9 7th sign | refinement / confirmation | 0.80 |
| D9 7th lord | refinement / confirmation | 0.80 |
| Planet occupying D9 7th | direct D9 spouse modifier | 0.75 |
| Planet aspecting D9 7th or D9 7th lord | D9 modifier | 0.55 |
| D1 7th lord's Navamsha sign/lord | refinement of spouse type | 0.65 |

### C. Supplemental channels

| Channel | Role | Base strength |
|---|---|---|
| Darakaraka | supplementary spouse signature | 0.50 |
| Natural spouse karaka (Venus for wife, Jupiter for husband) | supportive only | 0.40 |
| UL / A7 etc. | optional advanced layer, not default | 0.30 |

### Important dependency rule

If multiple signals arise from the same root chain, reduce duplication.

Example:

- 7th sign = Taurus
- 7th lord = Venus
- Venus aspects Taurus

This is strong Venus dominance, but **not** three fully separate votes.

**Chain cap:** for one same-root pattern, total effective strength should be capped at **2.2** before Navamsha confirmation. This prevents fake overconfidence.

---

## 5) What each channel is allowed to influence

Different channels influence different features with different priority.

| Feature | Best channels |
|---|---|
| Build / frame | 7th sign, 7th lord, D9 7th sign |
| Face shape | 7th sign, 7th lord, 7th occupant |
| Complexion | 7th lord, 7th occupant, D9 7th lord/occupant; spouse karaka only if marriage-linked |
| Hair | Venus, Saturn, Rahu/Ketu, sign influences |
| Eyes / expression | Sun, Moon, Venus, Mars, Saturn, Rahu |
| Temperament / vibe | all channels |
| Attractiveness / polish | Venus, Moon, Jupiter, Libra/Taurus/Pisces |
| Distinctiveness / unusualness | Rahu, Ketu, Scorpio, Aquarius |

---

## 6) Condition handling — do NOT use hard multipliers

Do **not** use artificial numeric multipliers such as:

- exalted × 1.20
- debilitated × 0.55
- combust × 0.80

Instead, split each graha into:

1. **Representation strength** — how much this graha describes the spouse.
2. **Condition quality** — how cleanly or distortedly the trait manifests.

### Recommended condition tags

| Condition | Effect on portrait inference |
|---|---|
| Exalted / own / moolatrikona | clear, high-quality expression |
| Friendly sign | supportive expression |
| Neutral sign | normal expression |
| Enemy sign | mixed or less clean expression |
| Debilitated | weakened / refined-distorted expression, not erased |
| Neecha-bhanga | mixed but restored / unusual strength after weakness |
| Combust | visible but overheated, tightened, less smooth |
| Retrograde | intensified / internalized / atypical expression |
| Rahu influence | exotic, unusual, mixed, amplified |
| Ketu influence | fine, detached, understated, unusual |
| Saturn influence | dries, lengthens, darkens, ages |
| Venus influence | beautifies, smoothens, harmonizes |
| Moon influence | softens, rounds, brightens |
| Mars influence | sharpens, reddens, leans |

So a debilitated Venus can still make a spouse Venusian-looking, but with:

- less softness
- more irregularity
- less refined expression of beauty

---

## 7) Graha portrait rules

Corrected portrait-inference rules. First phrase = classical cue; second = real portrait output.

### Sun

**Classical:** reddish, square body, limited hair, honey-coloured eyes, dignified

**Portrait inference:**

- complexion: warm medium to reddish-wheatish
- face: structured, squarish, defined bone lines
- build: upright, firm, moderate
- hair: less abundant or neatly kept
- eyes: bright, authoritative, warm
- vibe: dignified, composed, self-possessed

### Moon

**Classical:** round, pleasing, soft, changeful

**Portrait inference:**

- complexion: lighter, soft, luminous, fair-to-wheatish
- face: round/oval, full cheeks, gentle softness
- build: soft or rounded
- hair: soft
- eyes: moist, kind, approachable
- vibe: receptive, gentle, comforting

### Mars

**Classical:** reddish, thin waist, energetic, sharp

**Portrait inference:**

- complexion: warm wheatish with reddish cast
- face: angular, sharper jaw/features
- build: lean, wiry, athletic
- hair: coarser or practical
- eyes: direct, intense
- vibe: active, decisive, quick-reacting

### Mercury

**Classical:** greenish, attractive, intelligent, playful speech

**Portrait inference:**

- complexion: neutral-olive to wheatish; sometimes clearer undertone
- face: youthful, balanced, smaller refined features
- build: medium, neat, agile
- hair: neat, moderate
- eyes: alert, lively
- vibe: youthful, clever, articulate

**Important:** do not render literal green skin. Mercury’s “green” means olive undertone, neutral-wheatish, youthful freshness.

### Jupiter

**Classical:** tawny, large, substantial, wise

**Portrait inference:**

- complexion: warm golden-wheatish to lighter tawny
- face: fuller, broad, benevolent
- build: broad, substantial, healthy
- hair: fuller / warm brown
- eyes: calm, warm, dignified
- vibe: wise, protective, principled

### Venus

**Classical:** variegated, beautiful, charming eyes, curly hair

**Portrait inference:**

- complexion: clear, attractive, smooth, luminous; fair-to-wheatish depending on support
- face: symmetrical, pleasant, graceful, refined
- build: proportionate, appealing
- hair: soft, wavy/curly, well-shaped
- eyes: beautiful, attractive, charming
- vibe: affectionate, artistic, polished, socially graceful

**Important:** Venus does **not** automatically mean “very fair.” Venus means beauty + harmony + lustre first.

### Saturn

**Classical:** dark, thin, long, coarse hair, serious

**Portrait inference:**

- complexion: deeper / dusky / darker or dry-looking
- face: elongated, bony, restrained
- build: lean, long-limbed, spare
- hair: coarse, dry, less lush
- eyes: serious, slightly tired / deep-set
- vibe: reserved, enduring, mature

### Rahu

**Classical:** smoky, unusual, mixed

**Portrait inference:**

- complexion: mixed / difficult to classify; smoky, dusky or striking contrast
- face: unusual, memorable, unconventional
- build: irregular or standout
- hair/eyes: striking, hypnotic, unusual styling or texture
- vibe: magnetic, intense, unconventional

### Ketu

**Classical:** similar to Rahu, detached

**Portrait inference:**

- complexion: muted / fine / unusual / understated
- face: sharp or hard-to-place
- build: fine or lean
- eyes: detached, inward, perceptive
- vibe: private, subtle, detached, spiritual

---

## 8) Rashi portrait rules

Signs mainly describe body frame, shape tendency, and behavioral impression. They influence complexion **less** than planets.

| Sign | Build | Face | Vibe |
|---|---|---|---|
| Aries | active, energetic, medium-strong | prominent, defined | direct, courageous |
| Taurus | solid, stable, attractive, pleasant | fuller or well-shaped | grounded, sensual, calm |
| Gemini | medium, flexible, lively | youthful, expressive | communicative, curious |
| Cancer | soft, rounded, receptive | fuller, gentle | nurturing, sensitive |
| Leo | commanding, noticeable | dignified, broader upper structure | noble, confident |
| Virgo | neat, medium, fine | composed, cleaner lines | practical, observant |
| Libra | balanced, graceful | symmetrical, attractive | social, polished |
| Scorpio | compact or lean, intense | penetrating, private, magnetic | deep, guarded, powerful |
| Sagittarius | proportionate, open, longer frame possible | straightforward, clear | principled, expansive |
| Capricorn | bony, strong-framed or lean-dry | restrained, serious | practical, enduring |
| Aquarius | medium, distinctive, slightly unconventional | thoughtful, detached | independent, observant |
| Pisces | soft-medium, gentle | kind, fluid, dreamy | receptive, compassionate |

---

## 9) Trait dimensions to score separately

Do not merge everything into a single vague sentence. Score these separately:

1. **Skin tone depth** — very light / light / light-medium / medium / medium-deep / deep
2. **Undertone** — warm / neutral / cool / olive
3. **Lustre / clarity** — matte / soft / clear / luminous
4. **Face shape** — round / oval / square / elongated / angular / balanced
5. **Build** — lean / wiry / medium / soft-rounded / broad / substantial
6. **Height tendency** — shorter / medium / taller / long-limbed
7. **Hair** — sparse / moderate / thick; straight / wavy / curly / coarse; soft / dry
8. **Eyes** — soft / sharp / bright / beautiful / serious / penetrating
9. **Overall impression** — attractive / dignified / youthful / intense / unusual / reserved / graceful

---

## 10) Complexion resolution logic

Do not use one single graha to declare complexion unless evidence is very strong.

Use three subcomponents:

### A. Tone depth

- Moon / Jupiter / Venus tend to lighten or brighten
- Saturn / Rahu tend to deepen or darken
- Sun / Mars tend toward medium warm
- Mercury tends toward medium / olive / neutral
- Ketu tends toward muted / pale / dry

### B. Undertone

- Sun / Mars = warm / red
- Mercury = olive / neutral
- Moon = cool-soft / pale-soft
- Jupiter = golden-warm
- Venus = balanced-clear / luminous
- Saturn = dry-neutral / darker
- Rahu = smoky-mixed
- Ketu = muted-neutral

### C. Lustre

- Venus / Moon / Jupiter increase lustre
- Saturn / Ketu reduce lustre / dry it
- Rahu gives strange glamour or intensity
- Sun gives brightness but not always softness

### Complexion decision rule

Only output a specific complexion description if either:

- one dominant spouse chain clearly supports it, **and**
- D9 does not contradict strongly

Otherwise output a blended realistic phrase such as:

- wheatish complexion with warm undertone
- fair-to-wheatish with clear skin
- medium complexion with olive undertone
- dusky complexion with strong striking features

This is better than overclaiming “very fair” or “dark”.

---

## 11) Combination rules

Use combination rules because real charts are mixed.

| Combination | Portrait tendency |
|---|---|
| Moon + Venus | softer, prettier, fairer/clearer, attractive eyes, pleasing face |
| Venus + Jupiter | attractive + healthy + fuller + graceful; fair-to-wheatish / luminous |
| Venus + Mercury | youthful beauty, fine symmetry, clear skin, balanced features |
| Sun + Mars | warm or reddish complexion, sharper structure, stronger features |
| Mars + Saturn | lean, dry, angular, severe, darker or harsher look |
| Venus + Saturn | beauty with seriousness; attractive but less soft; can become wheatish/dusky, longer face |
| Venus + Rahu | glamorous, unconventional, eye-catching, “different” |
| Venus + Ketu | attractive but understated, refined, detached, not overly lush |
| Moon + Jupiter | soft, fuller, brighter, benevolent face; fair/wheatish-golden |
| Mercury + Saturn | lean, restrained, thoughtful, medium-to-darker neutral look |
| Mars + Rahu | intense, sharp, unusual, edgy appearance |

---

## 12) Confidence system

### Global levels

**Strong** when:

- clear D1 support, and
- D9 confirmation, and
- no major contradiction

**Moderate** when:

- D1 supports, but D9 is mixed, or
- one dominant chain exists but secondary channels are mixed

**Suggestive** when:

- evidence is scattered or contradictory

### Feature-level confidence

Each feature gets its own confidence. Example:

- complexion: moderate
- build: strong
- eyes: strong
- hair: suggestive

Prefer this over one single global confidence.

---

## 13) What goes into the final portrait prompt

Only include:

- features with **strong** or **moderate** confidence
- suggestive features only if needed and clearly softened

### Final prompt format (example)

> Create a realistic portrait of an Indian man in his early 30s. He has a medium-to-wheatish complexion with a warm golden undertone and clear skin. His face is balanced-oval with pleasant symmetry and attractive eyes. Build is medium and proportionate, with a calm dignified presence. Hair is soft and slightly wavy. Overall vibe is refined, grounded and quietly charismatic.

Notice:

- it does not overclaim exact identity
- it gives blended output
- it respects classical signals without becoming cartoonish

---

## 14) Portrait synthesis algorithm

### Step 1 — Identify spouse channels

Collect:

- D1 7th sign
- D1 7th lord
- D1 7th occupants
- aspects to 7th and 7th lord
- D9 7th sign / lord / occupants
- D1 7th lord in D9
- Darakaraka
- natural spouse karaka

### Step 2 — Build evidence chains

Group signals into chains (e.g. Venus chain, Moon chain, Saturn chain). Apply chain cap so one logic path is not overcounted.

### Step 3 — Score features separately

For each feature (complexion depth, undertone, lustre, face shape, build, height, hair, eyes, vibe), aggregate only relevant signals.

### Step 4 — Apply condition filters

Check:

- exaltation / debilitation
- combustion
- retrogression
- conjunction with Rahu / Ketu / Saturn / Mars / Venus / Moon
- dignity of 7th lord
- affliction to 7th / D9 7th

Use this to modify **quality**, not erase the feature.

### Step 5 — Resolve contradictions

Example:

- Venus says clear/fairer
- Saturn says darker/drier

Final output:

- wheatish to dusky-clear complexion
- attractive but serious
- graceful yet restrained

### Step 6 — Generate human-readable profile

Output should contain:

**A. Classical basis** — short explanation  
(“7th house Taurus and 7th lord Venus strongly influence the spouse; D9 confirms Saturn refinement…”)

**B. Portrait summary** — complexion, face, build, hair, eyes, vibe

**C. Image prompt** — clean prompt for the image generator

---

## 15) Rules for region and ethnicity

Important:

- region can shape **styling**, not override resolved form
- never do: “Indian means wheatish”
- never override classical result with social assumptions

Correct use — regional context only affects:

- clothing
- hair styling
- cultural appearance context
- background art direction

It should not erase the astrology-driven result.

---

## 16) Safe defaults when evidence is weak

| Weak feature | Default |
|---|---|
| Complexion | medium complexion |
| Hair | moderate dark hair |
| Height | medium height / average frame |
| Face shape | oval-balanced |

This prevents nonsense outputs.

---

## 17) Example output template

### Structured output

```text
Primary spouse chains:
- Venus chain: strong
- Moon chain: moderate
- Saturn chain: weak

Resolved portrait:
- Complexion: fair-to-wheatish, clear, softly luminous
- Undertone: warm-neutral
- Face: oval-balanced, pleasant symmetry
- Build: medium, proportionate
- Height tendency: medium
- Hair: soft, slightly wavy
- Eyes: attractive, calm, expressive
- Overall impression: refined, graceful, affectionate

Confidence:
- complexion: moderate
- build: strong
- face: strong
- hair: moderate
- eyes: strong
```

### Image prompt

> Create a realistic portrait of a spouse archetype, not an exact identity. Show an attractive adult with a fair-to-wheatish clear complexion, warm-neutral undertone, balanced oval face, pleasant symmetry, calm expressive eyes, medium proportionate build, and soft slightly wavy hair. Overall look should feel refined, graceful, and quietly affectionate. Keep the style realistic and natural.

---

## 18) Final implementation guidance

### Best practice

- keep classical descriptors
- convert them into realistic blended human features
- use D1 + D9 together
- avoid literal weird outputs from symbolic colours
- keep feature-level confidence

### Avoid

- literal “Mercury = green skin”
- “Venus = always fair”
- “debilitated graha = nearly no influence”
- counting the same Venus logic three times as three independent proofs

---

## Next-step options (not yet done)

| Option | Deliverable |
|---|---|
| **A** | Developer-ready JSON rule schema |
| **B** | Pseudocode / scoring logic for implementation |
| **C** | Prompt generator template: kundli → reasoning + structured traits + image prompt |
