"""
Node: GraphRAG Vectorization to Neo4j

Store destination entities in Neo4j knowledge graph
"""
from loguru import logger
from ..state import DocumentProcessingState
from typing import List
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_create_destination_nodes(neo4j, destinations: list):
    """
    Step 1: 创建景点节点到Neo4j

    Args:
        neo4j: Neo4j客户端
        destinations: 景点列表
    """
    logger.info(f"[GraphRAG] Creating {len(destinations)} destination nodes in Neo4j")

    success_count = 0
    for dest in destinations:
        try:
            neo4j.create_destination(
                name=dest.get('name', ''),
                description=dest.get('description', ''),
                location=f"{dest.get('province', '')}{dest.get('city', '')}",
                properties=dest
            )
            success_count += 1
        except Exception as e:
            logger.warning(f"[GraphRAG] Failed to add {dest.get('name', 'Unknown')}: {e}")
            continue

    logger.success(f"[GraphRAG] Created {success_count}/{len(destinations)} nodes in Neo4j")


def step2_create_relationships(neo4j, destinations: list):
    """
    Step 2: 创建节点之间的关系

    关系类型：
    1. LOCATED_IN - 景点→城市
    2. NEAR_BY - 同城市景点互为附近

    Args:
        neo4j: Neo4j客户端
        destinations: 景点列表
    """
    logger.info(f"[GraphRAG] Creating relationships for {len(destinations)} destinations")

    try:
        # 1. 创建 LOCATED_IN 关系（景点 -> 城市）
        logger.info("[GraphRAG] Step 2.1: Creating LOCATED_IN relationships...")
        cypher_located = """
        MATCH (d:Destination)
        WHERE d.city IS NOT NULL AND d.city <> ''
        MERGE (c:City {name: d.city, province: d.province})
        MERGE (d)-[:LOCATED_IN]->(c)
        RETURN count(d) as count
        """

        result = neo4j.query(cypher_located)
        count = result[0]['count'] if result else 0
        logger.success(f"[GraphRAG] Created {count} LOCATED_IN relationships")

        # 2. 创建 NEAR_BY 关系（同城市的景点互为附近）
        logger.info("[GraphRAG] Step 2.2: Creating NEAR_BY relationships...")
        cypher_nearby = """
        MATCH (d1:Destination)-[:LOCATED_IN]->(c:City)<-[:LOCATED_IN]-(d2:Destination)
        WHERE d1.name <> d2.name AND id(d1) < id(d2)
        MERGE (d1)-[:NEAR_BY]-(d2)
        RETURN count(*) as count
        """

        result = neo4j.query(cypher_nearby)
        count = result[0]['count'] if result else 0
        logger.success(f"[GraphRAG] Created {count} NEAR_BY relationships")

    except Exception as e:
        logger.error(f"[GraphRAG] Failed to create relationships: {e}")
        import traceback
        traceback.print_exc()


# ==================== 主节点函数 ====================

async def vectorize_graph(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: GraphRAG向量化到Neo4j

    流程:
        1. 创建景点节点到Neo4j知识图谱
        2. 创建节点关系（可选）

    Args:
        state: 工作流状态

    Returns:
        更新后的状态
    """
    task_id = state.get('task_id')

    # 发送node_start事件
    if task_id:
        await send_node_start(
            task_id=task_id,
            flow_type=FLOW_TYPE,
            step_id="vectorize_graph",
            step_name="GraphRAG向量化",
            progress=90,
            message="正在构建Neo4j知识图谱..."
        )

    logger.info("[GraphRAG] === Starting GraphRAG vectorization ===")

    try:
        destinations = state.get('destinations', [])

        if not destinations:
            logger.warning("[GraphRAG] No destinations for graph vectorization")
            state['graph_vector_success'] = False
            return state

        from app.core.neo4j_client import get_neo4j_client
        neo4j = get_neo4j_client()

        # Step 1: 创建景点节点
        step1_create_destination_nodes(neo4j, destinations)

        # Step 2: 创建关系（自动建立LOCATED_IN和NEAR_BY关系）
        step2_create_relationships(neo4j, destinations)

        state['graph_vector_success'] = True
        logger.success(f"[GraphRAG] === GraphRAG completed: {len(destinations)} entities ===")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="vectorize_graph",
                step_name="GraphRAG向量化",
                progress=90,
                message=f"知识图谱构建完成 ({len(destinations)} 个节点)"
            )

        # 并行节点只返回自己修改的字段，避免冲突
        return {"graph_vector_success": True}

    except Exception as e:
        logger.error(f"[GraphRAG] Graph vectorization failed: {e}")
        import traceback
        traceback.print_exc()

        # 并行节点只返回自己修改的字段
        return {
            "graph_vector_success": False,
            "errors": [f"GraphRAG vectorization error: {str(e)}"]
        }


async def graph_vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: 跳过GraphRAG向量化
    """
    logger.warning("[GraphRAG] Using fallback - skipping GraphRAG vectorization")
    state['graph_vector_success'] = True
    return state
