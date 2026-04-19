# Agent JSON schemas

Conventions:

- Sign integer `s` is **always 1–12** in outputs: **1 = Aries, 2 = Taurus, …, 12 = Pisces** (not 0-based; same as “sign number” in common UI text).

## `ashtakavarga` (`a` = `"ashtakavarga"`)

D1 **Sarvashtakavarga** (12 sign totals) + **Bhinnashtakavarga** per classical planet (12 bindus each). Optional **D9** compact block when present in static context. Source: `ChatContextBuilder` static `ashtakavarga` (same as chat). Schema **v2** adds **`D1.Ho`** / **`D1.La`** when ascendant is available on static context.

| Key | Meaning |
|-----|--------|
| `D1.S` | 12 integers — total SAV bindus per **zodiac sign** index 0=Aries … 11=Pisces. **Do not treat index 0 as “1st house”** — use `D1.Ho` for house-numbered bindus. |
| `D1.La` | (v2) Lagna **sign** 1–12 (1=Aries … 12=Pisces). Present when `Ho` is emitted. |
| `D1.Ho` | (v2) **House from lagna (1–12)** → `{ "z", "zn", "s", "B" }`: `z`/`zn` = zodiac sign occupied by that house, `s` = SAV at that sign, `B` = per-planet BAV at that sign. **Prefer this object** whenever you cite “Nth house” SAV/BAV. |
| `D1.tb` | Total bindus (if available). |
| `D1.B` | Planet → 12 bindus (BAV per **sign** index, same indexing as `D1.S`). |
| `D9` | Optional: `S9` / `B9` when navamsa AV exists (sign-indexed; D9 lagna mapping is not expanded here). |

---

### Time scope (`sc`)

Many agents include **`sc`**: `"full"` | `"intent_window"` | `"current"`, resolved from `AgentContext.intent_result` (e.g. `mode=LIFESPAN_EVENT_TIMING` → `full`), `requested_period`, `transit_request`, or explicit `AgentContext.time_scope`. Env override: **`CONTEXT_AGENT_TIME_SCOPE`**. See `context_agents/scope.py` and README “Time scope”.
- **`nm`** is the English sign name for that `s` (disambiguates for LLMs).
- Longitudes are **sidereal absolute degrees** (0–360) as in `ChartCalculator` output.
- House `h` is **1–12** whole-sign from lagna (`ChartCalculator`).

---

## `core_d1` (`a` = `"core_d1"`)

Minimal natal D1 for identity + house/planet geometry. **Does not** include nakshatra names, divisionals, dashas, yogas, transits, or instructional text (other agents own those).

**Schema version** is in `v` (current **3**): v3 drops place/coords/tz from `b` (still required in input `birth_data` for the calculator). v2 added sign names on lagna and each planet row.

```json
{
  "a": "core_d1",
  "v": 3,
  "b": { "n": "string", "d": "YYYY-MM-DD", "t": "HH:MM" },
  "L": { "s": 6, "d": 25.25, "nm": "Virgo" },
  "P": [["Sun", 120.5, 5, "Leo", 10], ["Moon", 95.0, 4, "Cancer", 7]],
  "H": { "Mars": [1, 8], "Mercury": [2, 5] }
}
```

| Key | Meaning |
|-----|---------|
| `b` | Name + local date/time only (no lat/lon/place/tz in payload; those stay on the server input for chart math). |
| `L` | **Lagna (ascendant):** `s` = sign 1–12, `d` = degree within sign (0–30), `nm` = sign name (e.g. `"Virgo"`). |
| `P` | Planets in fixed order: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. Each row: `[name, longitude, sign_1_12, sign_name, house]`. |
| `H` | **House lordships (whole-sign):** each classical lord → list of **house numbers (1–12) it rules** from this lagna. Example: if lagna is Virgo, Mercury rules Virgo → **1st** house and Gemini → **10th** house, so `"Mercury": [1, 10]`. Venus rules Libra → **2nd** and Taurus → **9th** → `"Venus": [2, 9]`, etc. Sun and Moon each rule **one** sign in the zodiac, so they appear with **one** house number. Rahu/Ketu are omitted (not sign lords in this classical map). |

**Note:** Internally `ChartCalculator` uses sign index **0–11**; this agent always emits **1–12** plus **`nm`** so models are not confused with 0-based indexing.

**Omitted on purpose (other agents):** `bhav_chalit`, full `nakshatra` objects, `divisions`, per-planet **retro/dignity/combust** (see `d1_graha`), `asc_note` / validation prose.

---

## `d1_graha` (`a` = `"d1_graha"`)

Dignity / motion / combustion / avastha / strength summary **per graha**, same source as chat `planetary_analysis`: `ChatContextBuilder._build_static_context` → `PlanetAnalyzer.analyze_planet` → `_filter_planetary_analysis`. **Does not** add new calculators; runs full static context internally (heavy) and only emits `G`.

```json
{
  "a": "d1_graha",
  "v": 1,
  "G": {
    "Sun": {
      "r": false,
      "d": "exalted",
      "fn": "malefic",
      "sm": 1.2,
      "cb": false,
      "cz": false,
      "cs": "normal",
      "av": "Bala",
      "cg": "A",
      "sc": 72.5
    }
  }
}
```

| Field | Source in filtered `planetary_analysis` |
|-------|------------------------------------------|
| `r` | `retrograde_analysis.is_retrograde` |
| `d` | `dignity_analysis.dignity` |
| `fn` | `dignity_analysis.functional_nature` |
| `sm` | `dignity_analysis.strength_multiplier` |
| `cb` | `combustion_status.is_combust` |
| `cz` | `combustion_status.is_cazimi` |
| `cs` | `combustion_status.status` |
| `av` | `basic_info.avastha` (Baladi via `ChartCalculator.get_baladi_avastha`) |
| `cg` | `overall_assessment.classical_grade` |
| `sc` | `overall_assessment.overall_strength_score` |

**Not included here (same as filtered context omits or other agents):** full `aspects_received` list, `conjunctions` detail, `house_position_analysis` text — add a follow-up agent if needed.

---

## `vim_dasha` (`a` = `"vim_dasha"`)

Current **Vimshottari** periods (as of server “now”), **maraka_analysis** for MD/AD lords vs relative lagnas, and the same **house / sign / analysis_hint** injection as chat (`ChatContextBuilder.augment_current_dashas_with_chart_hints`). Built from `_build_static_context` → `_build_dynamic_context` (same `DashaCalculator.calculate_current_dashas` + maraka block). **Does not** emit `maha_dashas` (full MD list is large; use chat or a dedicated agent if needed).

```json
{
  "a": "vim_dasha",
  "v": 1,
  "D": {
    "md": { "p": "Jupiter", "st": "2015-11-02", "en": "2031-11-02", "h": 5, "sn": "Libra", "ah": "Jupiter is in house 5 (Libra). It rules houses 3, 6." },
    "ad": { "p": "Saturn", "st": "2024-01-10", "en": "2026-05-20", "h": 8, "sn": "Aries", "ah": "..." },
    "pd": { "p": "Ketu" },
    "sk": { "p": "Venus" },
    "pr": { "p": "Sun" },
    "mn": 14,
    "ml": "Jupiter",
    "mk": {
      "mahadasha_lord": { "Mother": "...", "Father": "...", "Spouse": "...", "First_Child": "...", "Second_Child": "...", "Third_Child": "..." },
      "antardasha_lord": { "...": "..." }
    }
  }
}
```

| Key | Meaning |
|-----|---------|
| `D.md` / `D.ad` / `D.pd` | Mahadasha / antardasha / pratyantardasha: `p` planet; `st`/`en` ISO dates where applicable; `h` house, `sn` sign name, `ah` hint (MD/AD/PD only get `h`/`sn`/`ah` when the dasha lord is in D1). |
| `D.sk` / `D.pr` | Sookshma / prana: `p` only (same as calculator). |
| `D.mn` | Moon nakshatra index **1–27** (same as `DashaCalculator`). |
| `D.ml` | Vimshottari lord of birth Moon’s nakshatra. |
| `D.mk` | `maraka_analysis` from dynamic context (string status per relative for MD and AD lords). |

---

## `chara_dasha` (`a` = `"chara_dasha"`)

**Jaimini Chara Dasha** (K.N. Rao style) from `CharaDashaCalculator`: **Mahadasha** = zodiac sign; **Antardasha** = 12 sub-periods per MD (sign-based). Source: same `d1_chart` + birth date as chat static context.

| Scope | Meaning |
|-------|--------|
| **This agent** | Emits the **full** calculator result: **12 MD** periods from birth (one full Chara cycle in the current engine), each with **12 AD** rows. Dates are authoritative from the calculator. |
| **Legacy chat dynamic** | Builds the same full sequence, then **filters** `chara_dasha.periods` to the **current** MD only, or to periods overlapping a **transit window** — so the model usually does **not** see the full lifetime list. |
| **Multi-cycle lifetime** | The calculator does not advance to a second 12-sign round; true multi-cycle Chara would need an extended calculator. |

```json
{
  "a": "chara_dasha",
  "v": 1,
  "sys": "Jaimini Chara Dasha (K.N. Rao)",
  "n": "…human-readable note…",
  "P": [
    {
      "s": 6,
      "nm": "Virgo",
      "y": 9,
      "ds": "1990-05-01",
      "de": "1999-05-01",
      "ic": false,
      "ad": [
        { "s": 7, "nm": "Libra", "ds": "1990-05-01", "de": "1991-02-01", "ic": false }
      ]
    }
  ]
}
```

| Key | Meaning |
|-----|--------|
| `sys` | System label (short). |
| `n` | Explains full-cycle vs legacy filtered behavior. |
| `P` | Mahadashas in order from birth: `s` = sign **1–12**, `nm` = English sign name, `y` = MD length in years, `ds`/`de` = ISO dates, `ic` = contains “now” for this MD. |
| `P[].ad` | Antardashas: same sign + date keys; `ic` = current AD. |

---

## `div_d9` (`a` = `"div_d9"`)

**Navamsa (D9)** geometry only: D9 lagna, planet longitudes/signs/houses, and **whole-sign house lordships from the D9 lagna** (same mapping rules as `core_d1`’s `H`, but in the navāṁśa frame). Source: `ChatContextBuilder._build_static_context` → `divisional_charts['d9_navamsa']` (including `_add_sign_names_to_divisional_chart`). **No** birth fingerprint `b` — use `core_d1` for name/date/time; avoid duplicating identity fields.

Row shape matches `core_d1` `P`: `[name, longitude_deg, sign_1_12, sign_name, house]`. Signs are **1 = Aries … 12 = Pisces**.

```json
{
  "a": "div_d9",
  "v": 1,
  "L": { "s": 5, "d": 12.34, "nm": "Leo" },
  "P": [["Sun", 150.25, 6, "Virgo", 3], ["Moon", 45.0, 2, "Taurus", 11]],
  "H": { "Sun": [12], "Mars": [1, 8] }
}
```

| Key | Meaning |
|-----|---------|
| `L` | D9 ascendant: `s` sign 1–12, `d` degree within sign (0–30), `nm` English sign name. |
| `P` | Grahas in fixed order Sun→Ketu; each row: name, sidereal longitude 0–360°, sign 1–12, sign name, house 1–12 from **D9** lagna. |
| `H` | Same lord→ruled-houses convention as `core_d1` `H`, computed from **D9** lagna sign. |

**Not included:** D1, dignity/combust (see `d1_graha`), nakshatra names, vargottama flags, Jaimini D9-derived charts (`karkamsa` / `swamsa`) — separate agents if needed.

---

## `div_intent` (`a` = `"div_intent"`)

**Router-driven divisionals:** reads `intent_result.divisional_charts` (same string codes as the intent router / chat filter: `D1`, `D3`, `D4`, `D7`, `D9`, `D10`, `D12`, `D16`, `D20`, `D24`, `D27`, `D30`, `D40`, `D45`, `D60`, `Karkamsa`, `Swamsa`). Emits one compact wheel per code under **`C`** (same `L` / `P` / `H` shape as `div_d9` / `core_d1`). **`Q`** lists chart keys actually present in **`C`** (subset of requested, deduped, max **14**).

- **D1** from `d1_chart`; **D3–D60** only for charts precomputed in `_build_static_context`’s `divisional_charts` (same mapping as chat). Unsupported or missing codes are omitted and listed under **`S`** when non-empty (e.g. `D2:unsupported`, `D99:missing`, `Karkamsa:no_ak`).
- **Karkamsa** / **Swamsa**: computed with `JaiminiChartCalculator` and Atmakaraka from static `chara_karakas` (same dependency as chat’s optional charts).
- If `divisional_charts` is missing or empty, defaults to **`["D9"]`**.
- **`AgentContext.div_intent_omit_codes`** (optional `frozenset` of router codes, e.g. `D1`, `D9`): those charts are skipped (listed under **`S`** as `D1:omit_overlap`, …). Parallel Parashari sets this when `core_d1` / `div_d9` are already in the same bundle so `div_intent` only carries *additional* divisionals.

```json
{
  "a": "div_intent",
  "v": 1,
  "Q": ["D1", "D9", "D10"],
  "C": {
    "D1": { "L": { "s": 6, "d": 12.3, "nm": "Virgo" }, "P": [], "H": {} },
    "D9": { "L": {}, "P": [], "H": {} },
    "D10": { "L": {}, "P": [], "H": {} }
  },
  "S": ["D2:unsupported"]
}
```

Use with **`AgentContext(..., intent_result={...})`**; CLI: `print_agent_json --agent div_intent --intent-json intent.json`.

---

## `dasha_win` (`a` = `"dasha_win"`)

Vimshottari for a **chosen window**, not “now” (see **`vim_dasha`** for current). **v2** adds **`T`** (pratyantardasha-level **timeline** across the whole window via `get_dasha_periods_for_range`).

**Window (same optional shape as `transit_request`):** `startYear`, `endYear`, optional **`yearMonthMap`**. If only years are given, the span is **Jan 1 startYear → Dec 31 endYear**. Alternatively **`dasha_as_of`**: `"YYYY-MM-DD"` for a **single day** (always includes top-level **sk** / **pr** on the snapshot).

**Anchor:** `calculate_dashas_for_date` for **`md`/`ad`/`pd`** snapshot is at **noon on `W.sd`**. **`T`** still covers **`W.sd`…`W.ed`** fully (subject to cap).

| Key | Meaning |
|-----|---------|
| `W` | `{ "sd", "ed", "sp" }` — window start/end ISO dates, **`sp`** = inclusive span in days. |
| `dt` | Anchor date for the **snapshot** levels (noon on `W.sd`). |
| `md` / `ad` / `pd` | Mahadasha / antardasha / pratyantardasha — same compact keys as **`vim_dasha`**. |
| `sk` / `pr` | Top-level snapshot **only if** `W.sp` ≤ **31**. |
| `mn` / `ml` | Moon nakshatra index (1–27) and lord at `dt`. |
| `T` | Timeline rows (max **`CONTEXT_AGENT_DASHA_TIMELINE_MAX`**, default **80**). Each: `sd`, `ed`, `M`, `A`, `P` (lords for that segment); **`sk`/`pr`** on a row only if that row’s `(ed−sd)` span ≤ **31** days. |
| `tn` | Raw segment count from the calculator before capping. |
| `tx` | Present and **true** if `tn` > cap (output truncated). |

**Not included:** full `maha_dashas` list, maraka — use **`vim_dasha`** for current maraka bundle.

```json
{
  "a": "dasha_win",
  "v": 2,
  "W": { "sd": "2027-01-01", "ed": "2027-12-31", "sp": 365 },
  "dt": "2027-01-01",
  "md": { "p": "Jupiter", "st": "2015-11-02", "en": "2031-11-02" },
  "ad": { "p": "Saturn" },
  "pd": { "p": "Ketu" },
  "mn": 14,
  "ml": "Jupiter",
  "tn": 120,
  "tx": true,
  "T": [
    { "sd": "2027-01-01", "ed": "2027-01-28", "M": "Jupiter", "A": "Saturn", "P": "Ketu", "sk": "Mars", "pr": "Rahu" }
  ]
}
```

---

## `panch_maitri` (`a` = `"panch_maitri"`)

**Panchadha maitri** (5-fold planetary friendship): compound of naisargika + tatkalika, same as chat static **`friendship_analysis.friendship_matrix`** from `FriendshipCalculator.calculate_friendship` (`ChatContextBuilder._build_static_context`). **Does not** emit Vedic **drishti** (`aspects_matrix`) or raw longitudes (`planet_positions`).

| Key | Meaning |
|-----|---------|
| `F` | 9×9 matrix: row planet → column planet → **one character** relation code (see table below). Diagonal is always **`.`** (self). |

**Relation codes** (cell values in `F`):

| Code | Internal / chat string |
|------|-------------------------|
| `.` | `self` |
| `++` | `great_friend` |
| `+` | `friend` |
| `0` | `neutral` |
| `-` | `enemy` |
| `--` | `great_enemy` |
| `?` | unknown / missing (should not appear on success) |

Shape: **`F`** has nine row keys and nine column keys per row, in order `Sun`, `Moon`, `Mars`, `Mercury`, `Jupiter`, `Venus`, `Saturn`, `Rahu`, `Ketu`. Diagonal entries are always **`.`**. Off-diagonal codes are chart-dependent (illustrative snippet only):

```json
{
  "a": "panch_maitri",
  "v": 1,
  "F": {
    "Sun": { "Sun": ".", "Moon": "+", "Mars": "++", "Mercury": "0", "Jupiter": "++", "Venus": "-", "Saturn": "--", "Rahu": "0", "Ketu": "-" },
    "Moon": { "Sun": "+", "Moon": ".", "Mars": "+", "Mercury": "++", "Jupiter": "0", "Venus": "-", "Saturn": "-", "Rahu": "-", "Ketu": "++" }
  }
}
```

(Second row and remaining seven row planets omitted for brevity; real output includes all nine rows.)

---

## `sniper_pts` (`a` = `"sniper_pts"`)

Same static bundle as chat **`sniper_points`**: `SniperPointsCalculator(d1_chart, d3_drekkana, d9_navamsa).get_all_sniper_points()` from `_build_static_context`. **Omitted on purpose:** `significance`, `transit_watch`, `lord_location_d1`, `formatted`, **`bhrigu_bindu.upcoming_transits`** (heavy and clock-sensitive).

Sign integer **`s`** where present is **1–12** (Aries … Pisces), same as other agents.

| Key | Source block | Meaning |
|-----|----------------|--------|
| `K` | `kharesh` | `s` = danger sign 1–12 (or `nm` if name not in catalog), `kl` = Kharesh sign lord. On failure: `e` = error string. |
| `N` | `navamsa_64th` | `s` / `nm`, `l` = danger sign lord. On failure: `e`. |
| `B` | `bhrigu_bindu` | `lon` sidereal ° (0–360), `d` = degree within sign, `h` = whole-sign house from lagna, `ld` = sign lord, `s` / `nm`. On failure: `e`. |
| `M` | `mrityu_bhaga` | `x` = `has_affliction`, `r` = afflicted rows: `p` = `"Asc"` or graha name, optional `h` (house), `dg` = degree in sign, `o` = orb, `i` = intensity (**1** = Critical, **2** = High/Strong). On failure: `e`. |

```json
{
  "a": "sniper_pts",
  "v": 1,
  "K": { "s": 8, "kl": "Mars" },
  "N": { "s": 11, "l": "Saturn" },
  "B": { "lon": 182.5, "d": 2.5, "h": 7, "ld": "Venus", "s": 7 },
  "M": { "x": false, "r": [] }
}
```

---

## `jaimini` (`a` = `"jaimini"`)

Static Jaimini bundle from `_build_static_context`: **`jaimini_points`**, **`chara_karakas`**, **`relationships.argala_analysis`**. Does **not** include dynamic **`jaimini_full_analysis`** (that is built in `_build_dynamic_context` with `focus_date`).

Sign integer **`s`** is **1–12** (Aries … Pisces). **`JP`** uses `sign_id` from the calculator (0–11) → **`s` = sign_id + 1**.

| Key | Chat source | Meaning |
|-----|-------------|---------|
| `JP` | `jaimini_points` | Special lagnas: **`AL`** Arudha, **`A7`** Darapada, **`UL`** Upapada, **`KL`** Karkamsa, **`S9`** Swamsa (D9 asc), **`HL`** Hora, **`GL`** Ghatika — each `{ "s": 1–12 }` when present. |
| `CK` | `chara_karakas.chara_karakas` | Seven karakas: **`AK`**, **`AmK`**, **`BK`**, **`MK`**, **`PK`**, **`GK`**, **`DK`** — each `{ "p": planet, "dg": degree in sign, "s": sign 1–12, "h": house }`. Omits `title` / `description` / `life_areas`. |
| `AG` | `relationships.argala_analysis` | Houses **`"1"`** … **`"12"`**: `n` = net_argala_strength, `g` = grade code (**1** = Very Strong Support … **7** = Very Strong Obstruction, **4** = Neutral), `ap` = Argala contributors `{ "p", "rs", "k" }` where **`k`** is **2 / 4 / 11** (Argala from 2nd / 4th / 11th from target), `vp` = Virodha `{ "p", "rs", "k" }` with **`k`** **12 / 10 / 3** (house label from calculator). Omits `shadbala_rupas`, `dignity`, long type strings. |

**`g` (Argala grade) codes:** 1 Very Strong Support, 2 Strong Support, 3 Good Support, 4 Neutral, 5 Mild Obstruction, 6 Strong Obstruction, 7 Very Strong Obstruction.

```json
{
  "a": "jaimini",
  "v": 1,
  "JP": { "AL": { "s": 3 }, "UL": { "s": 9 }, "KL": { "s": 5 } },
  "CK": { "AK": { "p": "Venus", "dg": 28.5, "s": 6, "h": 2 } },
  "AG": {
    "1": { "n": 12.3, "g": 4, "ap": [{ "p": "Jupiter", "rs": 40.0, "k": 4 }], "vp": [] }
  }
}
```

---

## `nakshatra` (`a` = `"nakshatra"`)

**Lunar-mansion bundle** from static `ChatContextBuilder._build_static_context`: per-graha **D1** (`P1`) and **D9** (`P9`) rows derived from `planetary_analysis` / `d9_planetary_analysis`, optional **`R`** = `nakshatra_remedies`, **`NV`** = `navatara_warnings`, **`PK`** = `pushkara_navamsa`. Parallel chat runs a dedicated **nakshatra** LLM branch with a thinned `nakshatra_context` slice; this agent emits the same facts in compact keys.

| Key | Meaning |
|-----|--------|
| `P1` / `P9` | Graha name → `{ "nk", "ni", "pd", "h", "sn", "nl" }` subset (omitted keys dropped). `nk` = nakshatra name; `ni` = 0-based index in the canonical 27 list; `pd` = pada **1–4**; `h` = whole-sign house; `sn` = sign name; `nl` = Vimshottari lord of that nakshatra (derived). |
| `R` | `nakshatra_remedies` when present. |
| `NV` | `navatara_warnings` when present. |
| `PK` | `pushkara_navamsa` when present. |

```json
{
  "a": "nakshatra",
  "v": 1,
  "sc": "current",
  "P1": { "Moon": { "nk": "Chitra", "ni": 13, "pd": 2, "h": 5, "sn": "Libra", "nl": "Mars" } },
  "P9": { "Moon": { "nk": "Uttara Bhadrapada", "ni": 25, "pd": 4, "h": 11, "sn": "Aquarius", "nl": "Saturn" } }
}
```

---

## `kp` (`a` = `"kp"`)

**Krishnamurti Paddhati** summary from static `ChatContextBuilder._build_static_context` → **`kp_analysis`**: `planet_lords`, `cusp_lords`, `significators` (from `KPChartService.calculate_kp_chart`). On failure the chat builder stores `{ "error": "..." }` instead. Parallel chat runs a dedicated **kp** LLM branch with `kp_context` + `shared_kernel` (Vimshottari for dasha trigger). Payload key **`KP`** mirrors `kp_analysis`.

```json
{
  "a": "kp",
  "v": 1,
  "sc": "current",
  "KP": {
    "planet_lords": {},
    "cusp_lords": {},
    "significators": {}
  }
}
```

---

## `nadi` (`a` = `"nadi"`)

Bhrigu Nandi Nadi–style data that appears in **chat context** today (not the separate `/api/nadi/*` JSON services).

| Key | Chat source | Meaning |
|-----|-------------|---------|
| `LK` | `nadi_links` | Per graha (`Sun` … `Ketu`): **`s`** = sign **1–12** (from `sign_info.sign_id` + 1), **`rv`** retro, **`ex`** parivartana virtual sign, **`t`/`f`/`b`/`o`** = sorted linked grahas for **trine / next (2nd) / prev (12th) / opposite**, **`a`** = sorted **`all_links`** (union). |
| `AA` | `nadi_age_activation` | **null** if no milestone age this year. Else **`y`** = age, **`k`** = activated nakshatra name(s), **`pl`** = `{ "p", "n", "h" }` rows (natal planet in those nakshatras). Rebuilt from birth **`date`** + static **`planetary_analysis`** when dynamic blob is missing or `nadi_age_activation` is null. **Omitted:** long `instruction` text from chat. |

**Linkage geometry (`t` trine, etc.):** Built by `NadiLinkageCalculator` (`backend/calculators/nadi_linkage_calculator.py`), **not** a generic D1 aspect matrix. For **retrograde** grahas (`rv: true`), the calculator also treats the **previous sign** as an active base (Bhrigu Nandi Nadi–style “influence from the sign behind”). Trine sets are the **whole-sign 1/5/9 triplicity** from **each** active base. So e.g. Venus in Leo + retro adds Cancer’s water triplicity; Jupiter in Scorpio can appear in Venus’s **`t`** list as a **Cancer–Scorpio trine relation**, not as “Leo squares Scorpio but we called it trine.” When narrating, mention retro/virtual base if you contrast nominal signs.

**Not included:** KP cusps, event-timeline `nadi_validation`, standalone **`backend/nadi/`** HTTP payloads — add other agents or call those APIs if needed.

```json
{
  "a": "nadi",
  "v": 1,
  "LK": {
    "Saturn": { "s": 10, "rv": false, "ex": false, "t": ["Jupiter"], "f": [], "b": [], "o": ["Moon"], "a": ["Jupiter", "Moon"] }
  },
  "AA": { "y": 36, "k": ["Rohini", "Pushya"], "pl": [{ "p": "Mars", "n": "Rohini", "h": 5 }] }
}
```

---

## `transit_win` (`a` = `"transit_win"`)

Compact **slow-graha transit activations** from the same path as chat: `_build_dynamic_context(..., intent_result)` with **`needs_transits`: true** and **`transit_request`**: `startYear`, `endYear`, optional **`yearMonthMap`**. Rows are taken from **`transit_activations`** with heavy keys removed (`all_aspects_cast`, `comprehensive_dashas`, etc.). **v2** drops **`ak`** (ashtakavarga); use a separate Ashtakavarga agent/context if needed.

If **`intent_result`** omits transits, the agent merges a **default window**: current calendar **`startYear`** through **`endYear` = startYear + 2**, full `yearMonthMap` for those years (same shape as intent-router fallback today). **Intent router code is not modified** — callers pass `intent_result` when they have it.

| Key | Meaning |
|-----|---------|
| `Y` | `{ "sy", "ey" }` resolved year span. |
| `n` | Count of raw activations before capping. |
| `A` | Up to **`CONTEXT_AGENT_TRANSIT_MAX`** (default **32**) rows: `tp` transit graha, `np` natal graha, `an` aspect number, `sd`/`ed` ISO dates, `th`/`nh` whole-sign houses, `at` aspect label, optional `pk` (dasha ref peak), optional `sg` (short significance string). |
| `d` | Optional Vimshottari anchor: `{ "m": MD lord, "a": AD lord }` from `current_dashas`. |
| `p` | Optional slim **`period_dasha_activations.dasha_activations`** (≤12 rows, short keys only when present in source). |

**Not included:** `unified_dasha_timeline`, `macro_transits_timeline`, `transit_data_availability` prose, full per-period dasha trees, **ashtakavarga** — use chat context or future agents if needed.

```json
{
  "a": "transit_win",
  "v": 2,
  "Y": { "sy": 2026, "ey": 2028 },
  "n": 14,
  "A": [
    { "tp": "Jupiter", "np": "Venus", "an": 5, "sd": "2026-03-01", "ed": "2026-08-20", "th": 4, "nh": 7, "at": "5th_house", "pk": "2026-03-01" }
  ],
  "d": { "m": "Saturn", "a": "Mercury" },
  "p": [{ "planet": "Jupiter", "dasha_level": "mahadasha", "probability": "high" }]
}
```
