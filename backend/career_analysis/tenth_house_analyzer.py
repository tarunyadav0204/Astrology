from fastapi import HTTPException

class TenthHouseAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                          'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        self.house_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
            8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def analyze_tenth_lord(self):
        """Analyze 10th house lord"""
        try:
            # Use comprehensive planet analyzer for real analysis
            from calculators.planet_analyzer import PlanetAnalyzer
            planet_analyzer = PlanetAnalyzer(self.chart_data)
            
            ascendant_degrees = self.chart_data['ascendant']
            ascendant_sign = int(ascendant_degrees / 30)
            tenth_house_sign = (ascendant_sign + 9) % 12
            tenth_lord = self.house_lords[tenth_house_sign]
            
            lord_analysis = planet_analyzer.analyze_planet(tenth_lord)
            
            return {
                'tenth_house_info': {
                    'house_sign_name': self.sign_names[tenth_house_sign],
                    'house_lord': tenth_lord
                },
                'lord_analysis': lord_analysis,
                'yogi_significance': {
                    'has_impact': True,
                    'lord_significance': {
                        'has_impact': True,
                        'special_status': 'yogi_lord'
                    },
                    'house_impact': {
                        'total_impact': 75
                    },
                    'career_impact': {
                        'total_impact': 80
                    }
                },
                'badhaka_impact': {
                    'has_impact': False,
                    'lord_impact': {
                        'has_impact': False,
                        'is_badhaka_lord': False
                    },
                    'house_impact': {
                        'impact_score': 0
                    },
                    'career_impact': {
                        'impact_score': 0
                    }
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def analyze_tenth_house(self):
        """Analyze 10th house"""
        try:
            # Use comprehensive house analyzer for real analysis
            from calculators.tenth_house_analyzer import TenthHouseAnalyzer as ComprehensiveAnalyzer
            comprehensive_analyzer = ComprehensiveAnalyzer(self.chart_data, {})
            comprehensive_result = comprehensive_analyzer.analyze_tenth_house()
            
            # Format result to match frontend expectations
            return {
                'house_sign': comprehensive_result['sign_analysis']['sign'],
                'strength': comprehensive_result['house_strength']['grade'],
                'strength_details': {
                    'enhanced_strength': comprehensive_result['house_strength']['total_score']
                },
                'planets_in_house': [{
                    'name': p['planet'],
                    'effect': p['career_significance']
                } for p in comprehensive_result['planets_in_house']['planets']],
                'aspects': comprehensive_result['aspects_on_house']['aspects'],
                'yogi_analysis': {
                    'has_impact': True,
                    'house_impact': {
                        'total_impact': 75
                    },
                    'career_impact': {
                        'total_impact': 75
                    }
                },
                'badhaka_analysis': {
                    'has_impact': False,
                    'house_impact': {
                        'has_impact': False,
                        'impact_score': 0
                    },
                    'career_impact': {
                        'has_impact': False,
                        'impact_score': 0
                    }
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def analyze_d10_chart(self):
        """Analyze D10 chart"""
        try:
            from calculators.divisional_chart_calculator import DivisionalChartCalculator
            d10_calc = DivisionalChartCalculator(self.chart_data)
            d10_result = d10_calc.calculate_divisional_chart(10)
            
            # Get D10 ascendant sign name
            d10_asc_sign = int(d10_result['divisional_chart']['ascendant'] / 30)
            
            # Calculate 10th lord in D10
            tenth_house_sign = (d10_asc_sign + 9) % 12
            tenth_lord = self.house_lords[tenth_house_sign]
            
            return {
                'ascendant_analysis': {
                    'sign': self.sign_names[d10_asc_sign],
                    'strength': 'Medium'
                },
                'tenth_lord_analysis': {
                    'tenth_lord': tenth_lord,
                    'position_sign': self.sign_names[d10_result['divisional_chart']['planets'][tenth_lord]['sign']],
                    'position_house': ((d10_result['divisional_chart']['planets'][tenth_lord]['sign'] - d10_asc_sign) % 12) + 1
                },
                'professional_strength': {
                    'score': 70,
                    'grade': 'Good'
                },
                'career_indicators': ['Leadership potential', 'Technical skills'],
                'career_recommendations': ['Focus on structured approach'],
                'planet_analysis': {
                    planet: {
                        'sign': self.sign_names[data['sign']],
                        'house': ((data['sign'] - d10_asc_sign) % 12) + 1,
                        'overall_effect': f'{planet} influence in career'
                    } for planet, data in d10_result['divisional_chart']['planets'].items()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def analyze_saturn_karaka(self):
        """Analyze Saturn as karma karaka"""
        try:
            from calculators.planet_analyzer import PlanetAnalyzer
            planet_analyzer = PlanetAnalyzer(self.chart_data)
            saturn_analysis = planet_analyzer.analyze_planet('Saturn')
            
            saturn_data = self.chart_data['planets']['Saturn']
            return {
                'saturn_basic_info': {
                    'sign_name': saturn_analysis['basic_info']['sign_name'],
                    'house': saturn_data['house']
                },
                'saturn_analysis': saturn_analysis,
                'karma_interpretation': {
                    'karmic_strength_level': saturn_analysis['overall_assessment']['overall_grade']
                },
                'career_karma_insights': {
                    'career_timing': {
                        'maturation_age': '36 years',
                        'peak_periods': 'Saturn Mahadasha',
                        'advice': saturn_analysis['overall_assessment']['recommendations'][0] if saturn_analysis['overall_assessment']['recommendations'] else 'Focus on discipline'
                    },
                    'karmic_lessons': saturn_analysis['overall_assessment']['key_strengths'],
                    'remedial_guidance': saturn_analysis['overall_assessment']['recommendations']
                },
                'saturn_yogi_significance': {
                    'has_impact': True,
                    'saturn_significance': {
                        'has_impact': True,
                        'special_status': 'karma_karaka'
                    },
                    'house_impact': {
                        'total_impact': 70
                    },
                    'career_impact': {
                        'total_impact': 65
                    }
                },
                'saturn_badhaka_impact': {
                    'has_impact': False,
                    'badhaka_impact': {
                        'has_impact': False,
                        'is_badhaka_lord': False,
                        'impact_score': 0
                    },
                    'house_impact': {
                        'has_impact': False
                    },
                    'career_impact': {
                        'has_impact': False
                    }
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def analyze_saturn_tenth(self):
        """Analyze 10th from Saturn"""
        try:
            from calculators.tenth_house_analyzer import TenthHouseAnalyzer as ComprehensiveAnalyzer
            from calculators.planet_analyzer import PlanetAnalyzer
            
            saturn_data = self.chart_data['planets']['Saturn']
            saturn_house = saturn_data['house']
            
            # Create temporary chart with Saturn as reference point
            temp_chart = self.chart_data.copy()
            temp_chart['ascendant'] = (saturn_data['longitude'] - 270) % 360
            temp_analyzer = ComprehensiveAnalyzer(temp_chart, {})
            saturn_tenth_analysis = temp_analyzer.analyze_tenth_house()
            
            saturn_analyzer = PlanetAnalyzer(self.chart_data)
            saturn_analysis = saturn_analyzer.analyze_planet('Saturn')
            
            return {
                'saturn_info': {
                    'saturn_house': saturn_house,
                    'saturn_sign': saturn_analysis['basic_info']['sign_name']
                },
                'saturn_tenth_house_info': saturn_tenth_analysis['house_info'],
                'sign_analysis': saturn_tenth_analysis['sign_analysis'],
                'planets_in_house': saturn_tenth_analysis['planets_in_house'],
                'aspects_on_house': saturn_tenth_analysis['aspects_on_house'],
                'house_strength': saturn_tenth_analysis['house_strength'],
                'ashtakavarga_points': saturn_tenth_analysis['ashtakavarga_points'],
                'overall_assessment': saturn_tenth_analysis['overall_assessment'],
                'saturn_tenth_yogi_analysis': {
                    'has_impact': True,
                    'house_impact': {
                        'total_impact': 60
                    },
                    'career_impact': {
                        'total_impact': 55
                    }
                },
                'saturn_tenth_badhaka_analysis': {
                    'has_impact': False,
                    'house_impact': {
                        'has_impact': False,
                        'impact_score': 0
                    },
                    'career_impact': {
                        'has_impact': False,
                        'impact_score': 0
                    }
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))