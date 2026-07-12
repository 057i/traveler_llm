# 相似度分数过低诊断报告

## 问题概述
查询"三清山旅游攻略推荐"的检索结果中，最高相似度分数仅为 **0.6505**，远低于期望的 **0.85**，且所有结果都被阈值 0.7 过滤掉。

---

## 核心问题分析

### 1. **加权融合导致分数被稀释** ⭐⭐⭐⭐⭐
**问题位置**: `rag_engine.py:681`

```python
# 当前实现
fused_scores[doc_id] = dense_weight * dense_score + sparse_weight * sparse_score
# 权重: dense_weight=0.9, sparse_weight=0.1
```

**问题原因**:
- 假设稠密向量检索分数为 0.85（语义相似度高）
- 假设稀疏向量检索分数为 0.30（关键词匹配弱）
- 融合后: `0.9 × 0.85 + 0.1 × 0.30 = 0.765 + 0.03 = 0.795`
- **分数被拉低了 5.5%**

更严重的情况：
- 如果文档只在稠密检索中出现（sparse_score=0）
- 融合后: `0.9 × 0.85 + 0.1 × 0 = 0.765`
- **分数被砍掉 10%！**

**这是最大的问题**：本来相似度很高的文档，经过加权融合后分数严重缩水。

---

### 2. **相似度阈值设置不合理** ⭐⭐⭐⭐
**配置位置**: `settings.py:57`

```python
RAG_SIMILARITY_THRESHOLD: float = 0.7
```

**问题**:
- 阈值 0.7 是针对单一向量检索设置的
- 但实际使用的是混合检索（加权融合），分数已经被稀释
- 应该根据融合策略调整阈值

**建议阈值**:
- 如果使用加权融合（0.9/0.1）：阈值应降至 **0.60-0.65**
- 如果优化融合算法：阈值可保持在 **0.70-0.75**
- 如果追求 0.85+ 准确率：需要从根本上优化向量和数据质量

---

### 3. **稀疏向量检索性能问题** ⭐⭐⭐
**问题位置**: `rag_engine.py:598-632`

```python
def _sparse_search(self, query: str, top_k: int):
    # 问题：全量加载文档再计算相似度
    results = self.collection.query(
        expr="id >= 0",
        output_fields=["id", "sparse_vector"],
        limit=10000  # 加载10000条文档！
    )
```

**性能问题**:
1. 每次查询加载 10000 条文档
2. 在内存中逐一计算余弦相似度
3. 效率低下，且容易产生低质量匹配

**对分数的影响**:
- 稀疏向量匹配可能不准确
- 低质量的稀疏分数拖累融合结果

---

### 4. **数据质量和向量质量** ⭐⭐⭐
从日志看，稠密向量检索返回了 20 条结果，但即使是第一名的分数也不理想。

**可能原因**:
1. **向量模型问题**: `bge-base-zh-v1.5` 对旅游领域的语义理解不够精准
2. **数据质量问题**: 
   - 文档描述不够详细
   - 关键信息缺失
   - 内容与查询意图不匹配
3. **查询重写不够优化**: "三清山旅游攻略推荐" 可能需要更精细的重写策略

---

### 5. **Milvus 检索参数** ⭐⭐
**配置位置**: `rag_engine.py:582`

```python
search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
```

**nprobe=10** 可能不够：
- nprobe 控制搜索的聚类数量
- 值越大，召回率越高，但速度越慢
- 对于小数据集，可以增大到 16-32

---

## 解决方案（按优先级排序）

### 🔥 方案1: 优化加权融合算法（最重要）

**策略A: 使用 MAX 融合而非加权平均**
```python
def _weighted_fusion(self, dense_results, sparse_results, dense_weight=0.9, sparse_weight=0.1):
    """使用MAX策略：取两个分数中的最大值"""
    dense_scores = {doc_id: score for doc_id, score in dense_results}
    sparse_scores = {doc_id: score for doc_id, score in sparse_results}
    
    all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
    
    fused_scores = {}
    for doc_id in all_ids:
        dense_score = dense_scores.get(doc_id, 0.0)
        sparse_score = sparse_scores.get(doc_id, 0.0)
        
        # 策略1: 取最大值（保留最好的信号）
        fused_scores[doc_id] = max(dense_score, sparse_score)
        
        # 或策略2: 加权MAX（给稠密向量更多权重）
        # fused_scores[doc_id] = max(dense_score * dense_weight, sparse_score * sparse_weight) / max(dense_weight, sparse_weight)
    
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
```

**优势**:
- 不会稀释高分结果
- 保留最强的匹配信号
- 分数更接近原始相似度

---

**策略B: 使用 RRF (Reciprocal Rank Fusion) - 推荐！**
```python
def _weighted_fusion_rrf(self, dense_results, sparse_results, k=60):
    """使用RRF算法进行融合"""
    def compute_rrf_score(rank: int, k: int = 60) -> float:
        return 1.0 / (k + rank)
    
    # 构建排名映射
    dense_ranks = {doc_id: i + 1 for i, (doc_id, _) in enumerate(dense_results)}
    sparse_ranks = {doc_id: i + 1 for i, (doc_id, _) in enumerate(sparse_results)}
    
    all_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())
    
    rrf_scores = {}
    for doc_id in all_ids:
        score = 0.0
        if doc_id in dense_ranks:
            score += compute_rrf_score(dense_ranks[doc_id], k)
        if doc_id in sparse_ranks:
            score += compute_rrf_score(sparse_ranks[doc_id], k)
        
        # 归一化到 [0, 1]
        rrf_scores[doc_id] = score * k / 2  # 简单归一化
    
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
```

**优势**:
- 基于排名而非分数，更稳定
- 已有成熟的实现（你的项目中已有 RRF）
- 学术界广泛验证的方法

---

**策略C: 自适应加权**
```python
def _weighted_fusion_adaptive(self, dense_results, sparse_results):
    """自适应加权：根据结果质量动态调整权重"""
    dense_scores = {doc_id: score for doc_id, score in dense_results}
    sparse_scores = {doc_id: score for doc_id, score in sparse_results}
    
    # 计算平均分数（质量指标）
    avg_dense = sum(dense_scores.values()) / len(dense_scores) if dense_scores else 0
    avg_sparse = sum(sparse_scores.values()) / len(sparse_scores) if sparse_scores else 0
    
    # 动态调整权重：谁的平均分高，谁的权重就大
    total = avg_dense + avg_sparse
    if total > 0:
        dense_weight = avg_dense / total
        sparse_weight = avg_sparse / total
    else:
        dense_weight, sparse_weight = 0.9, 0.1
    
    all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
    
    fused_scores = {}
    for doc_id in all_ids:
        dense_score = dense_scores.get(doc_id, 0.0)
        sparse_score = sparse_scores.get(doc_id, 0.0)
        fused_scores[doc_id] = dense_weight * dense_score + sparse_weight * sparse_score
    
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
```

---

### 🔧 方案2: 调整相似度阈值

**立即生效的临时方案**:
```python
# settings.py
RAG_SIMILARITY_THRESHOLD: float = 0.60  # 从 0.7 降至 0.60
```

**更好的方案**: 根据融合策略设置不同阈值
```python
# settings.py
RAG_SIMILARITY_THRESHOLD_DENSE: float = 0.75  # 单纯稠密向量
RAG_SIMILARITY_THRESHOLD_HYBRID: float = 0.60  # 混合检索
RAG_SIMILARITY_THRESHOLD_RRF: float = 0.65    # RRF融合
```

---

### 🚀 方案3: 优化稀疏向量检索

**使用 Milvus 的稀疏向量索引**:
```python
def _sparse_search(self, query: str, top_k: int):
    """使用Milvus原生稀疏向量检索"""
    query_vector = self.sparse_generator.query_vector(query)
    
    if not query_vector:
        return []
    
    # 转换为Milvus稀疏格式
    sparse_data = [{int(k): float(v) for k, v in query_vector.items()}]
    
    search_params = {
        "metric_type": "IP",  # Inner Product
        "params": {}
    }
    
    results = self.collection.search(
        data=sparse_data,
        anns_field="sparse_vector",
        param=search_params,
        limit=top_k,
        output_fields=["id"]
    )
    
    sparse_results = []
    for hit in results[0]:
        sparse_results.append((hit.id, hit.score))
    
    return sparse_results
```

**前提**: Milvus 集合需要为稀疏向量字段建立索引

---

### 📊 方案4: 提升数据和向量质量

**4.1 使用更好的向量模型**:
- 当前: `bge-base-zh-v1.5` (768维)
- 升级: `bge-large-zh-v1.5` (1024维) - 精度更高
- 或考虑: 领域微调的模型

**4.2 数据清洗和增强**:
```python
# 检查当前数据质量
# 1. 查看"三清山"相关文档的描述是否完整
# 2. 确保包含关键信息：景点名、位置、特色、攻略等
# 3. 检查是否有重复或低质量文档
```

**4.3 查询增强**:
```python
# 在 query_rewriter_node 中添加查询扩展
expanded_queries = [
    "三清山旅游攻略推荐",
    "三清山旅游指南",
    "三清山景点介绍",
    "三清山游玩攻略"
]
# 对多个查询分别检索后合并
```

---

### ⚙️ 方案5: 调整 Milvus 参数

```python
# rag_engine.py
search_params = {
    "metric_type": "COSINE",
    "params": {
        "nprobe": 32,  # 从 10 提升到 32
        "ef": 64       # 如果使用HNSW索引
    }
}
```

---

## 推荐实施顺序

### 第一步：立即修复（今天）
1. ✅ **修改融合算法为 MAX 或 RRF**（优先RRF，因为你已有实现）
2. ✅ **降低阈值至 0.60**（临时措施）
3. ✅ **测试效果**

### 第二步：中期优化（本周）
1. ✅ 优化稀疏向量检索（使用Milvus原生索引）
2. ✅ 调整 nprobe 参数
3. ✅ 实施自适应阈值策略

### 第三步：长期提升（下周）
1. 🔍 评估数据质量，清洗低质量文档
2. 🔍 考虑升级向量模型
3. 🔍 添加查询扩展和多轮检索

---

## 预期效果

| 方案 | 预期分数提升 | 实施难度 | 风险 |
|------|------------|---------|------|
| MAX融合 | +10-15% | 低 | 低 |
| RRF融合 | +15-20% | 中 | 低 |
| 降低阈值 | N/A（更多结果） | 低 | 中（可能返回低质量结果）|
| 优化稀疏检索 | +5-10% | 中 | 中 |
| 升级向量模型 | +10-20% | 高 | 低 |
| 数据清洗 | +5-15% | 高 | 低 |

---

## 最终目标

要达到 **0.85+ 的准确率**，需要：
1. 优化融合算法（核心）
2. 提升向量模型质量
3. 保证数据质量
4. 合理设置阈值

**现实预期**:
- 短期（修复融合算法）: 分数可提升至 **0.72-0.78**
- 中期（优化检索 + 数据）: 分数可达到 **0.78-0.83**
- 长期（全面优化）: 分数有望达到 **0.83-0.88**

0.85+ 是一个很高的标准，需要系统性优化。
