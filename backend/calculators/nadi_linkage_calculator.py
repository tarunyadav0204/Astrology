from typing import Dict, List, Any, Set

class NadiLinkageCalculator:
    """
    ADVANCED Bhrigu Nandi Nadi (BNN) Calculator.
    
    Includes Core Rules:
    1. Trine (1, 5, 9), Directional (2, 12), Opposition (7)
    
    Includes Advanced Exceptions:
    2. Retrograde (Vakra): Retro planets ALSO influence from the previous sign.
    3. Exchange (Parivartana): Planets in mutual signs swap positions.
    """

    def __init__(self, chart_data: Dict[str, Any]):
        self.planets = chart_data.get('planets', {})
        self.sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
            8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        self.valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

    def get_nadi_links(self) -> Dict[str, Any]:
        """Returns the complete network of planetary connections."""
        
        # 1. Detect Exchanges (Parivartana) and create a "Virtual Chart"
        # If Mars & Venus exchange, we treat them as being in their OWN signs for prediction.
        virtual_positions = self._apply_exchange_logic()
        
        links = {}
        
        for p_name in self.valid_planets:
            if p_name not in virtual_positions: continue
            
            p_data = virtual_positions[p_name]
            current_sign = p_data['sign']
            is_retro = p_data.get('retrograde', False)
            
            # 2. Identify "Active Signs" for this planet
            # Normal: Just the current sign.
            # Retrograde: Current sign AND Previous sign.
            active_signs = [current_sign]
            if is_retro:
                prev_sign_idx = (current_sign - 1 + 12) % 12
                active_signs.append(prev_sign_idx)
            
            connected_planets = {
                "trine": set(), "next": set(), "prev": set(), "opposite": set()
            }
            
            # 3. Calculate Links from ALL Active Signs
            for sign_idx in active_signs:
                # Trine (1, 5, 9)
                trine_1 = (sign_idx + 4) % 12
                trine_2 = (sign_idx + 8) % 12
                self._add_links(connected_planets['trine'], [sign_idx, trine_1, trine_2], virtual_positions, p_name)
                
                # Next (2nd) - Future Direction
                next_sign = (sign_idx + 1) % 12
                self._add_links(connected_planets['next'], [next_sign], virtual_positions, p_name)
                
                # Prev (12th) - Past/Background
                prev_sign = (sign_idx - 1 + 12) % 12
                self._add_links(connected_planets['prev'], [prev_sign], virtual_positions, p_name)
                
                # Opposite (7th)
                opp_sign = (sign_idx + 6) % 12
                self._add_links(connected_planets['opposite'], [opp_sign], virtual_positions, p_name)

            links[p_name] = {
                "sign_info": {
                    "sign_id": current_sign,
                    "is_retro": is_retro,
                    "is_exchange": p_data.get('is_exchange', False)
                },
                "connections": {
                    "trine": list(connected_planets['trine']),
                    "next": list(connected_planets['next']),
                    "prev": list(connected_planets['prev']),
                    "opposite": list(connected_planets['opposite'])
                },
                "all_links": list(set.union(*connected_planets.values()))
            }
            
        return links

    # --- INTERNAL LOGIC ---

    def _apply_exchange_logic(self) -> Dict[str, Any]:
        """Creates a 'Virtual Chart' where Exchanged planets are moved to their Own Signs."""
        virtual = {}
        
        # First, copy original data
        for p in self.valid_planets:
            if p in self.planets:
                virtual[p] = self.planets[p].copy()
                virtual[p]['is_exchange'] = False

        # Detect Exchanges
        checked = set()
        for p1 in self.valid_planets:
            if p1 not in virtual: continue
            
            s1 = virtual[p1]['sign']
            lord1 = self.sign_lords.get(s1) 
            
            if lord1 and lord1 != p1 and lord1 in virtual:
                p2 = lord1
                s2 = virtual[p2]['sign']
                owner_of_s2 = self.sign_lords.get(s2)
                
                if p1 in ['Rahu', 'Ketu'] or p2 in ['Rahu', 'Ketu']: continue

                if owner_of_s2 == p1:
                    pair = tuple(sorted((p1, p2)))
                    if pair not in checked:
                        virtual[p1]['sign'] = s2
                        virtual[p1]['is_exchange'] = True
                        virtual[p2]['sign'] = s1
                        virtual[p2]['is_exchange'] = True
                        checked.add(pair)
        
        return virtual

    def _add_links(self, target_set: Set[str], sign_indices: List[int], 
                  virtual_chart: Dict[str, Any], self_name: str):
        for p_name, data in virtual_chart.items():
            if p_name == self_name: continue
            if data['sign'] in sign_indices:
                target_set.add(p_name)
