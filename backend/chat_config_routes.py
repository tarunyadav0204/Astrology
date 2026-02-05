from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from auth import get_current_user, User
from chat.PromptConfig.layer_config_service import LayerConfigService

router = APIRouter(prefix="/api/admin/chat-config", tags=["admin-chat-config"])

class LayerRequirementUpdate(BaseModel):
    category_key: str
    tier_key: str
    layer_key: str
    is_required: bool

class ChartRequirementUpdate(BaseModel):
    category_key: str
    tier_key: str
    chart_key: str
    is_required: bool

class TransitLimitsUpdate(BaseModel):
    category_key: str
    tier_key: str
    max_transit_activations: int
    include_macro_transits: bool
    include_navatara_warnings: bool

@router.get("/tiers")
async def get_tiers(current_user: dict = Depends(get_current_user)):
    """Get all available tiers"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tier_key, tier_name, description, max_instruction_size, max_context_size, priority
        FROM prompt_tiers
        ORDER BY priority DESC
    """)
    
    tiers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"tiers": tiers}

@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get all available categories"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "categories": [
            {"key": "career", "name": "Career"},
            {"key": "health", "name": "Health"},
            {"key": "marriage", "name": "Marriage"},
            {"key": "wealth", "name": "Wealth"},
            {"key": "progeny", "name": "Progeny"},
            {"key": "education", "name": "Education"},
            {"key": "timing", "name": "Timing"},
            {"key": "general", "name": "General"}
        ]
    }

@router.get("/layers")
async def get_all_layers(current_user: dict = Depends(get_current_user)):
    """Get all astrological layers"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    layers = service.get_all_layers()
    return {"layers": layers}

@router.get("/fields")
async def get_all_fields(current_user: dict = Depends(get_current_user)):
    """Get all context fields"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    fields = service.get_all_fields()
    return {"fields": fields}

@router.get("/charts")
async def get_all_charts(current_user: dict = Depends(get_current_user)):
    """Get all divisional charts"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    charts = service.get_all_divisional_charts()
    return {"charts": charts}

@router.get("/category/{category_key}")
async def get_category_config(category_key: str, tier_key: str = 'normal', current_user: dict = Depends(get_current_user)):
    """Get complete configuration for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    config = service.get_category_configuration(category_key, tier_key)
    size_info = service.get_estimated_context_size(category_key, tier_key)
    
    return {
        "config": config,
        "size_info": size_info
    }

@router.get("/category/{category_key}/layers")
async def get_category_layers(category_key: str, tier_key: str = 'normal', current_user: dict = Depends(get_current_user)):
    """Get layer requirements for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    layers = service.get_category_layer_requirements(category_key, tier_key)
    return {"layers": layers}

@router.get("/category/{category_key}/charts")
async def get_category_charts(category_key: str, tier_key: str = 'normal', current_user: dict = Depends(get_current_user)):
    """Get chart requirements for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    charts = service.get_category_chart_requirements(category_key, tier_key)
    return {"charts": charts}

@router.post("/category/layer")
async def update_layer_requirement(
    update: LayerRequirementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update layer requirement for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    service.update_category_layer_requirement(
        update.category_key,
        update.layer_key,
        update.is_required,
        update.tier_key
    )
    return {"success": True, "message": "Layer requirement updated"}

@router.post("/category/chart")
async def update_chart_requirement(
    update: ChartRequirementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update chart requirement for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    service.update_category_chart_requirement(
        update.category_key,
        update.chart_key,
        update.is_required,
        update.tier_key
    )
    return {"success": True, "message": "Chart requirement updated"}

@router.post("/category/transit-limits")
async def update_transit_limits(
    update: TransitLimitsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update transit limits for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    service.update_transit_limits(
        update.category_key,
        update.max_transit_activations,
        update.include_macro_transits,
        update.include_navatara_warnings,
        update.tier_key
    )
    return {"success": True, "message": "Transit limits updated"}

@router.get("/size-estimates")
async def get_all_size_estimates(current_user: dict = Depends(get_current_user)):
    """Get size estimates for all categories"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    service = LayerConfigService()
    categories = ["career", "health", "marriage", "wealth", "progeny", "education", "timing", "general"]
    
    estimates = []
    for category in categories:
        size_info = service.get_estimated_context_size(category)
        estimates.append(size_info)
    
    return {"estimates": estimates}

@router.get("/instruction-modules")
async def get_instruction_modules(current_user: dict = Depends(get_current_user)):
    """Get all instruction modules"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, module_key, module_name, character_count, priority, is_active
        FROM prompt_instruction_modules
        ORDER BY priority
    """)
    
    modules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"modules": modules}

@router.get("/category/{category_key}/instruction-modules")
async def get_category_instruction_modules(category_key: str, tier_key: str = 'normal', current_user: dict = Depends(get_current_user)):
    """Get instruction module requirements for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    import json
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT required_modules, tier_context_config
        FROM prompt_category_config
        WHERE category_key = ? AND tier_key = ?
    """, (category_key, tier_key))
    
    result = cursor.fetchone()
    required_modules = []
    tier_context_config = {}
    if result:
        if result['required_modules']:
            try:
                required_modules = json.loads(result['required_modules'])
            except:
                required_modules = result['required_modules'].split(',') if result['required_modules'] else []
        if result['tier_context_config']:
            try:
                tier_context_config = json.loads(result['tier_context_config'])
            except:
                tier_context_config = {}
    
    cursor.execute("""
        SELECT id, module_key, module_name, character_count, priority, is_active
        FROM prompt_instruction_modules
        ORDER BY priority
    """)
    
    modules = []
    for row in cursor.fetchall():
        module = dict(row)
        module['is_required'] = module['module_key'] in required_modules
        modules.append(module)
    
    conn.close()
    return {"modules": modules, "tier_context_config": tier_context_config}

class InstructionModuleUpdate(BaseModel):
    category_key: str
    tier_key: str
    module_keys: List[str]
    tier_context_config: Optional[Dict] = None

class InstructionTextUpdate(BaseModel):
    module_key: str
    instruction_text: str

@router.get("/instruction-module/{module_key}")
async def get_instruction_module_text(module_key: str, current_user: dict = Depends(get_current_user)):
    """Get instruction text for a specific module"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT module_key, module_name, instruction_text, character_count
        FROM prompt_instruction_modules
        WHERE module_key = ?
    """, (module_key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {"module": dict(result)}

@router.post("/instruction-module/update")
async def update_instruction_module_text(
    update: InstructionTextUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update instruction text for a module"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    char_count = len(update.instruction_text)
    cursor.execute("""
        UPDATE prompt_instruction_modules
        SET instruction_text = ?, character_count = ?, updated_at = CURRENT_TIMESTAMP
        WHERE module_key = ?
    """, (update.instruction_text, char_count, update.module_key))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Instruction text updated", "character_count": char_count}

@router.post("/category/instruction-modules")
async def update_category_instruction_modules(
    update: InstructionModuleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update instruction module requirements for a category and tier"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    import sqlite3
    import json
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    modules_str = json.dumps(update.module_keys)
    context_config_str = json.dumps(update.tier_context_config) if update.tier_context_config else '{}'
    
    cursor.execute("""
        UPDATE prompt_category_config
        SET required_modules = ?, tier_context_config = ?
        WHERE category_key = ? AND tier_key = ?
    """, (modules_str, context_config_str, update.category_key, update.tier_key))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Instruction modules and context config updated"}

class CopyConfigRequest(BaseModel):
    source_category: str
    tier_key: str

@router.post("/copy-to-all")
async def copy_config_to_all_categories(
    request: CopyConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """Copy instruction module config from one category to all others"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import sqlite3
    conn = None
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get source config
        cursor.execute("""
            SELECT required_modules
            FROM prompt_category_config
            WHERE category_key = ? AND tier_key = ?
        """, (request.source_category, request.tier_key))
        
        result = cursor.fetchone()
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Source config not found")
        
        required_modules = result[0]
        
        # Get all categories
        categories = ["career", "health", "marriage", "wealth", "progeny", "education", "timing", "general"]
        
        # Update all categories except source
        for category in categories:
            if category != request.source_category:
                cursor.execute("""
                    UPDATE prompt_category_config
                    SET required_modules = ?
                    WHERE category_key = ? AND tier_key = ?
                """, (required_modules, category, request.tier_key))
        
        conn.commit()
        return {"success": True, "message": f"Config copied to all categories for {request.tier_key} tier"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error copying config: {str(e)}")
    finally:
        if conn:
            conn.close()
