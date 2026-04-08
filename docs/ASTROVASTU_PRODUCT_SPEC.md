# AstroVastu — product specification

**Status:** Living document — for product, design, and engineering alignment while building.  
**Last updated:** 2026-04-07  
**Internal positioning:** Generic Vastu optimizes the building; AstroVastu optimizes the *person inside the building* — and updates when *their time* changes.

---

## Table of contents

1. [Product pillars](#1-product-pillars)
2. [High-level architecture](#2-high-level-architecture)
3. [Conceptual data model](#3-conceptual-data-model)
4. [End-to-end user experience](#4-end-to-end-user-experience)
5. [Screen-by-screen wireframes](#5-screen-by-screen-wireframes)
6. [Global UX patterns](#6-global-ux-patterns)
7. [Phased rollout](#7-phased-rollout)
8. [Non-functional requirements](#8-non-functional-requirements)
9. [Open decisions](#9-open-decisions)

---

## 1. Product pillars

| Pillar | What it means |
|--------|----------------|
| **Chart-native** | Every insight ties to *this user’s* chart (lords, dignity, affliction, Dasha, Gochar), not generic Vastu copy. |
| **Space-native** | Outputs name **zones and objects** (toilet, bed, stove, clutter), not only abstract advice. |
| **Time-dynamic** | Guidance shifts with **Dasha / Antardasha** and material transits (“active zone this month”). |
| **Low-friction remedies** | Prefer **non-destructive** steps (color, element, rearrange) before structural changes. |
| **Evidence loop** | User check-ins (“shift / no shift”) build trust and tune recommendations over time. |

---

## 2. High-level architecture

Five layers. Ship incrementally; together they form a defensible product.

### Layer A — Identity and chart engine

- Auth, saved profiles, existing chart pipeline (`ChartCalculator`, etc.).
- **Single source of truth:** a normalized **chart package** (planets, houses, lords; optional D9/D10 snippets) per run or cached per user.

### Layer B — Chart → space mapping engine (core IP)

- **Deterministic, versioned rules** (e.g. `mapping_v1`, `mapping_v2`): house/sign/lord ↔ **8 or 16 Vastu zones** (pick one convention and document it).
- **Outputs:** per zone — weights, active lord, karakatwa hints, flags (amplify / stabilize / drain).
- **Temporal overlay:** from “today” → Vimshottari slice (Maha ± Antara as needed), key transits to lagna / relevant houses → **priority-ranked zones** for a horizon (days / weeks / months).

### Layer C — Home model (physical reality)

| Stage | What the user provides |
|-------|-------------------------|
| **V1** | Main **door facing** (compass or manual N/E/S/W ± deviation). **Tap grid**: tag zones with toilet, bed, kitchen/stove, desk, storage, main door, other. |
| **V2** | Richer layout (simple room polygons); still zone-centric. |
| **V3** | Optional sketch/photo + labels; ML later if justified. |

Persist **`HomeProfile`**: primary home, office, other locations.

### Layer D — Reasoning / narrative (AI + guardrails)

- **AI must not invent directions.** Input = structured JSON from Layer B + C + goal + constraints (“renting”, “no renovation”).
- **AI role:** explain, prioritize, phrase remedies, connect chart language ↔ room language, localization.
- **Guardrails:** link to `rule_id` + `mapping_version`; wellness/legal disclaimers; no false certainty.

### Layer E — Engagement and trust

- Outcome check-ins tied to specific recommendations.
- **Explainability:** “Why this for me” with optional advanced (rule ids).
- Shareable **teaser** card (viral) without leaking full private detail.

---

## 3. Conceptual data model

| Entity | Purpose |
|--------|---------|
| **`UserChartSnapshot`** | Chart hash, computed payload, `created_at`. |
| **`HomeProfile`** | Facing, layout type, zone tags, optional plan metadata; multi-location. |
| **`AstroVastuRun`** | Inputs: snapshot id, home id, goal, date range; outputs: deterministic scores JSON, narrative id, version pins. |
| **`Recommendation`** | `zone_id`, severity, `rationale_refs[]`, remedy steps (tiers), effort, contraindications. |
| **`FeedbackEvent`** | `rec_id`, Likert + optional text, `days_since`. |

Enables reproducibility (“why did we say NE?”) and iteration without black-box drift.

---

## 4. End-to-end user experience

### Discovery

- One-line hook: *Your chart, mapped onto your home — not generic Vastu.*

### Onboarding (happy path)

1. **Goal** — wealth / career / relationship / health / focus / “stuck”.
2. **Birth data** — confirm or edit; compute chart package.
3. **Facing** — compass or manual; approximate is OK.
4. **Quick space map** — tap zones + tag key functions (toilet, bed, stove, etc.); optional skip (degraded precision).

### Core loop

5. **Processing** — short interstitial; educate (“houses + your tags”).
6. **Hero: Personal Energy Map** — heatmap + **one hero action** + optional “generic vs yours”.
7. **Ranked zone list** — tap into zone detail.
8. **Zone detail** — chart paragraph, home paragraph, **tiered remedies** (5 min / this week / renovate if possible), “Why for me?” sheet.
9. **Check-in scheduling** — reminder cadence (3 / 7 / 14 days).
10. **Outcome** — yes / unsure / no → branch to next step or softer remedy / diagnostic (more tags).
11. **Next lever** — next zone or second location; retention.

### Growth surfaces

- **Share card** — branded teaser.
- **Push / widget** — time-dynamic (“sensitive zone shifted”, “new period — refresh East”).

### Tablet / desktop

- Hero: map left, card + list right.
- Zone detail: optional sticky remedy checklist.

---

## 5. Screen-by-screen wireframes

### Global (all screens)

- Top bar: **Back** (if nested) · **Title** · **`?`** explainability.
- **Primary CTA** in thumb zone when advancing a flow.
- **Explain drawer:** bottom sheet, optional “Advanced” (rule ids).

---

### S0 — Entry / discovery

```
┌─────────────────────────────┐
│  [←]  AstroVastu        [?] │
├─────────────────────────────┤
│  [ Hero illustration ]      │
│                             │
│  Your chart. Your space.    │
│  Not generic Vastu.         │
│                             │
│  Find the one zone that’s   │
│  fighting your energy now.  │
│                             │
│  [ Start — 2 min ]          │
│  [ How it’s different ]     │
└─────────────────────────────┘
```

**CTA:** `Start — 2 min` · Secondary: `How it’s different` (short modal).

---

### S1 — Goal selection

```
┌─────────────────────────────┐
│  [←]  What do you want      │
│       to improve?       [?] │
├─────────────────────────────┤
│  Pick one (you can change   │
│  later):                    │
│                             │
│  ( ) Wealth / stability     │
│  ( ) Career / reputation    │
│  ( ) Relationship / family  │
│  ( ) Health / rest          │
│  ( ) Focus / mental noise   │
│  ( ) Everything feels stuck │
│                             │
│  [ Continue ]               │
└─────────────────────────────┘
```

**Validation:** one selection required.

---

### S2 — Birth data confirm

```
┌─────────────────────────────┐
│  [←]  Your birth details    │
│                         [?] │
├─────────────────────────────┤
│  Using: Name · DOB · time   │
│  · place                    │
│                             │
│  [ Edit details ]           │
│                             │
│  We use this to map houses  │
│  to directions for *you*.   │
│                             │
│  [ Use this chart ]         │
└─────────────────────────────┘
```

**Empty:** no saved chart → inline birth form. **Error:** chart compute fail → Retry.

---

### S3 — Home facing (compass anchor)

```
┌─────────────────────────────┐
│  [←]  Which way does your   │
│       main door face?   [?] │
├─────────────────────────────┤
│      [ Compass / wheel ]    │
│  Selected: East (E)         │
│  [ Calibrate compass ]      │
│  [ I’ll pick manually ]     │
│  [ Continue ]               │
└─────────────────────────────┘
```

**Error:** compass denied → manual only + tip.

---

### S4 — Quick space map (tap grid)

```
┌─────────────────────────────┐
│  [←]  Mark your home        │
│       (approximate)     [?] │
├─────────────────────────────┤
│        NW    N    NE        │
│   W  [ BRAHM ]  E          │
│        SW    S    SE       │
├─────────────────────────────┤
│  Tap zone → tag: Toilet,    │
│  Bed, Kitchen/stove, Desk,  │
│  Storage, Main door, Other   │
│  Progress: 3 / 8            │
│  [ Skip — use minimal map ] │
│  [ Build my energy map ]    │
└─────────────────────────────┘
```

**CTA:** enabled when main door + minimal signals, or explicit skip.

---

### S5 — Processing interstitial

Skeleton + copy: *Mapping your houses to directions…* + one-sentence trust tip. Auto-advance. **Error:** Retry.

---

### S6 — Hero: Personal Energy Map

```
┌─────────────────────────────┐
│  [←]  Your energy map [Share]│
├─────────────────────────────┤
│  Goal: …                    │
│  [ Compass heatmap ]        │
│  ┌─────────────────────┐   │
│  │ THIS MONTH FOR YOU  │   │
│  │ One hero zone + tag  │   │
│  └─────────────────────┘   │
│  [ See full breakdown ]     │
│  [ Compare vs generic ]     │
└─────────────────────────────┘
```

**Degraded:** banner if user skipped tags — CTA to complete map.

---

### S7 — Zone list (priority ranked)

```
┌─────────────────────────────┐
│  [←]  Zones ranked for you │
├─────────────────────────────┤
│  1 ● NE    HIGH  …         │
│  2 ● SW    MED   …         │
│  3 ○ E     WATCH …         │
│  [ Open top priority ]      │
└─────────────────────────────┘
```

Row tap → S8.

---

### S8 — Zone detail

```
┌─────────────────────────────┐
│  [←]  Zone name      [Why?]│
├─────────────────────────────┤
│  FOR YOUR CHART (plain)     │
│  IN YOUR HOME (tags)        │
│  DO THIS                    │
│  □ 5 min  □ week  □ renovate│
│  [ I did the 5-min fix ]    │
│  [ Set reminder ]           │
└─────────────────────────────┘
```

**Why?** → sheet with optional Advanced (rule ids).

---

### S9 — Check-in scheduler

Remind in 3 / 7 / 14 days. Save → toast. **Error:** notifications denied → in-app only copy.

---

### S10 — Check-in outcome

Yes / small / no + optional note → branch to celebrate, softer remedy, or diagnostic (more tags).

---

### S11 — Next step

Next zone or “Add office / second home” (new `HomeProfile`).

---

### S12 — Share preview

Branded image + teaser copy; `Copy link` / system share. **Error:** fall back to text.

---

### S13 — Settings

Homes list, mapping version explainer, **Re-run analysis today**.

---

### S14 — Push / widget (system)

Deep link to **S6** with **time ribbon** expanded. Example copy: *Your sensitive zone shifted this week.*

---

### Flow summary

`S0 → S1 → S2 → S3 → S4 → S5 → S6 → (S7) → S8 → S9 → … → S10 → S11` (repeat).

---

## 6. Global UX patterns

- **Empty states:** always one clear next action (edit chart, add tags, skip with honest precision loss).
- **Errors:** retry + human message; never dead ends.
- **Accessibility:** compass fallback; no color-only status (icons/text also).
- **Privacy:** floor plan / layout as sensitive; retention policy stated in product legal copy.

---

## 7. Phased rollout

| Phase | Scope |
|-------|--------|
| **V1** | Wizard (goal, chart, facing, tap grid) + deterministic map + short AI narrative + 7-day check-in. |
| **V2** | Dasha/transit time ribbon + richer home model + “generic vs personal” compare. |
| **V3** | Multi-location, partner overlay, optional AR compass overlay. |

---

## 8. Non-functional requirements

- **Versioning:** mapping rules and prompt versions pinned per `AstroVastuRun`.
- **Performance:** target first interactive map **&lt; 2s** after chart + home known (excluding AI stream).
- **Safety:** avoid medical/legal guarantees; supportive disclaimers.
- **Observability:** log `run_id`, `mapping_version`, goal, home fidelity (full / skipped).

---

## 9. Open decisions

Track here as you decide:

- [ ] **Zone system:** 8 directions vs 16 zones (fixed choice + doc).
- [ ] **Mapping prescription:** exact house-to-compass rule book (reference text / guru approval).
- [ ] **Credits / paywall:** free tier vs credits (align with marriage/health patterns).
- [ ] **Locales:** `en` first; `hi` copy deck second?
- [ ] **AR:** in-scope for V3 only vs never.

---

## Document maintenance

- Bump **Last updated** when pillars, screens, or phases change.
- Add **Implementation links** (PRs, ADRs) below as they exist.

### Implementation links

- _(None yet — add e.g. `feat: AstroVastu V1 API` when started.)_
