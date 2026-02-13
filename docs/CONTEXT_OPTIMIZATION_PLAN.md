# Context Data Inventory & Optimization Plan

## Current State Analysis

**Total Context Size**: 153,628 bytes (150 KB) - WITHOUT transits
**With Transits**: ~251 KB (based on previous measurements)

## Complete Field Inventory (35 fields)

### Top 10 Largest Fields (82% of total)
1. **divisional_charts** (42,908 B / 27.9%) - All D-charts (D3-D60)
2. **chara_dasha** (22,450 B / 14.6%) - Jaimini sign-based dasha with antardashas
3. **planetary_analysis** (10,071 B / 6.6%) - D1 planet analysis for all 9 planets
4. **relationships** (10,007 B / 6.5%) - Argala analysis
5. **d9_planetary_analysis** (9,755 B / 6.3%) - D9 planet analysis for all 9 planets
6. **nakshatra_remedies** (9,311 B / 6.1%) - Remedies for all planets
7. **ashtakavarga** (6,505 B / 4.2%) - SAV + BAV for D1 and D9
8. **macro_transits_timeline** (6,085 B / 4.0%) - 5-year slow planet transits
9. **transit_data_availability** (6,011 B / 3.9%) - Transit request instructions
10. **jaimini_full_analysis** (4,939 B / 3.2%) - Relative views, raj yogas

### By Category

**Divisional Charts (27.9%)**
- divisional_charts: 42,908 B - Contains D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60

**Dasha Systems (17.1%)**
- chara_dasha: 22,450 B
- current_dashas: 1,908 B (Vimshottari MD/AD/PD with maraka analysis)
- shoola_dasha: 1,486 B
- yogini_dasha: 341 B
- kalchakra_dasha: 131 B

**Core Chart Data (15.4%)**
- planetary_analysis: 10,071 B (D1)
- d9_planetary_analysis: 9,755 B (D9)
- d1_chart: 3,404 B
- ascendant_info: 287 B
- birth_details: 124 B

**Yogas & Analysis (9.5%)**
- relationships: 10,007 B (Argala)
- yogas: 3,172 B
- advanced_analysis: 1,416 B (wars, vargottama, neecha bhanga, pancha mahapurusha)

**Transits (8.4%)**
- macro_transits_timeline: 6,085 B
- transit_data_availability: 6,011 B
- navatara_warnings: 765 B
- **transit_activations**: ~100 KB (when requested)

**Remedies (6.1%)**
- nakshatra_remedies: 9,311 B

**Jaimini System (5.1%)**
- jaimini_full_analysis: 4,939 B
- chara_karakas: 2,207 B
- jaimini_points: 716 B

**Ashtakavarga (4.2%)**
- ashtakavarga: 6,505 B (SAV + BAV for D1 and D9)

**Nadi & Advanced (1.8%)**
- nadi_links: 2,550 B
- nadi_age_activation: 229 B

**Special Points (1.9%)**
- sniper_points: 2,070 B (Bhrigu Bindu, Mrityu Bhaga)
- special_points: 787 B (Gandanta, Yogi/Avayogi)

**Kota Chakra (0.8%)**
- kota_chakra: 1,208 B

**Pushkara (0.4%)**
- pushkara_navamsa: 675 B

**Sudarshana (0.3%)**
- sudarshana_chakra: 535 B

**Other (0.9%)**
- RESPONSE_STRUCTURE_REQUIRED: 794 B
- birth_panchang: 331 B
- special_lagnas: 146 B (Indu Lagna)
- prediction_matrix: 141 B
- house_lordships: 117 B
- dasha_conflicts: 46 B

---

## Optimization Strategy: Category-Specific Requirements

### CAREER Category
**Required Fields** (Estimated: ~80 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D9, D10 (Dasamsa), Karkamsa
- ✅ Dashas: current_dashas, chara_dasha, yogini_dasha
- ✅ Jaimini: jaimini_points (AL, GL), jaimini_full_analysis (AmK analysis), chara_karakas
- ✅ Nadi: nadi_links (Saturn links for career nature)
- ✅ Yogas: yogas (career-related only)
- ✅ Transits: macro_transits_timeline, transit_activations (max 15)
- ✅ Ashtakavarga: ashtakavarga (for 10th house strength)
- ❌ Remove: D3, D4, D7, D12, D16, D20, D24, D27, D30, D40, D45, D60
- ❌ Remove: relationships (Argala), nakshatra_remedies, kota_chakra, pushkara_navamsa, shoola_dasha, kalchakra_dasha

### HEALTH Category
**Required Fields** (Estimated: ~70 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D9, D30 (Trimsamsa)
- ✅ Dashas: current_dashas, yogini_dasha
- ✅ Special: kota_chakra, sniper_points (Mrityu Bhaga)
- ✅ Transits: macro_transits_timeline, transit_activations (max 10), navatara_warnings
- ✅ Ashtakavarga: ashtakavarga (for 1st/6th/8th house strength)
- ✅ Advanced: advanced_analysis (neecha bhanga for recovery)
- ❌ Remove: D3, D4, D7, D10, D12, D16, D20, D24, D27, D40, D45, D60
- ❌ Remove: chara_dasha, jaimini_full_analysis, nadi_links, relationships, nakshatra_remedies

### MARRIAGE Category
**Required Fields** (Estimated: ~75 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D7 (Saptamsa), D9
- ✅ Dashas: current_dashas, chara_dasha, yogini_dasha
- ✅ Jaimini: jaimini_points (UL), jaimini_full_analysis, chara_karakas (DK)
- ✅ Nadi: nadi_links (Venus links for spouse nature)
- ✅ Yogas: yogas (marriage-related only)
- ✅ Transits: macro_transits_timeline, transit_activations (max 12)
- ✅ Ashtakavarga: ashtakavarga (for 7th house strength)
- ❌ Remove: D3, D4, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60
- ❌ Remove: relationships, nakshatra_remedies, kota_chakra, shoola_dasha, kalchakra_dasha

### WEALTH Category
**Required Fields** (Estimated: ~75 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D9
- ✅ Dashas: current_dashas, chara_dasha, yogini_dasha
- ✅ Jaimini: jaimini_points (HL, AL), jaimini_full_analysis, chara_karakas
- ✅ Nadi: nadi_links (Venus/Jupiter links for wealth sources)
- ✅ Special: special_lagnas (Indu Lagna), pushkara_navamsa
- ✅ Yogas: yogas (dhana yoga only)
- ✅ Transits: macro_transits_timeline, transit_activations (max 15)
- ✅ Ashtakavarga: ashtakavarga (for 2nd/11th house strength)
- ❌ Remove: All other D-charts
- ❌ Remove: relationships, nakshatra_remedies, kota_chakra, shoola_dasha, kalchakra_dasha

### TIMING Category
**Required Fields** (Estimated: ~120 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D9
- ✅ Dashas: ALL (current_dashas, chara_dasha, yogini_dasha, shoola_dasha, kalchakra_dasha)
- ✅ Jaimini: jaimini_full_analysis, chara_karakas
- ✅ Special: sniper_points (Bhrigu Bindu), sudarshana_chakra, nadi_age_activation
- ✅ Transits: macro_transits_timeline, transit_activations (max 25)
- ✅ Ashtakavarga: ashtakavarga (full)
- ✅ Prediction: prediction_matrix, dasha_conflicts
- ❌ Remove: Other D-charts, relationships, nakshatra_remedies, kota_chakra

### GENERAL Category (Fallback)
**Required Fields** (Estimated: ~100 KB):
- ✅ Core: birth_details, ascendant_info, d1_chart, house_lordships
- ✅ Planets: planetary_analysis, d9_planetary_analysis
- ✅ Divisional: D1, D9
- ✅ Dashas: current_dashas, chara_dasha, yogini_dasha
- ✅ Jaimini: jaimini_points, jaimini_full_analysis, chara_karakas
- ✅ Nadi: nadi_links
- ✅ Special: special_points, sniper_points
- ✅ Yogas: yogas (all)
- ✅ Transits: macro_transits_timeline, transit_activations (max 20)
- ✅ Ashtakavarga: ashtakavarga
- ❌ Remove: Other D-charts, relationships, nakshatra_remedies, kota_chakra, shoola_dasha, kalchakra_dasha

---

## Expected Size Reductions

| Category | Current | Optimized | Reduction |
|----------|---------|-----------|-----------|
| Career   | ~251 KB | ~95 KB    | 62%       |
| Health   | ~251 KB | ~85 KB    | 66%       |
| Marriage | ~251 KB | ~90 KB    | 64%       |
| Wealth   | ~251 KB | ~90 KB    | 64%       |
| Timing   | ~251 KB | ~135 KB   | 46%       |
| General  | ~251 KB | ~115 KB   | 54%       |

**Average Reduction**: ~59%

---

## Implementation Steps

1. ✅ **Phase 1**: Create database schema (DONE)
2. ✅ **Phase 2**: Extract all instruction modules (DONE)
3. ✅ **Phase 3**: Update Intent Router to return category keys (DONE)
4. **Phase 4**: Update seed data with detailed `required_data_fields` for each category
5. **Phase 5**: Implement context filtering in PromptConfigService
6. **Phase 6**: Update Chat Analyzer to use modular instructions + filtered context
7. **Phase 7**: Test and measure actual size reductions
8. **Phase 8**: Create admin UI for module/field management

---

## Next Action Required

**Decision Point**: Review the category-specific requirements above and confirm:
1. Are the field selections correct for each category?
2. Any critical fields missing?
3. Any unnecessary fields included?
4. Should we proceed with Phase 4 (updating seed data)?
