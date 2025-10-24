from datetime import datetime, timedelta
from ..utils.kp_calculations import KPCalculations
from ..config.kp_constants import EVENT_HOUSES

class KPEventTimingService:
    @staticmethod
    def predict_event_timing(birth_data, event_type, current_date=None):
        """Predict timing for specific events using KP principles"""
        if current_date is None:
            current_date = datetime.now()
        
        # Get relevant houses for the event
        relevant_houses = EVENT_HOUSES.get(event_type, [1, 10, 11])
        
        # Calculate ruling planets for the person
        birth_datetime = datetime.strptime(f"{birth_data['birth_date']} {birth_data['birth_time']}", "%Y-%m-%d %H:%M")
        ruling_planets = KPCalculations.get_ruling_planets(
            birth_datetime, 
            birth_data['latitude'], 
            birth_data['longitude']
        )
        
        # Generate predictions
        predictions = KPEventTimingService._generate_timing_predictions(
            ruling_planets, relevant_houses, event_type, current_date
        )
        
        return {
            "event_type": event_type,
            "relevant_houses": relevant_houses,
            "ruling_planets": ruling_planets,
            "favorable_periods": predictions["favorable_periods"],
            "challenging_periods": predictions["challenging_periods"],
            "best_timing": predictions["favorable_periods"][0] if predictions["favorable_periods"] else None,
            "general_advice": predictions["overall_outlook"],
            "generated_on": current_date.isoformat()
        }
    
    @staticmethod
    def _generate_timing_predictions(ruling_planets, relevant_houses, event_type, base_date):
        """Generate timing predictions based on KP principles"""
        predictions = {
            "favorable_periods": [],
            "challenging_periods": [],
            "neutral_periods": [],
            "overall_outlook": ""
        }
        
        # Define planet strengths for different events
        event_planet_strengths = {
            "marriage": {
                "strong": ["Venus", "Jupiter", "Moon"],
                "moderate": ["Mercury", "Sun"],
                "weak": ["Mars", "Saturn", "Rahu", "Ketu"]
            },
            "career": {
                "strong": ["Sun", "Jupiter", "Mercury", "Saturn"],
                "moderate": ["Mars", "Venus"],
                "weak": ["Moon", "Rahu", "Ketu"]
            },
            "health": {
                "strong": ["Sun", "Jupiter", "Moon"],
                "moderate": ["Venus", "Mercury"],
                "weak": ["Mars", "Saturn", "Rahu", "Ketu"]
            },
            "education": {
                "strong": ["Mercury", "Jupiter", "Sun"],
                "moderate": ["Venus", "Moon"],
                "weak": ["Mars", "Saturn", "Rahu", "Ketu"]
            },
            "children": {
                "strong": ["Jupiter", "Sun", "Moon"],
                "moderate": ["Venus", "Mercury"],
                "weak": ["Mars", "Saturn", "Rahu", "Ketu"]
            },
            "property": {
                "strong": ["Mars", "Saturn", "Sun"],
                "moderate": ["Jupiter", "Venus"],
                "weak": ["Moon", "Mercury", "Rahu", "Ketu"]
            },
            "travel": {
                "strong": ["Moon", "Rahu", "Mercury"],
                "moderate": ["Jupiter", "Venus"],
                "weak": ["Sun", "Mars", "Saturn", "Ketu"]
            },
            "wealth": {
                "strong": ["Jupiter", "Venus", "Mercury"],
                "moderate": ["Sun", "Moon"],
                "weak": ["Mars", "Saturn", "Rahu", "Ketu"]
            }
        }
        
        strengths = event_planet_strengths.get(event_type, event_planet_strengths["career"])
        
        # Analyze ruling planets
        asc_strength = KPEventTimingService._get_planet_strength(
            ruling_planets["ascendant"]["star_lord"], strengths
        )
        moon_strength = KPEventTimingService._get_planet_strength(
            ruling_planets["moon"]["star_lord"], strengths
        )
        
        # Generate periods for next 2 years
        for month_offset in range(24):
            period_date = base_date + timedelta(days=30 * month_offset)
            period_strength = KPEventTimingService._calculate_period_strength(
                period_date, asc_strength, moon_strength, ruling_planets
            )
            
            period_info = {
                "start_date": period_date.strftime("%Y-%m-%d"),
                "end_date": (period_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                "strength": period_strength["strength"],
                "description": period_strength["description"]
            }
            
            if period_strength["strength"] >= 7:
                predictions["favorable_periods"].append(period_info)
            elif period_strength["strength"] <= 3:
                predictions["challenging_periods"].append(period_info)
            else:
                predictions["neutral_periods"].append(period_info)
        
        # Generate overall outlook
        favorable_count = len(predictions["favorable_periods"])
        challenging_count = len(predictions["challenging_periods"])
        
        if favorable_count > challenging_count:
            predictions["overall_outlook"] = "Generally favorable period ahead with good opportunities"
        elif challenging_count > favorable_count:
            predictions["overall_outlook"] = "Some challenges expected, patience and careful planning advised"
        else:
            predictions["overall_outlook"] = "Mixed period with both opportunities and challenges"
        
        return predictions
    
    @staticmethod
    def _get_planet_strength(planet, strengths):
        """Get strength rating for a planet"""
        if planet in strengths["strong"]:
            return 3
        elif planet in strengths["moderate"]:
            return 2
        else:
            return 1
    
    @staticmethod
    def _calculate_period_strength(date, asc_strength, moon_strength, ruling_planets):
        """Calculate strength for a specific time period"""
        # Base strength from ruling planets
        base_strength = (asc_strength + moon_strength) * 2
        
        # Add monthly variations based on date
        month_factor = (date.month % 12) + 1
        day_factor = (date.day % 7) + 1
        
        # Adjust based on day lord
        day_lords = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        current_day_lord = day_lords[date.weekday()]
        
        if current_day_lord == ruling_planets["day_lord"]:
            base_strength += 2
        
        # Add some randomness for variety (in real implementation, use actual transits)
        import random
        random.seed(date.toordinal())  # Consistent randomness based on date
        variation = random.randint(-2, 2)
        
        final_strength = max(1, min(10, base_strength + variation))
        
        descriptions = {
            (1, 3): "Challenging period, avoid major decisions",
            (4, 6): "Neutral period, steady progress possible",
            (7, 8): "Favorable period, good for new initiatives",
            (9, 10): "Highly favorable period, excellent for major decisions"
        }
        
        description = "Neutral period"
        for (min_val, max_val), desc in descriptions.items():
            if min_val <= final_strength <= max_val:
                description = desc
                break
        
        return {
            "strength": final_strength,
            "description": description
        }