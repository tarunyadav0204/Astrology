from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from .tenth_house_analyzer import TenthHouseAnalyzer
from calculators.tenth_house_analyzer import TenthHouseAnalyzer as TenthHouseAnalyzerCalc
from .career_paths_analyzer import CareerPathsAnalyzer
from calculators.nakshatra_career_analyzer import NakshatraCareerAnalyzer
from .leadership_analyzer import LeadershipAnalyzer
from .work_style_analyzer import WorkStyleAnalyzer

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

@router.post("/career/comprehensive-analysis")
async def get_comprehensive_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get comprehensive career analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use existing analyzers
        leadership_analyzer = LeadershipAnalyzer(chart_data)
        work_style_analyzer = WorkStyleAnalyzer(chart_data)
        
        result = {
            'leadership_analysis': leadership_analyzer.analyze_leadership_tendencies(birth_data),
            'work_style_analysis': work_style_analyzer.analyze_creative_vs_structured(birth_data),
            'solo_team_analysis': work_style_analyzer.analyze_solo_vs_team(birth_data)
        }
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Comprehensive analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis failed: {str(e)}")

@router.post("/career/nakshatra-analysis")
async def get_nakshatra_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get nakshatra-based career analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use NakshatraCareerAnalyzer
        analyzer = NakshatraCareerAnalyzer(chart_data)
        result = analyzer.analyze_career_nakshatras()
        
        return {'nakshatra_analysis': result}
        
    except Exception as e:
        import traceback
        print(f"Nakshatra analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Nakshatra analysis failed: {str(e)}")

@router.post("/career/leadership-analysis")
async def get_leadership_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get leadership style analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use LeadershipAnalyzer
        analyzer = LeadershipAnalyzer(chart_data)
        result = analyzer.analyze_leadership_tendencies(birth_data)
        
        return {'leadership_analysis': result}
        
    except Exception as e:
        import traceback
        print(f"Leadership analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Leadership analysis failed: {str(e)}")

@router.post("/career/work-style-analysis")
async def get_work_style_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get work style analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use WorkStyleAnalyzer
        analyzer = WorkStyleAnalyzer(chart_data)
        result = analyzer.analyze_creative_vs_structured(birth_data)
        
        return {'work_style_analysis': result}
        
    except Exception as e:
        import traceback
        print(f"Work style analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Work style analysis failed: {str(e)}")

@router.post("/career/solo-team-analysis")
async def get_solo_team_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get solo vs team work analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use WorkStyleAnalyzer
        analyzer = WorkStyleAnalyzer(chart_data)
        result = analyzer.analyze_solo_vs_team(birth_data)
        
        return {'solo_team_analysis': result}
        
    except Exception as e:
        import traceback
        print(f"Solo team analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Solo team analysis failed: {str(e)}")

@router.post("/career/career-fields-analysis")
async def get_career_fields_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze top 3 career fields based on planetary positions"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_career_fields()
        
        return {'career_fields': result}
        
    except Exception as e:
        import traceback
        print(f"Career fields analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Career fields analysis failed: {str(e)}")

@router.post("/career/job-roles-analysis")
async def get_job_roles_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze specific job roles based on Atmakaraka"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_job_roles()
        
        return {'job_roles': result}
        
    except Exception as e:
        import traceback
        print(f"Job roles analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Job roles analysis failed: {str(e)}")

@router.post("/career/work-mode-analysis")
async def get_work_mode_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze entrepreneur vs employee preference"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_work_mode()
        
        return {'work_mode': result}
        
    except Exception as e:
        import traceback
        print(f"Work mode analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Work mode analysis failed: {str(e)}")

@router.post("/career/industries-analysis")
async def get_industries_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze suitable industries based on elemental influences"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_industries()
        
        return {'industries': result}
        
    except Exception as e:
        import traceback
        print(f"Industries analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Industries analysis failed: {str(e)}")

@router.post("/career/work-type-analysis")
async def get_work_type_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze creative vs technical vs service work preference"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_work_type()
        
        return {'work_type': result}
        
    except Exception as e:
        import traceback
        print(f"Work type analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Work type analysis failed: {str(e)}")

@router.post("/career/avoid-careers-analysis")
async def get_avoid_careers_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze career fields to avoid based on planetary weaknesses"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use CareerPathsAnalyzer
        analyzer = CareerPathsAnalyzer(chart_data)
        result = analyzer.analyze_avoid_careers()
        
        return {'avoid_careers': result}
        
    except Exception as e:
        import traceback
        print(f"Avoid careers analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Avoid careers analysis failed: {str(e)}")

@router.post("/career/conjunction-analysis")
async def get_conjunction_analysis(request: dict, current_user = Depends(get_current_user)):
    """Analyze planetary conjunctions for career with modern interpretations"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use ConjunctionAnalyzer
        from .conjunction_analyzer import ConjunctionAnalyzer
        analyzer = ConjunctionAnalyzer(chart_data)
        
        result = {
            'career_conjunctions': analyzer.analyze_career_conjunctions(),
            'tenth_house_conjunctions': analyzer.analyze_tenth_house_conjunctions(),
            'karmic_patterns': analyzer.analyze_karmic_career_patterns()
        }
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Conjunction analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Conjunction analysis failed: {str(e)}")

@router.post("/career/tenth-lord-analysis")
async def get_tenth_lord_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get 10th house lord analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer
        analyzer = TenthHouseAnalyzer(chart_data)
        result = analyzer.analyze_tenth_lord()
        
        return {'tenth_lord_analysis': result}
        
    except Exception as e:
        import traceback
        print(f"Tenth lord analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Tenth lord analysis failed: {str(e)}")

@router.post("/career/tenth-house-analysis")
async def get_tenth_house_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get 10th house analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer
        analyzer = TenthHouseAnalyzer(chart_data)
        result = analyzer.analyze_tenth_house()
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Tenth house analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Tenth house analysis failed: {str(e)}")

@router.post("/career/d10-analysis")
async def get_d10_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get D10 divisional chart analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer for D10
        analyzer = TenthHouseAnalyzer(chart_data)
        result = analyzer.analyze_d10_chart()
        
        return result
        
    except Exception as e:
        import traceback
        print(f"D10 analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"D10 analysis failed: {str(e)}")

@router.post("/career/saturn-karaka-analysis")
async def get_saturn_karaka_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get Saturn Karma Karaka analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer for Saturn analysis
        analyzer = TenthHouseAnalyzer(chart_data)
        result = analyzer.analyze_saturn_karaka()
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Saturn karaka analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Saturn karaka analysis failed: {str(e)}")

@router.post("/career/saturn-tenth-analysis")
async def get_saturn_tenth_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get 10th from Saturn analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use TenthHouseAnalyzer for Saturn 10th analysis
        analyzer = TenthHouseAnalyzer(chart_data)
        result = analyzer.analyze_saturn_tenth()
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Saturn tenth analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Saturn tenth analysis failed: {str(e)}")

@router.post("/career/amatyakaraka-analysis")
async def get_amatyakaraka_analysis(request: dict, current_user = Depends(get_current_user)):
    """Get Amatyakaraka analysis"""
    try:
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        from main import calculate_chart
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
        
        # Use existing Amatyakaraka analyzer
        from calculators.amatyakaraka_analyzer import AmatyakarakaAnalyzer
        analyzer = AmatyakarakaAnalyzer(chart_data)
        result = analyzer.analyze_amatyakaraka()
        
        return result
        
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
        
        # Use existing yoga analyzer
        from calculators.yoga_analyzer import YogaAnalyzer
        analyzer = YogaAnalyzer(chart_data)
        result = analyzer.analyze_career_yogas()
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Career yogas analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Career yogas analysis failed: {str(e)}")

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