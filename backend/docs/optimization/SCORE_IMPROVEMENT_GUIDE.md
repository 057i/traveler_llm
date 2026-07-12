# 如何提升相似度分数 - 优化方案

当前状态：分数约 0.72-0.78，目标提升到 0.85+

---

## 📊 当前分数分析

从你的日志看：
- 稠密向量最高分：0.72
- 经过归一化加权融合：0.72（保留率100%）
- **问题**：原始分数本身就不够高（0.72）

**结论**：要提升最终分数，需要提升**原始向量检索的分数**。

---

## 🎯 快速提升方案（按效果排序）

### 方案1: 优化查询重写 ⭐⭐⭐⭐⭐
**影响最大，最容易实施**

#### 问题分析
当前查询重写：
```
原始: "推荐一下三清山的旅游攻略"
重写: "三清山旅游攻略推荐"
```

**改进方向**：
1. **添加关键词扩展**
2. **语义增强**
3. **多查询融合**

#### 实施代码

<details>
<summary>点击展开：查询优化实现</summary>

```python
# app/workflows/ai_recommend/nodes/node_query_rewriter.py

def enhance_query(original_query: str, entities: List[str], intent: str) -> List[str]:
    """
    查询增强：生成多个语义相关的查询
    
    Returns:
        增强后的查询列表
    """
    enhanced_queries = [original_query]  # 保留原始查询
    
    # 策略1: 添加同义词
    synonyms_map = {
        "旅游攻略": ["旅游指南", "游玩攻略", "旅行攻略", "景点推荐"],
        "推荐": ["介绍", "攻略", "指南"],
    }
    
    for entity in entities:
        # 基础查询
        enhanced_queries.append(f"{entity}旅游攻略")
        enhanced_queries.append(f"{entity}景点介绍")
        enhanced_queries.append(f"{entity}游玩指南")
        
        # 详细查询
        enhanced_queries.append(f"{entity}有哪些景点")
        enhanced_queries.append(f"{entity}怎么玩")
        enhanced_queries.append(f"{entity}必去景点")
    
    return enhanced_queries[:5]  # 返回前5个


# 在检索时使用多查询
def multi_query_retrieval(queries: List[str], top_k: int = 10):
    """多查询检索并融合"""
    all_results = {}
    
    for query in queries:
        results = rag_engine.hybrid_search(query, top_k=top_k)
        
        for result in results:
            doc_id = result.id
            if doc_id not in all_results:
                all_results[doc_id] = []
            all_results[doc_id].append(result.score)
    
    # 取每个文档的最高分
    final_results = []
    for doc_id, scores in all_results.items():
        max_score = max(scores)
        final_results.append((doc_id, max_score))
    
    final_results.sort(key=lambda x: x[1], reverse=True)
    return final_results[:top_k]
```

</details>

**预期提升**：+5-10%（0.72 → 0.77-0.79）

---

### 方案2: 升级向量模型 ⭐⭐⭐⭐⭐
**影响最大，但需要重新生成向量**

#### 当前模型
```
bge-base-zh-v1.5
- 维度: 768
- 大小: ~400MB
- 性能: 中等
```

#### 推荐升级
```
bge-large-zh-v1.5
- 维度: 1024
- 大小: ~1.3GB
- 性能: 优秀
- 相似度提升: 5-15%
```

#### 实施步骤

<details>
<summary>点击展开：模型升级步骤</summary>

1. **下载模型**
```bash
# 使用huggingface
pip install huggingface_hub
huggingface-cli download BAAI/bge-large-zh-v1.5 --local-dir ./models/bge-large-zh-v1.5
```

2. **修改配置**
```python
# config/settings.py
EMBEDDING_MODEL: str = "./models/bge-large-zh-v1.5"
```

3. **重新生成向量**
```bash
python scripts/rebuild_vectors.py
```

</details>

**预期提升**：+10-15%（0.72 → 0.79-0.83）

**注意**：需要重新为所有文档生成向量，耗时较长。

---

### 方案3: 调整Milvus检索参数 ⭐⭐⭐⭐
**立即生效，无需重新索引**

#### 当前配置
```python
search_params = {
    "metric_type": "COSINE",
    "params": {"nprobe": 10}  # 太小
}
```

#### 优化配置
```python
search_params = {
    "metric_type": "COSINE", 
    "params": {
        "nprobe": 32,     # 增加搜索聚类数
        "radius": 0.5,    # 最小相似度（可选）
        "range_filter": 0.9  # 最大相似度（可选）
    }
}
```

#### 实施代码

<details>
<summary>点击展开：参数优化实现</summary>

```python
# app/core/rag_engine.py

def _dense_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
    """优化的稠密向量检索"""
    query_vector = self.embedding_model.encode([query], normalize_embeddings=True)[0]
    
    # 优化的搜索参数
    search_params = {
        "metric_type": "COSINE",
        "params": {
            "nprobe": 32,      # 从10提升到32，召回率更高
            "ef": 64,          # HNSW索引参数（如果使用HNSW）
        }
    }
    
    # 增加检索数量，后续过滤
    results = self.collection.search(
        data=[query_vector.tolist()],
        anns_field="dense_vector",
        param=search_params,
        limit=top_k * 3,  # 多取一些，提高召回
        output_fields=["id"]
    )
    
    dense_results = []
    for hit in results[0]:
        dense_results.append((hit.id, hit.score))
    
    logger.info(f"  🔍 nprobe=32, 召回 {len(dense_results)} 条")
    return dense_results
```

</details>

**预期提升**：+3-5%（0.72 → 0.74-0.76）

---

### 方案4: 文档内容增强 ⭐⭐⭐⭐
**治本之策，但工作量大**

#### 问题诊断
检查你的文档是否有这些问题：
```python
# 运行诊断脚本
python scripts/check_document_quality.py
```

#### 改进方向

<details>
<summary>点击展开：文档质量提升方案</summary>

**1. 增加文档描述字段**
```python
# 当前文档结构（可能）
{
    "name": "三清山",
    "description": "三清山是..."  # 可能太简短
}

# 优化后
{
    "name": "三清山",
    "description": "三清山是...",
    "keywords": ["三清山", "旅游", "攻略", "景点"],
    "long_description": "详细的旅游攻略内容...",  # 新增
    "highlights": ["观日出", "云海", "奇峰"],      # 新增
    "travel_tips": "最佳旅游时间..."              # 新增
}
```

**2. 向量化时拼接多个字段**
```python
def build_text_for_embedding(doc):
    """构建更丰富的文本用于向量化"""
    parts = [
        doc['name'],
        doc['description'],
        ' '.join(doc.get('keywords', [])),
        doc.get('long_description', ''),
        ' '.join(doc.get('highlights', [])),
        doc.get('travel_tips', '')
    ]
    
    # 拼接成一段丰富的文本
    text = ' '.join([p for p in parts if p])
    return text
```

**3. 添加同义词和常见表达**
```python
# 为"三清山"添加变体
document_text = """
三清山 三清山风景区 三清山景区 
三清山旅游 三清山攻略 三清山游玩
江西三清山 上饶三清山
三清山有什么好玩的 三清山怎么玩
...
"""
```

</details>

**预期提升**：+10-20%（0.72 → 0.79-0.86）

---

### 方案5: 使用更激进的融合策略 ⭐⭐⭐
**立即生效，改配置即可**

#### 方案A: 使用RRF融合
RRF融合通常会产生更高的分数。

```python
# config/fusion_config.py
FUSION_STRATEGY = "rrf"  # 从 normalized_weighted 改为 rrf
```

**特点**：
- 基于排名，不受分数尺度影响
- 归一化后分数通常更高
- 最高分可达 0.85-0.90

#### 方案B: 调整融合权重
```python
# config/settings.py
AI_RECOMMEND_DENSE_WEIGHT: float = 0.95  # 从0.9提升到0.95
AI_RECOMMEND_SPARSE_WEIGHT: float = 0.05  # 从0.1降低到0.05
```

**原理**：稠密向量更可靠，给它更高权重。

**预期提升**：+2-5%（0.72 → 0.74-0.76）

---

### 方案6: Rerank精排 ⭐⭐⭐⭐⭐
**效果显著，已有模型可直接用**

#### 当前流程
```
查询 → 向量检索 → 返回结果
```

#### 优化流程
```
查询 → 向量检索（召回50条）→ Rerank精排（选Top10）→ 返回结果
```

#### 实施代码

<details>
<summary>点击展开：Rerank实现</summary>

```python
# app/core/reranker.py
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        # 使用你已有的rerank模型
        self.model = CrossEncoder('./models/BAAI--bge-reranker-v2-m3/snapshots/master')
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 10):
        """
        对检索结果进行精排
        
        Args:
            query: 查询文本
            documents: 初步检索的文档列表
            top_k: 返回前k个
        
        Returns:
            精排后的文档列表
        """
        # 准备输入
        pairs = [(query, doc['content']) for doc in documents]
        
        # 计算精排分数
        scores = self.model.predict(pairs)
        
        # 按分数排序
        for i, doc in enumerate(documents):
            doc['rerank_score'] = scores[i]
        
        documents.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        logger.info(f"Rerank: 输入{len(documents)}条, 输出{top_k}条")
        logger.info(f"  最高分: {documents[0]['rerank_score']:.4f}")
        
        return documents[:top_k]


# 在检索流程中使用
def hybrid_search_with_rerank(query, top_k=10):
    # 步骤1: 向量检索（多召回）
    initial_results = hybrid_search(query, top_k=50)
    
    # 步骤2: Rerank精排
    reranker = Reranker()
    final_results = reranker.rerank(query, initial_results, top_k=top_k)
    
    return final_results
```

</details>

**预期提升**：+15-25%（0.72 → 0.83-0.90）

**优势**：
- 你已有rerank模型（`bge-reranker-v2-m3`）
- 可以立即使用
- 效果显著

---

### 方案7: 调整稀疏向量权重 ⭐⭐
**快速调整，立即生效**

如果稀疏向量质量差，可以进一步降低其权重：

```python
# config/settings.py
AI_RECOMMEND_DENSE_WEIGHT: float = 0.95  # 提高
AI_RECOMMEND_SPARSE_WEIGHT: float = 0.05  # 降低

# 或者直接禁用稀疏向量
# 在 rag_engine.py 中跳过稀疏检索
```

**预期提升**：+2-3%（0.72 → 0.74-0.75）

---

## 📊 方案对比

| 方案 | 难度 | 耗时 | 预期提升 | 最终分数 | 推荐指数 |
|------|------|------|---------|---------|---------|
| 1. 查询优化 | 中 | 1天 | +5-10% | 0.77-0.79 | ⭐⭐⭐⭐⭐ |
| 2. 升级模型 | 高 | 2-3天 | +10-15% | 0.79-0.83 | ⭐⭐⭐⭐⭐ |
| 3. 调整参数 | 低 | 10分钟 | +3-5% | 0.74-0.76 | ⭐⭐⭐⭐ |
| 4. 文档增强 | 高 | 5-7天 | +10-20% | 0.79-0.86 | ⭐⭐⭐⭐ |
| 5. RRF融合 | 低 | 5分钟 | +2-5% | 0.74-0.76 | ⭐⭐⭐ |
| 6. Rerank | 中 | 半天 | +15-25% | 0.83-0.90 | ⭐⭐⭐⭐⭐ |
| 7. 调整权重 | 低 | 5分钟 | +2-3% | 0.74-0.75 | ⭐⭐ |

---

## 🎯 推荐实施路线

### 立即实施（今天，10-30分钟）
1. ✅ **调整Milvus参数**（方案3）- nprobe: 10→32
2. ✅ **切换RRF融合**（方案5A）- 改配置即可
3. ✅ **调整权重**（方案7）- Dense: 0.9→0.95

**预期效果**: 0.72 → 0.76-0.78

### 短期实施（本周，1-2天）
4. ✅ **实施Rerank**（方案6）- 你已有模型
5. ✅ **查询优化**（方案1）- 多查询融合

**预期效果**: 0.76 → 0.83-0.88

### 中期实施（下周，3-5天）
6. ✅ **升级向量模型**（方案2）- bge-large
7. ✅ **文档增强**（方案4）- 丰富内容

**预期效果**: 0.83 → 0.88-0.92

---

## 💡 最快见效的组合方案

### 组合1: 零成本快速提升（10分钟）
```bash
1. 调整nprobe: 10→32
2. 切换RRF融合
3. 调整权重: 0.9→0.95
```
**预期**: 0.72 → 0.76-0.78（+5-8%）

### 组合2: 最佳性价比（1天）
```bash
1. 实施Rerank精排
2. 查询优化（多查询）
3. 调整Milvus参数
```
**预期**: 0.72 → 0.83-0.88（+15-22%）

### 组合3: 最大化效果（1周）
```bash
1. 升级bge-large模型
2. 实施Rerank
3. 查询优化
4. 文档内容增强
```
**预期**: 0.72 → 0.88-0.92（+22-28%）

---

## 🚀 立即可用的优化代码

我可以立即帮你实施：

1. **调整Milvus参数**（5分钟）
2. **切换RRF融合**（5分钟）
3. **实施Rerank精排**（1小时）

你想先实施哪个？我现在就可以帮你修改代码！
