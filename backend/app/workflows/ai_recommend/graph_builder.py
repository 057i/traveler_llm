"""
AI Recommendation Workflow - Graph Builder

构建AI推荐工作流图
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from .state import AIRecommendState
from .nodes import (
    query_rewriter_node,
    milvus_hybrid_node,
    neo4j_nearby_node,
    confidence_check_node,
    tavily_search_node,
    rerank_node,
    synthesizer_node
)
from .nodes.node_rrf_fusion import rrf_fusion_node


def should_skip_retrieval(state: AIRecommendState) -> str:
    """
    条件判断：是否跳过检索

    如果是非旅游问题，直接跳到END
    """
    if state.get("should_skip_retrieval", False):
        logger.info("[GraphBuilder] Skipping retrieval - non-travel query")
        return "end"
    return "continue"


def build_ai_recommend_graph():
    """
    Build AI recommendation workflow graph

    流程：
    1. query_rewriter (查询分析+意图识别)
       ├─ 非旅游问题 → END
       └─ 旅游问题 → 继续
    2. milvus_hybrid (Milvus混合检索: 稠密+稀疏+精确匹配)
    3. neo4j_nearby (Neo4j附近检索，条件执行)
    4. confidence_check (置信度检查)
    5. tavily_search (Tavily网络搜索，条件执行)
    6. rrf_fusion (RRF融合: Milvus + Tavily)
    7. rerank (智能重排)
    8. synthesizer (LLM生成答案)
    9. END
    """
    logger.info("[GraphBuilder] Building AI recommendation workflow graph")

    workflow = StateGraph(AIRecommendState)

    # ========== 添加节点 ==========
    workflow.add_node("query_rewriter", query_rewriter_node)
    workflow.add_node("milvus_hybrid", milvus_hybrid_node)
    workflow.add_node("neo4j_nearby", neo4j_nearby_node)
    workflow.add_node("confidence_check", confidence_check_node)
    workflow.add_node("tavily_search", tavily_search_node)
    workflow.add_node("rrf_fusion", rrf_fusion_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # ========== 设置入口 ==========
    workflow.set_entry_point("query_rewriter")

    # ========== 条件边：query_rewriter之后 ==========
    workflow.add_conditional_edges(
        "query_rewriter",
        should_skip_retrieval,
        {
            "end": END,  # 非旅游问题，直接结束
            "continue": "milvus_hybrid"  # 旅游问题，继续检索
        }
    )

    # ========== 线性流程 ==========
    workflow.add_edge("milvus_hybrid", "neo4j_nearby")
    workflow.add_edge("neo4j_nearby", "confidence_check")
    workflow.add_edge("confidence_check", "tavily_search")
    workflow.add_edge("tavily_search", "rrf_fusion")
    workflow.add_edge("rrf_fusion", "rerank")
    workflow.add_edge("rerank", "synthesizer")
    workflow.add_edge("synthesizer", END)

    # ========== 编译 ==========
    app = workflow.compile()

    logger.success("[GraphBuilder] AI recommendation workflow graph built successfully")
    logger.info("[GraphBuilder] Total nodes: 8")
    logger.info("[GraphBuilder] Flow: Rewriter → Milvus → Neo4j → Confidence → Tavily → Fusion → Rerank → Synthesize")

    return app


_workflow_instance = None


def get_ai_recommend_workflow():
    """Get AI recommendation workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = build_ai_recommend_graph()
    return _workflow_instance
