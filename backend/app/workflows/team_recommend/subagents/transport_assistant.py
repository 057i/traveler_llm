"""
Transport Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class TransportAssistant(BaseSubAgent):
    """Transport Assistant - recommends transportation"""

    def __init__(self):
        super().__init__(
            name="Transport Assistant",
            system_prompt="You are a transport assistant that recommends transportation options."
        )
