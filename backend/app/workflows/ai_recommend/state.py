"""
AI Recommendation Workflow - State definition
"""
from typing import TypedDict, List, Dict, Any, Optional


class AIRecommendState(TypedDict):
    """State for AI recommendation workflow"""

    query: str
    session_id: str

    rewritten_query: str
    entities: List[str]

    milvus_results: List[Dict[str, Any]]
    neo4j_results: List[Dict[str, Any]]

    rrf_results: List[Dict[str, Any]]

    confidence_score: float
    needs_web_search: bool

    tavily_results: Optional[List[Dict[str, Any]]]

    reranked_results: List[Dict[str, Any]]

    final_answer: str
