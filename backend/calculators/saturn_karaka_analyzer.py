from .planet_analyzer import PlanetAnalyzer

class SaturnKarakaAnalyzer:
    """Saturn Karma Karaka analysis for career"""
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planet_analyzer = PlanetAnalyzer(chart_data)
    
    def analyze_saturn_karaka(self):
        """Complete Saturn Karma Karaka analysis using PlanetAnalyzer"""
        saturn_analysis = self.planet_analyzer.analyze_planet('Saturn')
        
        return {
            'saturn_basic_info': saturn_analysis['basic_info'],
            'saturn_analysis': saturn_analysis,
            'karma_interpretation': self._get_karma_interpretation(saturn_analysis),
            'career_karma_insights': self._get_career_karma_insights(saturn_analysis)
        }
    
    def _get_karma_interpretation(self, saturn_analysis):
        """Get karma-specific interpretation of Saturn analysis"""
        house = saturn_analysis['house_position_analysis']['house_number']
        dignity = saturn_analysis['dignity_analysis']['dignity']
        
        karma_patterns = {
            1: "Self-discipline and personal responsibility shape career path",
            2: "Financial discipline and resource management are key career themes", 
            3: "Communication skills and networking affect career karma",
            4: "Home-based work or real estate may be karmic career paths",
            5: "Creative discipline and teaching fulfill career karma",
            6: "Service and overcoming obstacles are career karma themes",
            7: "Partnerships and public relations shape career destiny",
            8: "Research, transformation, or crisis management fulfills karma",
            9: "Teaching, law, or spiritual work aligns with career karma",
            10: "Authority, leadership, and public recognition are karmic goals",
            11: "Group work, networking, and gains through discipline",
            12: "Foreign work, spirituality, or behind-scenes roles fulfill karma"
        }
        
        karmic_strength = self._assess_karmic_strength(saturn_analysis)
        
        return {
            'primary_karma_pattern': karma_patterns.get(house, "General career karma"),
            'karmic_strength_level': karmic_strength['grade'],
            'karmic_strength_details': karmic_strength,
            'work_dharma': self._get_work_dharma(house, dignity)
        }
    
    def _get_career_karma_insights(self, saturn_analysis):
        """Get career-specific karma insights"""
        return {
            'career_timing': {
                'maturation_age': "Career stabilizes after age 36 (Saturn maturation)",
                'peak_periods': "Ages 36-42 and 54-60 are strongest career periods", 
                'advice': "Build career foundation slowly and steadily for lasting success"
            },
            'karmic_lessons': self._get_karmic_lessons(saturn_analysis),
            'remedial_guidance': self._get_remedial_guidance(saturn_analysis)
        }
    
    def _assess_karmic_strength(self, saturn_analysis):
        """Assess Saturn's karmic strength for career"""
        dignity = saturn_analysis['dignity_analysis']['dignity']
        shadbala = saturn_analysis['strength_analysis']['shadbala_rupas']
        house_types = saturn_analysis['house_position_analysis']['house_types']
        
        strength_score = 0
        
        # Dignity assessment
        if dignity == 'exalted':
            strength_score += 30
            dignity_effect = "Excellent karmic strength - disciplined approach to career"
        elif dignity == 'own_sign':
            strength_score += 25
            dignity_effect = "Strong karmic foundation - natural work discipline"
        elif dignity == 'debilitated':
            strength_score -= 20
            dignity_effect = "Karmic challenges - need to develop patience and discipline"
        else:
            strength_score += 10
            dignity_effect = "Moderate karmic influence on career"
        
        # Shadbala contribution
        strength_score += min(shadbala * 8, 25)
        
        # House position
        if 'Kendra' in house_types:
            strength_score += 15
        if 'Trikona' in house_types:
            strength_score += 20
        if 'Dusthana' in house_types:
            strength_score -= 10
        
        strength_score = max(0, min(100, strength_score))
        
        return {
            'score': strength_score,
            'grade': self._get_karma_grade(strength_score),
            'dignity_effect': dignity_effect,
            'interpretation': self._interpret_karma_strength(strength_score)
        }
    
    def _analyze_career_karma(self, saturn_analysis):
        """Analyze career karma patterns"""
        house = saturn_analysis['house_position_analysis']['house_number']
        dignity = saturn_analysis['dignity_analysis']['dignity']
        
        karma_patterns = {
            1: "Self-discipline and personal responsibility shape career path",
            2: "Financial discipline and resource management are key career themes",
            3: "Communication skills and sibling relationships affect career karma",
            4: "Home-based work or real estate may be karmic career paths",
            5: "Creative discipline and teaching may fulfill career karma",
            6: "Service, health, or overcoming obstacles are career karma themes",
            7: "Partnerships and public relations shape career destiny",
            8: "Research, transformation, or dealing with crises fulfills karma",
            9: "Teaching, law, or spiritual work aligns with career karma",
            10: "Authority, leadership, and public recognition are karmic goals",
            11: "Group work, networking, and gains through discipline",
            12: "Foreign work, spirituality, or behind-scenes roles fulfill karma"
        }
        
        return {
            'primary_pattern': karma_patterns.get(house, "General career karma"),
            'karmic_field': self._get_karmic_career_field(house, dignity),
            'life_purpose': self._get_career_life_purpose(house)
        }
    
    def _analyze_work_ethics(self, saturn_analysis):
        """Analyze work ethics and discipline"""
        dignity = saturn_analysis['dignity_analysis']['dignity']
        aspects = saturn_analysis['aspects_received']['aspects']
        
        ethics_profile = {
            'discipline_level': self._assess_discipline_level(dignity, aspects),
            'work_approach': self._get_work_approach(dignity),
            'leadership_style': self._get_leadership_style(dignity, aspects),
            'time_management': self._assess_time_management(dignity)
        }
        
        return ethics_profile
    
    def _identify_career_obstacles(self, saturn_analysis):
        """Identify Saturn-related career obstacles"""
        obstacles = []
        
        dignity = saturn_analysis['dignity_analysis']['dignity']
        combustion = saturn_analysis['combustion_status']['is_combust']
        malefic_aspects = saturn_analysis['aspects_received']['malefic_aspects']
        
        if dignity == 'debilitated':
            obstacles.append({
                'type': 'Discipline Challenges',
                'description': 'Difficulty maintaining consistent work habits',
                'remedy': 'Develop structured daily routines and patience'
            })
        
        if combustion:
            obstacles.append({
                'type': 'Authority Conflicts',
                'description': 'Ego clashes with superiors or authority figures',
                'remedy': 'Practice humility and respect for hierarchy'
            })
        
        if len(malefic_aspects) > 2:
            obstacles.append({
                'type': 'External Pressures',
                'description': 'Multiple challenging influences affecting career',
                'remedy': 'Focus on long-term goals despite short-term setbacks'
            })
        
        return obstacles
    
    def _get_work_dharma(self, house, dignity):
        """Get work dharma based on Saturn's position"""
        dharma_paths = {
            1: "Lead by example through self-discipline",
            2: "Build financial security through honest work", 
            3: "Communicate wisdom gained through experience",
            4: "Create stable foundations for family and community",
            5: "Teach discipline through creative expression",
            6: "Serve others while overcoming personal limitations",
            7: "Build lasting partnerships and public trust",
            8: "Transform challenges into wisdom for others",
            9: "Share knowledge and guide others ethically",
            10: "Accept responsibility and lead with integrity",
            11: "Work for collective progress and social good",
            12: "Serve higher purposes beyond personal gain"
        }
        return dharma_paths.get(house, "Fulfill dharma through disciplined work")
    
    def _get_karmic_lessons(self, saturn_analysis):
        """Get karmic lessons for career growth"""
        house = saturn_analysis['house_position_analysis']['house_number']
        dignity = saturn_analysis['dignity_analysis']['dignity']
        
        house_lessons = {
            1: "Learn self-reliance and personal accountability",
            2: "Master financial responsibility and resource conservation",
            3: "Develop patience in communication and networking", 
            4: "Build emotional stability and secure foundations",
            5: "Balance creativity with practical discipline",
            6: "Serve others while maintaining personal boundaries",
            7: "Learn compromise and commitment in partnerships",
            8: "Embrace transformation and face fears courageously",
            9: "Develop wisdom through experience and teaching",
            10: "Accept responsibility and lead with integrity",
            11: "Work for collective good while achieving personal goals",
            12: "Release ego and serve higher purposes"
        }
        
        lessons = [house_lessons.get(house, "General life discipline")]
        
        if dignity == 'debilitated':
            lessons.append("Learn patience and persistence through career challenges")
        elif dignity == 'exalted':
            lessons.append("Use natural discipline to help others achieve their goals")
        
        return lessons
    
    def _analyze_career_timing(self, saturn_analysis):
        """Analyze Saturn's timing influence on career"""
        return {
            'maturation_age': "Career stabilizes after age 36 (Saturn maturation)",
            'peak_periods': "Ages 36-42 and 54-60 are strongest career periods",
            'challenging_periods': "Saturn transits and Sade Sati may bring career tests",
            'advice': "Build career foundation slowly and steadily for lasting success"
        }
    
    def _get_remedial_guidance(self, saturn_analysis):
        """Get Saturn remedial guidance for career"""
        dignity = saturn_analysis['dignity_analysis']['dignity']
        strength_score = saturn_analysis['overall_assessment']['overall_strength_score']
        
        remedies = []
        
        if strength_score < 50:
            remedies.extend([
                "Worship Lord Hanuman or Shani Dev on Saturdays",
                "Donate black sesame seeds, iron, or blue cloth",
                "Practice discipline in daily routine and work habits"
            ])
        
        if dignity == 'debilitated':
            remedies.extend([
                "Serve elderly people and laborers",
                "Practice patience and avoid shortcuts in career",
                "Strengthen Saturn through consistent hard work"
            ])
        
        remedies.extend([
            "Maintain honesty and integrity in all professional dealings",
            "Accept responsibility for mistakes and learn from them",
            "Build career through sustained effort rather than quick gains"
        ])
        
        return remedies
    
    # Helper methods
    def _get_nakshatra(self, longitude):
        """Get nakshatra from longitude"""
        nakshatra_num = int(longitude / 13.333333) + 1
        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        return nakshatra_names[min(nakshatra_num - 1, 26)]
    
    def _get_karma_grade(self, score):
        """Get karma strength grade"""
        if score >= 80:
            return 'Excellent'
        elif score >= 65:
            return 'Very Good'
        elif score >= 50:
            return 'Good'
        elif score >= 35:
            return 'Average'
        else:
            return 'Needs Development'
    
    def _interpret_karma_strength(self, score):
        """Interpret karma strength score"""
        if score >= 70:
            return "Strong karmic foundation supports steady career growth"
        elif score >= 50:
            return "Moderate karmic strength requires consistent effort"
        else:
            return "Karmic challenges need patience and disciplined approach"
    
    def _get_karmic_career_field(self, house, dignity):
        """Get karmic career field based on house and dignity"""
        fields = {
            1: "Leadership, entrepreneurship, self-employment",
            2: "Finance, banking, resource management",
            3: "Communication, media, transportation",
            4: "Real estate, agriculture, home-based business",
            5: "Education, entertainment, creative fields",
            6: "Healthcare, service, legal profession",
            7: "Business partnerships, public relations",
            8: "Research, investigation, transformation industries",
            9: "Teaching, law, publishing, spirituality",
            10: "Government, administration, corporate leadership",
            11: "Technology, networking, social organizations",
            12: "Foreign trade, spirituality, charitable work"
        }
        return fields.get(house, "General professional work")
    
    def _get_career_life_purpose(self, house):
        """Get career life purpose based on Saturn's house"""
        purposes = {
            1: "Develop self-discipline and lead by example",
            2: "Build financial security through honest work",
            3: "Communicate wisdom gained through experience",
            4: "Create stable foundations for others",
            5: "Teach discipline through creative expression",
            6: "Serve others while overcoming personal limitations",
            7: "Build lasting partnerships and public trust",
            8: "Transform challenges into wisdom for others",
            9: "Share knowledge and guide others ethically",
            10: "Accept responsibility and lead with integrity",
            11: "Work for collective progress and social good",
            12: "Serve higher purposes beyond personal gain"
        }
        return purposes.get(house, "Fulfill dharma through disciplined work")
    
    def _assess_discipline_level(self, dignity, aspects):
        """Assess discipline level"""
        if dignity in ['exalted', 'own_sign']:
            return "High - Natural self-discipline and work ethic"
        elif dignity == 'debilitated':
            return "Developing - Needs to cultivate consistent habits"
        else:
            return "Moderate - Can develop strong discipline with effort"
    
    def _get_work_approach(self, dignity):
        """Get work approach based on dignity"""
        approaches = {
            'exalted': "Methodical, patient, and highly organized",
            'own_sign': "Structured, reliable, and systematic",
            'debilitated': "May struggle with consistency, needs external structure",
            'neutral': "Balanced approach with room for improvement"
        }
        return approaches.get(dignity, "Practical and steady approach")
    
    def _get_leadership_style(self, dignity, aspects):
        """Get leadership style"""
        if dignity in ['exalted', 'own_sign']:
            return "Authoritative but fair, leads by example"
        elif dignity == 'debilitated':
            return "May be too strict or too lenient, needs balance"
        else:
            return "Develops leadership through experience and patience"
    
    def _assess_time_management(self, dignity):
        """Assess time management skills"""
        if dignity in ['exalted', 'own_sign']:
            return "Excellent - Natural ability to plan and execute long-term"
        elif dignity == 'debilitated':
            return "Challenging - May procrastinate or rush, needs structure"
        else:
            return "Good - Can develop excellent time management with practice"