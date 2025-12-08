from typing import Dict, Any, List
from datetime import datetime
from .base_calculator import BaseCalculator
from .nakshatra_calculator import NakshatraCalculator
from .yogi_calculator import YogiCalculator
from .badhaka_calculator import BadhakaCalculator
from .gandanta_calculator import GandantaCalculator
from panchang.panchang_calculator import PanchangCalculator

class TradingLuckCalculator(BaseCalculator):
    """Financial Luck Engine for Stock Market Trading"""
    
    NAKSHATRA_NATURES = {
        1: 'Swift', 8: 'Swift', 13: 'Swift',
        5: 'Soft', 14: 'Soft', 17: 'Soft', 27: 'Soft',
        6: 'Fierce', 9: 'Fierce', 18: 'Fierce', 19: 'Fierce',
        4: 'Fixed', 12: 'Fixed', 21: 'Fixed', 26: 'Fixed',
        7: 'Movable', 15: 'Movable', 22: 'Movable', 23: 'Movable', 24: 'Movable',
        3: 'Mixed', 16: 'Mixed',
        2: 'Cruel', 10: 'Cruel', 11: 'Cruel', 20: 'Cruel', 25: 'Cruel'
    }

    def __init__(self, natal_chart: Dict, transit_chart: Dict, birth_data: Dict, transit_date: datetime, natal_ashtakavarga: Dict = None):
        super().__init__(natal_chart)
        self.natal = natal_chart
        self.transit = transit_chart
        self.birth_data = birth_data
        self.transit_date = transit_date
        self.sav = natal_ashtakavarga
        
    def calculate_trading_forecast(self) -> Dict[str, Any]:
        # Basic Moon Data
        natal_moon_lon = self.natal['planets']['Moon']['longitude']
        transit_moon_lon = self.transit['planets']['Moon']['longitude']
        
        natal_nak_id = self._get_nakshatra_id(natal_moon_lon)
        transit_nak_id = self._get_nakshatra_id(transit_moon_lon)
        
        natal_sign_id = int(natal_moon_lon / 30)
        transit_sign_id = int(transit_moon_lon / 30)
        
        # Core Calculators
        tara_bala = self._calculate_tara_bala(natal_nak_id, transit_nak_id)
        chandra_bala = self._calculate_chandra_bala(natal_sign_id, transit_sign_id)
        sav_strength = self._get_sav_strength(transit_sign_id)
        nak_nature = self._analyze_nakshatra_nature(transit_nak_id)
        
        # Risk Checks
        risks = self._check_advanced_risks(transit_moon_lon, transit_sign_id, transit_nak_id)
        
        # Final Score
        base_score = (tara_bala['score'] * 0.4) + (chandra_bala['score'] * 0.3) + (sav_strength['score'] * 0.3)
        
        final_score = base_score
        for risk in risks:
            final_score -= risk['penalty']
        
        final_score = max(0, final_score)
        
        # Recommendation
        verdict = self._get_recommendation(final_score, tara_bala, chandra_bala, risks)
        
        return {
            "date": self.transit_date.strftime('%Y-%m-%d'),
            "luck_score": round(final_score, 1),
            "signal": verdict['signal'],
            "action": verdict['action'],
            "headline": verdict['reason'],
            "market_mood": nak_nature,
            "risk_factors": risks,
            "details": {
                "tara_bala": tara_bala,
                "chandra_bala": chandra_bala,
                "ashtakavarga": sav_strength
            }
        }

    def _check_advanced_risks(self, transit_moon_lon: float, transit_sign_id: int, transit_nak_id: int) -> list:
        risks = []
        
        # Gandanta Check
        gandanta_calc = GandantaCalculator(self.transit)
        moon_gandanta = gandanta_calc._check_planet_gandanta('Moon', transit_moon_lon)
        if moon_gandanta['is_gandanta']:
            risks.append({
                "type": "GANDANTA",
                "name": moon_gandanta['gandanta_name'],
                "desc": "Moon is in a Karmic Knot (Gandanta). Extreme volatility expected.",
                "penalty": 40
            })

        # Badhaka Check
        asc_sign = int(self.natal['ascendant'] / 30)
        badhaka_calc = BadhakaCalculator(self.natal)
        badhaka_house = badhaka_calc.get_badhaka_house(asc_sign)
        badhaka_sign = (asc_sign + badhaka_house - 1) % 12
        
        if transit_sign_id == badhaka_sign:
            risks.append({
                "type": "BADHAKA",
                "name": "Badhaka Sign",
                "desc": "Moon is in your Badhaka (Obstacle) sign. Unexpected glitches likely.",
                "penalty": 20
            })

        # Yogi/Avayogi Check
        yogi_calc = YogiCalculator(self.natal)
        yogi_data = yogi_calc.calculate_yogi_points(self.birth_data)
        
        avayogi_lon = yogi_data['avayogi']['longitude']
        avayogi_nak = self._get_nakshatra_id(avayogi_lon)
        
        if transit_nak_id == avayogi_nak:
            risks.append({
                "type": "AVAYOGI",
                "name": "Avayogi Star",
                "desc": "Moon touches your Point of Pain. Stop-losses will likely hit.",
                "penalty": 30
            })
            
        # Tithi Shunya Check
        try:
            panchang_calc = PanchangCalculator()
            tz = self.birth_data.get('timezone', 'UTC+5:30') 
            panchang = panchang_calc.calculate_panchang(
                self.transit_date.strftime('%Y-%m-%d'), 
                self.birth_data.get('latitude', 28.61), 
                self.birth_data.get('longitude', 77.20), 
                str(tz)
            )
            tithi_num = panchang['tithi']['number']
            
            tithi_shunya_signs = {
                1: [11], 2: [5], 3: [6], 4: [7], 5: [8], 6: [9], 7: [10], 8: [11],
                9: [0], 10: [1], 11: [2], 12: [3], 13: [4], 14: [5], 15: [6],
                16: [11], 17: [5], 18: [6], 19: [7], 20: [8], 21: [9], 22: [10], 23: [11],
                24: [0], 25: [1], 26: [2], 27: [3], 28: [4], 29: [5], 30: [6]
            }
            
            zero_signs = tithi_shunya_signs.get(tithi_num, [])
            if transit_sign_id in zero_signs:
                risks.append({
                    "type": "TITHI_SHUNYA",
                    "name": "Zero Sign",
                    "desc": "Moon is in a Burnt Sign (Dagdha Rashi). Efforts yield no results.",
                    "penalty": 25
                })
        except Exception as e:
            # Fail silently on panchang error to allow main forecast
            print(f"Warning: Tithi check failed: {e}")

        return risks

    def _get_nakshatra_id(self, longitude):
        return int(longitude / (360/27)) + 1

    def _analyze_nakshatra_nature(self, nak_id):
        nature = self.NAKSHATRA_NATURES.get(nak_id, 'Mixed')
        strategies = {
            'Swift': "Scalping & Momentum. Fast entries/exits recommended.",
            'Soft': "Accumulation. Good for buying delivery.",
            'Fierce': "High Volatility. Good for Puts/Shorting.",
            'Fixed': "Low Volatility. Avoid Options buying.",
            'Movable': "Trend Following. Ride the wave.",
            'Cruel': "Choppy/Traps. High risk of stop-loss hunting.",
            'Mixed': "Range-bound. Trade support/resistance."
        }
        return {"nature": nature, "strategy": strategies.get(nature, "Caution.")}

    def _calculate_tara_bala(self, natal_nak, transit_nak):
        distance = (transit_nak - natal_nak)
        if distance < 0: distance += 27
        distance += 1 
        tara_value = distance % 9
        if tara_value == 0: tara_value = 9
        
        tara_map = {
            1: {"name": "Janma", "quality": "Neutral", "score": 40},
            2: {"name": "Sampat", "quality": "Excellent", "score": 100},
            3: {"name": "Vipat", "quality": "Danger", "score": 0},
            4: {"name": "Kshema", "quality": "Good", "score": 80},
            5: {"name": "Pratyak", "quality": "Obstacle", "score": 10},
            6: {"name": "Sadhana", "quality": "Excellent", "score": 90},
            7: {"name": "Naidhana", "quality": "Critical", "score": 0},
            8: {"name": "Mitra", "quality": "Good", "score": 75},
            9: {"name": "Parama Mitra", "quality": "Excellent", "score": 95}
        }
        return tara_map[tara_value]

    def _calculate_chandra_bala(self, natal_sign, transit_sign):
        distance = ((transit_sign - natal_sign) % 12) + 1
        if distance == 8: return {"score": 0, "quality": "Chandrashtama", "transit_house_from_natal": 8}
        elif distance == 12: return {"score": 20, "quality": "Losses", "transit_house_from_natal": 12}
        elif distance in [6, 3, 10, 11]: return {"score": 100, "quality": "Excellent", "transit_house_from_natal": distance}
        return {"score": 50, "quality": "Average", "transit_house_from_natal": distance}

    def _get_sav_strength(self, transit_sign_index):
        points = 28
        if self.sav and 'd1_rashi' in self.sav:
             sav = self.sav['d1_rashi'].get('sarvashtakavarga', [])
             if isinstance(sav, dict): points = sav.get(transit_sign_index, 28)
             elif isinstance(sav, list): points = sav[transit_sign_index]
        score = 0 if points < 20 else (100 if points > 30 else 50)
        return {"points": points, "score": score}

    def _get_recommendation(self, score, tara, chandra, risks):
        # Hard Kill Switches
        if any(r['type'] == 'GANDANTA' for r in risks):
            return {"signal": "RED", "action": "NO TRADE", "reason": "Market in Gandanta (Karmic Knot). Extreme unpredictability."}
        
        if chandra['quality'] == 'Chandrashtama':
            return {"signal": "RED", "action": "NO TRADE", "reason": "Moon in 8th House. Your psychology is your enemy today."}
            
        if any(r['type'] == 'AVAYOGI' for r in risks):
            return {"signal": "ORANGE", "action": "AVOID", "reason": "Avayogi (Obstacle) Star active. Unexpected losses likely."}

        if tara['score'] < 20: 
            return {"signal": "ORANGE", "action": "AVOID", "reason": f"Negative Star ({tara['name']}) active."}

        # Score Based
        if score >= 75:
            return {"signal": "GREEN", "action": "AGGRESSIVE", "reason": "High Luck Score. Strong SAV + Favorable Star."}
        elif score >= 50:
            return {"signal": "YELLOW", "action": "CAUTIOUS", "reason": "Moderate conditions. Reduce position size."}
        else:
            return {"signal": "ORANGE", "action": "AVOID", "reason": "Low Luck Score. Not worth the risk."}