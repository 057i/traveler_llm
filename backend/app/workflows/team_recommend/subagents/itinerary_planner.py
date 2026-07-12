"""
Itinerary Planner for Team Recommendation
"""
from .base import BaseSubAgent


class ItineraryPlanner(BaseSubAgent):
    """Itinerary Planner - creates travel itineraries"""

    def __init__(self):
        super().__init__(
            name="Itinerary Planner",
            system_prompt="You are an itinerary planner that creates detailed travel plans."
        )
