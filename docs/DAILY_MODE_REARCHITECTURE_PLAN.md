# Daily Mode Rearchitecture Plan

Status: In progress
Owner: Codex + AstroRoshni team
Scope: Backend-first rearchitecture for exact-day astrology answers

## Goal

Make `PREDICT_DAILY` a dedicated backend product surface instead of a lightly constrained version of generic chat.

## Architecture Target

1. Intent router detects an exact-day question.
2. Daily orchestrator builds authoritative deterministic evidence.
3. Daily context reducer sends a compact daily-only JSON payload to the LLM.
4. Daily answer generator produces a practical, date-specific answer.
5. Generic natal chat flow is bypassed for `PREDICT_DAILY`.

## Phase Checklist

### Phase 1: Dedicated Daily Path

- [x] Define the multi-phase rearchitecture plan in-repo
- [x] Add a dedicated `daily_orchestrator`
- [x] Add a dedicated `daily_context_reducer`
- [x] Add a dedicated `daily_schema`
- [x] Branch early in chat generation for `PREDICT_DAILY`
- [ ] Tighten user-local exact-date handling end-to-end
- [ ] Add targeted regression coverage for daily orchestration

### Phase 2: Fast-Planet Daily Layer

- [x] Add deterministic daily fast-planet evidence for Sun, Moon, Mercury, Venus, Mars
- [x] Model practical daily tones: communication, relationship climate, conflict risk, comfort, visibility
- [x] Merge fast-planet evidence into the compact daily payload

### Phase 3: Intraday Timing Layer

- [x] Add morning / afternoon / evening segmentation
- [x] Add Moon sign / nakshatra transition windows
- [x] Add tithi / yoga / karana transition windows
- [x] Add practical favorable / caution windows
- [x] Expose intraday payload for UI and chat reuse

### Phase 4: Daily Micro-Intents

- [x] Add micro-intent classification for day-level action questions
- [x] Support: communication, interview/meeting, money/payment, relationship outreach, travel/commute
- [x] Support: health/treatment, study/exam, decision/signing, confrontation, general-day
- [x] Map each micro-intent to event houses and daily evidence emphasis

### Phase 5: Confidence + Contradictions

- [x] Add deterministic confidence scoring
- [x] Add supportive vs contradicting factor synthesis
- [x] Add favorable / mixed / challenging verdict logic
- [x] Add “eventful but frictional” vs “smooth but low manifestation” handling

### Phase 6: Daily School Refinement

- [x] Strengthen KP daily materialization logic by action-type
- [x] Strengthen Nadi daily activation weighting
- [x] Strengthen Jaimini daily manifestation logic
- [x] Strengthen Ashtakavarga daily usability logic

### Phase 7: Output Contract + Benchmarks

- [x] Add canonical structured daily answer schema
- [x] Add deterministic benchmark cases
- [x] Add binary daily question handling
- [x] Add outcome-quality tests for directness, date-specificity, and anti-drift behavior

## Current Risks Still Open

- Daily “today / tomorrow” resolution can still depend too much on server-local time in some entry paths.
- User-local exact-date resolution is not yet fully hardened across all entry paths.
- Daily timezone/date resolution is now the main architectural gap before this feels fully locked.

## Guiding Principles

- Daily answers must be driven by exact-day evidence, not broad lifetime storytelling.
- PR / SK / PD should dominate event logic; AD / MD should remain background permission.
- Slow planets are backdrop unless they directly connect to active daily triggers.
- The user should get concrete “what to do / what to avoid / when in the day” guidance.
