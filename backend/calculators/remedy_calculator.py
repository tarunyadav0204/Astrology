"""Remedy calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator

class RemedyCalculator(BaseCalculator):
    """Calculate remedies for houses and planets"""
    
    def suggest_remedies(self, house_num, strength):
        """Suggest remedies - extracted from UniversalHouseAnalyzer"""
        house_lord = self.get_sign_lord(self.chart_data['houses'][house_num - 1]['sign'])
        
        if strength >= 70:
            return ["Continue positive practices", "Express gratitude for blessings"]
        
        remedies = []
        
        # Lord-specific remedies from UniversalHouseAnalyzer
        lord_remedies = {
            'Sun': ["Offer water to Sun at sunrise", "Donate wheat on Sundays", "Wear ruby (if suitable)"],
            'Moon': ["Offer milk to Shiva", "Donate white items on Mondays", "Wear pearl (if suitable)"],
            'Mars': ["Recite Hanuman Chalisa", "Donate red items on Tuesdays", "Wear red coral (if suitable)"],
            'Mercury': ["Donate green items on Wednesdays", "Feed green grass to cows", "Wear emerald (if suitable)"],
            'Jupiter': ["Donate yellow items on Thursdays", "Respect teachers and elders", "Wear yellow sapphire (if suitable)"],
            'Venus': ["Donate white items on Fridays", "Respect women", "Wear diamond (if suitable)"],
            'Saturn': ["Donate black items on Saturdays", "Serve the poor", "Wear blue sapphire (if suitable)"]
        }
        
        remedies.extend(lord_remedies.get(house_lord, ["Consult an astrologer for specific remedies"]))
        
        # House-specific remedies from UniversalHouseAnalyzer
        house_remedies = {
            1: ["Maintain good health habits", "Practice meditation"],
            2: ["Save money regularly", "Speak truthfully"],
            3: ["Maintain good relationships with siblings", "Develop communication skills"],
            4: ["Respect mother and elders", "Keep home clean and peaceful"],
            5: ["Spend time with children", "Engage in creative activities"],
            6: ["Maintain good health", "Serve others selflessly"],
            7: ["Respect spouse and partners", "Maintain harmony in relationships"],
            8: ["Practice spiritual disciplines", "Study occult sciences carefully"],
            9: ["Respect father and teachers", "Follow dharmic principles"],
            10: ["Work with dedication", "Maintain good reputation"],
            11: ["Help friends in need", "Work towards goals systematically"],
            12: ["Practice charity", "Engage in spiritual practices"]
        }
        
        remedies.extend(house_remedies.get(house_num, []))
        
        return remedies[:5]  # Return top 5 remedies