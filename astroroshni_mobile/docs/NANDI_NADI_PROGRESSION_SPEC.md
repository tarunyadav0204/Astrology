# Bhrigu Nandi Nadi Screen — Product Spec

**Status:** Draft for review  
**Goal:** A complete Bhrigu Nandi Nadi view for astrologers: four Purushartha trikonas, trines, progression timeline, and Nadi-relevant chart summary.

---

## 1. Screen purpose and placement

- **Name (suggested):** “Bhrigu Nandi Nadi” or “Nandi Nadi Analysis”
- **One-liner:** Key Bhrigu/Nadi concepts in one place: Moksha, Artha, Dharma, Kama trikonas; trines; and life progression timeline.
- **Audience:** Astrologers and users who want a classical Nadi-style view (not just a simple “reading”).
- **Placement:** New screen under Analysis (or “Classical” / “For Astrologers”). Requires birth data.
- **Entry points:** Analysis hub, Dasha/Chart “See also”, or a “Nadi” subsection.

---

## 2. What a Nadi astrologer likes to see (design guide)

- **Four Purushartha trikonas** — Dharma (1-5-9), Artha (2-6-10), Kama (3-7-11), Moksha (4-8-12): which houses, which planets sit there, lords, and a simple “strength” or “focus” indicator so they can quickly see which life theme is strong/weak.
- **Trines and direction** — Classical trines (1-5-9, 3-7-11) and how planets relate (same direction 1-5-9 vs opposite 3-7-11); lords of trikona houses and their placement.
- **Moon nakshatra (and pada)** — Central to Nadi; always visible as birth context. Optional: which “Nadi year” or nakshatra cycle they’re in.
- **Progression over time** — Which period/phase they’re in now and what theme (which trikona or purushartha) is emphasized; past/future timeline for planning or client explanation.
- **Compact, scannable layout** — Trikonas as cards or rows (not a full chart only); one tap to expand “which planets, which signs” and lord positions.
- **Optional for later:** Reference to “which Nadi” or sutra (if we ever have Bhrigu Nadi text DB); dasha–Nadi correlation (current dasha + active trikona).

---

## 3. What we show (sections and fields)

### 3.1 Header / birth context (personalization)

| Item | Purpose |
|------|--------|
| Screen title | e.g. “Bhrigu Nandi Nadi” |
| Short subtitle or info link | “Four trikonas, trines & progression” |
| **Birth context (compact)** | **Moon nakshatra** + pada, Moon rashi; optional Lagna. So Nadi astrologer sees the key Nadi inputs at a glance. |

Backend: from existing chart API — `moonNakshatra`, `moonNakshatraPada`, `moonRashi`, optional `lagna`, `lagnaRashi`.

---

### 3.2 Four Purushartha trikonas (core Nadi concept)

Show all four trikonas in one scannable block (e.g. four cards or four rows). Each trikona = three houses from classical mapping:

| Trikona | Houses | Theme (Purushartha) | Phala (result) house |
|---------|--------|---------------------|----------------------|
| **Dharma** | 1, 5, 9 | Righteousness, wisdom, luck | 9th |
| **Artha** | 2, 6, 10 | Wealth, livelihood, karma/work | 2nd |
| **Kama** | 3, 7, 11 | Desire, partnership, gains | 7th |
| **Moksha** | 4, 8, 12 | Liberation, transformation, renunciation | 12th |

**Per trikona we show:**

| Item | Purpose |
|------|--------|
| **Trikona name** | Dharma / Artha / Kama / Moksha |
| **Houses** | e.g. “1–5–9” or “H1, H5, H9” |
| **Planets in these houses** | Which planets occupy any of the three houses (e.g. “Sun in 5, Mars in 9”) |
| **Lords of these houses** | Lords of 1st, 5th, 9th (etc.) and where they are placed (sign/house) |
| **Strength / status (optional)** | Simple indicator: Strong / Moderate / Weak or a score, so astrologer can see which purushartha is emphasized. |

Backend must provide (from chart calculation):

- For each trikona: `houses` (e.g. [1,5,9]), `planetsInHouses` (e.g. [{ planet, house, sign }]), `lords` (e.g. [{ house, lord, placedInSign, placedInHouse }]), optional `strength` or `score`.

---

### 3.3 Trines (classical trines and direction)

| Item | Purpose |
|------|--------|
| **Dharma Trine (1–5–9)** | Same-direction trine; planets here strengthen each other. Show planets in 1, 5, 9 and their lords’ placement. |
| **Kama / 3–7–11** | Opposite-direction; partnership, desire, gains. Show planets in 3, 7, 11 and lords. |
| **Optional short note** | One line: “1–5–9: same direction; 3–7–11: aspecting” so astrologers know the Nadi directional logic. |

Backend: can derive from same house/planet data as trikonas; optionally expose “trineSummary” (which planets in 1-5-9 vs 3-7-11) for labels.

---

### 3.4 Current period (hero block)

| Item | Purpose |
|------|--------|
| **Current period label** | e.g. “Current phase: [Name]” or “You are in the [X] period” |
| **Date range** | Start – End for current period (e.g. “Jan 2024 – Dec 2026”) |
| **Short interpretation (1–3 sentences)** | Theme and tone for “right now”; can tie to active trikona (e.g. “Artha period”) |
| Optional | One “theme” or “keyword” pill; link to “Active trikona: Artha” if applicable |

Backend: `currentPeriod`: `{ id?, name, startDate, endDate, summary, theme?, activeTrikona? }`

---

### 3.5 Progression timeline (main content)

A **list of periods** (past, current, future) so the user sees how Nandi Nadi “progresses” over their life.

| Per period | Purpose |
|------------|--------|
| **Period name** | e.g. “Rohini phase”, “Ardra phase”, or your naming scheme |
| **Date range** | Start – End (ISO or formatted) |
| **Short summary** | 1–2 sentences; same style as current period |
| **Visual state** | Past (muted), Current (highlighted), Future (normal). Optional: tag with **active trikona** (Dharma/Artha/Kama/Moksha) for that period. |

Backend: `periods`: array of `{ id?, name, startDate, endDate, summary, theme?, isCurrent?, activeTrikona? }`, sorted by `startDate`. Optional: `nakshatraBased` or `periodType` for “Why this period?”.

---

### 3.6 Period detail (tap to expand or modal)

When user taps a period (especially current or upcoming):

| Item | Purpose |
|------|--------|
| Same as timeline row | Name, date range, summary |
| **Extended interpretation** | 2–4 sentences or bullet points: areas of life (career, health, relationships, finances, spirituality) and tone |
| Optional | Simple “what to focus on” or one-line remedy; optional “Active trikona” for this period. |

Backend: per period `detail` or `extendedSummary`; or on-demand `GET /nandi-nadi-period-detail?periodId=...`.

---

### 3.7 Info / “What is Bhrigu Nandi Nadi?” (modal or expandable)

| Item | Purpose |
|------|--------|
| Title | “What is Bhrigu Nandi Nadi?” |
| Body (2–4 sentences) | Explain: classical Nadi system; four Purushartha trikonas (Dharma, Artha, Kama, Moksha); trines; and how progression shows which life theme is active over time. |
| Optional | Short “How we use your chart” (Moon nakshatra, houses, trikona lords). |

Copy in app or CMS; no backend.

---

### 3.8 Empty / error states

| State | What we show |
|-------|------------------|
| No birth data | Same as Sade Sati: redirect to Birth Profile Intro (returnTo: NandiNadiProgression) or show “Add birth profile” CTA. |
| Calculation error or no periods | “We couldn’t generate your Nandi Nadi progression. Please try again.” + Retry. |
| Loading | Spinner + “Loading your Nandi Nadi progression…” |

---

## 4. Data we need from backend (summary)

- **Birth context:** Moon nakshatra, pada, Moon rashi; optional Lagna (from existing chart API).
- **Four trikonas:** For each trikona (Dharma 1-5-9, Artha 2-6-10, Kama 3-7-11, Moksha 4-8-12): planets in those houses (planet, house, sign), lords of those houses and their placement (sign, house), optional strength/score.
- **Trines:** Can derive from same house/planet data; optional “trineSummary” for 1-5-9 vs 3-7-11.
- **Current period:** name, startDate, endDate, summary, theme?, activeTrikona?.
- **Periods list:** array of { name, startDate, endDate, summary, theme?, isCurrent?, activeTrikona? }, sorted by time.
- **Period detail (optional):** extendedSummary, optional focus/remedy, optional activeTrikona per period.

**Request:** Birth data (date, time, place) + optional “as of” date (default: today).

---

## 5. Open questions to finalize

1. **Period naming:** Do we use nakshatra names (e.g. “Rohini period”), your own phase names, or “Year 1 / Phase 1” style? This affects backend and copy.
2. **Time span:** How many years to show? (e.g. birth → 80 years, or “current decade + next 2”, or configurable?)
3. **Themes/tags:** Do we want consistent “life themes” (Health, Wealth, Career, etc.) per period, or free-form summary only?
4. **Credits:** Should this screen consume credits (e.g. one credit per view or per profile)? Affects where we call credit check and API design.
5. **Date picker:** Like Dasha Browser “as of date”, or always “today”? Recommend “today” for v1.
6. **Trikona strength:** Simple Strong/Moderate/Weak from rules (e.g. benefics in trikona, lord placement), or leave as “planets + lords” only for v1?

---

## 6. What we are NOT doing in v1 (out of scope)

- Full Nadi “readings” (long-form paragraphs from classical texts).
- Editing or customizing periods from the app.
- Comparing two profiles or two dates side-by-side.
- Remedy engine or product recommendations.
- Full Bhrigu Nadi “leaf” or grantha text lookup (can be a later phase if we have a text DB).

---

Once you confirm or adjust the sections above (trikona strength, period naming, time span, themes), we can treat this as the final spec and design the backend API (request/response shapes and endpoints) to match.
