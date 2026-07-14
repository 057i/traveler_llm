"""
Budget Expert for Team Recommendation
"""
from .base import BaseSubAgent


class BudgetExpert(BaseSubAgent):
    """预算专家 - 估算旅行费用"""

    def __init__(self):
        super().__init__(
            name="预算专家",
            system_prompt="你是一个预算专家，负责估算旅行费用。"
        )
