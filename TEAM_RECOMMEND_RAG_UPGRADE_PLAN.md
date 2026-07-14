# AI团队推荐 - RAG子智能体升级方案

## 📊 当前问题分析

### 现状
AI团队推荐中的两个子智能体只是占位符，没有实际的检索逻辑：

**RAG Assistant (rag_assistant.py)**
```python
class RAGAssistant(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="RAG Assistant",
            system_prompt="You are a RAG assistant..."
        )
```

**Graph RAG Assistant (graph_rag_assistant.py)**
```python
class GraphRAGAssistant(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="Graph RAG Assistant",
            system_prompt="You are a graph RAG assistant..."
        )
```

### 对比：AI推荐的实现

**AI推荐的Milvus检索 (node_milvus_hybrid.py)**
- ✅ 三路并行检索：稠密向量 + 稀疏向量 + 精确匹配
- ✅ 内部RRF融合
- ✅ 质量过滤（score阈值）
- ✅ 置信度计算
- ✅ 80-120行实现代码

**AI推荐的Neo4j检索 (node_neo4j_nearby.py)**
- ✅ 基于实体的附近景点查询
- ✅ 条件执行（needs_nearby_search）
- ✅ 关系遍历（NEARBY_OF、LOCATED_IN）
- ✅ 结果格式化
- ✅ 60-100行实现代码

## 🎯 升级方案

### 方案A：复用AI推荐的检索逻辑（推荐）

**优点**
- ✅ 快速实现，复用已验证的代码
- ✅ 保持一致性，检索质量有保障
- ✅ 易于维护，单一数据源

**实现步骤**

#### 1. 升级 RAG Assistant

```python
"""
RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent
from app.core.milvus_hybrid_client import get_milvus_hybrid_client
from loguru import logger
from typing import List, Dict, Any


class RAGAssistant(BaseSubAgent):
    """RAG Assistant - searches knowledge base using Milvus hybrid search"""

    def __init__(self):
        super().__init__(
            name="RAG Knowledge Assistant",
            system_prompt="""你是一个RAG知识库助手，负责从Milvus向量数据库中检索相关旅游信息。

你的任务：
1. 接收用户查询
2. 使用混合检索（稠密向量+稀疏向量+精确匹配）
3. 返回最相关的旅游景点和攻略信息

返回格式：
{
    "results": [
        {
            "name": "景点名称",
            "description": "描述",
            "score": 0.85,
            "category": "类别"
        }
    ],
    "count": 数量
}"""
        )

    async def process(self, query: str, entities: List[str] = None) -> Dict[str, Any]:
        """
        执行RAG检索
        
        Args:
            query: 用户查询
            entities: 提取的实体列表
            
        Returns:
            检索结果
        """
        logger.info(f"[RAG Assistant] Processing query: {query}")
        logger.info(f"[RAG Assistant] Entities: {entities}")

        try:
            # 获取Milvus客户端
            milvus_client = get_milvus_hybrid_client()

            # 执行混合检索
            dense_results = await milvus_client.search_dense(
                query_text=query,
                top_k=10
            )

            sparse_results = await milvus_client.search_sparse(
                query_text=query,
                top_k=10
            )

            # 精确匹配
            exact_results = []
            if entities:
                for entity in entities:
                    matches = await milvus_client.search_exact(
                        entity_name=entity,
                        top_k=5
                    )
                    exact_results.extend(matches)

            # RRF融合
            from app.utils.ranking import rrf_fusion
            fused_results = rrf_fusion(
                dense_results,
                sparse_results,
                exact_results,
                k=60
            )

            # 质量过滤
            filtered_results = [
                r for r in fused_results 
                if r.get('score', 0) >= 0.5
            ]

            logger.success(f"[RAG Assistant] Found {len(filtered_results)} results")

            return {
                "results": filtered_results[:10],
                "count": len(filtered_results),
                "confidence": self._calculate_confidence(filtered_results)
            }

        except Exception as e:
            logger.error(f"[RAG Assistant] Search failed: {e}")
            return {
                "results": [],
                "count": 0,
                "confidence": 0.0,
                "error": str(e)
            }

    def _calculate_confidence(self, results: List[Dict]) -> float:
        """计算置信度"""
        if not results:
            return 0.0
        
        # 基于平均分数和结果数量
        avg_score = sum(r.get('score', 0) for r in results[:5]) / min(len(results), 5)
        count_factor = min(len(results) / 5.0, 1.0)
        
        return avg_score * 0.7 + count_factor * 0.3
```

#### 2. 升级 Graph RAG Assistant

```python
"""
Graph RAG Assistant for Team Recommendation
"""
from .base import BaseSubAgent
from app.core.neo4j_client import get_neo4j_client
from loguru import logger
from typing import List, Dict, Any


class GraphRAGAssistant(BaseSubAgent):
    """Graph RAG Assistant - searches knowledge graph using Neo4j"""

    def __init__(self):
        super().__init__(
            name="Graph RAG Assistant",
            system_prompt="""你是一个图RAG助手，负责从Neo4j知识图谱中检索相关旅游信息。

你的任务：
1. 接收景点实体
2. 查询Neo4j图数据库
3. 找到相关景点、附近景点、同类推荐

返回格式：
{
    "results": [
        {
            "name": "景点名称",
            "city": "城市",
            "category": "类别",
            "relationships": ["附近", "同城"]
        }
    ],
    "count": 数量
}"""
        )

    async def process(self, entities: List[str], query: str = None) -> Dict[str, Any]:
        """
        执行图RAG检索
        
        Args:
            entities: 实体列表
            query: 原始查询（可选）
            
        Returns:
            图检索结果
        """
        logger.info(f"[Graph RAG Assistant] Processing entities: {entities}")

        if not entities:
            logger.warning("[Graph RAG Assistant] No entities provided")
            return {
                "results": [],
                "count": 0
            }

        try:
            neo4j_client = get_neo4j_client()
            all_results = []

            for entity in entities[:3]:  # 限制最多3个实体
                # 查询附近景点
                nearby_query = """
                MATCH (d1:Destination {name: $entity})-[:NEARBY_OF]->(d2:Destination)
                WHERE d2.name IS NOT NULL
                RETURN d2.name as name, 
                       d2.city as city, 
                       d2.category as category,
                       d2.description as description,
                       'nearby' as relationship
                LIMIT 5
                """
                
                nearby_results = neo4j_client.query(nearby_query, {"entity": entity})
                
                # 查询同城景点
                same_city_query = """
                MATCH (d1:Destination {name: $entity})-[:LOCATED_IN]->(c:City)
                MATCH (d2:Destination)-[:LOCATED_IN]->(c)
                WHERE d2.name <> d1.name AND d2.name IS NOT NULL
                RETURN d2.name as name,
                       d2.city as city,
                       d2.category as category,
                       d2.description as description,
                       'same_city' as relationship
                LIMIT 5
                """
                
                same_city_results = neo4j_client.query(same_city_query, {"entity": entity})
                
                all_results.extend(nearby_results)
                all_results.extend(same_city_results)

            # 去重
            seen = set()
            unique_results = []
            for r in all_results:
                if r['name'] not in seen:
                    seen.add(r['name'])
                    unique_results.append(r)

            logger.success(f"[Graph RAG Assistant] Found {len(unique_results)} related locations")

            return {
                "results": unique_results[:10],
                "count": len(unique_results)
            }

        except Exception as e:
            logger.error(f"[Graph RAG Assistant] Graph search failed: {e}")
            return {
                "results": [],
                "count": 0,
                "error": str(e)
            }
```

#### 3. 更新 Master Agent 调用逻辑

```python
# 在 master_agent.py 中更新子智能体调用

# 调用RAG Assistant
rag_result = await rag_assistant.process(
    query=query,
    entities=extracted_entities
)

# 调用Graph RAG Assistant
graph_result = await graph_rag_assistant.process(
    entities=extracted_entities,
    query=query
)

# 合并结果
all_results = []
all_results.extend(rag_result.get('results', []))
all_results.extend(graph_result.get('results', []))
```

---

### 方案B：独立实现（不推荐）

创建完全独立的检索逻辑，但会导致：
- ❌ 代码重复
- ❌ 维护成本高
- ❌ 结果不一致

---

## 📋 实施清单

### Phase 1: 升级RAG Assistant
- [ ] 添加Milvus混合检索逻辑
- [ ] 实现RRF融合
- [ ] 添加质量过滤
- [ ] 计算置信度
- [ ] 测试RAG检索结果

### Phase 2: 升级Graph RAG Assistant  
- [ ] 添加Neo4j查询逻辑
- [ ] 实现附近景点查询
- [ ] 实现同城景点查询
- [ ] 结果去重和排序
- [ ] 测试图检索结果

### Phase 3: 集成测试
- [ ] 更新Master Agent调用
- [ ] 测试完整流程
- [ ] 验证结果质量
- [ ] 性能优化

---

## 🎯 预期效果

### 升级前
- ❌ RAG Assistant: 空壳，无检索功能
- ❌ Graph RAG Assistant: 空壳，无图查询
- ❌ 结果质量: 依赖纯LLM生成

### 升级后
- ✅ RAG Assistant: 完整的混合检索+融合
- ✅ Graph RAG Assistant: 图谱关系查询
- ✅ 结果质量: 基于真实数据，准确度提升
- ✅ 一致性: 与AI推荐使用相同检索逻辑

---

## 🚀 开始实施？

准备好后，我可以帮你：
1. 实现RAG Assistant的完整代码
2. 实现Graph RAG Assistant的完整代码
3. 更新Master Agent的调用逻辑
4. 添加测试用例

**是否开始实施方案A？**
