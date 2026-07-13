"""
AI Recommendation Workflow - Node: Neo4j Nearby Search

Neo4j附近检索节点：条件执行，查找附近景点
"""
from loguru import logger
from typing import List, Dict, Any

from ..state import AIRecommendState
from app.utils.sse_utils import send_node_start, send_node_end
from config.settings import settings

FLOW_TYPE = "ai_recommend"


async def neo4j_nearby_node(state: AIRecommendState) -> AIRecommendState:
    """
    Node: Neo4j附近检索

    条件执行：仅当 needs_nearby_search = True 时执行
    查询Neo4j图数据库，找到指定景点附近的其他景点
    结果不参与RRF融合，仅作为附近信息补充
    """
    session_id = state.get("session_id")
    needs_nearby = state.get("needs_nearby_search", False)
    entities = state.get("entities", [])

    # ========== 节点开始 ==========
    logger.info("=" * 80)
    logger.info("[Neo4jNearby] 🚀 Starting Neo4j nearby search")
    logger.info(f"[Neo4jNearby] Session: {session_id}")
    logger.info(f"[Neo4jNearby] Needs nearby: {needs_nearby}")
    logger.info(f"[Neo4jNearby] Entities: {entities}")
    logger.info("=" * 80)

    # 发送node_start事件
    if session_id:
        await send_node_start(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="neo4j_nearby",
            step_name="附近检索",
            progress=40,
            message="正在查询附近景点..."
        )

    # ========== 节点处理 ==========
    # 条件判断：是否需要附近检索
    if not needs_nearby:
        logger.info("[Neo4jNearby] ⏭️  Skipping - nearby search not needed")
        state["neo4j_results"] = []

        # 发送node_end事件
        if session_id:
            await send_node_end(
                task_id=session_id,
                flow_type=FLOW_TYPE,
                step_id="neo4j_nearby",
                step_name="附近检索",
                progress=40,
                message="无需附近检索"
            )

        logger.info("=" * 80)
        logger.success("[Neo4jNearby] ✅ Node completed (skipped)")
        logger.info("=" * 80)

        return state

    # 检查实体
    if not entities:
        logger.warning("[Neo4jNearby] ⚠️  No entities found for nearby search")
        state["neo4j_results"] = []

        if session_id:
            await send_node_end(
                task_id=session_id,
                flow_type=FLOW_TYPE,
                step_id="neo4j_nearby",
                step_name="附近检索",
                progress=40,
                message="未找到实体"
            )

        logger.info("=" * 80)
        logger.success("[Neo4jNearby] ✅ Node completed (no entities)")
        logger.info("=" * 80)

        return state

    # 执行Neo4j查询
    try:
        from app.core.neo4j_client import get_neo4j_client

        neo4j = get_neo4j_client()

        center_location = entities[0]  # 使用第一个实体作为中心点
        logger.info(f"[Neo4jNearby] 📍 Searching nearby: {center_location}")

        # Cypher查询：查找附近景点（1-2跳关系）
        cypher = """
        MATCH (center:Destination)
        WHERE center.name CONTAINS $location OR center.city CONTAINS $location
        MATCH (center)-[:NEAR_BY|LOCATED_IN*1..2]-(nearby:Destination)
        WHERE nearby.name <> center.name
        RETURN DISTINCT nearby.name as name,
               nearby.description as description,
               nearby.province as province,
               nearby.city as city,
               nearby.category as category
        LIMIT $limit
        """

        results = neo4j.query(cypher, {
            "location": center_location,
            "limit": settings.NEO4J_NEARBY_LIMIT
        })

        logger.success(f"[Neo4jNearby] ✅ Found {len(results)} nearby locations")

        # 格式化结果
        formatted_results = []
        for r in results:
            formatted_results.append({
                "name": r.get("name", ""),
                "description": r.get("description", ""),
                "province": r.get("province", ""),
                "city": r.get("city", ""),
                "category": r.get("category", ""),
                "source": "neo4j_nearby",
                "is_nearby": True,
                "score": 0.0  # Neo4j结果不参与评分
            })

        state["neo4j_results"] = formatted_results

        # 打印结果
        if formatted_results:
            logger.info("[Neo4jNearby] Nearby locations:")
            for i, loc in enumerate(formatted_results[:5], start=1):
                logger.info(f"  #{i}: {loc['name']} ({loc['city']})")

    except Exception as e:
        logger.error(f"[Neo4jNearby] ❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

        state["neo4j_results"] = []

    # ========== 节点结束 ==========
    logger.info("=" * 80)
    logger.success("[Neo4jNearby] ✅ Neo4j nearby node completed")
    logger.info("=" * 80)

    # 发送node_end事件
    if session_id:
        await send_node_end(
            task_id=session_id,
            flow_type=FLOW_TYPE,
            step_id="neo4j_nearby",
            step_name="附近检索",
            progress=40,
            message=f"附近检索完成: {len(state['neo4j_results'])}条结果"
        )

    return state
