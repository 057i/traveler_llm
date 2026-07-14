"""
Graph RAG Assistant - 基于LangChain + Function Calling

使用Neo4j图查询工具
"""
from .langchain_base import LangChainAgent
from .rag_tools import (
    search_nearby_destinations,
    search_same_city_destinations
)
from loguru import logger
from typing import List, Dict, Any


class GraphRAGAssistant(LangChainAgent):
    """图RAG助手 - 使用LangChain + Neo4j tools"""

    def __init__(self):
        tools = [
            search_nearby_destinations,
            search_same_city_destinations
        ]

        system_prompt = """你是一个知识图谱助手，负责从Neo4j图数据库中查询景点关系。

你有以下工具可用：
1. search_nearby_destinations(destination_name) - 查询附近景点
2. search_same_city_destinations(destination_name) - 查询同城景点

**工作策略：**
- 当用户询问"附近有什么"时，使用 search_nearby_destinations
- 当用户询问"同城推荐"时，使用 search_same_city_destinations
- 可以同时调用多个工具获取全面信息

请自主决定调用哪些工具，并整合结果返回清晰的推荐列表。"""

        super().__init__(
            name="图RAG助手",
            system_prompt=system_prompt,
            tools=tools
        )

        logger.info("[Graph RAG Assistant] Initialized with LangChain + function calling")

    async def search(self, entities: List[str]) -> Dict[str, Any]:
        """
        便捷方法：综合搜索附近和同城景点

        Args:
            entities: 实体列表

        Returns:
            搜索结果
        """
        if not entities:
            return {
                "success": True,
                "results": [],
                "count": 0
            }

        try:
            all_results = []

            for entity in entities[:3]:  # 限制最多3个实体
                # 查询附近景点
                try:
                    nearby_json = await search_nearby_destinations.ainvoke(entity)
                    import json
                    nearby_data = json.loads(nearby_json)
                    if nearby_data.get('success'):
                        all_results.extend(nearby_data.get('nearby_places', []))
                except Exception as e:
                    logger.error(f"[Graph RAG] Nearby search failed for {entity}: {e}")

                # 查询同城景点
                try:
                    same_city_json = await search_same_city_destinations.ainvoke(entity)
                    import json
                    same_city_data = json.loads(same_city_json)
                    if same_city_data.get('success'):
                        all_results.extend(same_city_data.get('same_city_places', []))
                except Exception as e:
                    logger.error(f"[Graph RAG] Same city search failed for {entity}: {e}")

            # 去重
            seen = set()
            unique_results = []
            for r in all_results:
                name = r.get('name')
                if name and name not in seen:
                    seen.add(name)
                    unique_results.append(r)

            logger.success(f"[Graph RAG Assistant] Found {len(unique_results)} unique results")

            return {
                "success": True,
                "results": unique_results[:10],
                "count": len(unique_results)
            }

        except Exception as e:
            logger.error(f"[Graph RAG Assistant] Search failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": str(e)
            }

