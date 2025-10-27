from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from .tenth_house_analyzer import TenthHouseAnalyzer
from calculators.tenth_house_analyzer import TenthHouseAnalyzer as TenthHouseAnalyzerCalc

router = APIRouter()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str
    place: str = ""
    gender: str = ""

@router.post("/career/tenth-lord-analysis")
async def get_tenth_lord_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get comprehensive 10th house lord analysis using PlanetAnalyzer"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Get 10th house sign and lord
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        tenth_house_sign = (ascendant_sign + 9) % 12
        tenth_lord = _get_house_lord(tenth_house_sign)
        
        # Use PlanetAnalyzer for comprehensive analysis
        from calculators.planet_analyzer import PlanetAnalyzer
        planet_analyzer = PlanetAnalyzer(chart_data)
        
        # Get complete 10th lord analysis
        lord_analysis = planet_analyzer.analyze_planet(tenth_lord)
        
        result = {
            'tenth_house_info': {
                'house_number': 10,
                'house_sign': tenth_house_sign,
                'house_sign_name': _get_sign_name(tenth_house_sign),
                'house_lord': tenth_lord
            },
            'lord_analysis': lord_analysis
        }
        
        return result
        
    except Exception as e:
        import traceback
        print(f"10th lord analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"10th lord analysis failed: {str(e)}")

@router.post("/career/comprehensive-analysis")
async def get_comprehensive_career_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get complete career analysis using all calculators"""
    try:
        birth_data = BirthData(**request['birth_data'])
        print(f"Processing career analysis for: {birth_data.name}")
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        print(f"Chart data calculated successfully")
        
        # Initialize comprehensive calculator
        from calculators.comprehensive_calculator import ComprehensiveCalculator
        calc = ComprehensiveCalculator(birth_data, chart_data)
        print(f"Comprehensive calculator initialized")
        
        # Get career-focused analysis
        career_analysis = calc.get_career_focused_analysis()
        print(f"Career analysis keys: {list(career_analysis.keys())}")
        
        # Get additional career-specific data
        shadbala_data = calc.calculate_shadbala()
        current_dashas = calc.calculate_current_dashas()
        house_analysis = calc.analyze_single_house(10) if calc.chart_data else None
        print(f"Additional data calculated")
        
        # Structure comprehensive career report
        result = {
            'career_overview': _create_career_overview(career_analysis, shadbala_data),
            'professional_strengths': _analyze_professional_strengths(career_analysis, shadbala_data),
            'suitable_professions': _get_profession_recommendations(career_analysis),
            'career_timing': _analyze_career_timing(current_dashas, chart_data),
            'growth_strategy': _create_growth_strategy(career_analysis, house_analysis)
        }
        
        return result
    except Exception as e:
        import traceback
        print(f"Career analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Career analysis failed: {str(e)}")

@router.post("/career/tenth-house-analysis")
async def get_tenth_house_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze 10th house using modular calculators"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Use existing calculate_chart function
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use comprehensive calculators including Yogi and Badhaka points
        from calculators.house_strength_calculator import HouseStrengthCalculator
        from calculators.house_relationship_calculator import HouseRelationshipCalculator
        from calculators.timing_calculator import TimingCalculator
        from calculators.remedy_calculator import RemedyCalculator
        from calculators.strength_calculator import StrengthCalculator
        from calculators.aspect_calculator import AspectCalculator
        from calculators.yogi_calculator import YogiCalculator
        from calculators.badhaka_calculator import BadhakaCalculator
        
        house_strength_calc = HouseStrengthCalculator(chart_data)
        house_rel_calc = HouseRelationshipCalculator(chart_data)
        timing_calc = TimingCalculator(chart_data)
        remedy_calc = RemedyCalculator(chart_data)
        strength_calc = StrengthCalculator(chart_data)
        aspect_calc = AspectCalculator(chart_data)
        yogi_calc = YogiCalculator(chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        
        # Get ascendant for calculations
        ascendant_sign = int(chart_data['ascendant'] / 30)
        
        # Calculate Yogi points
        yogi_data = yogi_calc.calculate_yogi_points(birth_data)
        yogi_impact = yogi_calc.analyze_yogi_impact_on_house(10, yogi_data)
        
        # Calculate Badhaka impact on 10th house
        badhaka_impact = badhaka_calc.analyze_badhaka_impact_on_house(10, ascendant_sign)
        badhaka_summary = badhaka_calc.get_chart_badhaka_summary(ascendant_sign)
        
        # Calculate comprehensive 10th house analysis
        house_strength = house_strength_calc.calculate_house_strength(10)
        lord_analysis = house_rel_calc.analyze_house_lord(10)
        timing_indicators = timing_calc.get_timing_indicators(10)
        
        # Enhanced strength calculation with Yogi and Badhaka impact
        yogi_adjustment = (yogi_impact['total_impact'] - 50) * 0.3
        badhaka_adjustment = -badhaka_impact['impact_score'] * 0.2 if badhaka_impact['has_impact'] else 0
        
        enhanced_strength = house_strength['total_strength'] + yogi_adjustment + badhaka_adjustment
        enhanced_strength = max(0, min(100, enhanced_strength))
        
        remedies = remedy_calc.suggest_remedies(10, enhanced_strength)
        
        # Get basic data
        tenth_house_sign = (ascendant_sign + 9) % 12
        planets_in_tenth = strength_calc.get_planets_in_house(10)
        aspecting_planets = aspect_calc.get_aspecting_planets(10)
        
        result = {
            'house_sign': strength_calc.get_sign_name(tenth_house_sign),
            'house_lord': strength_calc.get_sign_lord(tenth_house_sign),
            'strength': _get_enhanced_grade(enhanced_strength),
            'strength_details': {
                **house_strength,
                'enhanced_strength': round(enhanced_strength, 2),
                'yogi_impact': yogi_impact['total_impact'],
                'badhaka_impact': badhaka_impact['impact_score']
            },
            'lord_analysis': lord_analysis,
            'planets_in_house': [{
                'name': planet,
                'effect': _get_career_effect(planet)
            } for planet in planets_in_tenth],
            'aspects': [{
                'planet': planet,
                'effect': _get_aspect_effect(planet)
            } for planet in aspecting_planets],
            'yogi_analysis': {
                'yogi_points': yogi_data,
                'career_impact': yogi_impact,
                'interpretation': _get_yogi_career_interpretation(yogi_impact, yogi_data)
            },
            'badhaka_analysis': {
                'career_impact': badhaka_impact,
                'chart_summary': badhaka_summary,
                'interpretation': _get_badhaka_career_interpretation(badhaka_impact)
            },
            'timing_indicators': timing_indicators,
            'remedies': remedies
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Career analysis failed: {str(e)}")

@router.post("/career/tenth-house-comprehensive")
async def get_tenth_house_comprehensive(request: dict, current_user = Depends(get_current_user)):
    """Get comprehensive 10th house analysis using TenthHouseAnalyzer"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer for comprehensive analysis
        analyzer = TenthHouseAnalyzerCalc(chart_data, birth_data.dict())
        analysis = analyzer.analyze_tenth_house()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"10th house comprehensive analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"10th house analysis failed: {str(e)}")

@router.post("/career/d10-analysis")
async def get_d10_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get D10 (Dasamsa) chart analysis for career"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use D10Analyzer for Dasamsa analysis
        from calculators.d10_analyzer import D10Analyzer
        analyzer = D10Analyzer(chart_data)
        analysis = analyzer.analyze_d10_chart()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"D10 analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"D10 analysis failed: {str(e)}")

@router.post("/career/saturn-karaka-analysis")
async def get_saturn_karaka_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get Saturn Karma Karaka analysis for career"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use SaturnKarakaAnalyzer
        from calculators.saturn_karaka_analyzer import SaturnKarakaAnalyzer
        analyzer = SaturnKarakaAnalyzer(chart_data)
        analysis = analyzer.analyze_saturn_karaka()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"Saturn Karaka analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Saturn Karaka analysis failed: {str(e)}")

def _get_career_effect(planet):
    """Career effects based on real Vedic principles"""
    effects = {
        'Sun': 'Leadership roles, government positions, authority-based careers',
        'Moon': 'Public relations, healthcare, hospitality, nurturing professions',
        'Mars': 'Engineering, military, sports, real estate, surgery',
        'Mercury': 'Business, communication, writing, IT, media, trading',
        'Jupiter': 'Teaching, law, finance, spirituality, consulting, advisory roles',
        'Venus': 'Arts, entertainment, beauty, luxury goods, fashion, creativity',
        'Saturn': 'Service sector, manufacturing, hard work, discipline-based careers'
    }
    return effects.get(planet, 'General career influence')

def _get_aspect_effect(planet):
    """Aspect effects on career based on Vedic principles"""
    effects = {
        'Jupiter': 'Positive influence on career growth and opportunities',
        'Venus': 'Creative and harmonious career environment',
        'Moon': 'Emotional influence on career, public recognition',
        'Sun': 'Authority and leadership in career',
        'Mercury': 'Communication and intellectual skills in career',
        'Mars': 'Drive and ambition, but potential conflicts',
        'Saturn': 'Discipline and hard work, delays but steady progress'
    }
    return effects.get(planet, 'Mixed influence on career')

def _get_enhanced_grade(strength):
    """Get enhanced strength grade including Yogi impact"""
    if strength >= 90:
        return 'A+'
    elif strength >= 80:
        return 'A'
    elif strength >= 70:
        return 'B+'
    elif strength >= 60:
        return 'B'
    elif strength >= 50:
        return 'C+'
    elif strength >= 40:
        return 'C'
    elif strength >= 30:
        return 'D'
    else:
        return 'F'

def _get_yogi_career_interpretation(yogi_impact, yogi_data):
    """Interpret Yogi impact on career"""
    interpretation = []
    
    if yogi_impact['yogi_impact'] > 60:
        interpretation.append(f"Yogi lord {yogi_impact['yogi_lord']} strongly supports career success")
    
    if yogi_impact['avayogi_impact'] > 60:
        interpretation.append(f"Avayogi lord {yogi_impact['avayogi_lord']} may create career obstacles")
    
    if yogi_impact['dagdha_impact'] > 60:
        interpretation.append(f"Dagdha lord {yogi_impact['dagdha_lord']} requires careful handling for career")
    
    # Tithi Shunya impact
    tithi_shunya_lord = yogi_data['tithi_shunya_rashi']['lord']
    interpretation.append(f"Tithi Shunya lord {tithi_shunya_lord} may affect career satisfaction")
    
    if yogi_impact['total_impact'] > 70:
        interpretation.append("Overall Yogi influence is highly favorable for career")
    elif yogi_impact['total_impact'] < 40:
        interpretation.append("Yogi influence suggests need for remedial measures in career")
    else:
        interpretation.append("Yogi influence is moderate on career matters")
    
    return interpretation

def _create_career_overview(career_analysis, shadbala_data):
    """Create career overview summary"""
    try:
        prof_analysis = career_analysis['professional_analysis']
        tenth_house = prof_analysis['tenth_house_analysis']
        ak_amk = prof_analysis['atmakaraka_amatyakaraka_analysis']
        
        # Calculate overall career strength
        career_strength = _calculate_overall_career_strength(prof_analysis, shadbala_data)
        
        return {
            'overall_strength': career_strength,
            'primary_career_planet': ak_amk['atmakaraka']['planet'],
            'secondary_career_planet': ak_amk['amatyakaraka']['planet'],
            'tenth_house_strength': tenth_house['house_strength_grade'],
            'key_insights': _generate_key_insights(prof_analysis, career_strength),
            'quick_recommendations': _get_quick_recommendations(prof_analysis)
        }
    except Exception as e:
        print(f"Error in _create_career_overview: {str(e)}")
        return {
            'overall_strength': {'score': 50, 'grade': 'Average', 'description': 'Analysis in progress'},
            'primary_career_planet': 'Sun',
            'secondary_career_planet': 'Mercury',
            'tenth_house_strength': 'Average',
            'key_insights': ['Career analysis in progress'],
            'quick_recommendations': ['Please wait for complete analysis']
        }

def _analyze_professional_strengths(career_analysis, shadbala_data):
    """Analyze professional strengths using real planetary data"""
    try:
        planetary_strengths = career_analysis['professional_analysis']['planetary_career_strengths']
        
        # Sort planets by career suitability
        sorted_strengths = sorted(
            planetary_strengths.items(),
            key=lambda x: x[1]['shadbala_rupas'] * x[1]['strength_multiplier'],
            reverse=True
        )
        
        return {
            'top_career_planets': sorted_strengths[:3],
            'strength_analysis': planetary_strengths,
            'skill_recommendations': _get_skill_recommendations(sorted_strengths)
        }
    except Exception as e:
        print(f"Error in _analyze_professional_strengths: {str(e)}")
        return {
            'top_career_planets': [('Sun', {'shadbala_rupas': 5.0, 'career_suitability': 'Good'})],
            'strength_analysis': {},
            'skill_recommendations': []
        }

def _get_profession_recommendations(career_analysis):
    """Get specific profession recommendations"""
    try:
        recommendations = career_analysis['professional_analysis']['profession_recommendations']
        ak_amk = career_analysis['professional_analysis']['atmakaraka_amatyakaraka_analysis']
        
        return {
            'primary_recommendations': recommendations[:3] if recommendations else [],
            'soul_calling': ak_amk.get('career_focus', 'General professional work'),
            'detailed_fields': _expand_profession_details(recommendations)
        }
    except Exception as e:
        print(f"Error in _get_profession_recommendations: {str(e)}")
        return {
            'primary_recommendations': [],
            'soul_calling': 'Analysis in progress',
            'detailed_fields': []
        }

def _analyze_career_timing(current_dashas, chart_data):
    """Analyze career timing using dasha periods"""
    if not current_dashas:
        return {'message': 'Dasha calculation unavailable'}
    
    return {
        'current_period': current_dashas.get('current_mahadasha', {}),
        'favorable_periods': _identify_favorable_periods(current_dashas),
        'timing_recommendations': _get_timing_recommendations(current_dashas)
    }

def _create_growth_strategy(career_analysis, house_analysis):
    """Create growth strategy with obstacles and remedies"""
    try:
        obstacles = career_analysis['professional_analysis']['career_obstacles']
        yogas = career_analysis['professional_analysis']['professional_yogas']
        
        return {
            'career_obstacles': obstacles,
            'favorable_yogas': yogas,
            'action_plan': _create_action_plan(obstacles, yogas),
            'remedial_measures': _get_remedial_measures(obstacles)
        }
    except Exception as e:
        print(f"Error in _create_growth_strategy: {str(e)}")
        return {
            'career_obstacles': [],
            'favorable_yogas': [],
            'action_plan': ['Focus on strengthening career significators'],
            'remedial_measures': ['General career strengthening recommended']
        }

def _calculate_overall_career_strength(prof_analysis, shadbala_data):
    """Calculate overall career strength score"""
    tenth_house = prof_analysis['tenth_house_analysis']
    ak_amk = prof_analysis['atmakaraka_amatyakaraka_analysis']
    
    # Base strength from 10th house
    base_strength = {
        'Excellent': 90, 'Good': 75, 'Average': 60, 'Weak': 40
    }.get(tenth_house['house_strength_grade'], 50)
    
    # AK-AMK combination strength
    ak_amk_strength = ak_amk.get('combination_strength', 0) * 2
    
    # Professional yogas bonus
    yoga_bonus = len(prof_analysis['professional_yogas']) * 5
    
    total_strength = min(100, base_strength + ak_amk_strength + yoga_bonus)
    
    if total_strength >= 85:
        return {'score': total_strength, 'grade': 'Excellent', 'description': 'Outstanding career potential'}
    elif total_strength >= 70:
        return {'score': total_strength, 'grade': 'Very Good', 'description': 'Strong career prospects'}
    elif total_strength >= 55:
        return {'score': total_strength, 'grade': 'Good', 'description': 'Favorable career indicators'}
    else:
        return {'score': total_strength, 'grade': 'Moderate', 'description': 'Requires focused effort'}

def _generate_key_insights(prof_analysis, career_strength):
    """Generate key career insights"""
    insights = []
    
    # Strength-based insight
    if career_strength['score'] >= 80:
        insights.append("You have exceptional career potential with strong planetary support")
    elif career_strength['score'] >= 60:
        insights.append("Your career prospects are favorable with good planetary backing")
    else:
        insights.append("Focus on strengthening career significators for better prospects")
    
    # 10th house insight
    tenth_house = prof_analysis['tenth_house_analysis']
    if tenth_house['planets_in_house']:
        strongest_planet = max(tenth_house['planets_in_house'], key=lambda p: p['shadbala_rupas'])
        insights.append(f"{strongest_planet['planet']} in 10th house indicates {strongest_planet['classical_profession'].lower()}")
    
    # Yoga insight
    yogas = prof_analysis['professional_yogas']
    if yogas:
        insights.append(f"You have {len(yogas)} career yoga(s) supporting professional success")
    
    return insights

def _get_quick_recommendations(prof_analysis):
    """Get quick actionable recommendations"""
    recommendations = prof_analysis['profession_recommendations']
    if not recommendations:
        return ["Focus on strengthening career significators"]
    
    top_rec = recommendations[0]
    return [
        f"Primary focus: {top_rec['profession_category']}",
        f"Leverage {top_rec['planet']} energy for career growth",
        "Consider timing career moves during favorable dasha periods"
    ]

def _get_skill_recommendations(sorted_strengths):
    """Get skill development recommendations"""
    skills = []
    for planet, data in sorted_strengths[:3]:
        if data['career_suitability'] in ['Excellent', 'Good']:
            planet_skills = {
                'Sun': 'Leadership, management, public speaking',
                'Moon': 'Emotional intelligence, public relations, counseling',
                'Mars': 'Technical skills, project management, competitive abilities',
                'Mercury': 'Communication, analytical thinking, technology',
                'Jupiter': 'Teaching, advisory skills, strategic thinking',
                'Venus': 'Creative abilities, aesthetic sense, relationship building',
                'Saturn': 'Discipline, systematic approach, long-term planning'
            }
            skills.append({
                'planet': planet,
                'skills': planet_skills.get(planet, 'General professional skills'),
                'strength': data['career_suitability']
            })
    return skills

def _expand_profession_details(recommendations):
    """Expand profession recommendations with specific fields"""
    detailed_fields = []
    for rec in recommendations[:3]:
        planet = rec['planet']
        detailed_professions = {
            'Sun': ['Government officer', 'Doctor', 'CEO', 'Politician', 'Judge'],
            'Moon': ['Nurse', 'Psychologist', 'Hotel manager', 'Travel agent', 'Social worker'],
            'Mars': ['Engineer', 'Surgeon', 'Military officer', 'Sports coach', 'Real estate'],
            'Mercury': ['Teacher', 'Writer', 'Accountant', 'IT professional', 'Trader'],
            'Jupiter': ['Lawyer', 'Professor', 'Financial advisor', 'Priest', 'Consultant'],
            'Venus': ['Artist', 'Designer', 'Actor', 'Beautician', 'Luxury goods'],
            'Saturn': ['Farmer', 'Miner', 'Factory worker', 'Security', 'Construction']
        }
        detailed_fields.append({
            'planet': planet,
            'strength_score': rec['strength_score'],
            'specific_fields': detailed_professions.get(planet, ['General professions'])
        })
    return detailed_fields

def _identify_favorable_periods(current_dashas):
    """Identify favorable career periods"""
    # This would need more complex dasha analysis
    return ["Current period analysis requires detailed dasha calculation"]

def _get_timing_recommendations(current_dashas):
    """Get timing-based recommendations"""
    return ["Consult detailed dasha analysis for optimal timing"]

def _create_action_plan(obstacles, yogas):
    """Create actionable career plan"""
    plan = []
    
    if yogas:
        plan.append(f"Leverage your {len(yogas)} career yoga(s) for advancement")
    
    if obstacles:
        plan.append(f"Address {len(obstacles)} identified obstacle(s) through targeted remedies")
    
    plan.extend([
        "Focus on strengthening your primary career significator",
        "Time major career moves with favorable planetary periods",
        "Develop skills aligned with your strongest planets"
    ])
    
    return plan

def _get_remedial_measures(obstacles):
    """Get specific remedial measures"""
    if not obstacles:
        return ["No major obstacles identified - maintain current positive trajectory"]
    
    remedies = []
    for obstacle in obstacles:
        remedies.append(obstacle.get('remedy', 'General strengthening recommended'))
    
    return remedies

def _get_house_lord(sign_num):
    """Get the lord of a zodiac sign"""
    lords = {
        0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
        6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
    }
    return lords.get(sign_num, 'Unknown')

def _get_sign_name(sign_num):
    """Get sign name from number"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs[sign_num] if 0 <= sign_num < 12 else 'Unknown'

def _get_badhaka_career_interpretation(badhaka_impact):
    """Interpret Badhaka impact on career"""
    if not badhaka_impact['has_impact']:
        return ["No significant Badhaka obstacles in career"]
    
    interpretation = []
    
    badhaka_lord = badhaka_impact['badhaka_lord']
    rasi_type = badhaka_impact['rasi_type']
    impact_score = badhaka_impact['impact_score']
    
    if impact_score > 50:
        interpretation.append(f"Strong Badhaka influence from {badhaka_lord} creates significant career obstacles")
    elif impact_score > 25:
        interpretation.append(f"Moderate Badhaka influence from {badhaka_lord} may cause career delays")
    else:
        interpretation.append(f"Mild Badhaka influence from {badhaka_lord} on career matters")
    
    # Add rasi-specific interpretation
    nature = badhaka_impact['effects']['nature']
    description = badhaka_impact['effects']['description']
    interpretation.append(f"Career obstacles are {nature} - {description}")
    
    # Add remedies
    remedies = badhaka_impact['effects']['remedies']
    interpretation.append(f"Recommended approaches: {', '.join(remedies)}")
    
    return interpretation
@router.post("/career/saturn-tenth-analysis")
async def get_saturn_tenth_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get 10th house from Saturn analysis for career"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use SaturnTenthAnalyzer
        from calculators.saturn_tenth_analyzer import SaturnTenthAnalyzer
        analyzer = SaturnTenthAnalyzer(chart_data)
        analysis = analyzer.analyze_saturn_tenth_house()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"Saturn 10th analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Saturn 10th analysis failed: {str(e)}")
@router.post("/career/amatyakaraka-analysis")
async def get_amatyakaraka_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get Jaimini Amatyakaraka analysis for profession"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use AmatyakarakaAnalyzer
        from calculators.amatyakaraka_analyzer import AmatyakarakaAnalyzer
        analyzer = AmatyakarakaAnalyzer(chart_data)
        analysis = analyzer.analyze_amatyakaraka()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"Amatyakaraka analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Amatyakaraka analysis failed: {str(e)}")

@router.post("/career/success-yogas-analysis")
async def get_success_yogas_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get career success yogas analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerYogaAnalyzer
        from calculators.career_yoga_analyzer import CareerYogaAnalyzer
        analyzer = CareerYogaAnalyzer(chart_data)
        analysis = analyzer.analyze_career_yogas()
        
        return analysis
        
    except Exception as e:
        import traceback
        print(f"Career yogas analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Career yogas analysis failed: {str(e)}")