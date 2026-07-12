"""
RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class RAGAssistant(BaseSubAgent):
    """RAG Assistant - searches knowledge base"""

    def __init__(self):
        super().__init__(
            name="RAG Assistant",
            system_prompt="You are a RAG assistant that searches the travel knowledge base."
        )
