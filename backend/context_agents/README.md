# Context agents (compact chat context)

This package is an **optional parallel path** to the legacy `chat/chat_context_builder.py` stack. Nothing in production chat imports it until you wire an orchestrator and flip the env flag.

## Switching (when orchestration exists)

- **Legacy (default):** unchanged — `ChatContextBuilder.build_complete_context()` as today.
- **Parallel chat + agents:** set `ASTRO_PARALLEL_CHAT=1` and **`ASTRO_PARALLEL_AGENT_CONTEXT=1`** so [`run_parallel_chat_pipeline`](../ai/parallel_chat/orchestrator.py) sends compact agent JSON per branch (see [`parallel_agent_payloads.py`](../ai/parallel_chat/parallel_agent_payloads.py)) instead of legacy `context_slices`.
- **`ASTRO_USE_CONTEXT_AGENTS`:** reserved for a future global “all chat uses agents” flag in [`registry.py`](registry.py); parallel chat does not require it when using `ASTRO_PARALLEL_AGENT_CONTEXT`.

## Time scope (parity with legacy chat)

`AgentContext` accepts the same signals as dynamic context:

- `intent_result` — especially `mode` (e.g. `LIFESPAN_EVENT_TIMING`, `PREDICT_DAILY`) and `transit_request` (`startYear` / `endYear`).
- `requested_period` — optional annual / backend year range.
- `target_date` — optional focus datetime for Chara overlap.
- `time_scope` — optional override: `"full"` | `"intent_window"` | `"current"`.

`context_agents/scope.py` resolves **`ContextTimeScope`** (same spirit as legacy filtering):

| Scope | Typical trigger | Effect on agents |
|-------|-----------------|------------------|
| `full` | `mode=LIFESPAN_EVENT_TIMING` or `time_scope=full` | Full Chara cycle; wide transit/dasha windows. |
| `intent_window` | `transit_request` years or `requested_period` | Overlap filter (Chara), router years (transits / Vim window). |
| `current` | Default; `PREDICT_DAILY`; no window | Current MD only (Chara); short transit years; `dasha_as_of` for `dasha_win`. |

Override for debugging: **`CONTEXT_AGENT_TIME_SCOPE=full`** (or `intent_window` / `current`).

## Design rules

1. **One agent = one JSON blob** with stable short keys, documented in `SCHEMA.md` per agent.
2. **No cross-agent duplication** — if another agent will own a field, this agent omits it.
3. **Compact over verbose** — omit prose, methodology, and keys the LLM does not need for reasoning.
4. **One agent at a time** — implement, document schema, add tests, then register.

## Implemented agents

| ID | Module | Purpose |
|----|--------|---------|
| `core_d1` | `agents/core_d1.py` | Sidereal D1 only: birth fingerprint, lagna, planet rows, house lord map. No divisionals, dasha, transits, nakshatra text, or panchang. |
| `d1_graha` | `agents/d1_graha_state.py` | Per-graha dignity, retro, combustion, avastha, grades — same `planetary_analysis` path as `ChatContextBuilder._build_static_context` (heavy one-off). |
| `vim_dasha` | `agents/vim_dasha.py` | Current Vimshottari MD/AD/PD/SK/PR + moon nakshatra/lord + maraka flags + chart hints — same static→dynamic path as chat; omits full `maha_dashas` list. |
| `chara_dasha` | `agents/chara_dasha.py` | **Jaimini Chara Dasha:** full calculator output — **12 MD** from birth (one cycle) + **12 AD** per MD. Legacy chat usually filters to current MD or transit overlap only. |
| `ashtakavarga` | `agents/ashtakavarga.py` | **SAV/BAV:** D1 Sarva + Bhinna bindu rows (12 **signs** Aries→Pisces); **`D1.Ho`** maps houses 1–12 from lagna to SAV/BAV when ascendant is on static context. Optional D9 compact block. Parallel chat also runs a dedicated **ashtakavarga** LLM branch. |
| `div_d9` | `agents/div_d9.py` | Navamsa (D9) lagna + planet rows + house lord map — same `divisional_charts['d9_navamsa']` as `_build_static_context` (no extra `b`; use `core_d1` for birth fingerprint). |
| `div_intent` | `agents/div_intent.py` | Bundle of charts from `intent_result['divisional_charts']` (`D1`, `D3`–`D60` subset in static cache, `Karkamsa`, `Swamsa`); each chart compact `L`/`P`/`H` like `div_d9`. Default list `["D9"]` if intent omits charts. |
| `parashari_day` | `agents/parashari_day.py` | **Exact-day Parashari helper:** daily Panchanga + Moon transit + fast transits (`Sun`, `Moon`, `Mercury`, `Venus`, `Mars`) for `dasha_as_of` / specific-date queries. |
| `transit_win` | `agents/transit_win.py` | Slow-graha `transit_activations` for `intent_result.needs_transits` + `transit_request` (same as chat dynamic build), compact rows + optional `d` (MD/AD anchor) / `p` (period dasha list). No Ashtakavarga in rows (separate agent). Defaults to current calendar year through +2 if intent omits window. Cap: `CONTEXT_AGENT_TRANSIT_MAX` (default 32). |
| `dasha_win` | `agents/dasha_win.py` | Vimshottari **snapshot** at window start + **`T`** timeline (`get_dasha_periods_for_range` over `W`, capped by `CONTEXT_AGENT_DASHA_TIMELINE_MAX`). Top **sk/pr** only if `W.sp` ≤31d; per-row **sk/pr** in `T` only for segments ≤31d. |
| `panch_maitri` | `agents/panch_maitri.py` | Panchadha (5-fold) **friendship matrix** only — same `FriendshipCalculator.calculate_friendship` → `friendship_matrix` as chat static `friendship_analysis` (natural + temporal compound). Omits `aspects_matrix` / `planet_positions`. With **`precomputed_static`**, reads `friendship_analysis` when present. |
| `sniper_pts` | `agents/sniper_pts.py` | **Sniper points** bundle: Kharesh (22nd drekkana), 64th navamsa, Bhrigu Bindu, Mrityu Bhaga — same `SniperPointsCalculator` / static `sniper_points` as chat. Compact keys; omits prose, `lord_location_d1`, and **`upcoming_transits`**. |
| `jaimini` | `agents/jaimini.py` | **Jaimini static bundle:** `jaimini_points` (AL, A7, UL, KL, D9 asc / S9, HL, GL), **`chara_karakas`** (seven karakas → `AK`…`DK`), **`relationships.argala_analysis`** (per-house net + grade code + compact planet rows). Omits long descriptions / karaka prose. |
| `nadi` | `agents/nadi.py` | **BNN Nadi (chat parity):** **`nadi_links`** (per-graha trine/next/prev/opposite + `all_links`) and **`nadi_age_activation`** (age milestones vs nakshatras + matching natal planets). Uses `precomputed_dynamic.nadi_age_activation` when a dict; otherwise recomputes age block from birth date + static `planetary_analysis`. Omits chat `instruction` string. |
| `nakshatra` | `agents/nakshatra.py` | **Nakshatra / pada / D9 mirror:** compact **`P1`** / **`P9`** rows per graha (nakshatra, pada, house, sign, derived Vimshottari lord of the nakshatra), plus optional **`R`** (remedies), **`NV`** (navatara warnings), **`PK`** (pushkara). Same static path as chat. Parallel chat also runs a dedicated **nakshatra** LLM branch. |
| `kp` | `agents/kp.py` | **KP:** `planet_lords`, `cusp_lords`, `significators` (same **`kp_analysis`** as chat). Parallel chat runs a dedicated **kp** LLM branch. |

## Tests

Install dev test deps once (pytest is not in the main app `requirements.txt`):

```bash
cd backend && .venv/bin/python3 -m pip install -r requirements-test.txt
```

Then:

```bash
cd backend && python3 -m pytest test_context_agent_core_d1.py -q
```

`test_context_agent_core_d1.py` loads the **latest** `birth_charts` row for **userid 7** (any `relation`). Override with `CONTEXT_AGENT_TEST_USER_ID=12`. If Postgres, `ENCRYPTION_KEY`, or any chart row for that user is missing, the integration tests are **skipped** (the `test_core_d1_registered` check still runs). Tests use `context_agents.birth_from_db.load_backend_dotenv()` so `backend/.env` and repo-root `.env` are loaded.

Heavy agents (`d1_graha`, `div_d9`, `div_intent`, `vim_dasha`) reuse **`backend/conftest.py`** session fixture **`context_agent_cached`**: one `_build_static_context` + `_build_dynamic_context` per pytest process, passed via **`AgentContext.precomputed_static`** / **`precomputed_dynamic`** so each test does not rerun the full chart stack.

## Inspect agent JSON (structure only, no logs)

Pytest is for pass/fail, not for dumping payloads. To print **only** the agent JSON (calculator noise is discarded during the build):

```bash
cd backend
python3 -m context_agents.print_agent_json --user-id 7
```

Indented JSON is the default; add `--compact` for one line. Use `--birth-json path/to/birth.json` instead of DB. `--agent core_d1` is the default; e.g. `--agent vim_dasha` (current dasha), `--agent chara_dasha` (full Chara MD+AD cycle from calculator), `--agent dasha_win --intent-json …` (window / `dasha_as_of`), `--agent transit_win`, `--agent panch_maitri`, `--agent sniper_pts`, `--agent jaimini`, `--agent nadi`, etc.
