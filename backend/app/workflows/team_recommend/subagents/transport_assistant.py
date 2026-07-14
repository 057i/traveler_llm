"""
Transport Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class TransportAssistant(BaseSubAgent):
    """交通助手 - 推荐交通方式"""

    def __init__(self):
        super().__init__(
            name="交通助手",
            system_prompt="你是一个交通助手，负责推荐交通方式和路线。"
        )
