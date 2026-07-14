"""
RAG工具定义 - 使用LangChain的@tool装饰器

提供Milvus混合检索和Neo4j图查询工具
"""
from typing import List, Optional
from loguru import logger
import json

try:
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available, using fallback decorator")
    LANGCHAIN_AVAILABLE = False

    # 简单的装饰器替代
    def tool(func):
        func.name = func.__name__
        func.description = func.__doc__
        async def ainvoke(args):
            if isinstance(args, dict):
                return await func(**args)
            else:
                return await func(args)
        func.ainvoke = ainvoke
        return func


@tool
async def search_travel_knowledge(query: str, entities: Optional[List[str]] = None) -> str:
    """
    从旅游知识库中搜索相关信息

    使用Milvus向量数据库进行混合检索（稠密向量+稀疏向量+精确匹配）

    Args:
        query: 用户查询，例如"三清山的旅游攻略"
        entities: 实体列表，例如["三清山", "上饶"]

    Returns:
        JSON字符串，包含检索到的景点信息
    """
    logger.info(f"[Tool] search_travel_knowledge called: query='{query}', entities={entities}")

    try:
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client
        from app.core.embedding_service import get_embedding_service
        from app.core.fusion_strategies import FusionStrategy

        milvus_client = get_milvus_hybrid_client()
        embedding_service = get_embedding_service()

        # 1. 稠密检索
        logger.info("[Tool] Executing dense search...")
        dense_vector = embedding_service.encode(query, normalize_embeddings=True)
        dense_results = await milvus_client._search_dense(dense_vector, top_k=10)
        logger.info(f"[Tool] Dense search: {len(dense_results)} results")

        # 2. 稀疏检索
        logger.info("[Tool] Executing sparse search...")
        sparse_results = await milvus_client._search_sparse(query, top_k=10)
        logger.info(f"[Tool] Sparse search: {len(sparse_results)} results")

        # 3. 精确匹配
        exact_results = []
        if entities:
            logger.info(f"[Tool] Executing exact match for {len(entities)} entities...")
            for entity in entities[:5]:
                try:
                    entity_results = milvus_client.collection.query(
                        expr=f'name == "{entity}"',
                        output_fields=["destination_id", "name", "province", "city",
                                      "category", "description", "full_text", "rating"],
                        limit=3
                    )

                    # 格式化为统一结构
                    for r in entity_results:
                        exact_results.append({
                            'name': r.get('name'),
                            'city': r.get('city'),
                            'province': r.get('province'),
                            'category': r.get('category'),
                            'description': r.get('description'),
                            'score': 1.0  # 精确匹配给最高分
                        })
                except Exception as e:
                    logger.warning(f"[Tool] Exact match for '{entity}' failed: {e}")

            logger.info(f"[Tool] Exact match: {len(exact_results)} results")

        # 4. RRF融合 - 直接合并结果，不使用复杂的RRF
        logger.info("[Tool] Merging results...")

        # 收集所有结果，使用name去重
        seen_names = set()
        merged_results = []

        # 精确匹配优先（最高权重）
        for r in exact_results:
            name = r.get('name')
            if name and name not in seen_names:
                seen_names.add(name)
                r['score'] = 1.0  # 精确匹配最高分
                merged_results.append(r)

        # 稠密检索结果
        for r in dense_results:
            name = r.get('name')
            if name and name not in seen_names:
                seen_names.add(name)
                merged_results.append(r)

        # 稀疏检索结果
        for r in sparse_results:
            name = r.get('name')
            if name and name not in seen_names:
                seen_names.add(name)
                merged_results.append(r)

        # 按分数排序
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        logger.info(f"[Tool] Merged {len(merged_results)} unique results")

        # 5. 质量过滤 - 使用0.7阈值
        filtered_results = [
            r for r in merged_results
            if r.get('score', 0) >= 0.7  # 高质量阈值
        ]

        logger.info(f"[Tool] After quality filter (threshold=0.7): {len(filtered_results)} results")

        # 格式化返回
        result_summary = {
            "success": True,
            "found": len(filtered_results),
            "top_results": [
                {
                    "name": r.get('name'),
                    "description": r.get('description', '')[:200],
                    "category": r.get('category'),
                    "city": r.get('city'),
                    "score": round(r.get('score', 0), 3)
                }
                for r in filtered_results[:5]
            ]
        }

        logger.success(f"[Tool] search_travel_knowledge: found {len(filtered_results)} results")

        return json.dumps(result_summary, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] search_travel_knowledge failed: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": str(e),
            "found": 0
        }, ensure_ascii=False)


@tool
async def search_nearby_destinations(destination_name: str) -> str:
    """
    查询指定景点附近的其他景点

    使用Neo4j知识图谱查询NEARBY_OF关系

    Args:
        destination_name: 景点名称，例如"三清山"

    Returns:
        JSON字符串，包含附近景点列表
    """
    logger.info(f"[Tool] search_nearby_destinations called: destination='{destination_name}'")

    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()

        query = """
        MATCH (d1:Destination {name: $name})-[:NEARBY_OF]->(d2:Destination)
        WHERE d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT 5
        """

        results = neo4j_client.query(query, {"name": destination_name})

        formatted = {
            "success": True,
            "destination": destination_name,
            "nearby_count": len(results),
            "nearby_places": [
                {
                    "name": r.get('name'),
                    "city": r.get('city'),
                    "category": r.get('category'),
                    "description": r.get('description', '')[:150]
                }
                for r in results
            ]
        }

        logger.success(f"[Tool] search_nearby_destinations: found {len(results)} nearby places")

        return json.dumps(formatted, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] search_nearby_destinations failed: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": str(e),
            "nearby_count": 0
        }, ensure_ascii=False)


@tool
async def search_same_city_destinations(destination_name: str) -> str:
    """
    查询与指定景点在同一城市的其他景点

    使用Neo4j知识图谱查询LOCATED_IN关系

    Args:
        destination_name: 景点名称，例如"三清山"

    Returns:
        JSON字符串，包含同城景点列表
    """
    logger.info(f"[Tool] search_same_city_destinations called: destination='{destination_name}'")

    try:
        from app.core.neo4j_client import get_neo4j_client
        neo4j_client = get_neo4j_client()

        query = """
        MATCH (d1:Destination {name: $name})-[:LOCATED_IN]->(c:City)
        MATCH (d2:Destination)-[:LOCATED_IN]->(c)
        WHERE d2.name <> d1.name AND d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT 5
        """

        results = neo4j_client.query(query, {"name": destination_name})

        formatted = {
            "success": True,
            "destination": destination_name,
            "same_city_count": len(results),
            "same_city_places": [
                {
                    "name": r.get('name'),
                    "city": r.get('city'),
                    "category": r.get('category'),
                    "description": r.get('description', '')[:150]
                }
                for r in results
            ]
        }

        logger.success(f"[Tool] search_same_city_destinations: found {len(results)} same city places")

        return json.dumps(formatted, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool] search_same_city_destinations failed: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": str(e),
            "same_city_count": 0
        }, ensure_ascii=False)
