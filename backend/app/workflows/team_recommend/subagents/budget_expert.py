"""
Budget Expert for Team Recommendation
"""
from .base import BaseSubAgent


class BudgetExpert(BaseSubAgent):
    """Budget Expert - estimates travel costs"""

    def __init__(self):
        super().__init__(
            name="Budget Expert",
            system_prompt="You are a budget expert that estimates travel costs."
        )
