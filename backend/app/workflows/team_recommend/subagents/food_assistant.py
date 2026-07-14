"""
Food Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class FoodAssistant(BaseSubAgent):
    """美食助手 - 推荐当地美食"""

    def __init__(self):
        super().__init__(
            name="美食助手",
            system_prompt="你是一个美食助手，负责推荐当地特色美食。"
        )
