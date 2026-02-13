# Context Data Categorization Matrix

## Two-Dimensional Categorization System

### Dimension 1: Domain Categories
- Career
- Health
- Marriage
- Wealth
- Progeny
- Education
- Timing
- General

### Dimension 2: Astrological Layers
- **Layer 1: Basic/Core** - Essential Vedic techniques
- **Layer 2: Intermediate** - Standard divisional charts and dashas
- **Layer 3: Advanced** - Specialized systems (Ashtakavarga, Shadbala)
- **Layer 4: Specialized** - Jaimini, Nadi, Kota Chakra

---

## Complete Field Mapping by Layer

### LAYER 1: BASIC/CORE (23,943 B / 15.6%)
**Essential for ALL queries**

| Field | Size | Description |
|-------|------|-------------|
| planetary_analysis | 10,071 B | D1 planet analysis (signs, houses, nakshatras) |
| d9_planetary_analysis | 9,755 B | D9 planet analysis |
| d1_chart | 3,404 B | Basic chart positions |
| ascendant_info | 287 B | Lagna details |
| house_lordships | 117 B | House rulers |
| birth_details | 124 B | Date, time, location |
| birth_panchang | 331 B | Tithi, nakshatra, yoga, karana |

**Usage**: Required for ALL categories, ALL queries

---

### LAYER 2: INTERMEDIATE (29,270 B / 19.0%)
**Standard Vedic techniques**

#### Divisional Charts (Domain-Specific)
| Chart | Size (est) | Primary Domain | Secondary Domains |
|-------|------------|----------------|-------------------|
| D3 (Drekkana) | ~3,000 B | Siblings, courage | General |
| D4 (Chaturthamsa) | ~3,000 B | Property, assets | Wealth |
| D7 (Saptamsa) | ~3,000 B | **Marriage, children** | Progeny |
| D10 (Dasamsa) | ~3,000 B | **Career, profession** | Timing |
| D12 (Dwadasamsa) | ~3,000 B | Parents, ancestry | General |
| D16 (Shodasamsa) | ~3,000 B | Vehicles, comforts | Wealth |
| D20 (Vimshamsa) | ~3,000 B | Spiritual progress | General |
| D24 (Chaturvimshamsa) | ~3,000 B | **Education, learning** | Career |
| D27 (Nakshatramsa) | ~3,000 B | Strengths/weaknesses | General |
| D30 (Trimsamsa) | ~3,000 B | **Health, diseases** | Timing |
| D40 (Khavedamsa) | ~3,000 B | Auspicious/inauspicious | General |
| D45 (Akshavedamsa) | ~3,000 B | Character, conduct | General |
| D60 (Shashtiamsa) | ~3,000 B | Past life karma | General |

**Total Divisional Charts**: 42,908 B (but domain-specific selection reduces this)

#### Basic Dashas
| Field | Size | Primary Domains |
|-------|------|-----------------|
| current_dashas | 1,908 B | ALL (Vimshottari MD/AD/PD) |
| yogini_dasha | 341 B | Career, Marriage, Wealth, Timing |

**Usage**: Select divisional charts based on domain; dashas for timing-related queries

---

### LAYER 3: ADVANCED (19,193 B / 12.5%)
**Specialized strength & yoga analysis**

| Field | Size | Description | Primary Domains |
|-------|------|-------------|-----------------|
| ashtakavarga | 6,505 B | SAV + BAV for D1 and D9 | Career, Health, Marriage, Wealth |
| yogas | 3,172 B | Raj, Dhana, Pancha Mahapurusha | Career, Wealth, General |
| advanced_analysis | 1,416 B | Wars, Vargottama, Neecha Bhanga | Health, Timing, General |
| nakshatra_remedies | 9,311 B | Remedies for all planets | Health, General (optional) |

**Usage**: Include for detailed strength analysis; remedies optional

---

### LAYER 4: JAIMINI SYSTEM (30,312 B / 19.7%)
**Jaimini-specific techniques**

| Field | Size | Description | Primary Domains |
|-------|------|-------------|-----------------|
| chara_dasha | 22,450 B | Sign-based dasha with antardashas | Career, Marriage, Timing |
| jaimini_full_analysis | 4,939 B | Relative views, raj yogas | Career, Marriage, Wealth |
| chara_karakas | 2,207 B | AK, AmK, BK, DK, etc. | Career, Marriage, General |
| jaimini_points | 716 B | AL, UL, HL, GL, A7 | Career, Marriage, Wealth |
| relationships | 10,007 B | Argala analysis | Marriage (optional), General |

**Usage**: Essential for Jaimini-based queries; optional for basic queries

---

### LAYER 5: NADI ASTROLOGY (2,779 B / 1.8%)
**Nadi-specific techniques**

| Field | Size | Description | Primary Domains |
|-------|------|-------------|-----------------|
| nadi_links | 2,550 B | Planet-to-planet links | Career, Marriage, Wealth |
| nadi_age_activation | 229 B | Age-based activations | Timing |

**Usage**: Include for career/marriage nature analysis; timing predictions

---

### LAYER 6: SPECIALIZED SYSTEMS (5,275 B / 3.4%)
**Rare/specialized techniques**

| Field | Size | Description | Primary Domains |
|-------|------|-------------|-----------------|
| sniper_points | 2,070 B | Bhrigu Bindu, Mrityu Bhaga | Health, Timing |
| kota_chakra | 1,208 B | Kota analysis | Health |
| special_points | 787 B | Gandanta, Yogi/Avayogi | General |
| pushkara_navamsa | 675 B | Pushkara degrees | Wealth |
| sudarshana_chakra | 535 B | Triple chakra analysis | Timing |

**Usage**: Domain-specific; include only when relevant

---

### LAYER 7: TIMING & TRANSITS (18,946 B / 12.3%)
**Transit and timing analysis**

| Field | Size | Description | Primary Domains |
|-------|------|-------------|-----------------|
| macro_transits_timeline | 6,085 B | 5-year slow planet transits | ALL timing queries |
| transit_data_availability | 6,011 B | Transit request instructions | ALL timing queries |
| transit_activations | ~100,000 B | Current transit activations | Timing (limit to 10-25) |
| navatara_warnings | 765 B | Nakshatra-based warnings | Health, Timing |
| shoola_dasha | 1,486 B | Event-based dasha | Timing |
| kalchakra_dasha | 131 B | Kalachakra dasha | Timing |
| prediction_matrix | 141 B | Prediction framework | Timing |
| dasha_conflicts | 46 B | Conflicting dasha results | Timing |

**Usage**: Include macro_transits for all; full transit_activations only for timing queries

---

### LAYER 8: METADATA (1,940 B / 1.3%)
**Response structure and special lagnas**

| Field | Size | Description |
|-------|------|-------------|
| RESPONSE_STRUCTURE_REQUIRED | 794 B | JSON response format |
| special_lagnas | 146 B | Indu Lagna |

**Usage**: Always include RESPONSE_STRUCTURE_REQUIRED

---

## Domain-Specific Layer Requirements

### CAREER
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D10, D24 only
- ✅ Layer 3: Ashtakavarga, Yogas (career-related)
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points AL/GL, chara_karakas AmK)
- ✅ Layer 5: Nadi (Saturn links)
- ❌ Layer 6: None
- ✅ Layer 7: Macro transits, limited activations (15)
- ✅ Layer 8: Metadata

**Estimated Size**: ~58 KB (62% reduction)

---

### HEALTH
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D30 only
- ✅ Layer 3: Ashtakavarga, Advanced analysis
- ❌ Layer 4: None
- ❌ Layer 5: None
- ✅ Layer 6: Kota Chakra, Sniper Points (Mrityu Bhaga)
- ✅ Layer 7: Macro transits, Navatara warnings, limited activations (10)
- ✅ Layer 8: Metadata

**Estimated Size**: ~52 KB (66% reduction)

---

### MARRIAGE
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D7, D9 only
- ✅ Layer 3: Ashtakavarga, Yogas (marriage-related)
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points UL, chara_karakas DK)
- ✅ Layer 5: Nadi (Venus links)
- ❌ Layer 6: None
- ✅ Layer 7: Macro transits, limited activations (12)
- ✅ Layer 8: Metadata

**Estimated Size**: ~60 KB (64% reduction)

---

### WEALTH
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D4, D16 only
- ✅ Layer 3: Ashtakavarga, Yogas (dhana yoga)
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points HL/AL, chara_karakas)
- ✅ Layer 5: Nadi (Venus/Jupiter links)
- ✅ Layer 6: Pushkara Navamsa, Special Lagnas (Indu)
- ✅ Layer 7: Macro transits, limited activations (15)
- ✅ Layer 8: Metadata

**Estimated Size**: ~62 KB (63% reduction)

---

### PROGENY
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D7 only
- ✅ Layer 3: Ashtakavarga
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points A5, chara_karakas PK)
- ✅ Layer 5: Nadi (Jupiter links)
- ❌ Layer 6: None
- ✅ Layer 7: Macro transits, limited activations (10)
- ✅ Layer 8: Metadata

**Estimated Size**: ~55 KB (65% reduction)

---

### EDUCATION
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D24 only
- ✅ Layer 3: Ashtakavarga, Yogas (education-related)
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points A4, chara_karakas)
- ✅ Layer 5: Nadi (Mercury links)
- ❌ Layer 6: None
- ✅ Layer 7: Macro transits, limited activations (12)
- ✅ Layer 8: Metadata

**Estimated Size**: ~58 KB (62% reduction)

---

### TIMING
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D9 only
- ✅ Layer 3: Ashtakavarga (full)
- ✅ Layer 4: Jaimini (ALL)
- ✅ Layer 5: Nadi (ALL)
- ✅ Layer 6: Sniper Points, Sudarshana Chakra
- ✅ Layer 7: ALL (macro, activations 25, shoola, kalchakra, prediction_matrix)
- ✅ Layer 8: Metadata

**Estimated Size**: ~105 KB (46% reduction)

---

### GENERAL (Fallback)
- ✅ Layer 1: Basic/Core (ALL)
- ✅ Layer 2: D9 only
- ✅ Layer 3: Ashtakavarga, Yogas (all)
- ✅ Layer 4: Jaimini (chara_dasha, jaimini_points, chara_karakas)
- ✅ Layer 5: Nadi (nadi_links)
- ✅ Layer 6: Special Points, Sniper Points
- ✅ Layer 7: Macro transits, limited activations (20)
- ✅ Layer 8: Metadata

**Estimated Size**: ~85 KB (54% reduction)

---

## Implementation Strategy

### Step 1: Define Layer Enum
```python
class AstrologicalLayer(Enum):
    BASIC_CORE = "basic_core"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    JAIMINI = "jaimini"
    NADI = "nadi"
    SPECIALIZED = "specialized"
    TIMING_TRANSITS = "timing_transits"
    METADATA = "metadata"
```

### Step 2: Map Fields to Layers
Create a mapping table in database or config:
```python
FIELD_LAYER_MAPPING = {
    # Layer 1: Basic/Core
    "planetary_analysis": "basic_core",
    "d9_planetary_analysis": "basic_core",
    "d1_chart": "basic_core",
    # ... etc
    
    # Layer 2: Intermediate
    "divisional_charts.D3": "intermediate",
    "divisional_charts.D7": "intermediate",
    # ... etc
}
```

### Step 3: Update Category Configuration
Add layer requirements to each category:
```json
{
  "category_key": "career",
  "required_layers": ["basic_core", "intermediate", "advanced", "jaimini", "nadi", "timing_transits", "metadata"],
  "required_divisional_charts": ["D10", "D24"],
  "transit_activation_limit": 15
}
```

### Step 4: Implement Layered Filtering
```python
def build_filtered_context(category_config, full_context):
    filtered = {}
    
    # Always include Layer 1
    filtered.update(get_layer_fields(full_context, "basic_core"))
    
    # Add required layers
    for layer in category_config["required_layers"]:
        filtered.update(get_layer_fields(full_context, layer))
    
    # Filter divisional charts
    if "divisional_charts" in filtered:
        filtered["divisional_charts"] = filter_divisional_charts(
            full_context["divisional_charts"],
            category_config["required_divisional_charts"]
        )
    
    return filtered
```

---

## Next Steps

1. **Review & Confirm**: Validate the layer categorization and domain requirements
2. **Create Layer Mapping Table**: Add new database table for field-to-layer mapping
3. **Update Seed Data**: Add layer requirements to category configurations
4. **Implement Filtering Logic**: Create layered context builder
5. **Test & Measure**: Verify actual size reductions match estimates

---

## Questions for Confirmation

1. **Layer Granularity**: Is the 8-layer system appropriate, or should we consolidate?
2. **Divisional Chart Selection**: Are the domain-specific D-chart selections correct?
3. **Jaimini Layer**: Should Jaimini be optional for basic queries or always included?
4. **Nadi Layer**: Is Nadi essential for career/marriage or optional?
5. **Transit Limits**: Are the activation limits (10-25) appropriate per domain?
