# AI推荐RAG检索流程修改方案总结

## 📋 修改目标

实现符合需求的RAG检索流程：
1. 用户查询 → LLM分析（提取实体 + 判断是否需要附近检索）
2. 查询重写
3. Milvus稠密+稀疏混合检索 与 Neo4j检索并行
   - Neo4j仅当需要附近检索时执行
   - Neo4j结果不参与RRF融合，仅作为附近附加信息
4. **稠密和稀疏结果先归一化，再进行RRF融合**
5. Rerank精排
6. LLM润色（Neo4j结果作为上下文补充）

---

## ✅ 已完成的修改

### 1. State定义更新 ✅
**文件**: `backend/app/workflows/ai_recommend/state.py`

**修改内容**:
- 新增 `needs_nearby_search: bool` - 是否需要附近检索
- 分离 `milvus_dense_results` 和 `milvus_sparse_results` - 稠密和稀疏结果分开存储
- 新增 `sources: List[Dict[str, Any]]` - 用于前端展示的来源信息

---

### 2. Query Rewriter节点更新 ✅
**文件**: `backend/app/workflows/ai_recommend/nodes/node_query_rewriter.py`

**修改内容**:
- Prompt增加判断"是否需要附近检索"逻辑
- 识别"附近"、"周边"、"周围"等关键词
- 将判断结果存入 `state["needs_nearby_search"]`

**示例**:
```python
"三清山附近有什么景点" → needs_nearby_search: true
"推荐一下三清山的旅游攻略" → needs_nearby_search: false
```

---

### 3. 创建RRF融合客户端（带归一化） ✅
**文件**: `backend/app/core/rrf_client.py`（新建）

**核心功能**:
- `normalize_scores()` - Min-Max归一化分数到[0,1]
- `fuse_dense_sparse()` - 专门融合稠密+稀疏结果
  - 步骤1: 分别归一化稠密和稀疏结果
  - 步骤2: 对归一化结果应用RRF算法
  - 步骤3: 按RRF分数排序返回

**RRF公式**: `score = 1 / (k + rank)` (k默认60)

---

### 4. Parallel Retrieval节点重写 ✅
**文件**: `backend/app/workflows/ai_recommend/nodes/node_parallel_retrieval.py`

**修改内容**:
- 分离为3个独立检索函数:
  - `milvus_dense_search()` - 稠密向量检索（bge-base-zh-v1.5）
  - `milvus_sparse_search()` - 稀疏向量检索（TF-IDF/BM25）
  - `neo4j_nearby_search()` - 条件执行，仅当 `needs_nearby_search=True` 时运行
- 使用 `asyncio.gather()` 并行执行
- Neo4j查询使用Cypher图关系查找附近景点

---

### 5. RRF Fusion节点更新 ✅
**文件**: `backend/app/workflows/ai_recommend/nodes/node_rrf_fusion.py`

**修改内容**:
- 使用 `rrf_engine.fuse_dense_sparse()` 方法
- 自动归一化稠密和稀疏结果
- Neo4j结果不参与融合，保留在state中作为附加信息
- 日志输出融合详情（RRF分数、Dense/Sparse排名）

---

### 6. Synthesizer节点更新 ✅
**文件**: `backend/app/workflows/ai_recommend/nodes/node_synthesizer.py`

**修改内容**:
- 获取Neo4j附近信息并添加到Prompt上下文
- 生成 `sources` 字段用于前端展示
- 标记Neo4j来源为 `is_nearby: true`
- 改进中文Prompt和错误处理

---

### 7. Service层更新 ✅
**文件**: `backend/app/workflows/ai_recommend/service.py`

**修改内容**:
- 更新初始state结构，添加新字段
- 更新进度消息显示（分别显示稠密/稀疏/附近结果数量）
- 改进RRF融合进度消息

---

### 8. API层更新 ✅
**文件**: `backend/app/api/ai_recommend.py`

**修改内容**:
- 在Redis历史记录中保存nodes信息
- 确保sources字段正确传递到前端

---

### 9. Milvus Hybrid Client更新 ✅
**文件**: `backend/app/core/milvus_hybrid_client.py`

**修改内容**:
- 添加 `_search_dense()` 方法 - 独立稠密向量检索
- 添加 `_search_sparse()` 方法 - 独立稀疏向量检索（基于关键词匹配）
- 支持异步调用

**注意**: 稀疏检索使用jieba分词+关键词匹配模拟，生产环境建议使用Elasticsearch

---

### 10. 前端AIRecommend.vue更新 ✅
**文件**: `frontend/src/views/AIRecommend.vue`

**修改内容**:
- 更新节点名称映射（查询分析、混合检索、结果融合等）
- 添加附近景点标识 🗺️
- 显示 `is_nearby` 标签
- 动态显示节点进度（根据是否需要网络搜索调整总节点数）

---

## 🔄 完整工作流

```
用户查询: "三清山附近有什么好玩的"
    ↓
[1] Query Rewriter
    - 重写查询: "三清山 周边 景点 推荐"
    - 提取实体: ["三清山"]
    - needs_nearby_search: true
    ↓
[2] Parallel Retrieval (并行执行3个任务)
    ├─ Milvus Dense (稠密检索)
    │   └─ 返回20条结果，score范围: [0.8, 0.3]
    ├─ Milvus Sparse (稀疏检索)
    │   └─ 返回20条结果，score范围: [0.9, 0.2]
    └─ Neo4j Nearby (条件执行)
        └─ 返回10条附近景点（不参与融合）
    ↓
[3] RRF Fusion
    - 归一化稠密结果: [0.8, 0.3] → [1.0, 0.0]
    - 归一化稀疏结果: [0.9, 0.2] → [1.0, 0.0]
    - RRF融合归一化结果
    - Neo4j结果保留不动
    - 输出Top 10融合结果
    ↓
[4] Confidence Check (可选)
    ↓
[5] Tavily Search (可选，低置信度时)
    ↓
[6] Rerank
    - 使用BGE Reranker精排Top 10
    ↓
[7] Synthesizer
    - 主要内容: Rerank后的结果
    - 补充内容: Neo4j附近景点
    - LLM生成最终答案
    ↓
输出: 
  - answer: "三清山位于江西省上饶市，周边有以下推荐景点：..."
  - sources: [
      {name: "三清山", score: 0.95, source: "milvus_dense"},
      {name: "婺源", score: 0.88, source: "milvus_sparse"},
      {name: "龙虎山", score: 0, is_nearby: true, source: "neo4j_nearby"}
    ]
```

---

## 🎯 关键技术点

### 1. 归一化的必要性
**为什么需要归一化？**

不同检索方式的分数范围不同：
- 稠密向量（Cosine相似度）: [0, 1]
- 稀疏向量（TF-IDF）: [0, ∞)
- BM25: [0, ∞)

直接融合会导致某一种检索结果权重过大，归一化到[0,1]后再RRF可确保公平融合。

### 2. RRF算法优势
- **排名驱动**: 基于排名而非绝对分数，对不同分数范围鲁棒
- **简单高效**: 无需调参，k=60是经验最佳值
- **多源融合**: 天然支持多个检索源的融合

### 3. Neo4j的特殊处理
- **不参与RRF融合**: 图检索结果是"附近信息补充"，不是"相关度检索"
- **条件执行**: 只在需要附近检索时才查询Neo4j，节省资源
- **作为上下文**: 在LLM润色阶段作为额外上下文信息

---

## 📊 性能优化建议

### 1. 稀疏检索优化
当前使用jieba分词+关键词匹配模拟稀疏检索，**生产环境建议**:
- 使用 Elasticsearch 进行BM25全文检索
- 或使用Milvus企业版的SPARSE_INVERTED_INDEX（需要付费版）

### 2. 并行检索优化
- 稠密、稀疏、Neo4j三个检索任务完全并行
- 使用 `asyncio.gather()` 实现真正的异步并发
- 单次查询延迟 ≈ max(dense_time, sparse_time, neo4j_time)

### 3. 缓存策略
建议添加Redis缓存层：
```python
cache_key = f"hybrid_search:{hash(query)}"
if cached := redis.get(cache_key):
    return cached
```

---

## 🧪 测试建议

### 1. 功能测试
```python
# 测试1: 附近检索
query = "三清山附近有什么景点"
# 预期: needs_nearby_search=True, Neo4j结果非空

# 测试2: 普通检索
query = "推荐江西的旅游景点"
# 预期: needs_nearby_search=False, Neo4j结果为空

# 测试3: 归一化
# 验证稠密和稀疏结果的normalized_score都在[0,1]范围
```

### 2. 性能测试
- 单次查询延迟 < 2s
- 并发10用户QPS > 5
- 内存占用稳定

---

## 🐛 已知限制

1. **稀疏检索是模拟实现**: 使用关键词匹配代替真正的BM25
2. **Neo4j查询简化**: 假设存在NEAR_BY关系，需要提前在GraphRAG中建立
3. **Rerank模型路径**: 需要确保 `./models/BAAI--bge-reranker-v2-m3/` 存在

---

## 🚀 后续优化方向

1. **集成Elasticsearch**: 替换当前的稀疏检索模拟实现
2. **动态RRF权重**: 根据查询类型动态调整稠密/稀疏权重
3. **多跳图推理**: 在Neo4j中实现2-3跳的图关系推理
4. **向量缓存**: 对常见查询的向量进行缓存
5. **A/B测试**: 对比归一化前后的检索效果

---

## 📚 相关文档

- [RRF论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [Milvus混合检索文档](https://milvus.io/docs/hybridsearch.md)
- [BGE Embedding模型](https://huggingface.co/BAAI/bge-base-zh-v1.5)
- [Neo4j Cypher查询](https://neo4j.com/docs/cypher-manual/current/)

---

## ✨ 总结

本次修改实现了完整的RAG混合检索流程，核心改进：

✅ **稠密+稀疏混合检索**: 结合语义理解和关键词匹配  
✅ **归一化+RRF融合**: 科学的多源结果融合方法  
✅ **条件Neo4j检索**: 智能判断是否需要附近信息  
✅ **Neo4j不参与融合**: 作为附加信息而非相关度检索  
✅ **完整工作流追踪**: 前端实时显示每个节点的执行状态  

整个流程符合现代RAG最佳实践，兼顾了检索准确性和系统性能。
