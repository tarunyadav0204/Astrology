from typing import Dict, Any, List
from .core import NumerologyCore
from .grid_analyzer import GridAnalyzer
from .name_optima import NameOptima
from .time_keeper import TimeKeeper

class NumerologyManager:
    """
    The Orchestrator.
    This is the single point of entry for the API.
    It combines Identity, Timing, and Grid analysis into cohesive reports.
    """

    def __init__(self):
        self.core = NumerologyCore()
        self.grid = GridAnalyzer()
        self.names = NameOptima()
        self.timer = TimeKeeper()

    def get_identity_report(self, name: str, dob: str, gender: str = None) -> Dict[str, Any]:
        """
        Generates the 'Who Am I?' report.
        Combines Life Path, Name Numbers, and the Lo Shu Grid.
        """
        # 1. Core Numbers
        life_path = self.core.calculate_life_path(dob)
        name_analysis = self.names.analyze_full_name(name, system='chaldean')
        
        # 2. The Grid (Visuals)
        grid_data = self.grid.generate_grid(dob)
        
        return {
            "profile": {
                "name": name,
                "dob": dob,
                "life_path_number": life_path['life_path_number'],
                "expression_number": name_analysis['expression']['number'],
                "soul_urge_number": name_analysis['soul_urge']['number']
            },
            "numerology_chart": {
                "core_numbers": {
                    "life_path": life_path,
                    "expression": name_analysis['expression'],
                    "soul_urge": name_analysis['soul_urge'],
                    "personality": name_analysis['personality']
                },
                "lo_shu_grid": grid_data,
                "name_verdict": name_analysis['verdict']
            }
        }

    def get_forecast_report(self, dob: str, target_date: str = None) -> Dict[str, Any]:
        """
        Generates the 'Future' report.
        Personal Year, Month, and Life Pinnacles.
        """
        current_cycles = self.timer.get_current_cycles(dob, target_date)
        life_map = self.timer.get_life_roadmap(dob)
        
        return {
            "current_energy": current_cycles,
            "life_timeline": life_map
        }

    def check_name_compatibility(self, current_name: str, system: str = 'chaldean') -> Dict[str, Any]:
        """
        Tool for users to check if their name is lucky.
        Returns analysis AND suggestions if it's unlucky.
        """
        analysis = self.names.analyze_full_name(current_name, system)
        is_lucky = analysis['expression']['compound'] in self.names.LUCKY_COMPOUNDS
        
        suggestions = []
        if not is_lucky:
            suggestions = self.names.suggest_corrections(current_name)
            
        return {
            "current_name": current_name,
            "compound_number": analysis['expression']['compound'],
            "single_number": analysis['expression']['number'],
            "verdict": analysis['verdict'],
            "is_lucky": is_lucky,
            "system": system,
            "system_comparison": self.names.compare_systems(current_name),
            "remedial_suggestions": suggestions
        }

    def get_full_report(self, name: str, dob: str) -> Dict[str, Any]:
        """
        The 'Mega' Report. Everything in one JSON.
        """
        identity = self.get_identity_report(name, dob)
        forecast = self.get_forecast_report(dob)
        
        # Merge them
        return {
            **identity,
            "forecast": forecast
        }