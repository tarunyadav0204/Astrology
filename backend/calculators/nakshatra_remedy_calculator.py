from typing import Dict, Any, List

class NakshatraRemedyCalculator:
    """
    Classical Nakshatra-based remedy engine.
    Maps 27 Nakshatras to their specific Shakti, Devata, Vriksha, and Beej Mantras.
    """
    
    NAKSHATRA_DATA = {
        "Ashwini": {"devata": "Ashwini Kumaras", "shakti": "Shidravyapani Shakti (Quick Reach)", "vriksha": "Strychnine Tree (Kuchila)", "mantra": "Om Am/Im"},
        "Bharani": {"devata": "Yama", "shakti": "Apabharani Shakti (Removal of burden)", "vriksha": "Amla", "mantra": "Om Lim"},
        "Krittika": {"devata": "Agni", "shakti": "Dahana Shakti (Power to burn/purify)", "vriksha": "Cluster Fig (Gular)", "mantra": "Om Am"},
        "Rohini": {"devata": "Brahma", "shakti": "Rohana Shakti (Power to grow)", "vriksha": "Jamun", "mantra": "Om Rm/Lrum"},
        "Mrigashira": {"devata": "Soma", "shakti": "Prinana Shakti (Power of fulfillment)", "vriksha": "Cutch Tree (Khair)", "mantra": "Om Em"},
        "Ardra": {"devata": "Rudra", "shakti": "Yatna Shakti (Power of effort)", "vriksha": "Long Pepper (Krishun)", "mantra": "Om Aeem"},
        "Punarvasu": {"devata": "Aditi", "shakti": "Vasutva Shakti (Power of wealth/renewal)", "vriksha": "Bamboo", "mantra": "Om Aam"},
        "Pushya": {"devata": "Brihaspati", "shakti": "Brahmavarchasa Shakti (Power of spiritual glow)", "vriksha": "Peepal", "mantra": "Om Kam"},
        "Ashlesha": {"devata": "Sarpas", "shakti": "Visasleshana Shakti (Power to paralyze/detach)", "vriksha": "Nagkesar", "mantra": "Om Gam"},
        "Magha": {"devata": "Pitris (Ancestors)", "shakti": "Tyagekshemana Shakti (Power to leave the body)", "vriksha": "Banyan", "mantra": "Om Mam"},
        "Purva Phalguni": {"devata": "Bhaga", "shakti": "Prajana Shakti (Power of procreation)", "vriksha": "Palash", "mantra": "Om Wam"},
        "Uttara Phalguni": {"devata": "Aryaman", "shakti": "Chayani Shakti (Power of accumulation)", "vriksha": "Kher", "mantra": "Om Pam"},
        "Hasta": {"devata": "Savitr", "shakti": "Hasta Sthapaniya Shakti (Power to put in hand)", "vriksha": "Jasmine", "mantra": "Om Jham"},
        "Chitra": {"devata": "Tvashtar", "shakti": "Punya Chayani Shakti (Power of merit)", "vriksha": "Bael", "mantra": "Om Tam"},
        "Swati": {"devata": "Vayu", "shakti": "Pradhvamsa Shakti (Power to scatter)", "vriksha": "Arjuna", "mantra": "Om Lam"},
        "Vishakha": {"devata": "Indragni", "shakti": "Vyapana Shakti (Power to achieve)", "vriksha": "Wood Apple (Kaitha)", "mantra": "Om Yum"},
        "Anuradha": {"devata": "Mitra", "shakti": "Radhana Shakti (Power of worship)", "vriksha": "Maulsari", "mantra": "Om Nam"},
        "Jyeshtha": {"devata": "Indra", "shakti": "Arohana Shakti (Power to rise/conquer)", "vriksha": "Semal", "mantra": "Om Dham"},
        "Mula": {"devata": "Nirriti", "shakti": "Barhana Shakti (Power to root out)", "vriksha": "Sal", "mantra": "Om Naam"},
        "Purva Ashadha": {"devata": "Apas (Water)", "shakti": "Varchasva Shakti (Power of invigoration)", "vriksha": "Ashoka", "mantra": "Om Bam"},
        "Uttara Ashadha": {"devata": "Vishvadevas", "shakti": "Apradhrishya Shakti (Power of victory)", "vriksha": "Jackfruit", "mantra": "Om Bham"},
        "Shravana": {"devata": "Vishnu", "shakti": "Aprati Shakti (Power of connection)", "vriksha": "Madar", "mantra": "Om Ksham"},
        "Dhanishta": {"devata": "Vasus", "shakti": "Khyapayitri Shakti (Power to give fame)", "vriksha": "Shami", "mantra": "Om Am/Im"},
        "Shatabhisha": {"devata": "Varuna", "shakti": "Bheshaja Shakti (Power of healing)", "vriksha": "Kadamba", "mantra": "Om Lam"},
        "Purva Bhadrapada": {"devata": "Aja Ekapada", "shakti": "Yajamana Shakti (Power of sacrifice)", "vriksha": "Mango", "mantra": "Om Seem"},
        "Uttara Bhadrapada": {"devata": "Ahirbudhnya", "shakti": "Varshodyamana Shakti (Power to bring rain/growth)", "vriksha": "Neem", "mantra": "Om Tham"},
        "Revati": {"devata": "Pushan", "shakti": "Kshiradyapani Shakti (Power of nourishment)", "vriksha": "Mahua", "mantra": "Om Aam/Eem"}
    }

    PADA_SYLLABLES = {
        "Ashwini": {1: "Chu", 2: "Che", 3: "Cho", 4: "La"},
        "Bharani": {1: "Li", 2: "Lu", 3: "Le", 4: "Lo"},
        "Krittika": {1: "A", 2: "I", 3: "U", 4: "E"},
        "Rohini": {1: "O", 2: "Va", 3: "Vi", 4: "Vu"},
        "Mrigashira": {1: "Ve", 2: "Vo", 3: "Ka", 4: "Ki"},
        "Ardra": {1: "Ku", 2: "Gha", 3: "Nga", 4: "Chha"},
        "Punarvasu": {1: "Ke", 2: "Ko", 3: "Ha", 4: "Hi"},
        "Pushya": {1: "Hu", 2: "He", 3: "Ho", 4: "Da"},
        "Ashlesha": {1: "Di", 2: "Du", 3: "De", 4: "Do"},
        "Magha": {1: "Ma", 2: "Mi", 3: "Mu", 4: "Me"},
        "Purva Phalguni": {1: "Mo", 2: "Ta", 3: "Ti", 4: "Tu"},
        "Uttara Phalguni": {1: "Te", 2: "To", 3: "Pa", 4: "Pi"},
        "Hasta": {1: "Pu", 2: "Sha", 3: "Na", 4: "Tha"},
        "Chitra": {1: "Pe", 2: "Po", 3: "Ra", 4: "Ri"},
        "Swati": {1: "Ru", 2: "Re", 3: "Ro", 4: "Ta"},
        "Vishakha": {1: "Ti", 2: "Tu", 3: "Te", 4: "To"},
        "Anuradha": {1: "Na", 2: "Ni", 3: "Nu", 4: "Ne"},
        "Jyeshtha": {1: "No", 2: "Ya", 3: "Yi", 4: "Yu"},
        "Mula": {1: "Ye", 2: "Yo", 3: "Ba", 4: "Bi"},
        "Purva Ashadha": {1: "Bu", 2: "Dha", 3: "Bha", 4: "Dha"},
        "Uttara Ashadha": {1: "Be", 2: "Bo", 3: "Ja", 4: "Ji"},
        "Shravana": {1: "Ju", 2: "Je", 3: "Jo", 4: "Gha"},
        "Dhanishta": {1: "Ga", 2: "Gi", 3: "Gu", 4: "Ge"},
        "Shatabhisha": {1: "Go", 2: "Sa", 3: "Si", 4: "Su"},
        "Purva Bhadrapada": {1: "Se", 2: "So", 3: "Da", 4: "Di"},
        "Uttara Bhadrapada": {1: "Du", 2: "Tha", 3: "Jha", 4: "Na"},
        "Revati": {1: "De", 2: "Do", 3: "Cha", 4: "Chi"}
    }

    def get_remedy(self, planet: str, nakshatra: str, pada: int, condition: str = "general") -> Dict[str, Any]:
        """Generates a complete classical remedy payload for a planet in a specific star."""
        star_info = self.NAKSHATRA_DATA.get(nakshatra)
        if not star_info:
            return {"error": "Nakshatra data not found"}

        syllable = self.PADA_SYLLABLES.get(nakshatra, {}).get(pada, "")
        
        remedy_payload = {
            "target_planet": planet,
            "nakshatra": nakshatra,
            "pada": pada,
            "condition_trigger": condition,
            "shakti": star_info["shakti"],
            "deity": star_info["devata"],
            "vriksha": star_info["vriksha"],
            "mantra": star_info["mantra"],
            "pada_syllable": syllable,
            "remedy_tier_1_biological": f"Plant or nurture a {star_info['vriksha']} tree. If unavailable, touch its wood or keep its leaf.",
            "remedy_tier_2_sound": f"Chant the Beej Mantra '{star_info['mantra']}' 108 times. Focus on the vibration '{syllable}' representing your specific pada.",
            "remedy_tier_3_ritual": self._generate_ritual(planet, nakshatra, star_info["devata"]),
            "rationale": f"Classic texts state {star_info['devata']} controls the results of this star. We are using {star_info['shakti']} to transform the current karma."
        }
        return remedy_payload

    def _generate_ritual(self, planet: str, nakshatra: str, devata: str) -> str:
        """Generate nakshatra-specific ritual recommendations"""
        rituals = {
            "Mula": "Offer root vegetables and incense to Lord Ganesha or ancestors, focusing on 'rooting out' obstacles.",
            "Shatabhisha": "Perform water-based charity (Apan Daan) or offer flowers to moving water bodies.",
            "Ashlesha": "Offer milk to serpent deities or perform Naga Puja on Nag Panchami.",
            "Magha": "Perform Pitru Tarpan (ancestral offerings) on Amavasya or visit ancestral places.",
            "Pushya": "Worship Brihaspati (Jupiter) on Thursdays, offer yellow flowers and turmeric.",
            "Ardra": "Offer bilva leaves to Lord Shiva, perform Rudra Abhishek.",
            "Bharani": "Donate to end-of-life care or hospices, honor the cycle of life and death.",
            "Revati": "Feed cows or offer food to travelers, honor Pushan the nourisher."
        }
        return rituals.get(nakshatra, f"Perform a silent meditation focusing on {devata}, the presiding lord of {nakshatra}.")
    
    def get_chart_remedies(self, planetary_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate remedies for all planets in the chart"""
        remedies = []
        
        for planet, data in planetary_analysis.items():
            basic_info = data.get('basic_info', {})
            nakshatra = basic_info.get('nakshatra')
            pada = basic_info.get('nakshatra_pada', {}).get('pada')
            
            if nakshatra and pada:
                remedy = self.get_remedy(planet, nakshatra, pada)
                if 'error' not in remedy:
                    remedies.append(remedy)
        
        return remedies
