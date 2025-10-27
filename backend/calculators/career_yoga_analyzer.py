from .yoga_calculator import YogaCalculator
from .planet_analyzer import PlanetAnalyzer

class CareerYogaAnalyzer(YogaCalculator):
    """Career-focused yoga analyzer that filters and presents yogas for career context"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data=chart_data)
        self.planet_analyzer = PlanetAnalyzer(chart_data)
    
    def analyze_career_yogas(self):
        """Filter and analyze career-relevant yogas from base calculator"""
        # Get all yogas from base calculator
        all_yogas = self.calculate_all_yogas()
        career_yogas = []
        
        # Process Raj Yogas
        for yoga in all_yogas['raj_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Raj Yoga', 'High - Authority and leadership roles'))
        
        # Process Dhana Yogas
        for yoga in all_yogas['dhana_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Dhana Yoga', 'High - Income and wealth periods'))
        
        # Process Mahapurusha Yogas
        for yoga in all_yogas['mahapurusha_yogas']:
            career_impact = self._get_mahapurusha_career_impact(yoga['name'])
            career_yogas.append(self._format_career_yoga(yoga, 'Mahapurusha Yoga', 'Very High - Professional excellence', career_impact))
        
        # Process Neecha Bhanga Yogas
        for yoga in all_yogas['neecha_bhanga_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Professional Excellence Yoga', 'Medium - Recovery periods', 'Overcoming career obstacles'))
        
        # Process Gaja Kesari Yogas
        for yoga in all_yogas['gaja_kesari_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Professional Excellence Yoga', 'High - Recognition periods', 'Wisdom and respect in profession'))
        
        # Process Amala Yogas
        for yoga in all_yogas['amala_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Professional Excellence Yoga', 'Very High - Fame periods', 'Pure reputation and lasting fame'))
        
        # Process Viparita Raja Yogas
        for yoga in all_yogas['viparita_raja_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Career Power Yoga', 'Medium - Success through adversity', 'Success through challenges'))
        
        # Process Dharma Karma Yogas
        for yoga in all_yogas['dharma_karma_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Raj Yoga', 'High - Ethical leadership', 'Righteous success and dharmic career'))
        
        # Process Career Specific Yogas
        for yoga in all_yogas['career_specific_yogas']:
            career_yogas.append(self._format_career_yoga(yoga, 'Career Power Yoga', 'Very High - Direct career impact', self._get_career_specific_impact(yoga['name'])))
        
        # Sort by strength
        career_yogas.sort(key=lambda x: x['strength_score'], reverse=True)
        
        return {
            'total_yogas': len(career_yogas),
            'strong_yogas': len([y for y in career_yogas if y['strength_score'] >= 70]),
            'moderate_yogas': len([y for y in career_yogas if 50 <= y['strength_score'] < 70]),
            'weak_yogas': len([y for y in career_yogas if y['strength_score'] < 50]),
            'yogas': career_yogas[:12],
            'overall_yoga_strength': self._calculate_overall_yoga_strength(career_yogas),
            'career_yoga_summary': self._generate_career_yoga_summary(career_yogas)
        }
    
    def _format_career_yoga(self, yoga, yoga_type, timing_relevance, career_impact=None):
        """Format yoga for career presentation"""
        strength_score = self._calculate_yoga_strength(yoga)
        
        if not career_impact:
            career_impact = self._get_default_career_impact(yoga_type)
        
        formatted_yoga = {
            'name': yoga['name'],
            'type': yoga_type,
            'strength_score': strength_score,
            'strength_grade': self._get_strength_grade(strength_score),
            'career_impact': career_impact,
            'description': yoga['description'],
            'timing_relevance': timing_relevance
        }
        
        # Add yoga-specific fields
        if 'planets' in yoga:
            formatted_yoga['planets'] = yoga['planets']
        if 'planet' in yoga:
            formatted_yoga['planet'] = yoga['planet']
        if 'houses' in yoga:
            formatted_yoga['houses'] = yoga['houses']
        if 'house' in yoga:
            formatted_yoga['house'] = yoga['house']
        if 'classical_reference' in yoga:
            formatted_yoga['classical_reference'] = yoga['classical_reference']
        if 'sanskrit_verse' in yoga:
            formatted_yoga['sanskrit_verse'] = yoga['sanskrit_verse']
        
        return formatted_yoga
    
    def _calculate_yoga_strength(self, yoga):
        """Calculate strength based on participating planets and yoga formation"""
        planets = []
        if 'planets' in yoga:
            planets = yoga['planets']
        elif 'planet' in yoga:
            planets = [yoga['planet']]
        
        if not planets:
            return 50
        
        # Base yoga formation strength
        yoga_base_strength = self._get_yoga_base_strength(yoga['name'])
        
        # Average planet strength
        total_strength = 0
        planet_count = 0
        
        for planet in planets:
            if planet in self.chart_data.get('planets', {}):
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                planet_strength = planet_analysis['overall_assessment']['overall_strength_score']
                total_strength += planet_strength
                planet_count += 1
        
        if planet_count == 0:
            return yoga_base_strength
        
        avg_planet_strength = total_strength / planet_count
        
        # Combine yoga formation strength with planet strength (weighted)
        final_strength = (yoga_base_strength * 0.4) + (avg_planet_strength * 0.6)
        
        return min(100, max(0, round(final_strength, 1)))
    
    def _get_yoga_base_strength(self, yoga_name):
        """Get base strength for yoga formation regardless of planet strength"""
        base_strengths = {
            'Kendra-Trikona Raj Yoga': 65,  # BPHS Ch. 38, Phaladīpikā 4.1-4.7
            'Dhana Yoga': 60,  # BPHS Ch. 40, Phaladīpikā 6.1-6.5
            'Ruchaka Yoga': 75,  # BPHS Ch. 76 Pañcha Mahāpuruṣa Yogas
            'Bhadra Yoga': 75,   # BPHS Ch. 76 Pañcha Mahāpuruṣa Yogas
            'Hamsa Yoga': 75,    # BPHS Ch. 76 Pañcha Mahāpuruṣa Yogas
            'Malavya Yoga': 75,  # BPHS Ch. 76 Pañcha Mahāpuruṣa Yogas
            'Sasha Yoga': 75,    # BPHS Ch. 76 Pañcha Mahāpuruṣa Yogas
            'Neecha Bhanga Yoga': 55,  # BPHS Ch. 39, Phaladīpikā 6.31-6.33
            'Gaja Kesari Yoga': 70,  # BPHS Ch. 40 § 31, Phaladīpikā 6.26
            'Amala Yoga': 70,  # Phaladīpikā 6.37, Jātaka Pārijāta 16.62
            'Viparita Raja Yoga': 50,  # BPHS Ch. 40 § 56-58, Phaladīpikā 6.22
            'Dharma-Karma Yoga': 65,  # BPHS Ch. 38 § 64, Jātaka Pārijāta 16.40,
            'Daśama-pati Lagna Yoga': 70,  # Phaladīpikā Ch. 6 § 14
            'Bhāgya-Karma Yoga': 75,        # BPHS Ch. 14
            'Śani-Karma Yoga': 70          # Phaladīpikā 6.16, Hora Sara 10.2
        }
        return base_strengths.get(yoga_name, 50)
    
    def _get_career_specific_impact(self, yoga_name):
        """Get career impact for specific career yogas"""
        impacts = {
            'Daśama-pati Lagna Yoga': 'Strong personal drive and focus on career advancement',
            'Bhāgya-Karma Yoga': 'Fortune and luck strongly support professional success',
            'Śani-Karma Yoga': 'Disciplined approach leads to long-term career stability'
        }
        return impacts.get(yoga_name, 'Direct positive career influence')
    
    def _get_mahapurusha_career_impact(self, yoga_name):
        """Get career impact for Mahapurusha Yogas"""
        impacts = {
            'Ruchaka Yoga': 'Leadership in technical fields, military, sports, or engineering',
            'Bhadra Yoga': 'Excellence in communication, business, writing, or intellectual pursuits',
            'Hamsa Yoga': 'Success in teaching, counseling, spiritual guidance, or advisory roles',
            'Malavya Yoga': 'Achievement in arts, entertainment, luxury goods, or beauty industry',
            'Sasha Yoga': 'Long-term success through discipline, persistence, and systematic approach'
        }
        return impacts.get(yoga_name, 'Professional excellence and recognition')
    
    def _get_default_career_impact(self, yoga_type):
        """Get default career impact by yoga type"""
        impacts = {
            'Raj Yoga': 'Leadership positions, authority, and high status in career',
            'Dhana Yoga': 'Financial growth and wealth accumulation through career',
            'Mahapurusha Yoga': 'Professional excellence and recognition',
            'Professional Excellence Yoga': 'Enhanced professional capabilities and recognition',
            'Career Power Yoga': 'Unique career advantages and opportunities'
        }
        return impacts.get(yoga_type, 'Positive career influence')
    
    def _get_strength_grade(self, score):
        """Convert numerical score to grade"""
        if score >= 80:
            return 'Excellent'
        elif score >= 70:
            return 'Very Good'
        elif score >= 60:
            return 'Good'
        elif score >= 50:
            return 'Average'
        elif score >= 40:
            return 'Below Average'
        else:
            return 'Weak'
    
    def _calculate_overall_yoga_strength(self, career_yogas):
        """Calculate overall yoga strength for career"""
        if not career_yogas:
            return {
                'score': 0,
                'grade': 'No Yogas',
                'interpretation': 'No significant career yogas detected'
            }
        
        # Simple average of top yogas
        top_yogas = career_yogas[:5]  # Top 5 yogas
        if top_yogas:
            avg_score = sum(y['strength_score'] for y in top_yogas) / len(top_yogas)
        else:
            avg_score = 0
        
        return {
            'score': round(avg_score, 1),
            'grade': self._get_strength_grade(avg_score),
            'interpretation': self._interpret_overall_yoga_strength(avg_score, len(career_yogas))
        }
    
    def _interpret_overall_yoga_strength(self, score, yoga_count):
        """Interpret overall yoga strength"""
        if score >= 80:
            return f'Exceptional career yoga combinations ({yoga_count} yogas) - destined for high achievements'
        elif score >= 70:
            return f'Very strong career yogas ({yoga_count} yogas) - significant professional success likely'
        elif score >= 60:
            return f'Good career yoga support ({yoga_count} yogas) - steady professional growth expected'
        elif score >= 50:
            return f'Moderate yoga influence ({yoga_count} yogas) - career success through effort'
        elif score >= 40:
            return f'Limited yoga support ({yoga_count} yogas) - focus on strengthening weak areas'
        else:
            return f'Weak yoga combinations ({yoga_count} yogas) - career requires extra effort and remedies'
    
    def _generate_career_yoga_summary(self, career_yogas):
        """Generate summary of career yoga impact"""
        if not career_yogas:
            return {
                'primary_strength': 'No significant yogas',
                'key_benefits': [],
                'timing_focus': 'Focus on planetary strengthening',
                'recommendations': ['Strengthen weak planets through remedies', 'Focus on skill development']
            }
        
        strong_yogas = [y for y in career_yogas if y['strength_score'] >= 70]
        yoga_types = list(set([y['type'] for y in strong_yogas]))
        
        primary_strength = 'Mixed yoga combinations'
        if 'Mahapurusha Yoga' in yoga_types:
            primary_strength = 'Professional excellence through planetary strength'
        elif 'Raj Yoga' in yoga_types:
            primary_strength = 'Leadership and authority potential'
        elif 'Dhana Yoga' in yoga_types:
            primary_strength = 'Financial growth through career'
        
        key_benefits = [y['career_impact'] for y in strong_yogas[:3]]
        
        return {
            'primary_strength': primary_strength,
            'key_benefits': key_benefits,
            'timing_focus': 'Leverage strong yoga periods',
            'recommendations': [
                'Focus on areas indicated by strongest yogas',
                'Time career decisions during favorable periods'
            ]
        }