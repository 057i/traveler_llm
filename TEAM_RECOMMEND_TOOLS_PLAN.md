# AI团队推荐 - Tools工具化方案

## 🎯 目标

将RAG和GraphRAG功能封装为独立的工具函数，供子智能体调用，而不是封装到类方法中。

## 📋 当前问题

**当前架构：**
```python
class BaseSubAgent:
    async def execute(self, task, context):
        # 直接调用Qwen LLM
        response = Generation.call(model=settings.QWEN_MODEL, ...)
        # 没有function calling支持
```

**限制：**
- ❌ Qwen的Generation API不支持function calling
- ❌ 无法让LLM自主决定调用工具
- ❌ 需要手动解析LLM输出并调用工具

## 🔧 解决方案

### 方案A：创建独立工具函数 + 手动路由（推荐）

创建独立的工具函数，Master Agent根据查询类型决定调用哪些工具。

#### 1. 创建工具函数文件

**`backend/app/workflows/team_recommend/tools/rag_tools.py`**

```python
"""
RAG Tools for Team Recommendation

独立的RAG检索工具函数
"""
from loguru import logger
from typing import List, Dict, Any
from app.core.milvus_hybrid_client import get_milvus_hybrid_client
from app.utils.ranking import rrf_fusion


async def search_milvus_hybrid(
    query: str,
    entities: List[str] = None,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Milvus混合检索工具
    
    执行稠密向量、稀疏向量、精确匹配的混合检索
    
    Args:
        query: 查询文本
        entities: 实体列表（用于精确匹配）
        top_k: 返回结果数
        
    Returns:
        {
            "results": [...],
            "count": 数量,
            "confidence": 置信度
        }
    """
    logger.info(f"[RAG Tool] search_milvus_hybrid: query='{query}', entities={entities}")
    
    try:
        milvus_client = get_milvus_hybrid_client()
        
        # 1. 稠密检索
        dense_results = await milvus_client.search_dense(
            query_text=query,
            top_k=top_k
        )
        
        # 2. 稀疏检索
        sparse_results = await milvus_client.search_sparse(
            query_text=query,
            top_k=top_k
        )
        
        # 3. 精确匹配
        exact_results = []
        if entities:
            for entity in entities[:5]:
                matches = await milvus_client.search_exact(
                    entity_name=entity,
                    top_k=3
                )
                exact_results.extend(matches)
        
        # 4. RRF融合
        fused_results = rrf_fusion(
            dense_results,
            sparse_results,
            exact_results,
            k=60
        )
        
        # 5. 质量过滤
        filtered_results = [
            r for r in fused_results
            if r.get('score', 0) >= 0.5
        ]
        
        # 6. 计算置信度
        confidence = _calculate_confidence(filtered_results)
        
        logger.success(f"[RAG Tool] Found {len(filtered_results)} results, confidence={confidence:.3f}")
        
        return {
            "success": True,
            "results": filtered_results[:top_k],
            "count": len(filtered_results),
            "confidence": confidence,
            "source": "milvus"
        }
        
    except Exception as e:
        logger.error(f"[RAG Tool] search_milvus_hybrid failed: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "confidence": 0.0,
            "error": str(e)
        }


def _calculate_confidence(results: List[Dict]) -> float:
    """计算置信度"""
    if not results:
        return 0.0
    
    top_results = results[:5]
    avg_score = sum(r.get('score', 0) for r in top_results) / len(top_results)
    count_factor = min(len(results) / 5.0, 1.0)
    
    return avg_score * 0.7 + count_factor * 0.3
```

**`backend/app/workflows/team_recommend/tools/graph_tools.py`**

```python
"""
Graph RAG Tools for Team Recommendation

独立的Neo4j图查询工具函数
"""
from loguru import logger
from typing import List, Dict, Any
from app.core.neo4j_client import get_neo4j_client


async def search_nearby_destinations(
    entity: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    查询附近景点
    
    Args:
        entity: 景点名称
        max_results: 最大结果数
        
    Returns:
        {
            "results": [...],
            "count": 数量
        }
    """
    logger.info(f"[Graph Tool] search_nearby_destinations: entity='{entity}'")
    
    try:
        neo4j_client = get_neo4j_client()
        
        query = """
        MATCH (d1:Destination {name: $entity})-[:NEARBY_OF]->(d2:Destination)
        WHERE d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT $limit
        """
        
        results = neo4j_client.query(query, {
            "entity": entity,
            "limit": max_results
        })
        
        logger.success(f"[Graph Tool] Found {len(results)} nearby destinations")
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "source": "neo4j_nearby"
        }
        
    except Exception as e:
        logger.error(f"[Graph Tool] search_nearby_destinations failed: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": str(e)
        }


async def search_same_city_destinations(
    entity: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    查询同城景点
    
    Args:
        entity: 景点名称
        max_results: 最大结果数
        
    Returns:
        {
            "results": [...],
            "count": 数量
        }
    """
    logger.info(f"[Graph Tool] search_same_city_destinations: entity='{entity}'")
    
    try:
        neo4j_client = get_neo4j_client()
        
        query = """
        MATCH (d1:Destination {name: $entity})-[:LOCATED_IN]->(c:City)
        MATCH (d2:Destination)-[:LOCATED_IN]->(c)
        WHERE d2.name <> d1.name AND d2.name IS NOT NULL
        RETURN d2.name as name,
               d2.city as city,
               d2.category as category,
               d2.description as description
        LIMIT $limit
        """
        
        results = neo4j_client.query(query, {
            "entity": entity,
            "limit": max_results
        })
        
        logger.success(f"[Graph Tool] Found {len(results)} same city destinations")
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "source": "neo4j_same_city"
        }
        
    except Exception as e:
        logger.error(f"[Graph Tool] search_same_city_destinations failed: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": str(e)
        }


async def search_graph_comprehensive(
    entities: List[str],
    max_results_per_type: int = 5
) -> Dict[str, Any]:
    """
    综合图查询（附近+同城+同类）
    
    Args:
        entities: 实体列表
        max_results_per_type: 每种类型的最大结果数
        
    Returns:
        {
            "results": [...],
            "count": 数量
        }
    """
    logger.info(f"[Graph Tool] search_graph_comprehensive: entities={entities}")
    
    if not entities:
        return {
            "success": True,
            "results": [],
            "count": 0
        }
    
    all_results = []
    
    try:
        for entity in entities[:3]:  # 限制最多3个实体
            # 附近景点
            nearby = await search_nearby_destinations(entity, max_results_per_type)
            all_results.extend(nearby.get('results', []))
            
            # 同城景点
            same_city = await search_same_city_destinations(entity, max_results_per_type)
            all_results.extend(same_city.get('results', []))
        
        # 去重
        unique_results = _deduplicate_results(all_results)
        
        logger.success(f"[Graph Tool] Comprehensive search: {len(unique_results)} unique results")
        
        return {
            "success": True,
            "results": unique_results[:15],
            "count": len(unique_results),
            "source": "neo4j_comprehensive"
        }
        
    except Exception as e:
        logger.error(f"[Graph Tool] search_graph_comprehensive failed: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "error": str(e)
        }


def _deduplicate_results(results: List[Dict]) -> List[Dict]:
    """结果去重"""
    seen = set()
    unique = []
    
    for r in results:
        name = r.get('name')
        if name and name not in seen:
            seen.add(name)
            unique.append(r)
    
    return unique
```

#### 2. 简化子智能体类

**新的 `rag_assistant.py`**

```python
"""
RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent
from ..tools.rag_tools import search_milvus_hybrid


class RAGAssistant(BaseSubAgent):
    """RAG Assistant - 使用Milvus混合检索工具"""

    def __init__(self):
        super().__init__(
            name="RAG Knowledge Assistant",
            system_prompt="""你是一个RAG知识库助手。

你可以使用 search_milvus_hybrid 工具从向量数据库中检索旅游信息。

工具说明：
- search_milvus_hybrid(query, entities) - 混合检索工具，返回相关景点

请根据用户查询调用工具并返回结果。"""
        )
        
        # 注册可用工具
        self.tools = {
            "search_milvus_hybrid": search_milvus_hybrid
        }
    
    async def search(self, query: str, entities: List[str] = None):
        """便捷方法：直接调用搜索工具"""
        return await search_milvus_hybrid(query, entities)
```

**新的 `graph_rag_assistant.py`**

```python
"""
Graph RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent
from ..tools.graph_tools import (
    search_nearby_destinations,
    search_same_city_destinations,
    search_graph_comprehensive
)


class GraphRAGAssistant(BaseSubAgent):
    """Graph RAG Assistant - 使用Neo4j图查询工具"""

    def __init__(self):
        super().__init__(
            name="Graph RAG Assistant",
            system_prompt="""你是一个图RAG助手。

你可以使用以下工具从知识图谱中检索信息：
- search_nearby_destinations(entity) - 查询附近景点
- search_same_city_destinations(entity) - 查询同城景点
- search_graph_comprehensive(entities) - 综合查询

请根据用户查询调用相应工具。"""
        )
        
        # 注册可用工具
        self.tools = {
            "search_nearby_destinations": search_nearby_destinations,
            "search_same_city_destinations": search_same_city_destinations,
            "search_graph_comprehensive": search_graph_comprehensive
        }
    
    async def search(self, entities: List[str]):
        """便捷方法：直接调用综合搜索"""
        return await search_graph_comprehensive(entities)
```

#### 3. 更新Master Agent

```python
async def _run_rag_assistant(self, query: str) -> List[Dict[str, Any]]:
    """执行RAG检索"""
    try:
        entities = self._extract_entities(query)
        
        # 直接调用工具
        result = await self.rag_assistant.search(query, entities)
        
        return result.get('results', [])
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return []

async def _run_graph_rag_assistant(self, query: str, rag_results: List[Dict]) -> List[Dict]:
    """执行图查询"""
    try:
        entities = [r.get('name') for r in rag_results[:5] if r.get('name')]
        
        # 直接调用工具
        result = await self.graph_rag_assistant.search(entities)
        
        return result.get('results', [])
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        return []
```

---

### 方案B：升级到LangChain + function calling（需要更多改动）

使用LangChain框架 + 支持function calling的模型（如GPT-4）。

**优点：**
- ✅ LLM自主决定调用工具
- ✅ 更灵活的工具组合

**缺点：**
- ❌ 需要替换整个Agent框架
- ❌ 需要使用支持function calling的模型
- ❌ 改动较大

---

## 🎯 推荐实施方案A

**优点：**
- ✅ 工具函数独立，易于测试和维护
- ✅ 不需要改动BaseSubAgent
- ✅ Master Agent统一调度
- ✅ 保持当前架构

**实施步骤：**
1. 创建 `tools/rag_tools.py`
2. 创建 `tools/graph_tools.py`
3. 简化子智能体类（添加便捷方法）
4. 更新Master Agent调用逻辑

**是否开始实施方案A？**
