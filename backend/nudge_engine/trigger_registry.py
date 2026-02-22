"""Registry of trigger implementations. Add new triggers here."""
from .trigger_base import TriggerBase
from .triggers.planet_transit_sign import PlanetTransitSignTrigger
from .triggers.lunar_phase import LunarPhaseTrigger
from .triggers.planet_retrograde import PlanetRetrogradeTrigger
from .triggers.festival import FestivalTrigger

TRIGGERS: dict[str, TriggerBase] = {
    "planet_transit_sign": PlanetTransitSignTrigger(),
    "lunar_phase": LunarPhaseTrigger(),
    "planet_retrograde": PlanetRetrogradeTrigger(),
    "festival": FestivalTrigger(),
}
