# 🔄 新搜索架构设计方案

---

## 📋 架构对比

### 当前架构
```
查询重写（单一） → 并行检索（Milvus + Neo4j） → RRF融合 → 置信度检查 → Tavily → Rerank → LLM润色
```

### 新架构
```
查询理解（多路重写） → 多查询向量检索 → 置信度判断 → (低分→Tavily补充) → 统一Rerank → LLM润色
                     ↓
                 条件化图谱检索（仅need_nearby=true）
```

---

## 🎯 核心改进点

### 1. 查询理解增强
**当前**：
```python
# 简单重写
rewritten_query = llm_rewrite(user_query)
needs_nearby = llm_judge(rewritten_query)
```

**改进后**：
```python
# 深度理解 + 多路重写
understanding = {
    "entities": ["故宫"],           # 实体提取
    "intent": "nearby_food",         # 意图识别
    "need_nearby": true,            # 是否需要附近
    "rewritten_queries": [          # 多个重写查询
        "故宫周边餐厅推荐",
        "故宫附近美食攻略",
        "前门大街美食"
    ]
}
```

### 2. 多查询向量检索
**当前**：
```python
# 只检索一次
milvus_results = milvus.search(rewritten_query, top_k=10)
```

**改进后**：
```python
# 对每个重写查询都检索
all_results = []
for query in rewritten_queries:
    dense_results = milvus.dense_search(query, top_k=10)
    sparse_results = milvus.sparse_search(query, top_k=10)
    fused = rrf_fusion(dense_results, sparse_results)
    all_results.extend(fused[:5])  # 每个查询取Top5

# 去重合并
final_results = deduplicate(all_results)
```

### 3. 置信度判断优化
**当前**：
```python
# 计算平均分
avg_score = sum(scores) / len(scores)
if avg_score < 0.6:
    # 触发Tavily
```

**改进后**：
```python
# 看最高分
max_score = max(scores)
if max_score < 0.5:  # 🆕 更严格的阈值
    logger.warning("置信度低，触发Tavily补充搜索")
    tavily_results = tavily_search(user_query)
    all_results.extend(tavily_results)
```

### 4. 条件化图谱检索
**当前**：
```python
# 总是执行Neo4j检索（虽然现在返回空）
neo4j_results = neo4j_search()
```

**改进后**：
```python
# 只在need_nearby=true时执行
if need_nearby and has_base_results:
    nearby = neo4j.find_nearby_destinations(
        top3_destinations,
        max_recommendations=5
    )
```

### 5. 统一Rerank
**当前**：
```python
# 分阶段Rerank
milvus_reranked = rerank(milvus_results)
if tavily_triggered:
    all_results = milvus_reranked + tavily_results
    final_reranked = rerank(all_results)
```

**改进后**：
```python
# 所有来源一起Rerank
all_sources = milvus_results + tavily_results + neo4j_results
final_top1 = rerank(all_sources, top_k=1)
```

---

## 📁 需要修改的文件

### 1. State定义
```python
# app/workflows/ai_recommend/state.py
class AIRecommendState(TypedDict):
    # 新增字段
    entities: List[str]              # 提取的实体
    intent: str                      # 用户意图
    rewritten_queries: List[str]     # 多个重写查询
    
    # 原有字段保持
    needs_nearby_recommendations: bool
    milvus_results: List[Dict]
    ...
```

### 2. 查询理解节点
```python
# app/workflows/ai_recommend/nodes/node_query_rewriter.py
async def query_rewriter_node(state):
    # 调用LLM做深度理解
    understanding = llm_understand(user_query)
    
    state["entities"] = understanding["entities"]
    state["intent"] = understanding["intent"]
    state["need_nearby"] = understanding["need_nearby"]
    state["rewritten_queries"] = understanding["rewritten_queries"]
    
    return state
```

### 3. 多查询检索节点
```python
# app/workflows/ai_recommend/nodes/node_parallel_retrieval.py
async def parallel_retrieval_node(state):
    rewritten_queries = state["rewritten_queries"]
    
    # 对每个查询做检索
    all_results = []
    for query in rewritten_queries:
        results = await milvus_search_single(query)
        all_results.extend(results[:5])
    
    # 去重
    unique_results = deduplicate_by_name(all_results)
    
    state["milvus_results"] = unique_results
    return state
```

### 4. 置信度检查节点（修改）
```python
# app/workflows/ai_recommend/nodes/node_confidence_check.py
async def confidence_check_node(state):
    results = state["rrf_results"]
    
    # 🆕 改为检查最高分
    max_score = max([r.score for r in results]) if results else 0.0
    
    # 🆕 阈值改为0.5
    needs_tavily = max_score < 0.5
    
    state["needs_web_search"] = needs_tavily
    state["confidence_score"] = max_score
    
    logger.info(f"最高分: {max_score:.3f}, 阈值: 0.5, 需要Tavily: {needs_tavily}")
    
    return state
```

### 5. Rerank节点（修改）
```python
# app/workflows/ai_recommend/nodes/node_rerank.py
async def rerank_node(state):
    # 合并所有来源
    all_results = (
        state["rrf_results"] + 
        (state["tavily_results"] or []) +
        state["nearby_destinations"]
    )
    
    # 统一Rerank
    reranked = rerank_engine.rerank(
        query=state["user_query"],
        candidates=all_results,
        top_n=5  # 最终返回Top5
    )
    
    state["reranked_results"] = reranked
    return state
```

---

## 🧪 测试用例

### 用例1: 故宫附近美食（低置信度 + need_nearby）
```python
输入：故宫附近有什么好吃的

查询理解：
  entities: ["故宫"]
  intent: "nearby_food"
  need_nearby: true
  rewritten_queries: [
    "故宫周边餐厅推荐",
    "故宫附近美食攻略",
    "前门大街美食"
  ]

向量检索（3个查询）：
  查询1: 杭州西湖美食攻略（0.3） ❌ 不相关
  查询2: 北京旅游指南（0.4）     ❌ 弱相关
  查询3: 上海美食推荐（0.35）     ❌ 不相关
  
  最高分: 0.4 < 0.5 ✅ 触发Tavily

Tavily补充：
  全聚德烤鸭店（故宫附近）
  护国寺小吃街
  前门大街美食

Neo4j附近推荐：
  天安门广场（故宫附近）
  景山公园（故宫后面）

统一Rerank（全部候选）：
  Top1: 全聚德烤鸭店（来自Tavily）
  Top2: 护国寺小吃街（来自Tavily）
  Top3: 天安门广场（来自Neo4j）
```

### 用例2: 三清山旅游（高置信度 + 不需要nearby）
```python
输入：三清山旅游攻略

查询理解：
  entities: ["三清山"]
  intent: "travel_guide"
  need_nearby: false
  rewritten_queries: [
    "三清山旅游攻略",
    "三清山景点介绍",
    "三清山最佳旅游时间"
  ]

向量检索（3个查询）：
  查询1: 三清山旅游攻略（0.85） ✅ 高相关
  查询2: 三清山景点详解（0.82） ✅ 高相关
  查询3: 三清山旅游指南（0.79） ✅ 高相关
  
  最高分: 0.85 > 0.5 ✅ 不触发Tavily

Neo4j附近推荐：
  need_nearby=false ✅ 跳过

统一Rerank（只有Milvus结果）：
  Top1: 三清山旅游攻略（0.85）
  Top2: 三清山景点详解（0.82）
  Top3: 三清山旅游指南（0.79）
```

---

## 🚀 实施计划

### 阶段1: State和查询理解（30分钟）
- [ ] 修改state.py，添加新字段
- [ ] 重写node_query_rewriter.py，实现深度理解
- [ ] 修改service.py初始化state

### 阶段2: 多查询检索（30分钟）
- [ ] 修改node_parallel_retrieval.py
- [ ] 实现多查询循环检索
- [ ] 实现去重逻辑

### 阶段3: 置信度优化（15分钟）
- [ ] 修改node_confidence_check.py
- [ ] 改为检查最高分
- [ ] 阈值改为0.5

### 阶段4: 统一Rerank（15分钟）
- [ ] 修改node_rerank.py
- [ ] 合并所有来源
- [ ] 统一重排序

### 阶段5: 测试验证（30分钟）
- [ ] 测试"故宫附近美食"
- [ ] 测试"三清山旅游"
- [ ] 验证Tavily触发逻辑

**总计：2小时**

---

## ⚠️ 注意事项

1. **多查询去重**：按景点名称去重，保留最高分
2. **性能开销**：3个查询 × 2次检索 = 6次Milvus调用
3. **Tavily配额**：只在低置信度时触发，节省配额
4. **Neo4j条件化**：只在need_nearby=true时执行
5. **向后兼容**：保持原有state字段，只添加新字段

---

**设计完成时间**: 2026-07-11 18:20  
**预计实施时间**: 2小时  
**风险等级**: 中等（需要重构多个节点）  
**建议**: 先在测试环境验证，再部署到生产
