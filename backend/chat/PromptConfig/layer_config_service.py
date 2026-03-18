import os
from typing import Dict, List, Optional

from db import get_conn, execute


class LayerConfigService:
    """Service for retrieving layer-based prompt configuration"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'astrology.db')
        self.db_path = db_path
    
    def get_category_configuration(self, category_key: str, tier_key: str = 'normal') -> Dict:
        """Get complete configuration for a category and tier including layers, fields, and charts"""
        with get_conn() as conn:
            # Get required layers
            cur = execute(
                conn,
                """
                SELECT al.layer_key, al.layer_name, al.priority
                FROM category_layer_requirements clr
                JOIN astrological_layers al ON clr.layer_id = al.layer_id
                WHERE clr.category_key = %s AND clr.tier_key = %s AND clr.is_required = TRUE AND al.is_active = TRUE
                ORDER BY al.priority
                """,
                (category_key, tier_key),
            )
            layer_rows = cur.fetchall() or []
            required_layers = [
                {"layer_key": r[0], "layer_name": r[1], "priority": r[2]}
                for r in layer_rows
            ]

            # Get required fields based on layers
            layer_keys = [layer["layer_key"] for layer in required_layers]
            required_fields: List[Dict] = []
            if layer_keys:
                placeholders = ",".join(["%s"] * len(layer_keys))
                cur = execute(
                    conn,
                    f"""
                    SELECT cf.field_key, cf.field_name, cf.estimated_size_bytes, al.layer_key
                    FROM context_fields cf
                    JOIN astrological_layers al ON cf.layer_id = al.layer_id
                    WHERE al.layer_key IN ({placeholders}) AND cf.is_active = TRUE
                    ORDER BY al.priority, cf.field_key
                    """,
                    tuple(layer_keys),
                )
                field_rows = cur.fetchall() or []
                required_fields = [
                    {
                        "field_key": r[0],
                        "field_name": r[1],
                        "estimated_size_bytes": r[2],
                        "layer_key": r[3],
                    }
                    for r in field_rows
                ]

            # Get required divisional charts
            cur = execute(
                conn,
                """
                SELECT dc.chart_key, dc.chart_name, dc.chart_number
                FROM category_divisional_requirements cdr
                JOIN divisional_charts dc ON cdr.chart_id = dc.chart_id
                WHERE cdr.category_key = %s AND cdr.tier_key = %s AND cdr.is_required = TRUE AND dc.is_active = TRUE
                ORDER BY dc.chart_number
                """,
                (category_key, tier_key),
            )
            chart_rows = cur.fetchall() or []
            required_charts = [
                {"chart_key": r[0], "chart_name": r[1], "chart_number": r[2]}
                for r in chart_rows
            ]

            # Get transit limits
            cur = execute(
                conn,
                """
                SELECT max_transit_activations, include_macro_transits, include_navatara_warnings
                FROM category_transit_limits
                WHERE category_key = %s AND tier_key = %s
                """,
                (category_key, tier_key),
            )
            tr = cur.fetchone()
            if tr:
                transit_limits = {
                    "max_transit_activations": tr[0],
                    "include_macro_transits": tr[1],
                    "include_navatara_warnings": tr[2],
                }
            else:
                transit_limits = {
                    "max_transit_activations": 20,
                    "include_macro_transits": 1,
                    "include_navatara_warnings": 0,
                }

        return {
            "category_key": category_key,
            "tier_key": tier_key,
            "required_layers": required_layers,
            "required_fields": required_fields,
            "required_divisional_charts": required_charts,
            "transit_limits": transit_limits,
        }
    
    def get_all_layers(self) -> List[Dict]:
        """Get all astrological layers"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT layer_id, layer_key, layer_name, description, priority, is_active
                FROM astrological_layers
                ORDER BY priority
                """,
            )
            rows = cur.fetchall() or []
        return [
            {
                "layer_id": r[0],
                "layer_key": r[1],
                "layer_name": r[2],
                "description": r[3],
                "priority": r[4],
                "is_active": r[5],
            }
            for r in rows
        ]
    
    def get_all_fields(self) -> List[Dict]:
        """Get all context fields with their layer assignments"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT cf.field_id, cf.field_key, cf.field_name, cf.description,
                       cf.estimated_size_bytes, cf.is_active,
                       al.layer_key, al.layer_name
                FROM context_fields cf
                JOIN astrological_layers al ON cf.layer_id = al.layer_id
                ORDER BY al.priority, cf.field_key
                """,
            )
            rows = cur.fetchall() or []
        return [
            {
                "field_id": r[0],
                "field_key": r[1],
                "field_name": r[2],
                "description": r[3],
                "estimated_size_bytes": r[4],
                "is_active": r[5],
                "layer_key": r[6],
                "layer_name": r[7],
            }
            for r in rows
        ]
    
    def get_all_divisional_charts(self) -> List[Dict]:
        """Get all divisional charts"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT chart_id, chart_key, chart_name, chart_number,
                       primary_domain, description, is_active
                FROM divisional_charts
                ORDER BY chart_number
                """,
            )
            rows = cur.fetchall() or []
        return [
            {
                "chart_id": r[0],
                "chart_key": r[1],
                "chart_name": r[2],
                "chart_number": r[3],
                "primary_domain": r[4],
                "description": r[5],
                "is_active": r[6],
            }
            for r in rows
        ]
    
    def get_category_layer_requirements(self, category_key: str, tier_key: str = 'normal') -> List[Dict]:
        """Get layer requirements for a specific category and tier"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT al.layer_key, al.layer_name, al.description, al.priority, clr.is_required
                FROM astrological_layers al
                LEFT JOIN category_layer_requirements clr
                    ON al.layer_id = clr.layer_id AND clr.category_key = %s AND clr.tier_key = %s
                ORDER BY al.priority
                """,
                (category_key, tier_key),
            )
            rows = cur.fetchall() or []
        return [
            {
                "layer_key": r[0],
                "layer_name": r[1],
                "description": r[2],
                "priority": r[3],
                "is_required": r[4],
            }
            for r in rows
        ]
    
    def get_category_chart_requirements(self, category_key: str, tier_key: str = 'normal') -> List[Dict]:
        """Get divisional chart requirements for a specific category and tier"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT dc.chart_key, dc.chart_name, cdr.is_required
                FROM divisional_charts dc
                LEFT JOIN category_divisional_requirements cdr
                    ON dc.chart_id = cdr.chart_id AND cdr.category_key = %s AND cdr.tier_key = %s
                ORDER BY dc.chart_number
                """,
                (category_key, tier_key),
            )
            rows = cur.fetchall() or []
        return [
            {
                "chart_key": r[0],
                "chart_name": r[1],
                "is_required": r[2],
            }
            for r in rows
        ]
    
    def update_category_layer_requirement(self, category_key: str, layer_key: str, is_required: bool, tier_key: str = 'normal'):
        """Update layer requirement for a category and tier (for admin UI)"""
        with get_conn() as conn:
            # Get layer_id
            cur = execute(
                conn,
                "SELECT layer_id FROM astrological_layers WHERE layer_key = %s",
                (layer_key,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown layer_key: {layer_key}")
            layer_id = row[0]

            execute(
                conn,
                """
                INSERT INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (category_key, tier_key, layer_id)
                DO UPDATE SET is_required = EXCLUDED.is_required
                """,
                (category_key, tier_key, layer_id, bool(is_required)),
            )
    
    def update_category_chart_requirement(self, category_key: str, chart_key: str, is_required: bool, tier_key: str = 'normal'):
        """Update divisional chart requirement for a category and tier (for admin UI)"""
        with get_conn() as conn:
            # Get chart_id
            cur = execute(
                conn,
                "SELECT chart_id FROM divisional_charts WHERE chart_key = %s",
                (chart_key,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown chart_key: {chart_key}")
            chart_id = row[0]

            execute(
                conn,
                """
                INSERT INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (category_key, tier_key, chart_id)
                DO UPDATE SET is_required = EXCLUDED.is_required
                """,
                (category_key, tier_key, chart_id, bool(is_required)),
            )
    
    def update_transit_limits(self, category_key: str, max_activations: int, 
                             include_macro: bool, include_navatara: bool, tier_key: str = 'normal'):
        """Update transit limits for a category and tier (for admin UI)"""
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO category_transit_limits
                    (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (category_key, tier_key)
                DO UPDATE SET
                    max_transit_activations = EXCLUDED.max_transit_activations,
                    include_macro_transits = EXCLUDED.include_macro_transits,
                    include_navatara_warnings = EXCLUDED.include_navatara_warnings
                """,
                (
                    category_key,
                    tier_key,
                    max_activations,
                    bool(include_macro),
                    bool(include_navatara),
                ),
            )
    
    def get_estimated_context_size(self, category_key: str, tier_key: str = 'normal') -> Dict:
        """Calculate estimated context size for a category and tier"""
        config = self.get_category_configuration(category_key, tier_key)
        
        # Sum field sizes
        field_size = sum(field['estimated_size_bytes'] for field in config['required_fields'])
        
        # Add divisional chart sizes (estimated 3KB each)
        chart_size = len(config['required_divisional_charts']) * 3000
        
        # Add transit size (estimated based on limit)
        transit_size = config['transit_limits']['max_transit_activations'] * 4000  # ~4KB per activation
        if config['transit_limits']['include_macro_transits']:
            transit_size += 6085
        if config['transit_limits']['include_navatara_warnings']:
            transit_size += 765
        
        total_size = field_size + chart_size + transit_size
        
        return {
            'category_key': category_key,
            'field_size_bytes': field_size,
            'chart_size_bytes': chart_size,
            'transit_size_bytes': transit_size,
            'total_size_bytes': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'reduction_percent': round((1 - total_size / 251000) * 100, 2)  # vs 251KB baseline
        }
