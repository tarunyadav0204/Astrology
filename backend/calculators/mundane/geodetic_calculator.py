from typing import Dict, Any, List

class GeodeticCalculator:
    """Maps Zodiacal degrees to terrestrial locations using Koorma Chakra"""
    
    def __init__(self):
        # Koorma Chakra: Map 27 Nakshatras to geographic directions
        self.nakshatra_directions = {
            'Ashwini': 'East', 'Bharani': 'Southeast', 'Krittika': 'South',
            'Rohini': 'Central', 'Mrigashira': 'Southwest', 'Ardra': 'West',
            'Punarvasu': 'Northwest', 'Pushya': 'North', 'Ashlesha': 'Northeast',
            'Magha': 'East', 'Purva Phalguni': 'Southeast', 'Uttara Phalguni': 'South',
            'Hasta': 'Central', 'Chitra': 'Southwest', 'Swati': 'West',
            'Vishakha': 'Northwest', 'Anuradha': 'North', 'Jyeshtha': 'Northeast',
            'Mula': 'East', 'Purva Ashadha': 'Southeast', 'Uttara Ashadha': 'South',
            'Shravana': 'Central', 'Dhanishta': 'Southwest', 'Shatabhisha': 'West',
            'Purva Bhadrapada': 'Northwest', 'Uttara Bhadrapada': 'North', 'Revati': 'Northeast'
        }
        
        # Regional mapping for major countries
        self.regional_mapping = {
            'India': {
                'North': ['Punjab', 'Haryana', 'Himachal Pradesh', 'Uttarakhand', 'Jammu & Kashmir'],
                'South': ['Tamil Nadu', 'Kerala', 'Karnataka', 'Andhra Pradesh', 'Telangana'],
                'East': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand', 'Assam'],
                'West': ['Gujarat', 'Maharashtra', 'Rajasthan', 'Goa'],
                'Central': ['Madhya Pradesh', 'Chhattisgarh', 'Uttar Pradesh', 'Delhi'],
                'Northeast': ['Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Tripura'],
                'Northwest': ['Punjab', 'Rajasthan', 'Haryana'],
                'Southeast': ['Andhra Pradesh', 'Tamil Nadu', 'Puducherry'],
                'Southwest': ['Kerala', 'Karnataka', 'Goa']
            },
            'USA': {
                'North': ['Montana', 'North Dakota', 'Minnesota', 'Wisconsin', 'Michigan'],
                'South': ['Texas', 'Louisiana', 'Mississippi', 'Alabama', 'Florida'],
                'East': ['New York', 'Pennsylvania', 'Virginia', 'North Carolina', 'South Carolina'],
                'West': ['California', 'Oregon', 'Washington', 'Nevada', 'Arizona'],
                'Central': ['Kansas', 'Nebraska', 'Oklahoma', 'Missouri', 'Iowa'],
                'Northeast': ['Maine', 'Vermont', 'New Hampshire', 'Massachusetts', 'Connecticut'],
                'Northwest': ['Washington', 'Oregon', 'Idaho', 'Montana'],
                'Southeast': ['Georgia', 'Florida', 'South Carolina', 'Alabama'],
                'Southwest': ['Arizona', 'New Mexico', 'Nevada', 'Southern California']
            }
        }
    
    def get_affected_regions(self, nakshatra: str, country: str = 'India') -> Dict[str, Any]:
        """Get geographic regions affected by planetary position in nakshatra"""
        direction = self.nakshatra_directions.get(nakshatra, 'Unknown')
        regions = self.regional_mapping.get(country, {}).get(direction, [])
        
        return {
            'nakshatra': nakshatra,
            'direction': direction,
            'country': country,
            'affected_regions': regions,
            'interpretation': f"{nakshatra} influences {direction} regions of {country}"
        }
    
    def analyze_planetary_impact(self, planet_data: Dict[str, Any], country: str = 'India') -> Dict[str, Any]:
        """Analyze geographic impact of a planet's position"""
        nakshatra = planet_data.get('nakshatra', {}).get('name', 'Unknown')
        planet_name = planet_data.get('name', 'Unknown')
        
        region_data = self.get_affected_regions(nakshatra, country)
        
        # Determine impact type based on planet
        impact_types = {
            'Saturn': 'Delays, restrictions, structural changes',
            'Mars': 'Conflicts, accidents, heat-related events',
            'Rahu': 'Sudden changes, foreign influences, technology',
            'Ketu': 'Spiritual movements, epidemics, isolation',
            'Jupiter': 'Growth, prosperity, legal matters',
            'Venus': 'Arts, entertainment, financial markets',
            'Mercury': 'Communication, trade, transportation',
            'Sun': 'Government, authority, leadership',
            'Moon': 'Public mood, agriculture, water resources',
            'Uranus': 'Revolution, innovation, sudden upheavals',
            'Neptune': 'Deception, spirituality, oil/gas',
            'Pluto': 'Transformation, power struggles, nuclear matters'
        }
        
        return {
            **region_data,
            'planet': planet_name,
            'impact_type': impact_types.get(planet_name, 'General influence'),
            'prediction': f"{planet_name} in {nakshatra} suggests {impact_types.get(planet_name, 'influence')} in {region_data['direction']} {country}"
        }
    
    def get_nakshatra_from_longitude(self, longitude: float) -> str:
        """Convert longitude to nakshatra name"""
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        nakshatra_span = 360 / 27
        nak_index = int(longitude / nakshatra_span)
        return nakshatras[nak_index % 27]
