"""
Food Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class FoodAssistant(BaseSubAgent):
    """Food Assistant - recommends local food"""

    def __init__(self):
        super().__init__(
            name="Food Assistant",
            system_prompt="You are a food assistant that recommends local cuisine."
        )
