"""
Karma Context Builder - Complete Past Life Karma Analysis
Integrates D60, Nadi, Jaimini, Badhaka, Gandanta, Mrityu Bhaga, Vargottama
"""

from typing import Dict, Any, List
from .chara_karaka_calculator import CharaKarakaCalculator
from .badhaka_calculator import BadhakaCalculator
from .gandanta_calculator import GandantaCalculator
from .mrityu_bhaga_calculator import MrityuBhagaCalculator
from .vargottama_calculator import VargottamaCalculator
from .nadi_linkage_calculator import NadiLinkageCalculator
from .nakshatra_calculator import NakshatraCalculator

class KarmaContextBuilder:
    """Comprehensive Past Life Karma and Soul Mission Analysis"""
    
    # Complete 60 Shashtiamsa Deities (D60)
    SHASHTIAMSA_DEITIES = {
        0: ("Ghora", "Cruel", "Past life aggression, severe challenges, warrior karma"),
        1: ("Rakshasa", "Demonic", "Overindulgence, ego-driven pursuits, material obsession"),
        2: ("Deva", "Divine", "Merit from selfless service, worship, spiritual practices"),
        3: ("Kubera", "Wealthy", "Resource management, charity, wealth stewardship"),
        4: ("Yaksha", "Guardian", "Protection of family values, secret knowledge keeper"),
        5: ("Kinnara", "Celestial Musician", "Arts, culture, music, creative expression"),
        6: ("Brahma", "Creator", "Knowledge creation, teaching, intellectual pursuits"),
        7: ("Vishnu", "Preserver", "Dharma protection, justice, maintaining order"),
        8: ("Rudra", "Destroyer", "Transformation, destruction of evil, intense change"),
        9: ("Kala", "Time", "Patience, timing mastery, understanding cycles"),
        10: ("Yama", "Death Lord", "Justice, karmic balance, life-death understanding"),
        11: ("Kinnara", "Half-human", "Dual nature, adaptability, artistic soul"),
        12: ("Pitru", "Ancestor", "Ancestral blessings, lineage karma, family duties"),
        13: ("Matru", "Mother", "Nurturing, maternal energy, emotional healing"),
        14: ("Indra", "King of Gods", "Leadership, authority, royal karma"),
        15: ("Agni", "Fire", "Purification, transformation, spiritual fire"),
        16: ("Vayu", "Wind", "Movement, change, communication, breath of life"),
        17: ("Varuna", "Water", "Emotional depth, healing, flow, adaptability"),
        18: ("Mitra", "Friend", "Friendship, alliances, social connections"),
        19: ("Aryama", "Nobility", "Noble conduct, aristocratic karma, refinement"),
        20: ("Bhaga", "Fortune", "Luck, prosperity, divine grace"),
        21: ("Vivasvan", "Sun", "Illumination, clarity, soul consciousness"),
        22: ("Pushan", "Nourisher", "Nourishment, growth, sustenance provider"),
        23: ("Tvashtri", "Craftsman", "Skill, craftsmanship, technical mastery"),
        24: ("Vishvakarma", "Divine Architect", "Building, construction, design"),
        25: ("Soma", "Moon Nectar", "Bliss, contentment, spiritual nourishment"),
        26: ("Ashwini", "Horse Twins", "Healing, speed, medical knowledge"),
        27: ("Yama", "Restraint", "Self-control, discipline, moral strength"),
        28: ("Gandharva", "Celestial Singer", "Music, arts, divine entertainment"),
        29: ("Apsara", "Celestial Dancer", "Beauty, grace, artistic performance"),
        30: ("Naga", "Serpent", "Kundalini, occult knowledge, hidden wisdom"),
        31: ("Sarpa", "Snake", "Transformation, shedding old patterns"),
        32: ("Preta", "Ghost", "Unfinished business, attachments, past regrets"),
        33: ("Pishacha", "Demon", "Addictions, obsessions, lower desires"),
        34: ("Deva", "God", "Divine blessings, spiritual merit"),
        35: ("Daitya", "Titan", "Power struggles, ambition, material strength"),
        36: ("Danava", "Demon", "Opposition, challenges, adversarial karma"),
        37: ("Manushya", "Human", "Balanced karma, human experiences"),
        38: ("Vanara", "Monkey", "Service, devotion, loyalty (Hanuman energy)"),
        39: ("Poornachandra", "Full Moon", "Complete emotional fulfillment, lunar blessings, nurturing mastery"),
        40: ("Kimpurusha", "Half-man", "Dual nature, transformation"),
        41: ("Siddha", "Perfected Being", "Spiritual attainment, mastery"),
        42: ("Vidyadhara", "Knowledge Holder", "Wisdom, learning, teaching"),
        43: ("Charana", "Wanderer", "Travel, exploration, seeking"),
        44: ("Gandharva", "Celestial", "Music, arts, divine connection"),
        45: ("Yaksha", "Nature Spirit", "Nature connection, elemental wisdom"),
        46: ("Rakshasa", "Protector", "Fierce protection, guardian energy"),
        47: ("Pishacha", "Spirit", "Subtle realm, psychic abilities"),
        48: ("Preta", "Ancestor Spirit", "Ancestral connection, lineage"),
        49: ("Brahma", "Creator", "Creative power, manifestation"),
        50: ("Vishnu", "Sustainer", "Preservation, maintenance, stability"),
        51: ("Maheshwara", "Great Lord", "Transcendence, liberation"),
        52: ("Surya", "Sun", "Vitality, life force, consciousness"),
        53: ("Chandra", "Moon", "Emotions, mind, receptivity"),
        54: ("Angaraka", "Mars", "Courage, action, warrior spirit"),
        55: ("Budha", "Mercury", "Intelligence, communication, trade"),
        56: ("Guru", "Jupiter", "Wisdom, teaching, expansion"),
        57: ("Shukra", "Venus", "Love, beauty, relationships"),
        58: ("Shani", "Saturn", "Discipline, karma, service"),
        59: ("Indu", "Moon Nectar", "Comfort, nourishment, emotional fulfillment")
    }
    
    # D60 Deity Benefic/Malefic Classification (BPHS)
    DEITY_NATURE = {
        # Malefic Deities (Past Life Negative Karma)
        0: "Malefic", 1: "Malefic", 8: "Malefic", 10: "Malefic", 27: "Malefic",
        32: "Malefic", 33: "Malefic", 35: "Malefic", 36: "Malefic", 46: "Malefic", 47: "Malefic",
        
        # Benefic Deities (Past Life Positive Karma)
        2: "Benefic", 3: "Benefic", 6: "Benefic", 7: "Benefic", 12: "Benefic", 13: "Benefic",
        14: "Benefic", 20: "Benefic", 21: "Benefic", 25: "Benefic", 34: "Benefic", 41: "Benefic",
        42: "Benefic", 49: "Benefic", 50: "Benefic", 51: "Benefic", 52: "Benefic", 53: "Benefic",
        56: "Benefic", 57: "Benefic", 59: "Benefic",
        
        # Mixed/Neutral Deities
        # All others default to "Mixed"
    }
    
    # Nakshatra Past Life Occupations
    NAKSHATRA_KARMA = {
        'Ashwini': 'Healer, physician, veterinarian, emergency responder, pioneer',
        'Bharani': 'Judge, midwife, death worker, creative artist, fertility specialist',
        'Krittika': 'Teacher, critic, purifier, military commander, chef',
        'Rohini': 'Farmer, artist, luxury merchant, beauty specialist, creator',
        'Mrigashira': 'Explorer, researcher, traveler, seeker, communicator',
        'Ardra': 'Storm worker, transformer, scientist, revolutionary, healer',
        'Punarvasu': 'Philosopher, teacher, spiritual guide, restorer, counselor',
        'Pushya': 'Nurturer, priest, spiritual teacher, organizer, caretaker',
        'Ashlesha': 'Mystic, psychologist, serpent charmer, occultist, healer',
        'Magha': 'King, royal administrator, ancestor worshipper, ceremonial priest',
        'Purva Phalguni': 'Entertainer, artist, pleasure provider, creative performer',
        'Uttara Phalguni': 'Helper, supporter, partnership facilitator, organizer',
        'Hasta': 'Craftsman, artisan, healer, skilled worker, surgeon',
        'Chitra': 'Architect, designer, jeweler, artist, creator of beauty',
        'Swati': 'Merchant, trader, diplomat, negotiator, independent businessperson',
        'Vishakha': 'Goal achiever, leader, competitor, strategic planner',
        'Anuradha': 'Friend, devotee, organizer, relationship builder, diplomat',
        'Jyeshtha': 'Elder, protector, authority figure, guardian, administrator',
        'Mula': 'Root investigator, philosopher, researcher, destroyer of falsehood',
        'Purva Ashadha': 'Purifier, influential leader, water worker, invincible warrior',
        'Uttara Ashadha': 'Ethical leader, long-term planner, righteous warrior, supporter',
        'Shravana': 'Listener, scholar, knowledge preserver, communicator, teacher',
        'Dhanishta': 'Musician, performer, group leader, wealth creator, rhythmic artist',
        'Shatabhisha': 'Healer, researcher, independent worker, mystery solver, innovator',
        'Purva Bhadrapada': 'Spiritual transformer, mystic, intense healer, philosopher',
        'Uttara Bhadrapada': 'Deep counselor, foundational worker, stable guide, wisdom keeper',
        'Revati': 'Nurturer, journey completer, caretaker, prosperity provider'
    }
    
    # Nadi Planetary Pair Interpretations
    NADI_PAIRS = {
        ('Saturn', 'Jupiter'): 'Dharma-Karma Adhipati: Soul of management, teaching, balancing duty and wisdom',
        ('Saturn', 'Mars'): 'Technical Master: Warrior karma, engineering, mechanical skills, discipline in action',
        ('Saturn', 'Ketu'): 'Moksha Yoga: Spiritual liberation path, detachment, past life renunciation',
        ('Saturn', 'Venus'): 'Delayed Beauty: Artistic discipline, late marriage, mature relationships',
        ('Saturn', 'Mercury'): 'Structured Mind: Systematic thinking, research, detailed work',
        ('Saturn', 'Sun'): 'Father-Authority Karma: Government service, leadership through discipline',
        ('Saturn', 'Moon'): 'Emotional Maturity: Late emotional development, responsible nurturing',
        ('Moon', 'Mars'): 'Emotional Warrior: Mother-son karma, protective instincts, emotional courage',
        ('Moon', 'Mercury'): 'Emotional Intelligence: Sensitive communication, intuitive thinking',
        ('Moon', 'Jupiter'): 'Emotional Wisdom: Nurturing teacher, compassionate guide',
        ('Moon', 'Venus'): 'Emotional Beauty: Artistic sensitivity, loving nature, aesthetic sense',
        ('Venus', 'Jupiter'): 'Wealth Through Relationships: Marriage blessings, prosperity, luxury',
        ('Venus', 'Mars'): 'Passionate Love: Intense relationships, creative energy, artistic passion',
        ('Venus', 'Mercury'): 'Artistic Communication: Creative writing, beautiful speech, design',
        ('Venus', 'Rahu'): 'Obsessive Relationships: Foreign spouse, unconventional love, material desires',
        ('Mercury', 'Jupiter'): 'Knowledge Transmission: Teaching karma, writing, intellectual expansion',
        ('Mercury', 'Mars'): 'Sharp Mind: Quick thinking, debate, technical communication',
        ('Mars', 'Jupiter'): 'Righteous Action: Dharmic warrior, protective teacher, principled fighter',
        ('Mars', 'Ketu'): 'Past Life Warrior: Technical occult knowledge, spiritual combat, detached action',
        ('Jupiter', 'Ketu'): 'Spiritual Wisdom: Past life guru, detached teaching, moksha path',
        ('Sun', 'Moon'): 'Soul-Mind Unity: Integrated personality, balanced ego and emotions',
        ('Sun', 'Mars'): 'Leadership Power: Authoritative action, commanding presence, royal warrior',
        ('Sun', 'Jupiter'): 'Divine Authority: Spiritual leadership, wise ruler, dharmic guide',
        ('Sun', 'Venus'): 'Creative Authority: Artistic leadership, refined power, diplomatic ruler',
        ('Rahu', 'Ketu'): 'Karmic Axis: Major soul evolution, destiny path, life purpose'
    }
    
    def __init__(self, chart_data: Dict[str, Any], divisional_charts: Dict[str, Any] = None):
        self.chart_data = chart_data
        self.divisional_charts = divisional_charts or {}
        
        # Initialize calculators
        self.chara_karaka_calc = CharaKarakaCalculator(chart_data)
        self.badhaka_calc = BadhakaCalculator(chart_data)
        self.gandanta_calc = GandantaCalculator(chart_data)
        self.mrityu_calc = MrityuBhagaCalculator(chart_data)
        self.nadi_calc = NadiLinkageCalculator(chart_data)
        self.nakshatra_calc = NakshatraCalculator(chart_data=chart_data)
        
        if divisional_charts:
            self.vargottama_calc = VargottamaCalculator(chart_data, divisional_charts)
        else:
            self.vargottama_calc = None
    
    def get_complete_karma_context(self) -> Dict[str, Any]:
        """Generate complete karmic analysis with raw charts"""
        return {
            # Raw charts for Gemini to analyze directly
            "d1_chart": self._add_sign_names(self.chart_data),
            "d9_navamsa": self._add_sign_names(self.divisional_charts.get('d9_navamsa', {})),
            "d60_shashtiamsa": self._add_sign_names(self.divisional_charts.get('d60_shashtiamsa', {})),
            
            # Calculated karma insights
            "soul_identity": self._analyze_d60_essence(),
            "soul_desire": self._analyze_atmakaraka(),
            "nakshatra_karma": self._analyze_nakshatra_karma(),
            "karmic_patterns": self._analyze_saturn_nadi_links(),
            "unfinished_debts": self._analyze_retrograde_planets(),
            "soul_talents": self._analyze_karkamsa_skills(),
            "destiny_axis": self._analyze_rahu_ketu_axis(),
            "dharma_evolution": self._analyze_d9_comparison(),
            "karmic_obstacles": self._analyze_badhaka(),
            "soul_junctions": self._analyze_gandanta(),
            "vulnerable_points": self._analyze_mrityu_bhaga(),
            "soul_continuity": self._analyze_vargottama(),
            "ancestral_karma": self._analyze_pitru_dosha(),
            "maternal_karma": self._analyze_matru_dosha(),
            "poorva_punya": self._analyze_5th_house(),
            "eighth_house_secrets": self._analyze_8th_house(),
            "bhagya_karma": self._analyze_9th_house(),
            "moksha_indicators": self._analyze_12th_house(),
            "karmic_timing": self._get_karmic_timing_summary()
        }
    
    def _analyze_d60_essence(self) -> Dict:
        """D60 Shashtiamsa - Soul's essence from past karma"""
        d60_data = self.divisional_charts.get('d60_shashtiamsa', {})
        
        if not d60_data:
            return {"available": False, "message": "D60 chart not calculated"}
        
        d60_asc = d60_data.get('ascendant', 0) % 30
        deity_idx = int(d60_asc / 0.5)  # 0.5° per deity, 60 divisions in 30°
        
        deity_name, nature, theme = self.SHASHTIAMSA_DEITIES.get(
            deity_idx, ("Unknown", "Neutral", "General karma")
        )
        
        # Get deity benefic/malefic classification
        deity_classification = self.DEITY_NATURE.get(deity_idx, "Mixed")
        
        result = {
            "lagna_deity": deity_name,
            "lagna_nature": nature,
            "lagna_theme": theme,
            "lagna_classification": deity_classification,
            "ascendant_degree": round(d60_asc, 2),
            "deity_index": deity_idx,
            "significance": "D60 Lagna shows the vessel, Atmakaraka shows the soul within (BPHS Ch.6)"
        }
        
        # Add Atmakaraka in D60 with nakshatra
        ak_data = self.chara_karaka_calc.get_atmakaraka()
        if ak_data:
            ak_planet = ak_data['planet']
            print(f"DEBUG: AK planet = {ak_planet}")
            print(f"DEBUG: d60_data keys = {d60_data.keys()}")
            print(f"DEBUG: d60_data.get('planets') = {d60_data.get('planets')}")
            
            if d60_data.get('planets'):
                ak_d60 = d60_data['planets'].get(ak_planet, {})
                print(f"DEBUG: ak_d60 = {ak_d60}")
                ak_longitude = ak_d60.get('longitude', 0)
                print(f"DEBUG: ak_longitude = {ak_longitude}")
                
                if ak_longitude > 0:
                    ak_degree = ak_longitude % 30
                    ak_deity_idx = int(ak_degree / 0.5)
                    ak_deity_name, ak_nature, ak_theme = self.SHASHTIAMSA_DEITIES.get(
                        ak_deity_idx, ("Unknown", "Neutral", "General karma")
                    )
                    ak_classification = self.DEITY_NATURE.get(ak_deity_idx, "Mixed")
                    
                    # Calculate nakshatra from longitude
                    nakshatra_span = 360 / 27
                    nakshatra_index = int(ak_longitude / nakshatra_span)
                    nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
                                 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
                                 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
                                 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
                                 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
                    ak_d60_nakshatra = nakshatras[min(nakshatra_index, 26)]
                    
                    result["atmakaraka_deity"] = ak_deity_name
                    result["atmakaraka_nature"] = ak_nature
                    result["atmakaraka_theme"] = ak_theme
                    result["atmakaraka_classification"] = ak_classification
                    result["atmakaraka_planet"] = ak_planet
                    result["atmakaraka_d60_nakshatra"] = ak_d60_nakshatra
                    result["karmic_balance"] = self._calculate_karmic_balance(deity_classification, ak_classification)
        
        return result
    
    def _analyze_nakshatra_karma(self) -> Dict:
        """Nakshatra-based karmic imprints from subconscious"""
        nakshatra_positions = self.nakshatra_calc.calculate_nakshatra_positions()
        
        ak_data = self.chara_karaka_calc.get_atmakaraka()
        ak_nakshatra = None
        ak_occupation = None
        if ak_data:
            ak_planet = ak_data['planet']
            ak_nakshatra = nakshatra_positions.get(ak_planet, {}).get('nakshatra_name')
            ak_occupation = self.NAKSHATRA_KARMA.get(ak_nakshatra, 'Unknown')
        
        ketu_nakshatra = nakshatra_positions.get('Ketu', {}).get('nakshatra_name')
        ketu_occupation = self.NAKSHATRA_KARMA.get(ketu_nakshatra, 'Unknown')
        
        moon_nakshatra = nakshatra_positions.get('Moon', {}).get('nakshatra_name')
        moon_occupation = self.NAKSHATRA_KARMA.get(moon_nakshatra, 'Unknown')
        
        # Ganda Moola (Gandanta) calculation - CORRECTED
        # Only specific degrees at Fire-Water junctions, not entire nakshatras
        print(f"\n🔮 GANDA MOOLA (GANDANTA) CHECK")
        
        # Get Moon longitude
        moon_data = self.chart_data.get('planets', {}).get('Moon', {})
        moon_longitude = moon_data.get('longitude', 0)
        moon_sign = int(moon_longitude / 30)
        moon_degree_in_sign = moon_longitude % 30
        
        print(f"Moon: {moon_nakshatra} at {moon_sign} sign, {moon_degree_in_sign:.2f}° in sign")
        
        # Check Moon for Gandanta (last 3°20' or first 3°20' of junction nakshatras)
        moon_ganda = False
        if moon_nakshatra == 'Ashlesha' and moon_degree_in_sign >= 26.666667:  # Cancer 26°40' - 30°
            moon_ganda = True
            print(f"✓ Moon in Gandanta: Last 3°20' of Ashlesha (Cancer-Leo junction)")
        elif moon_nakshatra == 'Magha' and moon_degree_in_sign <= 3.333333:  # Leo 0° - 3°20'
            moon_ganda = True
            print(f"✓ Moon in Gandanta: First 3°20' of Magha (Cancer-Leo junction)")
        elif moon_nakshatra == 'Jyeshtha' and moon_degree_in_sign >= 26.666667:  # Scorpio 26°40' - 30°
            moon_ganda = True
            print(f"✓ Moon in Gandanta: Last 3°20' of Jyeshtha (Scorpio-Sagittarius junction)")
        elif moon_nakshatra == 'Mula' and moon_degree_in_sign <= 3.333333:  # Sagittarius 0° - 3°20'
            moon_ganda = True
            print(f"✓ Moon in Gandanta: First 3°20' of Mula (Scorpio-Sagittarius junction)")
        elif moon_nakshatra == 'Revati' and moon_degree_in_sign >= 26.666667:  # Pisces 26°40' - 30°
            moon_ganda = True
            print(f"✓ Moon in Gandanta: Last 3°20' of Revati (Pisces-Aries junction)")
        elif moon_nakshatra == 'Ashwini' and moon_degree_in_sign <= 3.333333:  # Aries 0° - 3°20'
            moon_ganda = True
            print(f"✓ Moon in Gandanta: First 3°20' of Ashwini (Pisces-Aries junction)")
        else:
            print(f"✗ Moon NOT in Gandanta")
        
        # Get Lagna longitude
        lagna_longitude = self.chart_data.get('ascendant', 0)
        lagna_sign = int(lagna_longitude / 30)
        lagna_degree_in_sign = lagna_longitude % 30
        
        lagna_nak_info = self.nakshatra_calc.get_ascendant_nakshatra()
        lagna_nakshatra = lagna_nak_info.get('name')
        
        print(f"Lagna: {lagna_nakshatra} at {lagna_sign} sign, {lagna_degree_in_sign:.2f}° in sign")
        
        # Check Lagna for Gandanta
        lagna_ganda = False
        if lagna_nakshatra == 'Ashlesha' and lagna_degree_in_sign >= 26.666667:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: Last 3°20' of Ashlesha (Cancer-Leo junction)")
        elif lagna_nakshatra == 'Magha' and lagna_degree_in_sign <= 3.333333:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: First 3°20' of Magha (Cancer-Leo junction)")
        elif lagna_nakshatra == 'Jyeshtha' and lagna_degree_in_sign >= 26.666667:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: Last 3°20' of Jyeshtha (Scorpio-Sagittarius junction)")
        elif lagna_nakshatra == 'Mula' and lagna_degree_in_sign <= 3.333333:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: First 3°20' of Mula (Scorpio-Sagittarius junction)")
        elif lagna_nakshatra == 'Revati' and lagna_degree_in_sign >= 26.666667:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: Last 3°20' of Revati (Pisces-Aries junction)")
        elif lagna_nakshatra == 'Ashwini' and lagna_degree_in_sign <= 3.333333:
            lagna_ganda = True
            print(f"✓ Lagna in Gandanta: First 3°20' of Ashwini (Pisces-Aries junction)")
        else:
            print(f"✗ Lagna NOT in Gandanta")
        
        print(f"\n🎯 FINAL RESULT: Has Ganda Moola Dosha = {moon_ganda or lagna_ganda}\n")
        
        return {
            "atmakaraka_nakshatra": ak_nakshatra,
            "soul_flavor": f"Soul's intent through {ak_nakshatra}: {ak_occupation}",
            "ketu_nakshatra": ketu_nakshatra,
            "past_life_expertise": f"Innate skill from {ketu_nakshatra}: {ketu_occupation}",
            "moon_nakshatra": moon_nakshatra,
            "emotional_karma": f"Subconscious pattern from {moon_nakshatra}: {moon_occupation}",
            "ganda_moola_moon": moon_ganda,
            "ganda_moola_lagna": lagna_ganda,
            "karmic_knot": "Critical - Soul transitioned at karmic junction, must break ancestral patterns" if (moon_ganda or lagna_ganda) else "None"
        }
    
    def _analyze_atmakaraka(self) -> Dict:
        """Atmakaraka - Soul's primary desire"""
        ak_data = self.chara_karaka_calc.get_atmakaraka()
        
        if not ak_data:
            return {"available": False}
        
        planet = ak_data['planet']
        house = ak_data['house']
        
        ak_meanings = {
            'Sun': 'Soul seeks authority, recognition, leadership, father-like role',
            'Moon': 'Soul seeks emotional fulfillment, nurturing, public connection',
            'Mars': 'Soul seeks courage, action, warrior path, technical mastery',
            'Mercury': 'Soul seeks knowledge, communication, trade, intellectual pursuits',
            'Jupiter': 'Soul seeks wisdom, teaching, dharma, spiritual expansion',
            'Venus': 'Soul seeks beauty, relationships, luxury, artistic expression',
            'Saturn': 'Soul seeks service, discipline, moksha, karmic resolution'
        }
        
        return {
            "planet": planet,
            "house": house,
            "soul_desire": ak_meanings.get(planet, "Unknown desire"),
            "life_purpose": f"Primary life mission through {planet} in house {house}",
            "karmic_focus": ak_data.get('description', '')
        }
    
    def _analyze_rahu_ketu_axis(self) -> Dict:
        """Atmakaraka - Soul's primary desire"""
        ak_data = self.chara_karaka_calc.get_atmakaraka()
        
        if not ak_data:
            return {"available": False}
        
        planet = ak_data['planet']
        house = ak_data['house']
        
        ak_meanings = {
            'Sun': 'Soul seeks authority, recognition, leadership, father-like role',
            'Moon': 'Soul seeks emotional fulfillment, nurturing, public connection',
            'Mars': 'Soul seeks courage, action, warrior path, technical mastery',
            'Mercury': 'Soul seeks knowledge, communication, trade, intellectual pursuits',
            'Jupiter': 'Soul seeks wisdom, teaching, dharma, spiritual expansion',
            'Venus': 'Soul seeks beauty, relationships, luxury, artistic expression',
            'Saturn': 'Soul seeks service, discipline, moksha, karmic resolution'
        }
        
        return {
            "planet": planet,
            "house": house,
            "soul_desire": ak_meanings.get(planet, "Unknown desire"),
            "life_purpose": f"Primary life mission through {planet} in house {house}",
            "karmic_focus": ak_data.get('description', '')
        }
    
    def _analyze_saturn_nadi_links(self) -> List[Dict]:
        """Saturn's Nadi connections - karmic patterns"""
        nadi_links = self.nadi_calc.get_nadi_links()
        saturn_data = nadi_links.get('Saturn', {})
        
        if not saturn_data:
            return []
        
        patterns = []
        connections = saturn_data.get('connections', {})
        
        # Trine connections (strongest)
        for planet in connections.get('trine', []):
            pair_key = tuple(sorted(['Saturn', planet]))
            description = self.NADI_PAIRS.get(pair_key, f"Karmic connection between Saturn and {planet}")
            patterns.append({
                "planet": planet,
                "link_type": "Trine (Strongest)",
                "description": description,
                "strength": "High"
            })
        
        # Next/Prev connections
        for planet in connections.get('next', []):
            patterns.append({
                "planet": planet,
                "link_type": "Next (Future Direction)",
                "description": f"Saturn pushes toward {planet}'s lessons",
                "strength": "Medium"
            })
        
        return patterns
    
    def _analyze_retrograde_planets(self) -> List[Dict]:
        """Retrograde planets - unfinished karmic business"""
        retro_planets = []
        
        retro_meanings = {
            'Mercury': 'Unfinished communication, learning, trade karma',
            'Venus': 'Unfinished relationship, artistic, pleasure karma',
            'Mars': 'Unfinished action, courage, conflict karma',
            'Jupiter': 'Unfinished wisdom, teaching, dharma karma',
            'Saturn': 'Unfinished duty, service, discipline karma'
        }
        
        for planet, data in self.chart_data.get('planets', {}).items():
            if data.get('retrograde') and planet in retro_meanings:
                retro_planets.append({
                    "planet": planet,
                    "house": data.get('house'),
                    "karmic_debt": retro_meanings[planet],
                    "resolution": f"Must revisit and complete {planet}'s significations"
                })
        
        return retro_planets
    
    def _analyze_karkamsa_skills(self) -> Dict:
        """Karkamsa (D9 position of Atmakaraka) - soul talents"""
        ak_data = self.chara_karaka_calc.get_atmakaraka()
        
        if not ak_data:
            return {"available": False}
        
        d9_data = self.divisional_charts.get('d9_navamsa', {})
        if not d9_data:
            return {"available": False, "message": "D9 not calculated"}
        
        ak_planet = ak_data['planet']
        d9_planets = d9_data.get('planets', {})
        ak_d9_position = d9_planets.get(ak_planet, {})
        
        return {
            "atmakaraka": ak_planet,
            "karkamsa_sign": ak_d9_position.get('sign'),
            "karkamsa_house": ak_d9_position.get('house'),
            "soul_skill": f"Past life mastery in {ak_planet} significations",
            "current_expression": "These skills manifest naturally in this life"
        }
    
    def _analyze_rahu_ketu_axis(self) -> Dict:
        """Rahu-Ketu axis - destiny and past mastery"""
        planets = self.chart_data.get('planets', {})
        ketu_data = planets.get('Ketu', {})
        ketu_house = ketu_data.get('house', 0)
        rahu_house = planets.get('Rahu', {}).get('house', 0)
        
        house_themes = {
            1: "self, personality, physical body",
            2: "wealth, family, speech",
            3: "siblings, courage, communication",
            4: "home, mother, emotions",
            5: "children, creativity, intelligence",
            6: "health, service, enemies",
            7: "marriage, partnerships",
            8: "transformation, occult, longevity",
            9: "luck, dharma, higher learning",
            10: "career, reputation, authority",
            11: "gains, friendships, aspirations",
            12: "losses, spirituality, foreign lands"
        }
        
        result = {
            "ketu_house": ketu_house,
            "ketu_legacy": f"Past life mastery in {house_themes.get(ketu_house, 'unknown')}",
            "ketu_message": "These areas come naturally but may feel empty",
            "rahu_house": rahu_house,
            "rahu_mission": f"Current life expansion needed in {house_themes.get(rahu_house, 'unknown')}",
            "rahu_message": "This is where growth and evolution happen",
            "axis_balance": "Move from Ketu comfort zone toward Rahu growth zone"
        }
        
        # Ketu nakshatra monetization check
        ketu_nakshatra = ketu_data.get('nakshatra')
        if ketu_nakshatra:
            nakshatra_lords = {
                'Ashwini': 'Ketu', 'Bharani': 'Venus', 'Krittika': 'Sun',
                'Rohini': 'Moon', 'Mrigashira': 'Mars', 'Ardra': 'Rahu',
                'Punarvasu': 'Jupiter', 'Pushya': 'Saturn', 'Ashlesha': 'Mercury',
                'Magha': 'Ketu', 'Purva Phalguni': 'Venus', 'Uttara Phalguni': 'Sun',
                'Hasta': 'Moon', 'Chitra': 'Mars', 'Swati': 'Rahu',
                'Vishakha': 'Jupiter', 'Anuradha': 'Saturn', 'Jyeshtha': 'Mercury',
                'Mula': 'Ketu', 'Purva Ashadha': 'Venus', 'Uttara Ashadha': 'Sun',
                'Shravana': 'Moon', 'Dhanishta': 'Mars', 'Shatabhisha': 'Rahu',
                'Purva Bhadrapada': 'Jupiter', 'Uttara Bhadrapada': 'Saturn', 'Revati': 'Mercury'
            }
            nak_lord = nakshatra_lords.get(ketu_nakshatra)
            if nak_lord:
                nak_lord_house = planets.get(nak_lord, {}).get('house')
                if nak_lord_house == 10:
                    result["monetizable_skill"] = f"Ketu in {ketu_nakshatra} (lord {nak_lord} in 10th) - past life skill directly monetizable"
        
        return result
    
    def _analyze_d9_comparison(self) -> List[Dict]:
        """D1 vs D9 comparison - karmic evolution"""
        d9_data = self.divisional_charts.get('d9_navamsa', {})
        
        if not d9_data:
            return []
        
        d1_planets = self.chart_data.get('planets', {})
        d9_planets = d9_data.get('planets', {})
        
        evolution = []
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            d1_sign = d1_planets.get(planet, {}).get('sign')
            d9_sign = d9_planets.get(planet, {}).get('sign')
            
            if d1_sign is not None and d9_sign is not None:
                if d1_sign == d9_sign:
                    evolution.append({
                        "planet": planet,
                        "status": "Vargottama",
                        "meaning": f"{planet} shows strong karmic continuity - past life mastery continues"
                    })
                else:
                    evolution.append({
                        "planet": planet,
                        "status": "Evolved",
                        "d1_sign": d1_sign,
                        "d9_sign": d9_sign,
                        "meaning": f"{planet} evolved from sign {d1_sign} to {d9_sign} - karmic growth area"
                    })
        
        return evolution
    
    def _analyze_badhaka(self) -> Dict:
        """Badhaka - karmic obstacles"""
        ascendant_sign = self.chart_data.get('ascendant_sign', 0)
        badhaka_summary = self.badhaka_calc.get_chart_badhaka_summary(ascendant_sign)
        
        badhaka_info = badhaka_summary.get('badhaka', {})
        badhaka_lord = badhaka_info.get('lord')
        
        # Check if currently in Badhaka lord dasha
        current_dasha = self.chart_data.get('current_dasha', {}).get('mahadasha', {}).get('planet')
        is_active = current_dasha == badhaka_lord
        
        return {
            "badhaka_house": badhaka_info.get('house'),
            "badhaka_lord": badhaka_lord,
            "currently_active": is_active,
            "obstacle_type": badhaka_info.get('effects', {}).get('nature'),
            "description": badhaka_info.get('effects', {}).get('description'),
            "remedies": badhaka_info.get('effects', {}).get('remedies', []),
            "karmic_meaning": "Represents a person or situation you hindered in past life, now testing you"
        }
    
    def _analyze_gandanta(self) -> Dict:
        """Gandanta - soul junction points"""
        gandanta_analysis = self.gandanta_calc.calculate_gandanta_analysis()
        
        planets_in_gandanta = gandanta_analysis.get('planets_in_gandanta', [])
        lagna_gandanta = gandanta_analysis.get('lagna_gandanta', {})
        moon_gandanta = gandanta_analysis.get('moon_gandanta', {})
        
        return {
            "planets_affected": [p['planet'] for p in planets_in_gandanta],
            "lagna_in_gandanta": lagna_gandanta.get('is_gandanta', False),
            "moon_in_gandanta": moon_gandanta.get('is_gandanta', False),
            "total_count": len(planets_in_gandanta),
            "significance": "Gandanta indicates soul in transition, karmic knots to untie",
            "details": planets_in_gandanta
        }
    
    def _analyze_mrityu_bhaga(self) -> Dict:
        """Mrityu Bhaga - fatal degrees, closed karmic accounts"""
        mrityu_analysis = self.mrityu_calc.analyze_chart_mrityu_bhaga()
        
        planets_in_mrityu = mrityu_analysis.get('planets_in_mrityu', [])
        
        return {
            "planets_affected": [p['planet'] for p in planets_in_mrityu],
            "total_count": mrityu_analysis.get('total_count', 0),
            "overall_risk": mrityu_analysis.get('overall_risk'),
            "significance": "Mrityu Bhaga shows areas where karmic account is closed - no worldly results",
            "health_implications": [p.get('health_risk') for p in planets_in_mrityu],
            "details": planets_in_mrityu
        }
    
    def _analyze_vargottama(self) -> Dict:
        """Vargottama - strong karmic continuity"""
        if not self.vargottama_calc:
            return {"available": False, "message": "Divisional charts not provided"}
        
        vargottama_summary = self.vargottama_calc.get_vargottama_summary()
        
        return {
            "total_vargottama_planets": vargottama_summary.get('total_vargottama_planets', 0),
            "vargottama_planets": vargottama_summary.get('vargottama_planets', []),
            "significance": "Vargottama planets show strong past life continuity and mastery",
            "strongest": self.vargottama_calc.get_strongest_vargottama()
        }
    
    def _analyze_pitru_dosha(self) -> Dict:
        """Pitru Dosha - ancestral/paternal karma"""
        planets = self.chart_data.get('planets', {})
        sun = planets.get('Sun', {})
        rahu = planets.get('Rahu', {})
        saturn = planets.get('Saturn', {})
        gulika = planets.get('Gulika', {})
        
        has_pitru = (
            sun.get('house') == rahu.get('house') or
            sun.get('house') == saturn.get('house') or
            (sun.get('house') == 9 and (rahu.get('house') == 9 or saturn.get('house') == 9))
        )
        
        gulika_affliction = gulika.get('house') in [2, 9]
        
        return {
            "has_ancestral_debt": has_pitru or gulika_affliction,
            "type": "Pitru Dosha (Paternal)" if has_pitru else "No Pitru Dosha",
            "gulika_factor": "Gulika in 2nd/9th confirms family curses" if gulika_affliction else "No Gulika affliction",
            "indication": "Sun afflicted by Rahu/Saturn" if has_pitru else "Ancestral blessings strong",
            "remedy": "Tarpana for ancestors, feed Brahmins, donate on Amavasya" if has_pitru or gulika_affliction else "Continue ancestral worship",
            "karmic_meaning": "Unresolved obligations to father's lineage" if has_pitru or gulika_affliction else "Paternal blessings active"
        }
    
    def _analyze_matru_dosha(self) -> Dict:
        """Matru Dosha - maternal karma"""
        planets = self.chart_data.get('planets', {})
        moon = planets.get('Moon', {})
        rahu = planets.get('Rahu', {})
        saturn = planets.get('Saturn', {})
        
        has_matru = (
            moon.get('house') == rahu.get('house') or
            moon.get('house') == saturn.get('house') or
            moon.get('sign') == 7  # Debilitated in Scorpio
        )
        
        return {
            "has_maternal_debt": has_matru,
            "type": "Matru Dosha (Maternal)" if has_matru else "No Matru Dosha",
            "indication": "Moon afflicted by Rahu/Saturn or debilitated" if has_matru else "Maternal blessings strong",
            "remedy": "Worship Divine Mother, feed women, donate white items, milk" if has_matru else "Continue maternal respect",
            "karmic_meaning": "Unresolved obligations to mother's lineage" if has_matru else "Maternal blessings active"
        }
    
    def _analyze_5th_house(self) -> Dict:
        """5th house - Poorva Punya (past life merit/blessings)"""
        houses = self.chart_data.get('houses', [])
        
        if len(houses) < 5:
            return {"available": False}
        
        house_5 = houses[4]  # 0-indexed
        planets_in_5 = [p for p, data in self.chart_data.get('planets', {}).items() 
                        if data.get('house') == 5]
        
        benefics = ['Jupiter', 'Venus', 'Mercury']
        has_benefic = any(p in planets_in_5 for p in benefics)
        
        result = {
            "planets": planets_in_5,
            "lord": house_5.get('lord'),
            "theme": "Children, creativity, intelligence, romance, past life merit",
            "karma_type": "Poorva Punya - blessings earned from past good deeds",
            "past_life_merit": "Strong" if has_benefic else "Moderate" if planets_in_5 else "Neutral",
            "this_life_blessings": "Natural intelligence, creativity, and children blessings" if has_benefic else "Earned through effort",
            "significance": "5th house shows what you earned through past dharmic actions"
        }
        
        print("\n=== 5TH HOUSE ANALYSIS (Poorva Punya) ===")
        print(f"Planets: {result['planets']}")
        print(f"Lord: {result['lord']}")
        print(f"Past Life Merit: {result['past_life_merit']}")
        print(f"This Life Blessings: {result['this_life_blessings']}")
        print(f"Significance: {result['significance']}")
        
        return result
    
    def _analyze_8th_house(self) -> Dict:
        """8th house - Prarabdha (unavoidable transformation karma)"""
        houses = self.chart_data.get('houses', [])
        
        if len(houses) < 8:
            return {"available": False}
        
        house_8 = houses[7]  # 0-indexed
        planets_in_8 = [p for p, data in self.chart_data.get('planets', {}).items() 
                        if data.get('house') == 8]
        
        result = {
            "planets": planets_in_8,
            "lord": house_8.get('lord'),
            "theme": "Sudden events, transformation, occult, longevity, inheritance",
            "karma_type": "Prarabdha - unavoidable transformation karma",
            "karmic_debt": f"Must experience deep transformation through {', '.join(planets_in_8)}" if planets_in_8 else "Minimal 8th house karma",
            "occult_potential": "High" if 'Ketu' in planets_in_8 or 'Saturn' in planets_in_8 else "Moderate",
            "significance": "8th house shows unavoidable karmic events - transformation you cannot escape"
        }
        
        print("\n=== 8TH HOUSE ANALYSIS (Prarabdha) ===")
        print(f"Planets: {result['planets']}")
        print(f"Lord: {result['lord']}")
        print(f"Karmic Debt: {result['karmic_debt']}")
        print(f"Occult Potential: {result['occult_potential']}")
        print(f"Significance: {result['significance']}")
        
        return result
    
    def _analyze_9th_house(self) -> Dict:
        """9th house - Bhagya (fortune/dharma from past lives)"""
        houses = self.chart_data.get('houses', [])
        
        if len(houses) < 9:
            return {"available": False}
        
        house_9 = houses[8]  # 0-indexed
        planets_in_9 = [p for p, data in self.chart_data.get('planets', {}).items() 
                        if data.get('house') == 9]
        
        benefics = ['Jupiter', 'Venus', 'Mercury']
        has_benefic = any(p in planets_in_9 for p in benefics)
        
        result = {
            "planets": planets_in_9,
            "lord": house_9.get('lord'),
            "theme": "Luck, dharma, father, guru, higher learning, long journeys, fortune",
            "karma_type": "Bhagya - fortune earned from past dharmic actions",
            "past_dharma": "Strong dharmic merit" if has_benefic else "Moderate" if planets_in_9 else "Neutral",
            "this_life_luck": "Natural good fortune and blessings" if has_benefic else "Luck through righteous action",
            "significance": "9th house shows blessings from past life dharma and righteousness"
        }
        
        print("\n=== 9TH HOUSE ANALYSIS (Bhagya) ===")
        print(f"Planets: {result['planets']}")
        print(f"Lord: {result['lord']}")
        print(f"Past Dharma: {result['past_dharma']}")
        print(f"This Life Luck: {result['this_life_luck']}")
        print(f"Significance: {result['significance']}")
        
        return result
    
    def _analyze_12th_house(self) -> Dict:
        """12th house - moksha, liberation, foreign connections"""
        houses = self.chart_data.get('houses', [])
        
        if len(houses) < 12:
            return {"available": False}
        
        house_12 = houses[11]  # 0-indexed
        planets_in_12 = [p for p, data in self.chart_data.get('planets', {}).items() 
                         if data.get('house') == 12]
        
        moksha_planets = ['Jupiter', 'Ketu', 'Saturn']
        has_moksha_planet = any(p in planets_in_12 for p in moksha_planets)
        
        return {
            "planets": planets_in_12,
            "lord": house_12.get('lord'),
            "moksha_potential": "High" if has_moksha_planet else "Moderate",
            "theme": "Spiritual liberation, foreign lands, losses, expenses, bed pleasures, isolation",
            "karmic_indication": "Strong moksha karma" if has_moksha_planet else "Balanced material-spiritual path",
            "significance": "12th house shows liberation potential and foreign connections"
        }
    
    def _get_karmic_timing_summary(self) -> Dict:
        """Summary of when karma manifests"""
        planets = self.chart_data.get('planets', {})
        saturn_house = planets.get('Saturn', {}).get('house', 0)
        rahu_house = planets.get('Rahu', {}).get('house', 0)
        
        return {
            "saturn_dasha": "Major karmic testing period - discipline, delays, maturity",
            "rahu_dasha": "Obsessive desires, foreign connections, unconventional experiences",
            "ketu_dasha": "Spiritual detachment, past life memories, moksha pull",
            "sade_sati": "Saturn transit over Moon sign ±1 - 7.5 year karmic test",
            "saturn_return": "Age 29-30, 58-60 - Major life restructuring",
            "rahu_return": "Age 18-19, 37-38, 56-57 - Destiny activation",
            "current_focus": f"Saturn in house {saturn_house}, Rahu in house {rahu_house}"
        }
    
    def _calculate_karmic_balance(self, lagna_class: str, ak_class: str) -> Dict:
        """Calculate karmic balance score per BPHS"""
        score = 0
        if lagna_class == "Benefic":
            score += 50
        elif lagna_class == "Malefic":
            score -= 50
        
        if ak_class == "Benefic":
            score += 50
        elif ak_class == "Malefic":
            score -= 50
        
        if score > 50:
            verdict = "Excellent - Strong positive karma from past lives"
        elif score > 0:
            verdict = "Good - More merit than debt"
        elif score == 0:
            verdict = "Balanced - Equal merit and debt"
        elif score > -50:
            verdict = "Challenging - More debt than merit, requires remedies"
        else:
            verdict = "Difficult - Significant karmic debts to resolve"
        
        return {
            "score": score,
            "verdict": verdict,
            "lagna_contribution": lagna_class,
            "atmakaraka_contribution": ak_class
        }
    
    def _add_sign_names(self, chart_data: Dict) -> Dict:
        """Add sign names to chart data for Gemini clarity"""
        import copy
        chart_copy = copy.deepcopy(chart_data)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Add sign names to planets
        if 'planets' in chart_copy:
            for planet_name, planet_data in chart_copy['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        # Add sign names to divisional chart planets if nested
        if 'divisional_chart' in chart_copy and 'planets' in chart_copy['divisional_chart']:
            for planet_name, planet_data in chart_copy['divisional_chart']['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        return chart_copy
