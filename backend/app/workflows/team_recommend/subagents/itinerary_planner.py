"""
Itinerary Planner for Team Recommendation
"""
from .base import BaseSubAgent


class ItineraryPlanner(BaseSubAgent):
    """行程规划师 - 创建旅行计划"""

    def __init__(self):
        super().__init__(
            name="行程规划师",
            system_prompt="你是一个行程规划师，负责创建详细的旅行计划。"
        )
