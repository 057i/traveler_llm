"""
AI Recommendation Workflow - State definition
"""
from typing import TypedDict, List, Dict, Any, Optional


class AIRecommendState(TypedDict):
    """State for AI recommendation workflow"""

    query: str
    session_id: str

    # Query rewriter
    rewritten_query: str
    expanded_query: str  # 新增：查询扩展后的关键词
    entities: List[str]
    needs_nearby_search: bool
    nearby_type: str  # 新增：附近推荐类型 (attraction/hotel/food/all)
    is_travel_related: bool  # 新增：是否旅游相关
    should_skip_retrieval: bool  # 新增：是否跳过检索

    # Milvus混合检索（稠密+稀疏+精确匹配，内部RRF）
    milvus_hybrid_results: List[Dict[str, Any]]
    milvus_confidence: float

    # Neo4j检索结果（附近信息，不参与RRF）
    neo4j_results: List[Dict[str, Any]]

    # Confidence check
    confidence_score: float
    needs_web_search: bool

    # Tavily网络搜索
    tavily_results: Optional[List[Dict[str, Any]]]

    # RRF融合结果（Milvus + Tavily，加权）
    rrf_results: List[Dict[str, Any]]

    # Rerank
    reranked_results: List[Dict[str, Any]]

    # Final
    final_answer: str
    sources: List[Dict[str, Any]]
    nearby_recommendations: List[Dict[str, Any]]  # 新增：附近推荐（单独）
