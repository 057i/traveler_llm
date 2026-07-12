"""
Graph RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent


class GraphRAGAssistant(BaseSubAgent):
    """Graph RAG Assistant - searches knowledge graph"""

    def __init__(self):
        super().__init__(
            name="Graph RAG Assistant",
            system_prompt="You are a graph RAG assistant that searches the knowledge graph."
        )
