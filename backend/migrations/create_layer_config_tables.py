import sqlite3
import os

def create_layer_config_tables():
    """Create tables for managing astrological layers and field mappings"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Table 1: Astrological Layers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS astrological_layers (
                layer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_key TEXT UNIQUE NOT NULL,
                layer_name TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Context Fields (all 35 fields)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_fields (
                field_id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_key TEXT UNIQUE NOT NULL,
                field_name TEXT NOT NULL,
                description TEXT,
                estimated_size_bytes INTEGER,
                layer_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (layer_id) REFERENCES astrological_layers(layer_id)
            )
        """)
        
        # Table 3: Divisional Charts (separate table for granular control)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS divisional_charts (
                chart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_key TEXT UNIQUE NOT NULL,
                chart_name TEXT NOT NULL,
                chart_number INTEGER,
                primary_domain TEXT,
                description TEXT,
                estimated_size_bytes INTEGER DEFAULT 3000,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 4: Category Layer Requirements (which layers each category needs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_layer_requirements (
                requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_key TEXT NOT NULL,
                layer_id INTEGER NOT NULL,
                is_required BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (layer_id) REFERENCES astrological_layers(layer_id),
                UNIQUE(category_key, layer_id)
            )
        """)
        
        # Table 5: Category Divisional Chart Requirements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_divisional_requirements (
                requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_key TEXT NOT NULL,
                chart_id INTEGER NOT NULL,
                is_required BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chart_id) REFERENCES divisional_charts(chart_id),
                UNIQUE(category_key, chart_id)
            )
        """)
        
        # Table 6: Category Transit Limits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_transit_limits (
                limit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_key TEXT UNIQUE NOT NULL,
                max_transit_activations INTEGER DEFAULT 20,
                include_macro_transits BOOLEAN DEFAULT 1,
                include_navatara_warnings BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Layer configuration tables created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_layer_config_tables()
