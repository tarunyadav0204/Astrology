# calculators/financial/market_scanner.py
import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, List
from .sector_mapper import SECTOR_RULES
from .aspect_analyzer import AspectAnalyzer
from .vedha_calculator import VedhaCalculator

class MarketScanner:
    """Scans planetary transits for 5 years to find Bull/Bear cycles"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.aspect_analyzer = AspectAnalyzer()
        self.vedha_calc = VedhaCalculator()
    
    def generate_forecast(self, start_year: int = 2025, years: int = 5) -> Dict[str, List[Dict]]:
        """Main runner - returns timeline for each sector"""
        start_date = datetime(start_year, 1, 1)
        end_date = start_date + timedelta(days=365 * years)
        
        print(f"📈 Scanning Markets from {start_date.date()} to {end_date.date()}...")
        
        step_days = 1  # 1 day for perfect accuracy - catches all Moon transits (Moon changes sign every 2.25 days)
        current_date = start_date
        timeline = {sector: [] for sector in SECTOR_RULES.keys()}
        active_periods = {sector: None for sector in SECTOR_RULES.keys()}
        
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
            planets = self._get_planetary_positions(jd)
            aspects = self.aspect_analyzer.get_all_aspects(planets)
            
            for sector, rules in SECTOR_RULES.items():
                ruler_name = rules['ruler']
                ruler = planets[ruler_name]
                
                status, score, reason = self._analyze_sector(sector, rules, ruler, planets, aspects)
                
                current_active = active_periods[sector]
                
                if current_active is None:
                    active_periods[sector] = {
                        "trend": status,
                        "score": score,
                        "start_date": current_date.isoformat(),
                        "reason": reason
                    }
                else:
                    if status != current_active['trend']:
                        if current_active['trend'] != "NEUTRAL":
                            timeline[sector].append({
                                "start": current_active['start_date'],
                                "end": current_date.isoformat(),
                                "trend": current_active['trend'],
                                "intensity": "High" if abs(current_active['score']) > 2 else "Moderate",
                                "reason": current_active['reason']
                            })
                        
                        active_periods[sector] = {
                            "trend": status,
                            "score": score,
                            "start_date": current_date.isoformat(),
                            "reason": reason
                        }
            
            current_date += timedelta(days=step_days)
        
        # Close open periods
        for sector, active in active_periods.items():
            if active and active['trend'] != "NEUTRAL":
                timeline[sector].append({
                    "start": active['start_date'],
                    "end": end_date.isoformat(),
                    "trend": active['trend'],
                    "intensity": "High" if abs(active['score']) > 2 else "Moderate",
                    "reason": active['reason']
                })
        
        return timeline
    
    def _analyze_sector(self, sector, rules, ruler, all_planets, aspects):
        """Returns: (status, score, reason)"""
        score = 0
        reasons = []
        
        # 1. Sign Strength
        sign_num = ruler['sign']
        if sign_num in rules['bullish_signs']:
            score += 2
            reasons.append(f"{rules['ruler']} strong in sign")
        elif sign_num in rules['bearish_signs']:
            score -= 2
            reasons.append(f"{rules['ruler']} weak in sign")
        
        # 2. Retrograde Check (Chesta Bala - Vedic)
        if ruler.get('retrograde', False):
            # Benefics gain strength when retrograde (Chesta Bala)
            if rules['ruler'] in ['Jupiter', 'Venus', 'Mercury']:
                score += 1.0
                reasons.append(f"{rules['ruler']} Retrograde (Chesta Bala Strong)")
            else:
                # Malefics become more cruel when retrograde (Vakra)
                score -= 1.5
                reasons.append(f"{rules['ruler']} Retrograde (Vakra/Cruel)")
        
        # 3. Nakshatra Check
        if ruler.get('nakshatra') in rules['nakshatras']:
            score += 1
            reasons.append(f"Favorable nakshatra")
        
        # 4. Conjunctions
        for benefic in rules['benefics']:
            if all_planets[benefic]['sign'] == ruler['sign']:
                score += 1
                reasons.append(f"{rules['ruler']} joined by {benefic}")
        
        for malefic in rules['malefics']:
            if all_planets[malefic]['sign'] == ruler['sign']:
                score -= 1.5
                reasons.append(f"{rules['ruler']} afflicted by {malefic}")
        
        # 5. Vedic Aspects (Drishti)
        def get_house_dist(p1_sign, p2_sign):
            """Calculate house distance (1-12) from planet1 to planet2"""
            return ((p2_sign - p1_sign) % 12) + 1
        
        for planet_name, planet_data in all_planets.items():
            if planet_name == rules['ruler']:
                continue  # Don't aspect self
            
            # Distance from aspecting planet to ruler
            dist = get_house_dist(planet_data['sign'], ruler['sign'])
            
            is_aspecting = False
            
            # Standard 7th House Aspect (All planets)
            if dist == 7:
                is_aspecting = True
            
            # Special Vedic Aspects
            if planet_name == 'Mars' and dist in [4, 8]:
                is_aspecting = True
            if planet_name == 'Saturn' and dist in [3, 10]:
                is_aspecting = True
            if planet_name == 'Jupiter' and dist in [5, 9]:
                is_aspecting = True
            if planet_name in ['Rahu', 'Ketu'] and dist in [5, 9]:
                is_aspecting = True  # Trinal aspect
            
            if is_aspecting:
                if planet_name in rules['benefics']:
                    score += 1.5
                    reasons.append(f"Vedic Aspect from {planet_name}")
                elif planet_name in rules['malefics']:
                    score -= 2.0  # Malefic aspects are heavy
                    reasons.append(f"Vedic Aspect from {planet_name}")
        
        # 6. Combustion
        if rules['ruler'] not in ['Sun', 'Rahu', 'Ketu']:
            sun_long = all_planets['Sun']['longitude']
            ruler_long = ruler['longitude']
            diff = abs(sun_long - ruler_long)
            if diff > 180:
                diff = 360 - diff
            if diff < 6:
                score -= 2
                reasons.append("Combust")
        
        # 7. SBC Vedha Check (Nakshatra Piercing)
        for planet_name, planet_data in all_planets.items():
            if planet_name == rules['ruler']:
                continue
            
            planet_speed = planet_data.get('speed', 0)
            planet_long = planet_data['longitude']
            
            for sector_nak in rules['nakshatras']:
                hit = self.vedha_calc.check_vedha(
                    planet_long,
                    planet_speed,
                    sector_nak
                )
                
                if hit:
                    is_malefic = planet_name in rules['malefics']
                    is_benefic = planet_name in rules['benefics']
                    
                    if is_malefic:
                        score -= 1.5
                        reasons.append(f"Vedha: {planet_name} piercing {sector_nak}")
                    elif is_benefic:
                        score += 0.5
                        reasons.append(f"Vedha: {planet_name} blessing {sector_nak}")
        
        # Verdict
        if score >= 1.5:
            return "BULLISH", score, ", ".join(reasons)
        elif score <= -1.5:
            return "BEARISH", score, ", ".join(reasons)
        else:
            return "NEUTRAL", score, "Normal transit"
    
    def _get_planetary_positions(self, jd):
        """Get all planet positions with retrograde and nakshatra"""
        planets = {}
        mapping = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN,
            'Rahu': swe.MEAN_NODE
        }
        
        nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        
        for name, pid in mapping.items():
            result = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            pos = result[0][0]
            speed = result[0][3]
            
            if name == 'Rahu':
                pos = (pos + 180) % 360  # Ketu
            
            nakshatra_num = int(pos / (360/27))
            
            planets[name] = {
                'longitude': pos,
                'sign': int(pos / 30),
                'retrograde': speed < 0,
                'nakshatra': nakshatra_names[nakshatra_num],
                'speed': speed  # Store speed for Vedha calculations
            }
        
        # Add Ketu
        planets['Ketu'] = {
            'longitude': (planets['Rahu']['longitude'] + 180) % 360,
            'sign': int(((planets['Rahu']['longitude'] + 180) % 360) / 30),
            'retrograde': True,
            'nakshatra': nakshatra_names[int(((planets['Rahu']['longitude'] + 180) % 360) / (360/27))],
            'speed': -planets['Rahu']['speed']  # Ketu moves opposite to Rahu
        }
        
        return planets
