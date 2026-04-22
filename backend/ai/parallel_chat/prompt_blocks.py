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
1) SPECIALIST_BRANCH_OUTPUTS_JSON — their "analysis" / "bullets" fields.
2) LAST Q&A TURNS — up to 3 prior user/assistant exchanges (genuine follow-ups only).
3) CURRENT QUESTION — the same question the specialists answered.

You must:
- Produce ONE answer following the RESPONSE FORMAT template below (same section headers as legacy single-pass).
- Synthesize branch findings into those sections: Parashari drives primary "what/when"; weave in Jaimini/Nadi/Nakshatra/KP/Ashtakavarga/Sudarshana when present. If a branch is missing or status=unavailable, note briefly under that #### subsection and continue.
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


def build_parashari_branch_static(intent_category: str) -> str:
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
        "Apply ASHTAKAVARGA_FILTER [AV-4] BAV < 3 override where relevant.",
        "Do NOT repeat full Parashari, Jaimini, Nadi, Nakshatra, or KP doctrine — cite numerical bindus and house strength only.",
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
        "`shared_kernel` is minimal (birth, ascendant, current date, response_format, intent only) — no D1, divisionals, or Vimshottari timelines. "
        "Use ONLY `sudarshana_context` for chart mechanics: `sudarshana_chakra` (lagna_chart, chandra_lagna, surya_lagna rotated houses + synthesis) "
        "and `sudarshana_dasha` when present (precision year-clock / triggers for the focused year). "
        "Apply legacy Sudarshana rules: compare event/house themes across Body (Lagna), Mind (Moon), Soul (Sun); state agreement confidence (3/3, 2/3) per SUDARSHANA_LOGIC. "
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
        "When current Chara MD and AD signs are available, you MUST produce dual-frame analysis: (1) **MD-Lagna Frame** and (2) **AD-Lagna Frame**. "
        "Treat each sign as temporary Lagna, then add a short **Confluence/Conflict** conclusion; near-term priority goes to AD-Lagna when they differ.",
        "For marriage/partnership or 7th-house themes: thread **DK + UL + Darapada (A7)**. **A7 must be analyzed in depth** (sign + planets in that sign; GK or other grahas in A7’s sign = concrete friction or support in the physical/logistical reality of the union)—see JAIMINI_PILLAR [J-8]. Never stop at naming A7’s sign alone.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "jaimini"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nadi_branch_static() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NADI_PILLAR,
        NADI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (NADI BRANCH ONLY)\n",
        "Use ONLY Nadi linkage + age activation JSON.",
        "When you discuss a planet that is retrograde in the linkage data, state clearly that **in this Nadi (BNN-style) treatment, a retrograde graha is also considered from the previous sign** for trine / directional links—so connections may follow that virtual base, not the nominal sign alone.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "nadi"),
    ]
    return "\n\n".join(p for p in parts if p)


# --- Agent-payload TASK lines (VARIABLE_DATA_JSON uses compact SCHEMA.md keys; ASTRO_PARALLEL_AGENT_CONTEXT=1) ---


def build_parashari_branch_static_agent(intent_category: str) -> str:
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
        "Analyze using `parashari_agents` in VARIABLE_DATA_JSON (each key is a context agent id: "
        "core_d1, d1_graha, vim_dasha, div_d9, div_intent, transit_win, dasha_win, panch_maitri, sniper_pts). "
        "`div_intent` carries other intent-listed divisionals (D3–D60, Karkamsa, Swamsa); D1 and D9 are not repeated there because `core_d1` and `div_d9` already provide them. "
        "**If `div_intent` includes D7 (Saptamsa), you MUST analyze it** for marriage/children/partnership threads—do not ignore it. "
        "`d1_graha` → **`G`**: use **`av`** / **`sc`** for outcome delivery (Yogakaraka, 7th lord, etc.); never skip critical **Mrit/Dead**-style states per [P-7]. "
        "Each value is compact JSON with `a` = agent id; see `context_agents/SCHEMA.md` for field meanings (P, G, D, C, etc.).",
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
        "Use ONLY the `jaimini` object in VARIABLE_DATA_JSON (compact keys: JP, CK, AG, `a`=`jaimini`). See `context_agents/SCHEMA.md`.",
        "If current Chara MD and AD signs are present in `JP`, run both temporary ascendants explicitly: **MD-Lagna Frame** and **AD-Lagna Frame**, then a short **Confluence/Conflict** line (AD-Lagna prioritized for near-term manifestation when conflict appears).",
        "Marriage/partnership questions: full **DK → UL → A7** thread in `analysis`; **A7** requires interpretation of **grahas in the A7 sign** (e.g. GK = obstacle in embodied partnership), not sign-only—[J-8].",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "jaimini"),
    ]
    return "\n\n".join(p for p in parts if p)


def build_nadi_branch_static_agent() -> str:
    parts = [
        CORE_PERSONA,
        NO_DEATH_ETHICS,
        NADI_PILLAR,
        NADI_ANALYSIS_STRUCTURE,
        DATA_SOVEREIGNTY,
        "\n# TASK (NADI BRANCH ONLY — CONTEXT AGENT)\n",
        "Use ONLY the `nadi` object (LK, AA, `a`=`nadi`). See `context_agents/SCHEMA.md`.",
        "In `LK`, when **`rv` is true** for a graha, say explicitly in your write-up that **Nadi linkage here treats the planet as also active from the previous sign** (retro/vakra rule), so **`t`/`f`/`b`/`o` links** may reflect that base—not only the nominal sign in `s`.",
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
        "Use ONLY the `ashtakavarga` object (D1 SAV/BAV, optional D9, `a`=`ashtakavarga`). See `context_agents/SCHEMA.md`. "
        "Prefer **`D1.Ho`** for any \"Nth house\" bindus when present; **`D1.S`/`D1.B` are sign-indexed (0=Aries), not houses from lagna.",
        "Do NOT repeat Parashari bundle, Jaimini, Nadi, Nakshatra, or KP doctrine — cite bindus only.",
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
        "`shared_kernel` is minimal (birth, ascendant, dates, intent) — not full chart JSON. "
        "Use the same `sudarshana_context` as legacy slices: `sudarshana_chakra` + optional `sudarshana_dasha` from merged context (not context agents). "
        "Rotate Lagna / Moon / Sun perspectives; apply confidence wording from SUDARSHANA_LOGIC. "
        "Do NOT duplicate Parashari agent bundle, Jaimini, Nadi, Nakshatra, KP, or Ashtakavarga specialist passes — other branches cover them.",
        _BRANCH_JSON_FOOTER.replace("<branch_id>", "sudarshan"),
    ]
    return "\n\n".join(p for p in parts if p)
