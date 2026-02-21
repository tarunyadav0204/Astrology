"""Registry of trigger implementations. Add new triggers here."""
from .triggers.planet_transit_sign import PlanetTransitSignTrigger
from .trigger_base import TriggerBase

TRIGGERS: dict[str, TriggerBase] = {
    "planet_transit_sign": PlanetTransitSignTrigger(),
}
