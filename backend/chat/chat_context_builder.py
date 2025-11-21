import sys
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from calculators.chart_calculator import ChartCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.friendship_calculator import FriendshipCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.argala_calculator import ArgalaCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.pancha_mahapurusha_calculator import PanchaMahapurushaCalculator
from shared.dasha_calculator import DashaCalculator

class ChatContextBuilder:
    """Builds comprehensive astrological context for chat conversations"""
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
    
    def build_complete_context(self, birth_data: Dict, user_question: str = "", target_date: Optional[datetime] = None, requested_period: Optional[Dict] = None) -> Dict[str, Any]:
        """Build complete astrological context for chat"""
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        if birth_hash not in self.static_cache:
            self.static_cache[birth_hash] = self._build_static_context(birth_data)
        
        static_context = self.static_cache[birth_hash]
        
        # Add dynamic data
        dynamic_context = self._build_dynamic_context(birth_data, user_question, target_date, requested_period)
        
        # Combine contexts
        return {
            **static_context,
            **dynamic_context
        }
    
    def _build_static_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build static chart context (cached per birth data)"""
        
        # Calculate birth chart using existing API endpoint logic
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Initialize analyzers
        planet_analyzer = PlanetAnalyzer(chart_data, birth_obj)
        divisional_calc = DivisionalChartCalculator(chart_data)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yogi_calc = YogiCalculator(chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        friendship_calc = FriendshipCalculator()
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        argala_calc = ArgalaCalculator(chart_data)
        
        # Advanced calculators
        planetary_war_calc = PlanetaryWarCalculator(chart_data)
        vargottama_calc = VargottamaCalculator(chart_data, {})
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, {})
        pancha_mahapurusha_calc = PanchaMahapurushaCalculator(chart_data)
        
        # Extract and validate ascendant information
        ascendant_degree = chart_data.get('ascendant', 0)
        ascendant_sign_num = int(ascendant_degree / 30)
        ascendant_sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        ascendant_sign_name = ascendant_sign_names[ascendant_sign_num]
        
        # Validate ascendant calculation
        try:
            from chart_validator import validate_ascendant_calculation
            validation = validate_ascendant_calculation(birth_data, ascendant_degree)
            ascendant_validation_note = f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'} - Difference: {validation['difference_degrees']:.4f}°"
        except Exception as e:
            ascendant_validation_note = f"Validation unavailable: {str(e)}"
        
        # Build comprehensive context
        context = {
            # Basic chart
            "birth_details": {
                "name": birth_data.get('name'),
                "date": birth_data.get('date'),
                "time": birth_data.get('time'),
                "place": birth_data.get('place', birth_data.get('name', 'Unknown')),
                "latitude": birth_data.get('latitude'),
                "longitude": birth_data.get('longitude')
            },
            
            # Validated ascendant information
            "ascendant_info": {
                "degree": ascendant_degree,
                "sign_number": ascendant_sign_num + 1,
                "sign_name": ascendant_sign_name,
                "exact_degree_in_sign": ascendant_degree % 30,
                "note": "This is the calculated Sidereal/Vedic ascendant using Swiss Ephemeris with Lahiri Ayanamsa",
                "validation": ascendant_validation_note,
                "formatted": f"{ascendant_sign_name} {ascendant_degree % 30:.2f}°"
            },
            
            "d1_chart": chart_data,
        }
        
        # Calculate divisional charts
        d9_chart = divisional_calc.calculate_divisional_chart(9)
        d10_chart = divisional_calc.calculate_divisional_chart(10)
        d12_chart = divisional_calc.calculate_divisional_chart(12)
        
        divisional_charts = {
            "d9_navamsa": d9_chart,
            "d10_dasamsa": d10_chart,
            "d12_dwadasamsa": d12_chart
        }
        
        # Update advanced calculators with divisional charts
        vargottama_calc = VargottamaCalculator(chart_data, divisional_charts)
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, divisional_charts)
        
        context.update({
            # Key divisional charts
            "divisional_charts": divisional_charts,
            
            # Planetary analysis
            "planetary_analysis": {},
            
            # Special points
            "special_points": {
                "badhaka_lord": badhaka_calc.get_badhaka_lord(int(chart_data['ascendant'] / 30))
            },
            
            # Relationships
            "relationships": {
                "argala_analysis": argala_calc.calculate_argala_analysis()
            },
            
            # Yogas
            "yogas": yoga_calc.calculate_all_yogas(),
            
            # Chara Karakas
            "chara_karakas": chara_karaka_calc.calculate_chara_karakas(),
            
            # Advanced Analysis
            "advanced_analysis": {
                "planetary_wars": planetary_war_calc.get_war_summary(),
                "vargottama_positions": vargottama_calc.get_vargottama_summary(),
                "neecha_bhanga": neecha_bhanga_calc.get_neecha_bhanga_summary(),
                "pancha_mahapurusha": pancha_mahapurusha_calc.get_pancha_mahapurusha_summary()
            }
        })
        
        # Add planetary analysis for all planets
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        for planet in planets:
            try:
                context["planetary_analysis"][planet] = planet_analyzer.analyze_planet(planet)
            except Exception as e:
                # print(f"Error analyzing {planet}: {e}")
                continue
        
        return context
    
    def _build_dynamic_context(self, birth_data: Dict, user_question: str, target_date: Optional[datetime], requested_period: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dynamic context based on question and date"""
        
        context = {}
        
        # Always include current dashas
        dasha_calc = DashaCalculator()
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # Add specific date dashas if requested
        if target_date:
            context['target_date_dashas'] = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Add house lordship mapping
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        context['house_lordships'] = self._get_house_lordships(ascendant_sign)
        
        # Add comprehensive house significations with ALL possible meanings
        context['house_significations'] = {
            1: "Self, personality, health, appearance, vitality, general well-being, head, brain, identity, first impressions, leadership, independence, new beginnings, personal initiatives",
            2: "Wealth, family, speech, values, food, accumulated resources, face, right eye, savings, possessions, family traditions, oral communication, eating habits, financial security, material assets", 
            3: "Siblings, courage, communication, short travels, hands, efforts, neighbors, writing, media, local transport, hobbies, skills, manual dexterity, correspondence, nearby places, small journeys",
            4: "Home, mother, education, property, vehicles, happiness, chest, heart, domestic life, real estate, academic learning, emotional security, homeland, comfort, private life, inner peace",
            5: "Children, creativity, intelligence, romance, speculation, stomach, past life karma, entertainment, sports, gambling, artistic expression, love affairs, pregnancy, mental abilities, fun activities",
            6: "Health issues, enemies, service, daily work, debts, diseases, obstacles, employment, routine tasks, medical treatment, litigation, competition, pets, subordinates, work environment, health maintenance",
            7: "Marriage, partnerships, business, spouse, public relations, lower abdomen, contracts, legal matters, open enemies, cooperation, negotiations, public image, business partnerships, marital harmony",
            8: "Transformation, occult, longevity, inheritance, accidents, hidden things, research, surgery, insurance, taxes, spouse's money, mysteries, psychology, death and rebirth, joint resources, investigations",
            9: "Fortune, dharma, higher learning, father, spirituality, long travels, thighs, philosophy, religion, foreign countries, publishing, teaching, law, ethics, pilgrimage, wisdom, higher education, mentors",
            10: "Career, reputation, authority, public image, government, knees, profession, status, recognition, achievements, boss, public service, political power, social standing, professional success, fame",
            11: "Gains, friends, aspirations, elder siblings, income, fulfillment of desires, social networks, hopes, large organizations, profits, achievements of goals, community involvement, group activities",
            12: "Losses, spirituality, foreign lands, expenses, isolation, feet, moksha, hospitals, prisons, meditation, charity, hidden enemies, subconscious mind, sleep, dreams, liberation, sacrifice, foreign settlement"
        }
        
        # Add transit data availability info with enhanced methodology
        current_year = datetime.now().year
        context['transit_data_availability'] = {
            "current_period": f"{current_year}-{current_year + 2} (2 years)",
            "available_range": "1900-2100",
            "can_request": True,
            "request_format": "Include JSON in your response: {\"requestType\": \"transitRequest\", \"startYear\": 2027, \"endYear\": 2028, \"specificMonths\": [\"January\", \"February\", \"March\"]}",
            "note": "You can request specific periods for detailed timing analysis using JSON format",
            "comprehensive_analysis_methodology": {
                "principle": "Events manifest when dasha planets recreate natal relationships through transits, activating ALL connected house significations",
                "mandatory_analysis_steps": [
                    "1. Identify ALL houses involved: transit house + natal house + lordship houses of both planets",
                    "2. Combine ALL house significations to determine possible life areas affected", 
                    "3. Consider planetary natures (benefic/malefic) to determine positive/negative outcomes",
                    "4. Synthesize with dasha context for timing and intensity",
                    "5. Predict SPECIFIC life events, not general philosophical statements"
                ],
                "example_analysis": "Mars (lord 5th,10th, natal 2nd) transits 6th aspecting natal Sun (9th house, lord 1st): Houses involved = 1st,2nd,5th,6th,9th,10th = self,wealth,children,health,father,career. Possible events: health issues affecting father, career conflicts requiring courage, children's education expenses, property disputes, work-related stress affecting family finances.",
                "quick_answer_requirements": {
                    "must_include": "4-6 SPECIFIC life events with exact dates from transit periods - predict MORE events by combining house meanings",
                    "event_examples": "Property purchase opportunity, job promotion, relationship milestone, health checkup needed, father's travel for medical treatment, children's achievement ceremony, financial gain through work, legal matter resolution, vehicle purchase, educational course enrollment, long distance travel for work, family medical expenses, etc.",
                    "avoid_generic_terms": "Do NOT use vague terms like 'good period', 'challenges', 'growth'. Use specific event predictions.",
                    "house_synthesis_mandatory": "MUST combine multiple house meanings: 2nd+10th = career income, 4th+7th = home with spouse, 6th+9th = father's health + long travel = father's medical travel, 5th+12th = children's expenses, 3rd+9th = communication with father/mentor, 1st+6th = personal health from work, 6th+9th = service-related long travel, health issues requiring travel, father's work problems, etc.",
                    "comprehensive_event_prediction": "For each transit, predict events from ALL house combinations, not just obvious ones. Example: 6th+9th houses = father's health issues, father's work problems, long travel for medical treatment, legal issues with father, father's service to others, health expenses, work-related travel, educational travel, spiritual journey for healing, etc.",
                    "laymen_summary_mandatory": {
                        "purpose": "Quick Answer section MUST provide a clear, simple summary for non-astrologers",
                        "format": "Write as if explaining to someone who knows nothing about astrology",
                        "requirements": [
                            "Start with: 'Based on your birth chart and upcoming planetary movements:'",
                            "List 2-3 specific life events with exact date ranges",
                            "Place Key Insights section IMMEDIATELY after Quick Answer section",
                            "Use proper markdown: ## Key Insights (with double newline before content)",
                            "Format Key Insights as: ## Key Insights\n\n• Point 1\n• Point 2\n• Point 3"
                            "Explain WHY these events are likely (in simple terms)",
                            "End with: 'These predictions are based on the detailed astrological analysis below.'"
                        ],
                        "example_format": "Based on your birth chart and upcoming planetary movements: Between Jan 15-Mar 20, 2025, you're likely to have a property purchase opportunity through career advancement, as your career planet activates your wealth sector. From Feb 5-25, 2025, expect father's health to need attention with possible travel for treatment, creating family expenses. These predictions are based on the detailed astrological analysis below.",
                        "forbidden_in_summary": [
                            "Astrological jargon (houses, aspects, dashas, transits)",
                            "Planet names without context",
                            "Technical terms like 'benefic', 'malefic', 'conjunction'",
                            "Philosophical or spiritual language"
                        ],
                        "required_language": "Use everyday language: 'career opportunities', 'family matters', 'health concerns', 'financial gains', 'relationship changes', 'property matters', 'travel plans', etc."
                    },

                },
                "instruction": "MANDATORY: For ALL timing questions, request transit data using JSON format. After receiving transit data, provide comprehensive analysis using ALL house significations. RESPONSE MUST HAVE EXACTLY 6 SECTIONS IN THIS ORDER: 1) Quick Answer paragraph 2) ## Key Insights 3) ## Astrological Analysis 4) ## Nakshatra Insights 5) ## Timing & Guidance 6) ## Final Thoughts. Use standard markdown formatting only.",

            }
        }
        
        # Only calculate transit data if specifically requested by Gemini
        if requested_period:
            start_year = requested_period.get('start_year', current_year)
            end_year = requested_period.get('end_year', current_year + 2)
            year_range = end_year - start_year
            print(f"🎯 GEMINI REQUESTED TRANSIT PERIOD: {start_year}-{end_year} ({year_range} years)")
            
            try:
                print(f"📊 Initializing RealTransitCalculator...")
                real_calc = RealTransitCalculator()
                print(f"🔍 Finding real aspects for birth data...")
                aspects = real_calc.find_real_aspects(birth_data)
                print(f"   Found {len(aspects)} potential aspects")
                
                transit_activations = []
                
                for i, aspect in enumerate(aspects):
                    # print(f"   Processing aspect {i+1}/{len(aspects)}: {aspect['transit_planet']} -> {aspect['natal_planet']}")
                    # print(f"     Aspect details: {aspect}")
                    try:
                        timeline = real_calc.calculate_aspect_timeline(aspect, start_year, year_range, birth_data)
                        # print(f"     Timeline periods found: {len(timeline)}")
                        
                        for j, period in enumerate(timeline):
                            # print(f"     Period {j+1}: {period['start_date']} to {period['end_date']}")
                            # print(f"       Transit house: {period.get('transit_house')}, Natal house: {period.get('natal_house')}")
                            # print(f"       Conjunct planets: {period.get('conjunct_natal_planets', [])}")
                            # print(f"       All aspects cast: {len(period.get('all_aspects_cast', []))} aspects")
                            
                            # Log each aspect cast
                            for aspect_cast in period.get('all_aspects_cast', []):
                                # print(f"         {aspect_cast['aspect_type']} -> House {aspect_cast['target_house']} (planets: {aspect_cast['target_planets']})")
                                pass
                            
                            # Add dasha correlation for this transit period
                            start_date_obj = datetime.strptime(period['start_date'], '%Y-%m-%d')
                            end_date_obj = datetime.strptime(period['end_date'], '%Y-%m-%d')
                            
                            # print(f"       Calculating dashas for {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}")
                            dasha_periods = dasha_calc.get_dasha_periods_for_range(
                                birth_data, start_date_obj, end_date_obj
                            )
                            # print(f"       Dasha periods found: {len(dasha_periods)}")
                            
                            for k, dasha_period in enumerate(dasha_periods):
                                # print(f"         Dasha {k+1}: {dasha_period['start_date']} to {dasha_period['end_date']}")
                                # print(f"           Maha: {dasha_period['mahadasha']}, Antar: {dasha_period['antardasha']}, Pratyantar: {dasha_period['pratyantardasha']}")
                                # print(f"           Sookshma: {dasha_period['sookshma']}, Prana: {dasha_period['prana']}")
                                pass
                            
                            # Analyze dasha significance
                            significance = self._analyze_dasha_transit_significance(
                                aspect['transit_planet'], aspect['natal_planet'], dasha_periods
                            )
                            # print(f"       Dasha significance: {significance}")
                            
                            transit_activations.append({
                                **period,
                                'transit_planet': aspect['transit_planet'],
                                'natal_planet': aspect['natal_planet'],
                                'aspect_number': aspect['aspect_number'],
                                'dasha_periods': dasha_periods,
                                'dasha_significance': significance
                            })
                    except Exception as aspect_error:
                        # print(f"     ❌ Error calculating timeline: {aspect_error}")
                        # import traceback
                        # traceback.print_exc()
                        pass
                        continue
                
                context['transit_activations'] = transit_activations
                print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                print(f"   Period: {start_year}-{end_year}")
                print(f"   Total activations: {len(transit_activations)}")
                for i, activation in enumerate(transit_activations[:3]):
                    print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']})")
                if len(transit_activations) > 3:
                    print(f"     ... and {len(transit_activations) - 3} more")
                
                # Add comprehensive transit analysis instructions
                context['comprehensive_transit_analysis'] = {
                    "mandatory_approach": "For each transit activation, analyze ALL connected houses and predict MULTIPLE specific life events by combining house meanings",
                    "analysis_steps": [
                        "1. Identify transit planet's natal house + lordship houses",
                        "2. Identify natal planet's house + lordship houses", 
                        "3. Note the transit house where activation occurs",
                        "4. List ALL significations from each house (use complete house meanings provided)",
                        "5. Create event combinations by mixing house significations (e.g., 6th+9th = father's health + long travel = father's medical travel)",
                        "6. Apply planetary natures (benefic/malefic) for outcome polarity",
                        "7. Predict MINIMUM 3-5 specific events per transit activation, not just 1-2"
                    ],
                    "example_comprehensive_analysis": {
                        "scenario": "Saturn (natal 8th house, lord 9th,10th) transits 6th house aspecting natal Mars (2nd house, lord 5th,12th)",
                        "houses_involved": "2nd,5th,6th,8th,9th,10th,12th",
                        "significations": "wealth,children,health,transformation,father,career,expenses",
                        "predicted_events": [
                            "Career transformation requiring health attention",
                            "Father's health issues affecting family finances", 
                            "Children's education expenses through career changes",
                            "Property matters involving legal/health complications"
                        ]
                    },
                    "quick_answer_enhancement": {
                        "current_problem": "Quick answers are too high-level and philosophical",
                        "required_improvement": "Must synthesize ALL house significations to predict specific life events",
                        "format_requirement": "Date range: Specific event prediction based on house synthesis",
                        "examples": [
                            "Jan 15-Mar 20: Property purchase opportunity through career advancement (2nd+10th houses)",
                            "Feb 5-25: Father's travel for health treatment, family expenses (6th+9th+12th houses)",
                            "Apr 10-May 5: Children's achievement bringing recognition, celebration costs (5th+11th+12th houses)"
                        ]
                    },
                    "forbidden_approaches": [
                        "Generic philosophical statements about planetary influences",
                        "Vague terms like 'challenges', 'growth', 'good period'",
                        "Single house analysis ignoring lordships and connections",
                        "Theoretical discussions without specific event predictions"
                    ]
                }
                
                context["response_format_for_period_predictions"] = {
                    "structure": "When user asks for specific period predictions, use this EXACT format:",
                    "template": {
                        "quick_answer": "LAYMEN-FRIENDLY summary with 2-3 specific events and exact dates - NO astrological jargon",
                        "event_predictions": {
                            "high_probability_events": [
                                {
                                    "event_type": "Career/Finance/Relationship/Health/Property/Education",
                                    "description": "Specific event description",
                                    "dates": "YYYY-MM-DD to YYYY-MM-DD",
                                    "probability": "High/Medium percentage",
                                    "astrological_basis": "Brief reasoning"
                                }
                            ],
                            "best_action_days": [
                                {
                                    "date": "YYYY-MM-DD",
                                    "action": "Specific recommended action"
                                }
                            ]
                        },
                        "period_analysis": "Brief analysis of the selected period's astrological significance",
                        "precautions": "Any warnings or things to avoid during this period"
                    },
                    "mandatory_sections": [
                        "Quick Answer with specific events and dates (LAYMEN-FRIENDLY)",
                        "Event Predictions with probabilities",
                        "Best Action Days",
                        "Period Analysis",
                        "Precautions if any"
                    ],
                    "skip_sections": [
                        "General personality analysis",
                        "Full chart overview",
                        "Divisional chart detailed analysis",
                        "Complete yoga descriptions"
                    ],
                    "quick_answer_mandatory_format": {
                        "opening": "Based on your birth chart and upcoming planetary movements:",
                        "content": "2-3 specific life events with exact date ranges in simple language",
                        "closing": "These predictions are based on the detailed astrological analysis below.",
                        "language_requirement": "Use everyday language that anyone can understand, avoid all astrological terminology",
                        "example": "Based on your birth chart and upcoming planetary movements: Between Jan 15-Mar 20, 2025, you're likely to have a property purchase opportunity through career advancement. From Feb 5-25, 2025, expect father's health to need attention with possible travel for treatment. These predictions are based on the detailed astrological analysis below."
                    }
                }
                
                # Log transit data being sent
                # print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                # print(f"   Period: {start_year}-{end_year}")
                # print(f"   Total activations: {len(transit_activations)}")
                # for i, activation in enumerate(transit_activations[:5]):
                #     print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']})")
                # if len(transit_activations) > 5:
                #     print(f"     ... and {len(transit_activations) - 5} more")
                    
            except Exception as e:
                print(f"❌ Error calculating transit activations: {e}")
                import traceback
                traceback.print_exc()
                context['transit_activations'] = []
        
        # Add period focus instructions if this is for a specific period
        if hasattr(self, '_selected_period_data'):
            context['selected_period_focus'] = {
                "period_data": self._selected_period_data,
                "response_format": "event_prediction_focused",
                "instruction": "Focus ONLY on specific event predictions for the selected period. Use the response_format_for_period_predictions template. Skip general chart analysis sections."
            }
        
        # ESSENTIAL STRUCTURE ONLY
        context['RESPONSE_STRUCTURE_REQUIRED'] = {
            "sections_in_order": [
                "Quick Answer (paragraph)",
                "## Key Insights",
                "## Astrological Analysis", 
                "## Nakshatra Insights",
                "## Timing & Guidance",
                "## Final Thoughts"
            ],
            "formatting": "Standard markdown only: ## for headers, - for bullets",
            "critical_requirements": [
                "NEVER use HTML entities like &#39; or &amp; - use plain text apostrophes and ampersands",
                "ALL section headers MUST start with ## followed by space",
                "Use standard bullet points with - or • symbols only",
                "No special Unicode symbols like ◆ or ▸",
                "In Astrological Analysis section: start new paragraph for each major topic"
            ]
        }
        
        return context
    
    def set_selected_period(self, period_data: Dict):
        """Set selected period for focused predictions"""
        self._selected_period_data = period_data
    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def _analyze_dasha_transit_significance(self, transit_planet: str, natal_planet: str, dasha_periods: List[Dict]) -> str:
        """Analyze the significance of transit based on current dasha periods"""
        # print(f"         Analyzing significance for {transit_planet} -> {natal_planet}")
        
        if not dasha_periods:
            # print(f"         No dasha periods provided, returning moderate")
            return "moderate"
        
        max_significance = "moderate"
        
        # Check if transit planet or natal planet is in any dasha level
        for i, period in enumerate(dasha_periods):
            active_planets = [
                period.get('mahadasha'),
                period.get('antardasha'), 
                period.get('pratyantardasha'),
                period.get('sookshma'),
                period.get('prana')
            ]
            
            # print(f"         Period {i+1} active planets: {active_planets}")
            
            transit_in_dasha = transit_planet in active_planets
            natal_in_dasha = natal_planet in active_planets
            
            # print(f"         {transit_planet} in dasha: {transit_in_dasha}, {natal_planet} in dasha: {natal_in_dasha}")
            
            if transit_in_dasha and natal_in_dasha:
                # print(f"         Both planets in dasha - MAXIMUM significance")
                max_significance = "maximum"
            elif transit_in_dasha or natal_in_dasha:
                if max_significance != "maximum":
                    # print(f"         One planet in dasha - HIGH significance")
                    max_significance = "high"
        
        # print(f"         Final significance: {max_significance}")
        return max_significance
    
    def get_high_significance_periods(self, birth_data: Dict, years_ahead: int = 2, selected_year: int = None) -> List[Dict]:
        """Get high-significance event periods for the next specified years"""
        current_year = datetime.now().year
        
        if selected_year:
            start_year = selected_year
            end_year = selected_year + 1
        else:
            start_year = current_year
            end_year = current_year + years_ahead
        
        # Build context with transit data
        context = self.build_complete_context(
            birth_data, "", None, 
            requested_period={'start_year': start_year, 'end_year': end_year}
        )
        
        # Extract high-significance periods with enhanced data
        periods = []
        dasha_calc = DashaCalculator()
        
        for activation in context.get('transit_activations', []):
            if activation['dasha_significance'] in ['high', 'maximum']:
                # Get overlapping dasha periods for this specific transit period
                start_date_obj = datetime.strptime(activation['start_date'], '%Y-%m-%d')
                end_date_obj = datetime.strptime(activation['end_date'], '%Y-%m-%d')
                
                overlapping_dashas = dasha_calc.get_dasha_periods_for_range(
                    birth_data, start_date_obj, end_date_obj
                )
                
                # Get the actual aspect number from the activation data (already calculated correctly)
                aspect_number = activation.get('aspect_number')
                transit_house = activation.get('transit_house')
                natal_house = activation.get('natal_house')
                
                # Validate aspect against planet's capabilities
                transit_planet = activation['transit_planet']
                valid_aspects = {
                    'Sun': [1, 7],
                    'Moon': [1, 7], 
                    'Mars': [1, 4, 7, 8],
                    'Mercury': [1, 7],
                    'Jupiter': [1, 5, 7, 9],
                    'Venus': [1, 7],
                    'Saturn': [1, 3, 7, 10],
                    'Rahu': [1, 5, 7, 9],
                    'Ketu': [1, 5, 7, 9]
                }
                
                # Only include if aspect is valid for this planet
                if aspect_number not in valid_aspects.get(transit_planet, []):
                    continue
                
                # Find which dasha the transit planet will be in during this period
                transit_planet_dashas = []
                for dasha in overlapping_dashas:
                    if dasha['mahadasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Mahadasha',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['antardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Antardasha', 
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['pratyantardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Pratyantardasha',
                            'planet': transit_planet, 
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['sookshma'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Sookshma',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'], 
                            'end_date': dasha['end_date']
                        })
                    elif dasha['prana'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Prana',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                

                
                # Calculate life areas affected by this transit
                life_areas = self._calculate_life_areas(
                    activation['transit_planet'],
                    activation['natal_planet'], 
                    transit_house,
                    natal_house,
                    context.get('house_lordships', {})
                )
                
                periods.append({
                    'id': f"{activation['transit_planet']}-{activation['natal_planet']}-{activation['start_date']}",
                    'label': f"{activation['start_date']} to {activation['end_date']}: {activation['transit_planet']}→{activation['natal_planet']}",
                    'start_date': activation['start_date'],
                    'end_date': activation['end_date'],
                    'transit_planet': activation['transit_planet'],
                    'natal_planet': activation['natal_planet'],
                    'significance': activation['dasha_significance'],
                    'life_areas': life_areas,
                    'period_data': {
                        **activation,
                        'aspect_number': aspect_number,
                        'overlapping_dashas': overlapping_dashas,
                        'transit_planet_dashas': transit_planet_dashas,
                        'life_areas': life_areas
                    }
                })
                

        
        # Sort by date
        periods.sort(key=lambda x: x['start_date'])
        

        return periods[:20]  # Return top 20 periods
    
    def _get_house_lordships(self, ascendant_sign: int) -> Dict:
        """Get house lordships based on ascendant sign"""
        # Sign lordships (0=Aries, 1=Taurus, etc.)
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        house_lordships = {}
        for house in range(1, 13):
            # Calculate which sign rules this house
            house_sign = (ascendant_sign + house - 1) % 12
            lord = sign_lords[house_sign]
            
            if lord not in house_lordships:
                house_lordships[lord] = []
            house_lordships[lord].append(house)
        
        return house_lordships
    
    def _calculate_life_areas(self, transit_planet: str, natal_planet: str, transit_house: int, natal_house: int, house_lordships: Dict) -> List[str]:
        """Calculate life areas affected by transit activation"""
        
        # Comprehensive house signification mapping for all life areas
        house_areas = {
            1: ["Self", "Health", "Personality", "Appearance", "Vitality", "Leadership", "Independence", "Identity"],
            2: ["Wealth", "Family", "Speech", "Values", "Food", "Savings", "Possessions", "Financial Security", "Material Assets"],
            3: ["Siblings", "Courage", "Communication", "Short Travel", "Efforts", "Neighbors", "Writing", "Media", "Skills", "Hobbies"],
            4: ["Home", "Mother", "Education", "Property", "Vehicles", "Happiness", "Domestic Life", "Real Estate", "Comfort", "Inner Peace"],
            5: ["Children", "Creativity", "Intelligence", "Romance", "Speculation", "Entertainment", "Sports", "Gambling", "Love Affairs", "Pregnancy"],
            6: ["Health Issues", "Enemies", "Service", "Daily Work", "Debts", "Diseases", "Employment", "Medical Treatment", "Competition", "Pets"],
            7: ["Marriage", "Partnerships", "Business", "Spouse", "Public Relations", "Contracts", "Legal Matters", "Cooperation", "Negotiations"],
            8: ["Transformation", "Occult", "Longevity", "Inheritance", "Accidents", "Research", "Surgery", "Insurance", "Taxes", "Joint Resources"],
            9: ["Fortune", "Dharma", "Higher Learning", "Father", "Spirituality", "Long Travel", "Philosophy", "Religion", "Foreign Countries", "Teaching"],
            10: ["Career", "Reputation", "Authority", "Public Image", "Government", "Profession", "Status", "Recognition", "Boss", "Fame"],
            11: ["Gains", "Friends", "Aspirations", "Elder Siblings", "Income", "Fulfillment", "Social Networks", "Hopes", "Profits", "Community"],
            12: ["Losses", "Spirituality", "Foreign Lands", "Expenses", "Isolation", "Moksha", "Hospitals", "Meditation", "Charity", "Liberation"]
        }
        
        affected_houses = set()
        
        # Add primary houses
        if transit_house:
            affected_houses.add(transit_house)
        if natal_house:
            affected_houses.add(natal_house)
        
        # Add lordship houses
        if transit_planet in house_lordships:
            affected_houses.update(house_lordships[transit_planet])
        if natal_planet in house_lordships:
            affected_houses.update(house_lordships[natal_planet])
        
        # Convert to life areas and prioritize
        life_areas = []
        priority_houses = [transit_house, natal_house] if transit_house and natal_house else []
        
        # Add primary areas first (top 2 from each priority house)
        for house in priority_houses:
            if house in house_areas:
                house_significations = house_areas[house][:2]  # Take top 2 significations
                for area in house_significations:
                    if area not in life_areas:
                        life_areas.append(area)
        
        # Add secondary areas from lordships (1 from each house)
        for house in sorted(affected_houses):
            if house in house_areas and house not in priority_houses:
                area = house_areas[house][0]  # Take primary signification
                if area not in life_areas and len(life_areas) < 4:
                    life_areas.append(area)
        
        return life_areas[:4]  # Return top 4 most relevant areas