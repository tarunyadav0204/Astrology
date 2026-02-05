# Multi-Tier Chat Configuration System

## Overview
The multi-tier system allows granular control over both system instructions and context data sent to Gemini AI based on category and tier combinations.

## Architecture

### Database Schema

#### `prompt_tiers` Table
```sql
- tier_key (TEXT, PRIMARY KEY): 'premium', 'normal', 'light'
- tier_name (TEXT): Display name
- description (TEXT): Tier description
- max_instruction_size (INTEGER): Max instruction characters
- max_context_size (INTEGER): Max context data characters
- priority (INTEGER): Tier priority (3=premium, 2=normal, 1=light)
```

#### `prompt_category_config` Table (Updated)
```sql
- category_key (TEXT): 'career', 'health', 'marriage', etc.
- tier_key (TEXT): 'premium', 'normal', 'light'
- required_modules (TEXT): JSON array of instruction module keys
- tier_context_config (TEXT): JSON config for context data filtering
- enabled (BOOLEAN): Whether config is active
```

### Configuration Matrix
```
                    Premium                 Normal                  Light
Career          All 41 modules          Essential modules       Core modules only
                All layers              basic+houses+planets    basic only
                All charts              D1+D9                   D1 only
                Transits: Yes           Transits: No            Transits: No

Health          All 41 modules          Essential modules       Core modules only
                All layers              basic+houses+planets    basic only
                All charts              D1+D9                   D1 only
                Transits: Yes           Transits: No            Transits: No

... (8 categories × 3 tiers = 24 configurations)
```

## Default Tier Configurations

### Premium Tier
- **Limits**: 200KB instructions + 300KB context
- **Instructions**: All 41 modules
- **Context Config**:
  ```json
  {
    "layers": "all",
    "charts": "all",
    "transits": true
  }
  ```

### Normal Tier (Default)
- **Limits**: 100KB instructions + 150KB context
- **Instructions**: Essential modules (category-specific)
- **Context Config**:
  ```json
  {
    "layers": ["basic", "houses", "planets"],
    "charts": ["D1", "D9"],
    "transits": false
  }
  ```

### Light Tier
- **Limits**: 50KB instructions + 75KB context
- **Instructions**: Core modules only (core_identity, response_format)
- **Context Config**:
  ```json
  {
    "layers": ["basic"],
    "charts": ["D1"],
    "transits": false
  }
  ```

## Runtime Flow

1. **User sends chat message**
2. **Intent Router** determines `category_key` (e.g., "career")
3. **Context Builder** adds `tier_key` to context (default: "normal")
4. **System Instruction Loader** loads modules for (category, tier)
   ```python
   instruction_loader.get_instructions_for_category(category_key, tier_key)
   ```
5. **Context Filter Service** filters context data for (category, tier)
   ```python
   ContextFilterService.filter_context(context, category_key, tier_key)
   ```
6. **Gemini Analyzer** receives optimized prompt

## Admin UI Features

### Tier Selector
- Dropdown showing all tiers with limits
- Format: "Premium (200KB instructions + 300KB context)"
- Changes reload category configuration

### Tier Info Banner
- Shows current tier name and description
- Displays tier limits and purpose

### System Instructions Tab
- Shows tier-specific module selection
- Displays current tier_context_config
- Save updates to correct (category, tier) combination

### Context Data Tab
- Configure layers, charts, transits per tier
- Real-time size estimation
- Visual indication of tier limits

## API Endpoints

### Get Tiers
```
GET /api/admin/chat-config/tiers
Response: { tiers: [...] }
```

### Get Category Config (Tier-Specific)
```
GET /api/admin/chat-config/category/{category_key}?tier_key={tier_key}
Response: { config: {...}, size_info: {...} }
```

### Get Instruction Modules (Tier-Specific)
```
GET /api/admin/chat-config/category/{category_key}/instruction-modules?tier_key={tier_key}
Response: { modules: [...], tier_context_config: {...} }
```

### Update Instruction Modules (Tier-Specific)
```
POST /api/admin/chat-config/category/instruction-modules
Body: {
  category_key: "career",
  tier_key: "normal",
  module_keys: ["core_identity", "career_analysis", ...],
  tier_context_config: { layers: [...], charts: [...], transits: true }
}
```

## Service Layer

### SystemInstructionLoader
```python
def get_instructions_for_category(self, category_key: str, tier_key: str = 'normal') -> str:
    # Loads instruction modules from database based on category and tier
    # Returns assembled instruction text
```

### ContextFilterService
```python
@staticmethod
def filter_context(context: dict, category_key: str, tier_key: str = 'normal') -> dict:
    # Filters context data based on tier_context_config
    # Removes layers, charts, transits not in config
    
@staticmethod
def get_tier_limits(tier_key: str = 'normal') -> dict:
    # Returns max_instruction_size and max_context_size for tier
```

## Usage Examples

### Setting Tier at Runtime
```python
# In chat route or context builder
context['tier_key'] = 'premium'  # or 'normal', 'light'
```

### Filtering Context
```python
from chat.context_filter_service import ContextFilterService

# Filter context based on tier
filtered_context = ContextFilterService.filter_context(
    context=full_context,
    category_key='career',
    tier_key='normal'
)
```

### Loading Instructions
```python
from chat.system_instruction_loader import SystemInstructionLoader

loader = SystemInstructionLoader()
instructions = loader.get_instructions_for_category(
    category_key='career',
    tier_key='premium'
)
```

## Migration

Run the migration to create tier system:
```bash
cd backend
python3 migrations/create_tier_system.py
```

This will:
1. Create `prompt_tiers` table
2. Add `tier_key` and `tier_context_config` columns to `prompt_category_config`
3. Seed 3 tiers (premium, normal, light)
4. Create 24 default configurations (8 categories × 3 tiers)
5. Migrate existing configs to tier-based structure

## Future Enhancements

1. **User-Tier Mapping**: Assign tiers to users based on subscription
2. **Dynamic Tier Selection**: Auto-select tier based on user credits
3. **Tier Analytics**: Track usage and performance per tier
4. **Custom Tiers**: Allow admins to create custom tiers
5. **Tier Inheritance**: Allow tiers to inherit from parent tiers
6. **A/B Testing**: Compare performance across tiers

## Benefits

1. **Cost Control**: Reduce API costs by limiting context for lower tiers
2. **Performance**: Faster responses with smaller prompts
3. **Scalability**: Support more users with tiered pricing
4. **Flexibility**: Easy to add new tiers or modify existing ones
5. **Granular Control**: Per-category, per-tier configuration
6. **Database-Driven**: No code changes needed to adjust tiers
