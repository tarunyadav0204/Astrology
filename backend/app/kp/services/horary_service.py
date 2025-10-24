from datetime import datetime
import random
from ..utils.kp_calculations import KPCalculations
from ..config.kp_constants import EVENT_HOUSES

class KPHoraryService:
    @staticmethod
    def analyze_horary_question(question_number, question_text, query_time=None):
        """Analyze horary question using KP principles"""
        if query_time is None:
            query_time = datetime.now()
        
        # Use question number to determine ruling planets
        ruling_planets = KPHoraryService._get_ruling_planets_from_number(question_number)
        
        # Categorize question
        question_category = KPHoraryService._categorize_question(question_text)
        
        # Get relevant houses for the question
        relevant_houses = EVENT_HOUSES.get(question_category, [1, 10, 11])
        
        # Analyze using KP principles
        analysis = KPHoraryService._analyze_kp_horary(ruling_planets, relevant_houses, question_number)
        
        return {
            "question_number": question_number,
            "question_text": question_text,
            "query_time": query_time.isoformat(),
            "ruling_planets": ruling_planets,
            "question_category": question_category,
            "relevant_houses": relevant_houses,
            "answer": analysis["result"],
            "confidence": analysis["confidence"],
            "explanation": analysis["reasoning"],
            "timing": analysis["timing"]
        }
    
    @staticmethod
    def _get_ruling_planets_from_number(number):
        """Extract ruling planets from question number using KP method"""
        # Convert number to individual digits and map to planets
        planet_mapping = {
            1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
            6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars", 0: "Ketu"
        }
        
        digits = [int(d) for d in str(number)]
        ruling_planets = [planet_mapping[digit] for digit in digits]
        
        return {
            "primary": ruling_planets[0] if ruling_planets else "Sun",
            "secondary": ruling_planets[1] if len(ruling_planets) > 1 else ruling_planets[0],
            "all_digits": ruling_planets
        }
    
    @staticmethod
    def _categorize_question(question_text):
        """Categorize question based on keywords"""
        question_lower = question_text.lower()
        
        keywords = {
            "marriage": ["marriage", "marry", "wedding", "spouse", "partner", "relationship"],
            "career": ["job", "career", "work", "business", "promotion", "employment"],
            "health": ["health", "illness", "disease", "medical", "doctor", "treatment"],
            "education": ["education", "study", "exam", "degree", "school", "college"],
            "children": ["child", "children", "baby", "pregnancy", "son", "daughter"],
            "property": ["house", "property", "land", "real estate", "home", "building"],
            "travel": ["travel", "journey", "trip", "abroad", "foreign", "visa"],
            "litigation": ["court", "legal", "case", "lawsuit", "dispute", "litigation"],
            "spirituality": ["spiritual", "meditation", "god", "temple", "religious"],
            "wealth": ["money", "wealth", "finance", "income", "profit", "loss"]
        }
        
        for category, words in keywords.items():
            if any(word in question_lower for word in words):
                return category
        
        return "general"
    
    @staticmethod
    def _analyze_kp_horary(ruling_planets, relevant_houses, question_number):
        """Perform KP horary analysis"""
        primary_planet = ruling_planets["primary"]
        secondary_planet = ruling_planets["secondary"]
        
        # Determine strength based on ruling planets
        strong_planets = ["Sun", "Jupiter", "Venus", "Mercury"]
        weak_planets = ["Saturn", "Rahu", "Ketu"]
        
        primary_strength = "strong" if primary_planet in strong_planets else "weak" if primary_planet in weak_planets else "moderate"
        secondary_strength = "strong" if secondary_planet in strong_planets else "weak" if secondary_planet in weak_planets else "moderate"
        
        # Calculate overall strength
        strength_score = 0
        if primary_strength == "strong":
            strength_score += 3
        elif primary_strength == "moderate":
            strength_score += 2
        else:
            strength_score += 1
            
        if secondary_strength == "strong":
            strength_score += 2
        elif secondary_strength == "moderate":
            strength_score += 1
        
        # Determine timing based on question number
        timing_factor = question_number % 12 + 1
        timing_periods = {
            1: "immediate (within days)",
            2: "very soon (within weeks)",
            3: "soon (1-3 months)",
            4: "moderate delay (3-6 months)",
            5: "some delay (6-12 months)",
            6: "delayed (1-2 years)",
            7: "significant delay (2+ years)",
            8: "uncertain timing",
            9: "quick results",
            10: "steady progress",
            11: "favorable timing",
            12: "completion cycle"
        }
        
        timing = timing_periods.get(timing_factor, "uncertain")
        
        # Generate conclusion
        if strength_score >= 4:
            result = "Yes, favorable"
            confidence = "High"
        elif strength_score >= 3:
            result = "Likely positive"
            confidence = "Moderate"
        elif strength_score >= 2:
            result = "Mixed results"
            confidence = "Low"
        else:
            result = "Challenging"
            confidence = "Low"
        
        conclusion = f"{result}. Timing: {timing}. Confidence: {confidence}"
        
        return {
            "primary_planet_strength": primary_strength,
            "secondary_planet_strength": secondary_strength,
            "overall_strength": strength_score,
            "timing": timing,
            "result": result,
            "confidence": confidence,
            "conclusion": conclusion,
            "reasoning": f"Primary ruling planet {primary_planet} is {primary_strength}, secondary planet {secondary_planet} is {secondary_strength}. Combined strength suggests {result.lower()} outcome with {timing}."
        }