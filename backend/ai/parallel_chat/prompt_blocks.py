"""
Static instruction blocks for parallel chat branches.

Text is composed from `chat.system_instruction_config` so doctrine stays aligned
with legacy `build_system_instruction` — only layout and per-branch scope differ.
"""

from __future__ import annotations

from chat.system_instruction_config import (
    ASHTAKAVARGA_FILTER,
    BHAVAM_BHAVESH_RULES,
    CAREER_SUTRAS,
    CLASSICAL_CITATIONS,
    COMPLIANCE_RULES,
    CORE_PERSONA,
    DASHA_DATES_SOVEREIGNTY,
    DATA_SOVEREIGNTY,
    DIVISIONAL_ANALYSIS,
    EDUCATION_SUTRAS,
    HEALTH_SUTRAS,
    HOUSE_SIGNIFICATIONS,
    JAIMINI_ANALYSIS_STRUCTURE,
    JAIMINI_PILLAR,
    KOTA_LOGIC,
    LONGEVITY_ANALYSIS,
    MARRIAGE_SUTRAS,
    NADI_ANALYSIS_STRUCTURE,
    NADI_PILLAR,
    NAKSHATRA_PILLAR,
    NO_DEATH_ETHICS,
    PARASHARI_PILLAR,
    KP_PILLAR,
    KP_PARALLEL_LIFE_STAGE_RULE,
    PERSONAL_CONSULTATION_RULES,
    SUDARSHANA_LOGIC,
    SYNTHESIS_RULES,
    USER_MEMORY,
    WEALTH_SUTRAS,
)

_BRANCH_JSON_FOOTER = """
OUTPUT FORMAT (NON-NEGOTIABLE):
Return a single JSON object only (no markdown fences, no prose before or after). Schema:
{
  "branch": "<branch_id>",
  "analysis": "<technical markdown for this school only — substantive depth>",
  "bullets": ["<optional short fact bullets>"]
}
Keep "analysis" under 12000 characters. Use ONLY the variable JSON in the same message.
ACCURACY MANDATE: Be strictly technical and evidence-based. Do not invent or soften conclusions for politeness. Do not use motivational filler.
DASHA MANDATE: If dasha/chara/yogini period labels or windows are present in the payload, explicitly cite them in "analysis" (do not replace with generic timing language).
"""

_PARASHARI_JSON_FOOTER = """
OUTPUT FORMAT (NON-NEGOTIABLE):
Return a single JSON object only (no markdown fences, no prose before or after). Schema:
{
  "branch": "parashari",
  "analysis": "<technical markdown for this school only — substantive depth>",
  "bullets": ["<optional short fact bullets>"]
}
Keep "analysis" under 12000 characters. Use ONLY the variable JSON in the same message.
If `special_points.yogi_points` is present in VARIABLE_DATA_JSON (non-empty / populated), the markdown inside "analysis" MUST include a distinct subsection titled exactly #### Yogi & Avayogi Karma in which you explicitly list and interpret all four: **Yogi**, **Avayogi**, **Dagdha Rashi**, and **Tithi Shunya Rashi** (lords and signs as given), each in relation to the user's question and relevant houses. Do not skip any of the four when the payload provides them—do not answer with Avayogi alone or a partial subset.
ACCURACY MANDATE: Be strictly technical and evidence-based. Do not invent or soften conclusions for politeness. Do not use motivational filler.
DASHA MANDATE: If dasha period labels/windows are present, explicitly cite them in the analysis.
"""

MERGE_ROLE_PREAMBLE = """
# MERGE STEP (final writer only)

Prior specialist passes already produced structured JSON (Parashari required; Jaimini/Nadi/Nakshatra/KP/Ashtakavarga/Sudarshan may be partial).

You receive:
1) SPECIALIST_BRANCH_OUTPUTS_JSON — branch "analysis" / "bullets" fields plus optional `scope` metadata.
2) LAST Q&A TURNS — up to 3 prior user/assistant exchanges (genuine follow-ups only).
3) CURRENT QUESTION — the same question the specialists answered.

You must:
- Produce ONE answer following the RESPONSE FORMAT template below (same section headers as legacy single-pass).
- Synthesize branch findings into those sections: Parashari drives primary "what/when"; weave in Jaimini/Nadi/Nakshatra/KP/Ashtakavarga/Sudarshana when present.
- If `SPECIALIST_BRANCH_OUTPUTS_JSON.scope.chart_focus` is present, treat that as an intentional chart-focused run. In that case, do NOT complain that skipped branches are missing; keep the final answer centered on the requested chart/lens.
- If `SPECIALIST_BRANCH_OUTPUTS_JSON.scope.chart_focus` is present, follow the chart-focused RESPONSE FORMAT and present one integrated chart reading. Do not force exposed subsection labels like "The Jaimini View", "Nadi Interpretation", or "KP Stellar Perspective" unless the user explicitly asked for school-by-school comparison.
- If a branch is missing or status=unavailable unexpectedly, note briefly under that #### subsection and continue.
- Obey [MERGE-VOICE], [MERGE-HONESTY], [MERGE-TIME], [MERGE-DASHA-SOVEREIGNTY], and [SYNTH-FINAL] in the merge doctrine block below.
- If any branch provides explicit dasha/chara/yogini period names or date windows, you MUST retain them in final output (do not collapse into generic timing prose).
- Prioritize strict technical accuracy over conversational softness.

You must not:
- Copy-paste or concatenate specialist JSON as the user-facing answer.
- Hallucinate chart facts, dasha names, or date ranges not supported by the branch outputs.

The following blocks are the merge-only doctrine (consultant voice, honesty, Final Verdict), not the full single-pass encyclopedia.
"""


def _domain_sutras(intent_category: str) -> str:
    cat = (intent_category or "general").lower()
    parts = []
    if cat in ("career", "job", "promotion", "business"):
        parts.append(CAREER_SUTRAS)
    if cat in ("wealth", "money", "finance"):
        parts.append(WEALTH_SUTRAS)
    if cat in ("health", "disease"):
        parts.append(HEALTH_SUTRAS + "\n" + LONGEVITY_ANALYSIS)
    if cat in ("marriage", "love", "relationship", "partner", "spouse"):
        parts.append(MARRIAGE_SUTRAS)
    if cat == "education":
        parts.append(EDUCATION_SUTRAS)
    return "\n".join(parts) if parts else ""


def _is_health_category(intent_category: str) -> bool:
    return (intent_category or "").strip().lower() in ("health", "disease")


def build_parashari_branch_static(intent_category: str) -> str:
    health_prompt_line = (
        "For health questions, separate **Constitution/Vitality -> Disease Pattern -> Body-System Focus -> Current Activation -> Preventive Guidance**. Do not name diseases or give treatment instructions; stay at the level of astrological susceptibility, timing pressure, and preventive/recovery logic."
        if _is_health_category(intent_category)
        else ""
    )
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        SYNTHESIS_RULES,
        PARASHARI_PILLAR,
        _domain_sutras(intent_category),
        DIVISIONAL_ANALYSIS,
        KOTA_LOGIC,
        CLASSICAL_CITATIONS,
        USER_MEMORY,
        COMPLIANCE_RULES,
        DASHA_DATES_SOVEREIGNTY,
        HOUSE_SIGNIFICATIONS,
        BHAVAM_BHAVESH_RULES,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (PARASHARI BRANCH ONLY)\n",
        "Analyze using ONLY Parashari + divisional + dasha + transit logic from the JSON (no Ashtakavarga tables here).",
        "Use `planetary_analysis` / `d1_graha`-style graha rows for **`av` (avastha)** and strength (`sc`) on planets that matter for the question—especially Yogakaraka and house lords; flag **Mrit/Dead** or extreme weakness as delivery risk per [P-7].",
        "If **D7 / Saptamsa** appears in `divisional_charts` (or equivalent), marriage/partnership/children answers MUST include a real D7 interpretation—see [P-8].",
        "For marriage/spouse timing questions, explicitly separate **Promise -> Timing -> Manifestation -> Continuity**. Do not treat attraction, proposal, legal marriage, and stable married life as the same thing.",
        "For career/profession/field questions, explicitly separate **Aptitude -> Field Selection -> Work Function -> Status/Visibility -> Timing of Entry/Change**. Do not answer 'what career will I pick?' with a vague basket of unrelated professions unless the chart is genuinely mixed.",
        health_prompt_line,
        "When `special_points` is present, use `gandanta_analysis` if flagged and follow OUTPUT FORMAT rules for `yogi_points` below.",
        "Do NOT write the Jaimini View, Nadi Interpretation, KP technical pass, Ashtakavarga, deep Nakshatra-only analysis, or full Sudarshana triple-chakra synthesis — other passes cover them.",
        _PARASHARI_JSON_FOOTER,
    ]
    return "\n\n".join(p for p in parts if p)


def build_kp_branch_static(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        KP_PILLAR,
        KP_PARALLEL_LIFE_STAGE_RULE,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (KP BRANCH ONLY)\n",
        "Use ONLY `kp_analysis` (planet_lords, cusp_lords, significators) plus shared_kernel Vimshottari/dasha fields for the KP trigger step.",
        "For every primary house cusp you analyze, follow KP_PILLAR order: **Cusp Sign Lord → Cusp Star Lord (NL) → Cusp Sub Lord (CSL)** before the 4-step chain; do not open with CSL alone.",
        "Apply 4-step sub-lord theory and dasha trigger after that cusp hierarchy. "
        "Do NOT repeat full Parashari divisional exposition, Jaimini, Nadi tables, Nakshatra mansion doctrine, or Ashtakavarga — other passes cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "kp"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nakshatra_branch_static(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NAKSHATRA_PILLAR,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (NAKSHATRA BRANCH ONLY)\n",
        "Use ONLY the Nakshatra-context JSON: per-graha D1/D9 nakshatra fields, `nakshatra_remedies`, `navatara_warnings`, `pushkara_navamsa`, plus shared_kernel Vimshottari fields for Tara-from-Moon checks.",
        "Always include **relevant house lord(s)** (e.g. 7th lord for marriage) with full nakshatra+pada and **D9 / navamsa-sign implications**—not only karaka (Venus) or 7th-house occupants—see NAKSHATRA_PILLAR [NK-6]. "
        "Navatara / Tara and D9 own-sign claims MUST follow [NK-7] (math + sign lords)—never contradict `navatara_warnings` or classical sign ownership.",
        "Tie lunar-mansion (nakshatra) themes, pada, Navatara quality, and Pushkara hints to the question. "
        "Do NOT repeat full Parashari divisional doctrine, Jaimini, Nadi linkage tables, or Ashtakavarga bindus — other passes cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "nakshatra"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_ashtakavarga_branch_static() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        ASHTAKAVARGA_FILTER,
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        "\n# TASK (ASHTAKAVARGA BRANCH ONLY)\n",
        "Use ONLY the Ashtakavarga JSON (Sarvashtakavarga + Bhinnashtakavarga; D9 block if present). "
        "When `D1.Ho` is present, cite SAV/BAV for each **house** only from `D1.Ho[\"1\"]`…`[\"12\"]` (whole-sign from lagna); "
        "`D1.S` / `D1.B` rows are **Aries→Pisces** (index 0–11), never house ordinals. "
        "Apply ASHTAKAVARGA_FILTER [AV-4..AV-8]: SAV bands, event-planet BAV delivery filter, and conflict phrasing.",
        "Do NOT repeat full Parashari, Jaimini, Nadi, Nakshatra, or KP doctrine — stay Ashtakavarga-only, but provide real interpretive judgment (not raw table dump).",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "ashtakavarga"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_sudarshan_branch_static(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        SUDARSHANA_LOGIC,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (SUDARSHANA / TRIPLE-CHAKRA BRANCH ONLY)\n",
        "`shared_kernel` is minimal (birth, ascendant, current date, response_format, intent, and a compact dasha anchor) — no D1, divisionals, or heavy Vimshottari timelines. "
        "Use `sx` as the Sudarshana reasoning spine and `sudarshana_context` only for raw backup. `sx.topic.rows` = question-relevant houses with tri-perspective agreement, benefic/malefic tilt, and support band; `sx.career` / `sx.relationship` / `sx.education` / `sx.health` = topic-specific Sudarshana blocks; `sx.current.topic` and `sx.current.<topic>` = whether current MD/AD/PD are actually touching those houses from Lagna/Moon/Sun right now; `sx.dom` = dominant houses; `sx.patterns` = synthesis notes; `sx.triggers` = precision year-clock rows; `sx.D` = compact current dasha anchor. "
        "Use ONLY `sudarshana_context` for raw chart mechanics when needed: `sudarshana_chakra` (lagna_chart, chandra_lagna, surya_lagna rotated houses + synthesis) and `sudarshana_dasha` when present. "
        "Apply Sudarshana rules with disciplined wording: compare event/house themes across Body (Lagna), Mind (Moon), Soul (Sun); state whether support is 3/3, 2/3, or mixed from `sx.topic.rows`, and for predictive/current questions also cite `sx.current.topic` or the relevant `sx.current.<topic>` block so the branch says whether the active periods are presently energizing that Sudarshana theme. Treat Sudarshana triggers as confirmation windows, not standalone guarantees. "
        "Do NOT repeat full Parashari divisional doctrine, Jaimini, Nadi tables, Nakshatra mansion analysis, KP cusp steps, or Ashtakavarga bindus — other branches cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "sudarshan"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_jaimini_branch_static() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        JAIMINI_PILLAR,
        JAIMINI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (JAIMINI BRANCH ONLY)\n",
        "Use ONLY Jaimini-related JSON (Chara Karakas, Jaimini points, Argala, Chara Dasha, UL/DK/A7 fields, etc.).",
        "Your write-up must explicitly separate: **Static Promise** -> **current Chara timing (MD/AD)** -> **Manifestation Filter** (Arudha / Argala / occupants). Do not let a static yoga override a clearly hostile active Chara frame.",
        "When current Chara MD and AD signs are available, you MUST produce dual-frame analysis: (1) **MD-Lagna Frame** and (2) **AD-Lagna Frame**. "
        "Treat each sign as temporary Lagna, then add a short **Confluence/Conflict** conclusion; near-term priority goes to AD-Lagna when they differ.",
        "For marriage/partnership or 7th-house themes: thread **DK + UL + Darapada (A7)**. **A7 must be analyzed in depth** (sign + planets in that sign; GK or other grahas in A7’s sign = concrete friction or support in the physical/logistical reality of the union)—see JAIMINI_PILLAR [J-8]. Never stop at naming A7’s sign alone. Explicitly distinguish **partner nature (DK)**, **alliance/continuity (UL)**, and **lived manifestation (A7)**.",
        "For career/status questions: thread **AmK + KL + AL** and state separately whether the current frame shows work, authority, recognition, or only pressure without visible rise. Also distinguish vocation from public image: what the native is suited to do vs how visible or prestigious that work becomes.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "jaimini"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nadi_branch_static(intent_category: str = "") -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NADI_PILLAR,
        NADI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (NADI BRANCH ONLY)\n",
        "Use ONLY Nadi linkage + age activation JSON.",
        "Structure the branch as: **Dominant Nadi Grahas -> Linkage Logic -> Promise vs Activation -> Topic Verdict**. Do not drift into generic Parashari/Jaimini prose.",
        "When a clear graha pair/cluster emerges, convert it into a concrete topic statement: technical, commercial, advisory, relationship support, delay, karmic friction, research, wealth-building, health strain, or irregularity. Do not stop at 'X is linked to Y'.",
        "Apply negative evidence: Saturn in relationship clusters means delay/duty, Rahu/Ketu mean irregular or karmic manifestation, Mars adds heat/friction, benefics do not erase those factors.",
        "When you discuss a planet that is retrograde in the linkage data, state clearly that **in this Nadi (BNN-style) treatment, a retrograde graha is also considered from the previous sign** for trine / directional links—so connections may follow that virtual base, not the nominal sign alone.",
        "If the question is about wealth or health, still keep the same Nadi discipline: dominant grahas -> key signatures -> age activation -> verdict. Do not fallback to generic natal prose.",
        "If no age activation is present, explicitly say the Nadi read here is stronger for static promise / pattern and weaker for current-year timing.",
        "For health questions, do not name diseases or overstate outcomes; keep the Nadi read at the level of astrological pattern, sensitivity, irregularity, chronicity, or acute flare tendency."
        if _is_health_category(intent_category)
        else "",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "nadi"),
    ]
    return "\n\n".join(p for p in parts if p)


# --- Agent-payload TASK lines (VARIABLE_DATA_JSON uses compact SCHEMA.md keys; ASTRO_PARALLEL_AGENT_CONTEXT=1) ---


def build_parashari_branch_static_agent(intent_category: str) -> str:
    health_prompt_line = (
        "For health questions, explicitly separate **Constitution/Vitality -> Disease Pattern -> Sensitive Body Systems -> Current Activation -> Preventive Guidance**. Use `px.health` first: `score` = calculator-level health score when available, `pattern` = acute/chronic/sensitivity/mixed/preventive, `tone` = flare-up/wear-and-tear/mind-body, `risk` = vitality-vs-acute-vs-chronic-vs-mental pressure, `body` / `ph` = sensitive body systems and afflicted grahas, `hh` = key health-house summaries, `charak` / `charak_agent` = coarse Dr.-Charak-style dosha cue, `rw` = ranked risk windows, `dv.D30` = whether Trimsamsa confirmation exists. Do not give medical diagnosis; describe astrological vulnerability, timing pressure, and preventive logic only."
        if _is_health_category(intent_category)
        else ""
    )
    health_agent_line = (
        "For health/disease questions the `parashari_agents` bundle may also include `health`, a compact context-agent summary built from the existing HealthCalculator plus ranked transit pressure windows. Prefer that evidence instead of inferring everything from raw graha rows."
        if _is_health_category(intent_category)
        else ""
    )
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        SYNTHESIS_RULES,
        PARASHARI_PILLAR,
        _domain_sutras(intent_category),
        DIVISIONAL_ANALYSIS,
        KOTA_LOGIC,
        CLASSICAL_CITATIONS,
        USER_MEMORY,
        COMPLIANCE_RULES,
        DASHA_DATES_SOVEREIGNTY,
        HOUSE_SIGNIFICATIONS,
        BHAVAM_BHAVESH_RULES,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (PARASHARI BRANCH ONLY — CONTEXT AGENTS)\n",
        "Analyze using `parashari_agents` and `px` in VARIABLE_DATA_JSON. `parashari_agents` is the raw compact agent bundle (each key is a context agent id: "
        "core_d1, d1_graha, vim_dasha, div_d9, div_intent, parashari_day, transit_win, dasha_win, panch_maitri, sniper_pts). "
        "`div_intent` carries other intent-listed divisionals (D3–D60, Karkamsa, Swamsa); D1 and D9 are not repeated there because `core_d1` and `div_d9` already provide them. "
        "**If `div_intent` includes D7 (Saptamsa), you MUST analyze it** for marriage/children/partnership threads—do not ignore it. "
        "`d1_graha` → **`G`**: use **`av`** / **`sc`** for outcome delivery (Yogakaraka, 7th lord, etc.); never skip critical **Mrit/Dead**-style states per [P-7]. "
        "`px` is the derived Parashari reasoning spine: `px.src` = time authority (`current` / `window` / `day`), `px.hs` = priority houses for the topic, `px.dv` = divisional availability flags, `px.dx` = divisional evidence spine, `px.D` = active dasha lord summaries, `px.HI` = which active dasha levels rule/occupy/aspect the target houses, `px.TR` = compact transit pressure on those houses. `px.career` and `px.relationship` are dedicated compact topic blocks. Use `px` to stay concrete rather than inferring these links from scratch.",
        health_agent_line,
        "Each raw agent value is compact JSON with `a` = agent id; see `context_agents/SCHEMA.md` for field meanings (P, G, D, C, etc.).",
        "Time authority rule: follow `px.src`. `vim_dasha` is current/present only; `dasha_win` is the authority for the asked past/future window; for short-term windows, prioritize `transit_win.p` before generic transit activations.",
        "If `px.src=\"day\"` and `parashari_day.x=true`, this is an exact-day query. Prioritize `parashari_day` for Panchanga, Moon transit, and fast planets; use `dasha_win` for the exact 5-level Vimshottari snapshot on that date. Do not answer a single-day question from slow transits alone.",
        "For topic-specific questions, anchor the logic to `px.hs` and `px.HI`: say whether those houses are being activated by rulership, occupation, or graha drishti from active dasha lords. Use `px.D` to cite the actual active lords with their natal house placement, ruled houses, aspects, dignity, avastha, combustion, and strength.",
        "Use `px.dx` whenever divisional charts are relevant: `px.dx.rf` = D1-vs-D9 root/fruit confirmation for relevant lords/karakas; `px.dx.topic.charts` = topic-specific divisional house rows with lord placement, occupants, and support band; `px.dx.current` = whether current MD/AD/PD lords are actually linking into those divisional houses right now; `px.dx.career` / `relationship` / `education` / `health` = ready divisional support blocks. If a required divisional chart is missing, say that explicitly from `px.dx.*.avail` instead of implying certainty.",
        "For current or predictive questions, do not stop at static divisional promise. Also cite `px.dx.current.topic` or the relevant `px.dx.current.<life_area>` block to say whether the active periods are presently activating that divisional chart or not.",
        "Use `px.TR` as a compact transit filter: near-term answers should say whether transit hits are landing on the topic houses directly (`th`/`nh`) and whether active dasha planets are involved (`dp`).",
        "For marriage/spouse questions, explicitly separate **Promise -> Timing -> Manifestation -> Continuity**. Use `px.relationship` first: `mat` = materialization pressure, `fr` = friction pressure, `ct` = continuity emphasis, `mode` = supportive/mixed/obstructed, `dom` = dominant houses. Then refine with `px.hs`, `px.HI`, and raw graha detail. Do not equate generic relationship activation with legal or durable marriage.",
        "For career/profession/field questions, explicitly separate **Aptitude -> Field Selection -> Work Function -> Status/Visibility -> Timing of Entry/Change**. Use `px.career` first: `mode` = service/business/hybrid tendency, `work` = house-pattern scores, `fn` = ranked function tags, `vis` = visibility level, `dom` = dominant houses. Then refine with `px.hs`, `px.HI`, and raw graha detail. Rank the likely field signatures instead of listing many unrelated jobs equally.",
        health_prompt_line,
        "When `special_points` is present in VARIABLE_DATA_JSON (merged from chart context when available): "
        "use `gandanta_analysis` for Gandanta crisis zones if flagged. "
        "If `special_points` is absent or empty, skip without inventing values.",
        "Yoga lists, kota, and other legacy-only blocks may be absent from the bundle — work from what is present. "
        "Deep Sudarshana triple-chakra synthesis is handled by a dedicated parallel branch — do not expand full Sudarshana here.",
        "Do NOT write the Jaimini View, Nadi, KP, Ashtakavarga, Nakshatra, or Sudarshan specialist passes here — other branches cover them.",
        _PARASHARI_JSON_FOOTER,
    ]
    return "\n\n".join(p for p in parts if p)


def build_jaimini_branch_static_agent() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        JAIMINI_PILLAR,
        JAIMINI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (JAIMINI BRANCH ONLY — CONTEXT AGENT)\n",
        "Use ONLY the `jaimini`, `chara_dasha`, and `jx` objects in VARIABLE_DATA_JSON. `jaimini` carries compact keys JP/CK/PS/AG (`a`=`jaimini`); `chara_dasha` carries the active Chara timing spine (`P` rows with nested `ad`); `jx` carries derived Jaimini timing relationships (MD/AD relative to UL/A7/AL/KL and key karakas). See `context_agents/SCHEMA.md`.",
        "Structure the branch as: **Static Promise** -> **MD-Lagna Frame** -> **AD-Lagna Frame** -> **Manifestation Filter** -> **Confluence/Conflict**. Do not let a favorable static karaka story overrule a clearly adverse active MD/AD frame.",
        "Use `chara_dasha.P` to identify the active Mahadasha row (`ic=true`) and its active Antardasha row (`ad[].ic=true`). Run both temporary ascendants explicitly: **MD-Lagna Frame** and **AD-Lagna Frame**, then add a short **Confluence/Conflict** line (AD-Lagna prioritized for near-term manifestation when conflict appears).",
        "Marriage/partnership questions: full **DK → UL → A7** thread in `analysis`; **A7** requires interpretation of **grahas in the A7 sign** using `jaimini.JP.A7.pp` (e.g. GK = obstacle in embodied partnership), not sign-only—[J-8]. The same occupancy rule applies to UL/AL when relevant. Explicitly distinguish **partner nature**, **alliance/continuity**, and **embodied manifestation** rather than blending them into one verdict.",
        "When `jx` is present, use it to stay concrete: `jx.rf.UL/A7/AL/KL` gives MD/AD house positions from those lagnas; `jx.kr.AK/AmK/DK/GK` does the same for karakas; `jx.dk_asp` lists grahas aspecting DK sign; `jx.ul2`, `jx.al10`, and `jx.kl10` expose key manifestation/career signs with occupants. `jx.relationship` and `jx.career` are dedicated compact topic blocks.",
        "Career/status questions: include **AmK / KL / AL** explicitly and say whether the active Chara frame supports vocation, authority, visibility, or only workload without recognition. Use `jx.career` to distinguish vocation from status/image: `md`/`ad` = current support level from AmK frame, `img.al10` / `img.kl10` = image/vocation sign occupants.",
        "Marriage/partnership questions: use `jx.relationship` to stay concrete: `md`/`ad` = current A7 manifestation support, `gk_a7` = direct obstruction flag, `mal_a7` / `ben_a7` = A7 sign occupants by tone, `ul2_pp` = continuity filter.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "jaimini"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nadi_branch_static_agent(intent_category: str = "") -> str:
    health_prompt_line = (
        "Health questions: use `nx.health`: `dom`, `flags`, `sig`, `lead`, `systems`, `aa` / `aa_pl` to say whether the Nadi picture is chronic, acute, irregular, or sensitivity-driven, and which body-system themes are being pulled into the pattern. Do not give medical diagnosis; describe the astrological pattern only."
        if _is_health_category(intent_category)
        else ""
    )
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NADI_PILLAR,
        NADI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (NADI BRANCH ONLY — CONTEXT AGENT)\n",
        "Use ONLY the `nadi` and `nx` objects in VARIABLE_DATA_JSON. `nadi` carries raw linkage and age activation (`LK`, `AA`); `nx` carries derived Nadi topic summaries: dominant grahas, compact signatures, age-hit planets, and topic blocks for career / relationship / wealth / health. See `context_agents/SCHEMA.md`.",
        "Structure the branch as: **Dominant Nadi Grahas -> Linkage Logic -> Promise vs Activation -> Topic Verdict**. Use `nx.top` first so the analysis opens from the strongest grahas instead of reading all planets equally.",
        "Use `nx.sig` and the topic-level `sig` arrays whenever present. They are compact Nadi pair-signatures that already convert dominant graha pairs into topic meaning. Cite them explicitly instead of improvising broad planet prose.",
        "In `LK`, when **`rv` is true** for a graha, say explicitly in your write-up that **Nadi linkage here treats the planet as also active from the previous sign** (retro/vakra rule), so **`t`/`f`/`b`/`o` links** may reflect that base—not only the nominal sign in `s`.",
        "Use `nx.aa` to decide timing confidence. If `nx.aa` is empty, state that Nadi here is stronger for pattern/promise than current-year timing. If populated, explicitly mention the activated age, nakshatras, and planets.",
        "Career/profession questions: use `nx.career`: `dom` = dominant Nadi grahas, `tags` = ranked function themes, `sig` = high-value career signatures, `lead` = leading Nadi work-style, `aa` / `aa_pl` = age-hit career grahas.",
        "Marriage/relationship questions: use `nx.relationship`: `dom` = dominant relationship grahas, `flags` = support/delay/karmic/friction markers, `sig` = relationship signatures, `lead` = primary tone, `aa` / `aa_pl` = age-hit relationship grahas.",
        "Wealth questions: use `nx.wealth`: `dom`, `tags`, `sig`, `lead`, `aa` / `aa_pl` to say whether wealth is shown through advisory, commerce, client-facing, creative, or institutional channels.",
        health_prompt_line,
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "nadi"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nakshatra_branch_static_agent(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NAKSHATRA_PILLAR,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (NAKSHATRA BRANCH ONLY — CONTEXT AGENTS)\n",
        "Use ONLY `nakshatra` and `vim_dasha` objects in VARIABLE_DATA_JSON (compact keys per SCHEMA.md). "
        "`vim_dasha` provides current MD/AD and maraka flags for Tara-from-Moon / dasha quality checks.",
        "For any house-specific topic (e.g. marriage → 7th lord, career → 10th lord): the **house lord(s)** must appear in `analysis` with nakshatra+pada and **navamsa (D9) dignity** (debilitation/exaltation/own per pada mapping)—not only karaka or occupants—[NK-6]. "
        "Navatara/Tara and **own sign in D9** follow [NK-7]: verify against JSON; never claim Scorpio (e.g.) as Jupiter’s own sign.",
        "Do NOT repeat Parashari bundle, Jaimini, Nadi, KP, or Ashtakavarga — other passes cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "nakshatra"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_kp_branch_static_agent(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        KP_PILLAR,
        KP_PARALLEL_LIFE_STAGE_RULE,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (KP BRANCH ONLY — CONTEXT AGENTS)\n",
        "Use ONLY `kp` and `vim_dasha` in VARIABLE_DATA_JSON. `kp` has `KP` (cusp/significators); `vim_dasha` has current MD/AD for the trigger step.",
        "For each relevant house cusp, state **Sign Lord → Star Lord (NL) → Sub Lord (CSL)** from the JSON before CSL-only or 4-step detail; never skip Sign/Star lords when the payload lists them.",
        "Do NOT repeat Parashari bundle, Jaimini, Nadi, Nakshatra, or Ashtakavarga — other passes cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "kp"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_ashtakavarga_branch_static_agent() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        ASHTAKAVARGA_FILTER,
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        "\n# TASK (ASHTAKAVARGA BRANCH ONLY — CONTEXT AGENT)\n",
        "Use ONLY `ashtakavarga`, optional `vim_dasha`, and derived `ax` in VARIABLE_DATA_JSON. See `context_agents/SCHEMA.md`. "
        "Prefer **`D1.Ho`** for any \"Nth house\" bindus when present; **`D1.S`/`D1.B` are sign-indexed (0=Aries), not houses from lagna.",
        "`ax` is the AV reasoning spine: `top`/`weak` = strongest/weakest lagna houses, `topic.rows` = question-relevant houses with SAV+filtered BAV, `dasha` = MD/AD/PD AV quality rows, `transit` = event-planet usability rows, `conflicts` = SAV/BAV paradox flags. Use it explicitly.",
        "If `topic.rows_d9` is present, add D9 AV house confirmation briefly (secondary layer only).",
        "Do NOT repeat Parashari bundle, Jaimini, Nadi, Nakshatra, or KP doctrine — remain Ashtakavarga-only with concrete SAV/BAV judgment.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "ashtakavarga"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_sudarshan_branch_static_agent(intent_category: str) -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        SUDARSHANA_LOGIC,
        _domain_sutras(intent_category),
        HOUSE_SIGNIFICATIONS,
        DATA_SOVEREIGNTY,
        PERSONAL_CONSULTATION_RULES,
        "\n# TASK (SUDARSHANA BRANCH ONLY — MERGED CHART JSON)\n",
        "`shared_kernel` is minimal (birth, ascendant, dates, intent, compact dasha anchor) — not full chart JSON. "
        "Use `sx` as the Sudarshana reasoning spine and `sudarshana_context` only for raw backup: `sx.topic.rows` = relevant houses with 3-view agreement and support band, `sx.career` / `sx.relationship` / `sx.education` / `sx.health` = topic-specific Sudarshana blocks, `sx.current.topic` and `sx.current.<topic>` = current MD/AD/PD Sudarshana activation, `sx.dom` = dominant houses, `sx.patterns` = synthesis notes, `sx.triggers` = year-clock windows, `sx.D` = current dasha anchor. "
        "Rotate Lagna / Moon / Sun perspectives, but do not infer everything from scratch; prefer `sx` for disciplined reasoning, and for prediction/current questions explicitly say whether the active dasha planets are supporting or not supporting the Sudarshana topic. Treat triggers as confirmation windows rather than guaranteed events. "
        "Do NOT duplicate Parashari agent bundle, Jaimini, Nadi, Nakshatra, KP, or Ashtakavarga specialist passes — other branches cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "sudarshan"),
    ]
    return "\n\n".join(p for p in parts if p)
