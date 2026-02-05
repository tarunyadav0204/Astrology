import sqlite3
import os
from typing import Dict, List, Optional

class LayerConfigService:
    """Service for retrieving layer-based prompt configuration"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'astrology.db')
        self.db_path = db_path
    
    def get_category_configuration(self, category_key: str, tier_key: str = 'normal') -> Dict:
        """Get complete configuration for a category and tier including layers, fields, and charts"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get required layers
            cursor.execute("""
                SELECT al.layer_key, al.layer_name, al.priority
                FROM category_layer_requirements clr
                JOIN astrological_layers al ON clr.layer_id = al.layer_id
                WHERE clr.category_key = ? AND clr.tier_key = ? AND clr.is_required = 1 AND al.is_active = 1
                ORDER BY al.priority
            """, (category_key, tier_key))
            
            required_layers = [dict(row) for row in cursor.fetchall()]
            
            # Get required fields based on layers
            layer_keys = [layer['layer_key'] for layer in required_layers]
            placeholders = ','.join('?' * len(layer_keys))
            
            cursor.execute(f"""
                SELECT cf.field_key, cf.field_name, cf.estimated_size_bytes, al.layer_key
                FROM context_fields cf
                JOIN astrological_layers al ON cf.layer_id = al.layer_id
                WHERE al.layer_key IN ({placeholders}) AND cf.is_active = 1
                ORDER BY al.priority, cf.field_key
            """, layer_keys)
            
            required_fields = [dict(row) for row in cursor.fetchall()]
            
            # Get required divisional charts
            cursor.execute("""
                SELECT dc.chart_key, dc.chart_name, dc.chart_number
                FROM category_divisional_requirements cdr
                JOIN divisional_charts dc ON cdr.chart_id = dc.chart_id
                WHERE cdr.category_key = ? AND cdr.tier_key = ? AND cdr.is_required = 1 AND dc.is_active = 1
                ORDER BY dc.chart_number
            """, (category_key, tier_key))
            
            required_charts = [dict(row) for row in cursor.fetchall()]
            
            # Get transit limits
            cursor.execute("""
                SELECT max_transit_activations, include_macro_transits, include_navatara_warnings
                FROM category_transit_limits
                WHERE category_key = ? AND tier_key = ?
            """, (category_key, tier_key))
            
            transit_config = cursor.fetchone()
            transit_limits = dict(transit_config) if transit_config else {
                'max_transit_activations': 20,
                'include_macro_transits': 1,
                'include_navatara_warnings': 0
            }
            
            return {
                'category_key': category_key,
                'tier_key': tier_key,
                'required_layers': required_layers,
                'required_fields': required_fields,
                'required_divisional_charts': required_charts,
                'transit_limits': transit_limits
            }
            
        finally:
            conn.close()
    
    def get_all_layers(self) -> List[Dict]:
        """Get all astrological layers"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT layer_id, layer_key, layer_name, description, priority, is_active
                FROM astrological_layers
                ORDER BY priority
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_all_fields(self) -> List[Dict]:
        """Get all context fields with their layer assignments"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT cf.field_id, cf.field_key, cf.field_name, cf.description,
                       cf.estimated_size_bytes, cf.is_active,
                       al.layer_key, al.layer_name
                FROM context_fields cf
                JOIN astrological_layers al ON cf.layer_id = al.layer_id
                ORDER BY al.priority, cf.field_key
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_all_divisional_charts(self) -> List[Dict]:
        """Get all divisional charts"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT chart_id, chart_key, chart_name, chart_number, 
                       primary_domain, description, is_active
                FROM divisional_charts
                ORDER BY chart_number
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_category_layer_requirements(self, category_key: str, tier_key: str = 'normal') -> List[Dict]:
        """Get layer requirements for a specific category and tier"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT al.layer_key, al.layer_name, al.description, al.priority, clr.is_required
                FROM astrological_layers al
                LEFT JOIN category_layer_requirements clr 
                    ON al.layer_id = clr.layer_id AND clr.category_key = ? AND clr.tier_key = ?
                ORDER BY al.priority
            """, (category_key, tier_key))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_category_chart_requirements(self, category_key: str, tier_key: str = 'normal') -> List[Dict]:
        """Get divisional chart requirements for a specific category and tier"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT dc.chart_key, dc.chart_name, cdr.is_required
                FROM divisional_charts dc
                LEFT JOIN category_divisional_requirements cdr 
                    ON dc.chart_id = cdr.chart_id AND cdr.category_key = ? AND cdr.tier_key = ?
                ORDER BY dc.chart_number
            """, (category_key, tier_key))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def update_category_layer_requirement(self, category_key: str, layer_key: str, is_required: bool, tier_key: str = 'normal'):
        """Update layer requirement for a category and tier (for admin UI)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get layer_id
            cursor.execute("SELECT layer_id FROM astrological_layers WHERE layer_key = ?", (layer_key,))
            layer_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT OR REPLACE INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, ?, ?, ?)
            """, (category_key, tier_key, layer_id, 1 if is_required else 0))
            
            conn.commit()
        finally:
            conn.close()
    
    def update_category_chart_requirement(self, category_key: str, chart_key: str, is_required: bool, tier_key: str = 'normal'):
        """Update divisional chart requirement for a category and tier (for admin UI)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get chart_id
            cursor.execute("SELECT chart_id FROM divisional_charts WHERE chart_key = ?", (chart_key,))
            chart_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT OR REPLACE INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, ?, ?, ?)
            """, (category_key, tier_key, chart_id, 1 if is_required else 0))
            
            conn.commit()
        finally:
            conn.close()
    
    def update_transit_limits(self, category_key: str, max_activations: int, 
                             include_macro: bool, include_navatara: bool, tier_key: str = 'normal'):
        """Update transit limits for a category and tier (for admin UI)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO category_transit_limits 
                (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, ?, ?, ?, ?)
            """, (category_key, tier_key, max_activations, 1 if include_macro else 0, 1 if include_navatara else 0))
            
            conn.commit()
        finally:
            conn.close()
    
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
