from datetime import datetime, date
import sqlite3
import json
from typing import Dict, List, Any
from event_prediction.config import NAKSHATRA_NAMES, NAKSHATRA_LORDS
from classical_engine.prediction_engine import ClassicalPredictionEngine

class DailyPredictionEngine:
    def __init__(self):
        self.init_prediction_rules_db()
    
    def init_prediction_rules_db(self):
        """Initialize daily prediction rules database"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prediction_rules (
                id TEXT PRIMARY KEY,
                rule_type TEXT NOT NULL,
                conditions JSON NOT NULL,
                prediction_template TEXT NOT NULL,
                confidence_base INTEGER DEFAULT 50,
                life_areas JSON,
                timing_advice TEXT,
                colors JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert basic rules if table is empty
        cursor.execute("SELECT COUNT(*) FROM daily_prediction_rules")
        if cursor.fetchone()[0] == 0:
            self._insert_basic_rules(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_basic_rules(self, cursor):
        """Insert basic daily prediction rules"""
        basic_rules = [
            {
                "id": "venus_dasha_rohini_moon",
                "rule_type": "dasha_nakshatra_combo",
                "conditions": {
                    "maha_dasha": "Venus",
                    "moon_nakshatra": "Rohini"
                },
                "prediction_template": "Your Venus period combines with Moon in Rohini to enhance artistic sensibilities and material desires. Excellent day for beauty, luxury, and relationship matters.",
                "confidence_base": 85,
                "life_areas": ["relationships", "creativity", "luxury"],
                "timing_advice": "Best time: 10 AM - 2 PM",
                "colors": ["white", "pink"]
            },
            {
                "id": "mercury_antar_communication",
                "rule_type": "antar_dasha",
                "conditions": {
                    "antar_dasha": "Mercury"
                },
                "prediction_template": "Mercury's influence brings focus to communication, learning, and business matters. Ideal for writing, negotiations, and intellectual pursuits.",
                "confidence_base": 70,
                "life_areas": ["communication", "business", "learning"],
                "timing_advice": "Best time: 6 AM - 9 AM",
                "colors": ["green", "yellow"]
            },
            {
                "id": "jupiter_transit_benefic",
                "rule_type": "transit_aspect",
                "conditions": {
                    "jupiter_aspects": ["1st", "5th", "9th", "10th", "11th"]
                },
                "prediction_template": "Jupiter's benefic influence brings wisdom, growth, and positive opportunities. Focus on learning, teaching, and spiritual activities.",
                "confidence_base": 75,
                "life_areas": ["wisdom", "growth", "spirituality"],
                "timing_advice": "Best time: 12 PM - 3 PM",
                "colors": ["yellow", "gold"]
            },
            {
                "id": "saturn_aspect_discipline",
                "rule_type": "transit_aspect", 
                "conditions": {
                    "saturn_aspects": ["6th", "8th", "12th"]
                },
                "prediction_template": "Saturn's influence calls for patience, discipline, and careful planning. Avoid hasty decisions and focus on long-term goals.",
                "confidence_base": 65,
                "life_areas": ["discipline", "patience", "planning"],
                "timing_advice": "Best time: 2 PM - 5 PM",
                "colors": ["blue", "black"]
            },
            {
                "id": "mars_dasha_action",
                "rule_type": "dasha_energy",
                "conditions": {
                    "maha_dasha": "Mars"
                },
                "prediction_template": "Mars energy brings courage, action, and leadership opportunities. Channel this dynamic energy into productive activities and physical exercise.",
                "confidence_base": 80,
                "life_areas": ["action", "leadership", "energy"],
                "timing_advice": "Best time: 6 AM - 10 AM",
                "colors": ["red", "orange"]
            },
            {
                "id": "general_daily_guidance",
                "rule_type": "general",
                "conditions": {},
                "prediction_template": "Today brings opportunities for growth and self-reflection. Focus on your goals and maintain a positive mindset. Trust your intuition and take practical steps toward your aspirations.",
                "confidence_base": 60,
                "life_areas": ["general", "growth", "mindset"],
                "timing_advice": "Best time: Morning hours",
                "colors": ["white", "light blue"]
            },
            {
                "id": "moon_general_influence",
                "rule_type": "moon_influence",
                "conditions": {
                    "has_moon_nakshatra": True
                },
                "prediction_template": "The Moon's current position influences your emotional state and intuitive abilities. Pay attention to your feelings and use them as guidance for important decisions.",
                "confidence_base": 55,
                "life_areas": ["emotions", "intuition", "decisions"],
                "timing_advice": "Best time: Evening hours",
                "colors": ["silver", "white"]
            }
        ]
        
        for rule in basic_rules:
            cursor.execute('''
                INSERT INTO daily_prediction_rules 
                (id, rule_type, conditions, prediction_template, confidence_base, life_areas, timing_advice, colors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule["id"],
                rule["rule_type"], 
                json.dumps(rule["conditions"]),
                rule["prediction_template"],
                rule["confidence_base"],
                json.dumps(rule["life_areas"]),
                rule["timing_advice"],
                json.dumps(rule["colors"])
            ))
    
    def get_daily_predictions(self, birth_data: Dict, chart_data: Dict, dasha_data: Dict, transit_data: Dict, target_date: date = None) -> Dict:
        """Generate daily predictions using rule engine"""
        if target_date is None:
            target_date = date.today()
        
        # Extract current astrological state
        current_state = self._extract_current_state(birth_data, chart_data, dasha_data, transit_data, target_date)
        
        # Find matching rules
        matching_rules = self._find_matching_rules(current_state)
        
        # Calculate predictions with confidence scores
        predictions = self._calculate_predictions(matching_rules, current_state)
        
        # Generate classical prediction using your 7-step technique
        classical_engine = ClassicalPredictionEngine(birth_data)
        classical_result = classical_engine.generate_comprehensive_prediction()
        classical_prediction = {
            "prediction": classical_result["prediction"],
            "debug_summary": classical_engine.get_debug_summary()
        }
        
        return {
            "date": target_date.isoformat(),
            "current_state": current_state,
            "predictions": predictions,
            "total_confidence": self._calculate_total_confidence(predictions),
            "classical_prediction": classical_prediction,
            "debug_mode": True  # Enable detailed debugging
        }
    
    def _extract_current_state(self, birth_data: Dict, chart_data: Dict, dasha_data: Dict, transit_data: Dict, target_date: date) -> Dict:
        """Extract current astrological state for rule matching"""
        
        # Get current dashas
        current_maha = None
        current_antar = None
        
        if dasha_data and 'maha_dashas' in dasha_data:
            for dasha in dasha_data['maha_dashas']:
                start_date = datetime.strptime(dasha['start'], '%Y-%m-%d').date()
                end_date = datetime.strptime(dasha['end'], '%Y-%m-%d').date()
                if start_date <= target_date <= end_date:
                    current_maha = dasha['planet']
                    break
        
        # Get today's Moon nakshatra from transit data
        moon_nakshatra = None
        if transit_data and 'planets' in transit_data and 'Moon' in transit_data['planets']:
            moon_longitude = transit_data['planets']['Moon']['longitude']
            nakshatra_index = int(moon_longitude / 13.333333)
            moon_nakshatra = NAKSHATRA_NAMES[nakshatra_index]
        
        # Analyze Jupiter and Saturn aspects
        jupiter_aspects = []
        saturn_aspects = []
        
        if transit_data and 'planets' in transit_data:
            # Simple house aspect calculation (this is simplified)
            if 'Jupiter' in transit_data['planets']:
                jupiter_house = self._calculate_house_from_ascendant(
                    transit_data['planets']['Jupiter']['longitude'],
                    chart_data.get('ascendant', 0)
                )
                jupiter_aspects = [str(jupiter_house)]
            
            if 'Saturn' in transit_data['planets']:
                saturn_house = self._calculate_house_from_ascendant(
                    transit_data['planets']['Saturn']['longitude'], 
                    chart_data.get('ascendant', 0)
                )
                saturn_aspects = [str(saturn_house)]
        
        return {
            "maha_dasha": current_maha,
            "antar_dasha": current_antar,
            "moon_nakshatra": moon_nakshatra,
            "jupiter_aspects": jupiter_aspects,
            "saturn_aspects": saturn_aspects,
            "target_date": target_date.isoformat()
        }
    
    def _calculate_house_from_ascendant(self, planet_longitude: float, ascendant_longitude: float) -> int:
        """Calculate which house a planet is in from ascendant"""
        # Simplified whole sign house calculation
        planet_sign = int(planet_longitude / 30)
        ascendant_sign = int(ascendant_longitude / 30)
        house = ((planet_sign - ascendant_sign) % 12) + 1
        return house
    
    def _find_matching_rules(self, current_state: Dict) -> List[Dict]:
        """Find rules that match current astrological state"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM daily_prediction_rules WHERE is_active = TRUE")
        all_rules = cursor.fetchall()
        conn.close()
        
        matching_rules = []
        
        for rule_row in all_rules:
            rule = {
                "id": rule_row[0],
                "rule_type": rule_row[1], 
                "conditions": json.loads(rule_row[2]),
                "prediction_template": rule_row[3],
                "confidence_base": rule_row[4],
                "life_areas": json.loads(rule_row[5]) if rule_row[5] else [],
                "timing_advice": rule_row[6],
                "colors": json.loads(rule_row[7]) if rule_row[7] else []
            }
            
            if self._rule_matches(rule["conditions"], current_state):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches(self, conditions: Dict, current_state: Dict) -> bool:
        """Check if rule conditions match current state"""
        # General rules with no conditions always match
        if not conditions:
            return True
        
        for condition_key, condition_value in conditions.items():
            current_value = current_state.get(condition_key)
            
            if condition_key in ["maha_dasha", "antar_dasha", "moon_nakshatra"]:
                if current_value != condition_value:
                    return False
            
            elif condition_key == "has_moon_nakshatra":
                if condition_value and not current_state.get("moon_nakshatra"):
                    return False
            
            elif condition_key in ["jupiter_aspects", "saturn_aspects"]:
                if not current_value:
                    continue
                # Check if any of the current aspects match the condition
                if isinstance(condition_value, list):
                    if not any(aspect in condition_value for aspect in current_value):
                        return False
                else:
                    if condition_value not in current_value:
                        return False
        
        return True
    
    def _calculate_predictions(self, matching_rules: List[Dict], current_state: Dict) -> List[Dict]:
        """Calculate final predictions with confidence scores"""
        predictions = []
        
        for rule in matching_rules:
            # Base confidence from rule
            confidence = rule["confidence_base"]
            
            # Boost confidence if multiple factors align
            if current_state.get("maha_dasha") and current_state.get("moon_nakshatra"):
                confidence += 10
            
            # Cap confidence at 95%
            confidence = min(confidence, 95)
            
            prediction = {
                "rule_id": rule["id"],
                "prediction": rule["prediction_template"],
                "confidence": confidence,
                "life_areas": rule["life_areas"],
                "timing_advice": rule["timing_advice"],
                "colors": rule["colors"],
                "rule_type": rule["rule_type"]
            }
            
            predictions.append(prediction)
        
        # Sort by confidence (highest first)
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return predictions
    
    def _calculate_total_confidence(self, predictions: List[Dict]) -> int:
        """Calculate overall confidence score"""
        if not predictions:
            return 0
        
        # Weighted average of top 3 predictions
        top_predictions = predictions[:3]
        total_weight = 0
        weighted_sum = 0
        
        for i, pred in enumerate(top_predictions):
            weight = 1.0 / (i + 1)  # Decreasing weight
            weighted_sum += pred["confidence"] * weight
            total_weight += weight
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 0
    
    def add_prediction_rule(self, rule_data: Dict) -> bool:
        """Add new prediction rule"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO daily_prediction_rules 
                (id, rule_type, conditions, prediction_template, confidence_base, life_areas, timing_advice, colors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule_data["id"],
                rule_data["rule_type"],
                json.dumps(rule_data["conditions"]),
                rule_data["prediction_template"],
                rule_data.get("confidence_base", 50),
                json.dumps(rule_data.get("life_areas", [])),
                rule_data.get("timing_advice", ""),
                json.dumps(rule_data.get("colors", []))
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding rule: {e}")
            return False
        finally:
            conn.close()
    
    def reset_prediction_rules(self) -> bool:
        """Reset prediction rules to defaults"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM daily_prediction_rules")
            self._insert_basic_rules(cursor)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error resetting rules: {e}")
            return False
        finally:
            conn.close()