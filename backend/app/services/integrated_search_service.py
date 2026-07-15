"""
综合搜索服务

复用AI推荐的检索能力 + 添加结构化筛选
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
import asyncio


class IntegratedSearchService:
    """
    综合搜索服务 - 多路RAG检索 + 结构化筛选

    功能：
    - 多路RAG检索（复用AI推荐的检索能力）
    - 结构化筛选（预算、天数、类型、季节、兴趣标签）
    - Milvus层筛选（性能优化）
    - 应用层筛选（复杂条件）
    - 流式返回结果

    检索路径：
    1. Milvus稠密向量检索（语义相似度）
    2. Milvus稀疏向量检索（关键词匹配）
    3. Milvus精确匹配（实体名称）
    4. Neo4j图谱检索（附近景点）

    筛选方式：
    - Milvus层：预算范围、天数范围、旅行类型、季节（expr表达式）
    - 应用层：兴趣标签（数组交集，expr不易处理）

    使用场景：
    - 探索式搜索（用户主动搜索）
    - 高级筛选（多条件组合）
    - 分类浏览
    """

    def __init__(self):
        """初始化搜索服务"""
        self.milvus_client = None
        self.neo4j_client = None
        self.embedding_service = None

    async def search_stream(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式搜索"""
        logger.info(f"[IntegratedSearch] Starting search: {query}")
        logger.info(f"[IntegratedSearch] Filters: {filters}")

        try:
            # Step 1: Query处理
            yield {
                "type": "progress",
                "step": "query_processing",
                "message": "正在分析查询...",
                "progress": 10
            }

            entities = self._extract_entities(query)

            # Step 2: 多路RAG检索（传入filters）
            yield {
                "type": "progress",
                "step": "retrieval",
                "message": "正在搜索知识库...",
                "progress": 20
            }

            milvus_results, neo4j_results = await asyncio.gather(
                self._search_milvus(query, entities, top_k, filters),
                self._search_neo4j(entities),
                return_exceptions=True
            )

            if isinstance(milvus_results, Exception):
                milvus_results = []
            if isinstance(neo4j_results, Exception):
                neo4j_results = []

            yield {
                "type": "progress",
                "step": "retrieval_complete",
                "message": f"检索到 {len(milvus_results)} 条Milvus结果，{len(neo4j_results)} 条图谱结果",
                "progress": 50
            }

            # Step 3: 融合
            yield {
                "type": "progress",
                "step": "fusion",
                "message": "正在融合结果...",
                "progress": 60
            }

            fused_results = self._rrf_fusion(milvus_results, neo4j_results)

            # Step 4: 筛选
            if filters:
                yield {
                    "type": "progress",
                    "step": "filtering",
                    "message": "正在应用筛选条件...",
                    "progress": 70
                }
                filtered_results = self._apply_filters(fused_results, filters)
            else:
                filtered_results = fused_results

            # Step 5: 返回结果
            yield {
                "type": "progress",
                "step": "results_ready",
                "message": f"找到 {len(filtered_results)} 个符合条件的结果",
                "progress": 90
            }

            for idx, result in enumerate(filtered_results[:top_k]):
                yield {
                    "type": "result",
                    "index": idx,
                    "data": result
                }
                await asyncio.sleep(0.05)

            yield {
                "type": "complete",
                "total": len(filtered_results),
                "returned": min(len(filtered_results), top_k),
                "message": "搜索完成",
                "progress": 100
            }

        except Exception as e:
            logger.error(f"[IntegratedSearch] Search failed: {e}")
            yield {"type": "error", "message": str(e)}

    async def _search_milvus(
        self,
        query: str,
        entities: List[str],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Milvus混合检索（支持Milvus层过滤）"""
        try:
            from app.core.milvus_hybrid_client import get_milvus_hybrid_client
            from app.core.embedding_service import get_embedding_service

            if not self.milvus_client:
                self.milvus_client = get_milvus_hybrid_client()
            if not self.embedding_service:
                self.embedding_service = get_embedding_service()

            # 构建Milvus过滤表达式
            expr = self._build_milvus_expr(filters)
            if expr:
                logger.info(f"[IntegratedSearch] Milvus filter: {expr}")

            # 1. 稠密检索（带过滤）
            dense_vector = self.embedding_service.encode(query, normalize_embeddings=True)
            dense_results = await self.milvus_client._search_dense(dense_vector, top_k=top_k, expr=expr)

            # 2. 稀疏检索（带过滤）
            sparse_results = await self.milvus_client._search_sparse(query, top_k=top_k, expr=expr)

            # 3. 精确匹配（也带过滤）
            exact_results = []
            if entities:
                for entity in entities[:5]:
                    try:
                        # 构建包含过滤的表达式
                        entity_expr = f'name == "{entity}"'
                        if expr:
                            entity_expr = f'{entity_expr} && {expr}'

                        entity_results = self.milvus_client.collection.query(
                            expr=entity_expr,
                            output_fields=[
                                "name", "province", "city", "category", "description", "rating",
                                "estimated_budget", "recommended_days", "travel_type", "tags", "best_season"
                            ],
                            limit=3
                        )
                        for r in entity_results:
                            exact_results.append({
                                'name': r.get('name'),
                                'city': r.get('city'),
                                'province': r.get('province'),
                                'category': r.get('category'),
                                'description': r.get('description'),
                                'rating': r.get('rating', 0),
                                'estimated_budget': r.get('estimated_budget', 0),
                                'recommended_days': r.get('recommended_days', 1),
                                'travel_type': r.get('travel_type', ''),
                                'tags': list(r.get('tags', [])),  # 转换为list
                                'best_season': list(r.get('best_season', [])),  # 转换为list
                                'score': 1.0
                            })
                    except:
                        pass

            seen = set()
            merged = []
            for r in exact_results + dense_results + sparse_results:
                name = r.get('name')
                if name and name not in seen:
                    seen.add(name)
                    merged.append(r)

            filtered = [r for r in merged if r.get('score', 0) >= 0.7]
            return filtered
        except Exception as e:
            logger.error(f"Milvus search failed: {e}")
            return []

    async def _search_neo4j(self, entities: List[str]) -> List[Dict[str, Any]]:
        """Neo4j图谱检索"""
        if not entities:
            return []
        try:
            from app.core.neo4j_client import get_neo4j_client
            if not self.neo4j_client:
                self.neo4j_client = get_neo4j_client()

            results = []
            for entity in entities[:3]:
                try:
                    query = """
                    MATCH (d1:Destination {name: $name})-[:LOCATED_IN]->(c:City)
                    MATCH (d2:Destination)-[:LOCATED_IN]->(c)
                    WHERE d2.name <> d1.name
                    RETURN d2.name as name, d2.city as city, d2.category as category, d2.description as description
                    LIMIT 5
                    """
                    same_city = self.neo4j_client.query(query, {"name": entity})
                    for r in same_city:
                        results.append({
                            'name': r.get('name'),
                            'city': r.get('city'),
                            'category': r.get('category'),
                            'description': r.get('description', ''),
                            'score': 0.8,
                            'source': 'neo4j'
                        })
                except:
                    pass
            return results
        except Exception as e:
            logger.error(f"Neo4j search failed: {e}")
            return []

    def _rrf_fusion(self, milvus_results: List[Dict], neo4j_results: List[Dict]) -> List[Dict]:
        """融合"""
        all_results = milvus_results + neo4j_results
        seen = set()
        unique = []
        for r in all_results:
            name = r.get('name')
            if name and name not in seen:
                seen.add(name)
                unique.append(r)
        unique.sort(key=lambda x: x.get('score', 0), reverse=True)
        return unique

    def _apply_filters(self, results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """筛选（仅处理Milvus无法处理的复杂筛选）"""
        filtered = results

        # 兴趣标签筛选（数组交集，Milvus expr不易处理）
        if filters.get("interests"):
            interests = set(filters["interests"])
            filtered = [r for r in filtered if interests & set(r.get('tags', []))]
            logger.info(f"[Filter] Interests filter: {len(filtered)} results")

        return filtered

    def _build_milvus_expr(self, filters: Optional[Dict[str, Any]]) -> str:
        """构建Milvus过滤表达式"""
        if not filters:
            return ""

        conditions = []

        # 1. 预算范围
        if filters.get("budget_range"):
            min_b, max_b = filters["budget_range"]
            conditions.append(f"estimated_budget >= {min_b} && estimated_budget <= {max_b}")

        # 2. 天数范围
        if filters.get("duration_range"):
            min_d, max_d = filters["duration_range"]
            conditions.append(f"recommended_days >= {min_d} && recommended_days <= {max_d}")

        # 3. 旅行类型（精确匹配）
        if filters.get("travel_type"):
            travel_type = filters["travel_type"]
            conditions.append(f'travel_type == "{travel_type}"')

        # 4. 季节（数组包含）
        if filters.get("season"):
            season = filters["season"]
            conditions.append(f'array_contains(best_season, "{season}")')

        # 组合条件
        if conditions:
            expr = " && ".join(conditions)
            return expr

        return ""

    def _extract_entities(self, query: str) -> List[str]:
        """实体提取"""
        import re
        keywords = ['山', '寺', '湖', '岛', '古镇', '公园', '景区']
        entities = []
        for kw in keywords:
            pattern = f'[\\u4e00-\\u9fa5]+{kw}'
            matches = re.findall(pattern, query)
            entities.extend(matches)
        return list(set(entities))[:5]


_integrated_search_service = None

def get_integrated_search_service() -> IntegratedSearchService:
    global _integrated_search_service
    if _integrated_search_service is None:
        _integrated_search_service = IntegratedSearchService()
    return _integrated_search_service
