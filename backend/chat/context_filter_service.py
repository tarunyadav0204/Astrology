import json

from db import get_conn, execute


class ContextFilterService:
    """Service to filter context data based on tier configuration"""
    
    @staticmethod
    def filter_context(context: dict, category_key: str, tier_key: str = 'normal') -> dict:
        """Filter context data based on tier configuration from database
        
        Chart Filtering Strategy:
        - Intent Router suggests relevant charts based on question analysis
        - Database config defines baseline charts for category/tier
        - Final result is UNION of both (keep if suggested OR configured)
        - This preserves Intent Router intelligence while respecting admin limits
        """
        
        print(f"\n🔍 CONTEXT FILTER: category={category_key}, tier={tier_key}")
        print(f"   Input context keys: {list(context.keys())}")
        with get_conn() as conn:
            # Get tier context config
            cur = execute(
                conn,
                """
                SELECT tier_context_config FROM prompt_category_config
                WHERE category_key = %s AND tier_key = %s
                """,
                (category_key, tier_key),
            )
            result = cur.fetchone()
            
            if not result or not result[0]:
                print(f"   ⚠️ No tier config found, returning full context")
                return context
            
            try:
                tier_config = json.loads(result[0])
                print(f"   📋 Tier config: {tier_config}")
            except:
                print(f"   ⚠️ Failed to parse tier config, returning full context")
                return context
            
            # If config says "all", return as-is
            if not tier_config or tier_config.get('layers') == 'all':
                print(f"   ✅ Config says 'all', returning full context")
                return context
            
            # Get required layers for this tier
            cur = execute(
                conn,
                """
                SELECT al.layer_key FROM category_layer_requirements clr
                JOIN astrological_layers al ON clr.layer_id = al.layer_id
                WHERE clr.category_key = %s AND clr.tier_key = %s AND clr.is_required = TRUE
                """,
                (category_key, tier_key),
            )
            required_layer_keys = [row[0] for row in cur.fetchall()]
            print(f"   📦 Required layers: {required_layer_keys}")
            
            # Get context field keys for required layers
            if required_layer_keys:
                placeholders = ','.join('?' * len(required_layer_keys))
                cur = execute(
                    conn,
                    f"""
                    SELECT cf.field_key FROM context_fields cf
                    JOIN astrological_layers al ON cf.layer_id = al.layer_id
                    WHERE al.layer_key IN ({placeholders}) AND cf.is_active = TRUE
                    """,
                    tuple(required_layer_keys),
                )
                allowed_field_keys = [row[0] for row in cur.fetchall()]
                print(f"   ✅ Allowed fields: {allowed_field_keys}")
            else:
                allowed_field_keys = []
                print(f"   ⚠️ No required layers, no fields allowed")
        
        # Create filtered context
        filtered_context = {}
        removed_keys = []
        
        # Only include allowed fields
        for key, value in context.items():
            if key in allowed_field_keys or key in ['tier_key', 'intent_category', 'analysis_type', 'current_date_info', 'response_format', 'user_facts']:
                filtered_context[key] = value
            else:
                removed_keys.append(key)
        
        print(f"   🗑️ REMOVED KEYS: {removed_keys}")
        print(f"   ✅ Filtered context keys: {list(filtered_context.keys())}")
        
        # Handle charts separately - UNION of Intent Router suggestions and database config
        charts_config = tier_config.get('charts', 'all')
        if 'divisional_charts' in filtered_context:
            divisional_charts = filtered_context['divisional_charts']
            original_charts = list(divisional_charts.keys())
            
            # Get Intent Router's chart suggestions from context
            intent_suggested_charts = context.get('intent_result', {}).get('divisional_charts', [])
            
            if charts_config != 'all' and isinstance(charts_config, list):
                # UNION: Keep charts that are EITHER in database config OR suggested by Intent Router
                allowed_charts = set(charts_config) | set(intent_suggested_charts)
                filtered_charts = {k: v for k, v in divisional_charts.items() if k in allowed_charts}
                removed_charts = [k for k in original_charts if k not in filtered_charts]
                filtered_context['divisional_charts'] = filtered_charts
                print(f"   📊 Intent Router suggested: {intent_suggested_charts}")
                print(f"   📊 Database config allows: {charts_config}")
                print(f"   ✅ UNION result (kept): {list(filtered_charts.keys())}")
                print(f"   🗑️ REMOVED CHARTS: {removed_charts}")
            else:
                print(f"   ✅ Charts config is 'all', keeping all charts: {original_charts}")
        
        # Handle transits
        if not tier_config.get('transits', True):
            if 'current_transits' in filtered_context:
                filtered_context.pop('current_transits')
                print(f"   🗑️ REMOVED: current_transits")
            if 'transit_activations' in filtered_context:
                filtered_context.pop('transit_activations')
                print(f"   🗑️ REMOVED: transit_activations")
        
        return filtered_context
    
    @staticmethod
    def get_tier_limits(tier_key: str = 'normal') -> dict:
        """Get size limits for a tier"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT max_instruction_size, max_context_size
                FROM prompt_tiers
                WHERE tier_key = %s
                """,
                (tier_key,),
            )
            result = cur.fetchone()
        
        if result:
            return {
                'max_instruction_size': result[0],
                'max_context_size': result[1]
            }
        
        return {'max_instruction_size': 100000, 'max_context_size': 150000}
