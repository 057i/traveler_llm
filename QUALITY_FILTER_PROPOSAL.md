# 💡 RRF + 质量过滤方案

## 🎯 方案对比

### **方案A：RRF后过滤（推荐）**

```python
# 流程
三路检索(不过滤) → RRF融合(Top 20) → 质量过滤 → Rerank(Top 5)

# 优势
✅ 先排序，再过滤
✅ 不丢失有价值结果
✅ 保留多样性
```

### **方案B：分路过滤 + RRF**

```python
# 流程
三路检索 → 分别过滤(每路不同阈值) → RRF融合 → Rerank

# 优势
✅ 针对性强
⚠️ 需要统计确定阈值
```

### **方案C：当前方案（最简单）**

```python
# 流程
三路检索 → RRF融合(Top 10) → Rerank(Top 3-5)

# 优势
✅ 简单直接
✅ RRF自动处理质量
```

---

## 🔧 实现：方案A（RRF后质量过滤）

### **代码示例**

```python
# 在 node_milvus_hybrid.py 中，RRF融合后添加质量过滤

# 2. RRF融合（先融合Top 20）
fused_results = await rrf_engine.fuse_multi_path(
    results=[dense_results, sparse_results, exact_results],
    weights=[0.4, 0.3, 0.3],
    top_k=20  # 先取20条
)

# 3. 质量过滤（新增）
filtered_results = []
for r in fused_results:
    # 保留条件（满足任一即可）:
    # 1. Dense分值 > 0.7
    # 2. 精确匹配
    # 3. Sparse排名靠前（Top 5）
    
    is_high_quality = (
        r.get("score", 0) > 0.7 or  # 原始分值高
        r.get("source") == "exact_match" or  # 精确匹配
        r.get("path_2_rank", 999) <= 5  # Sparse Top5
    )
    
    if is_high_quality:
        filtered_results.append(r)

logger.info(f"[MilvusHybrid] Quality filter: {len(fused_results)} → {len(filtered_results)} results")

# 4. 取Top 10
final_results = filtered_results[:10]
```

### **预期效果**

```
RRF融合: 20条
  ↓
质量过滤:
  ✅ 保留: Dense>0.7 或 Exact或 Sparse前5
  ❌ 过滤: Dense<0.7 且非Exact且Sparse靠后
  ↓
12条高质量结果
  ↓
取Top 10
```

---

## 📊 方案对比表

| 方案 | RRF前过滤 | RRF后过滤 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **你的想法** | ✅ 统一>0.7 | ❌ | 简单 | 误杀稀疏结果 |
| **方案A** | ❌ | ✅ 多条件 | 精准 | 稍复杂 |
| **方案B** | ✅ 分路阈值 | ❌ | 针对性强 | 需调参 |
| **方案C** | ❌ | ❌ | 最简单 | 可能有低质量 |

---

## 🎯 推荐配置

### **配置1：严格质量（适合数据量大）**

```python
# RRF融合Top 20
top_k = 20

# 质量过滤
dense_threshold = 0.75  # 提高到0.75
sparse_top_n = 5
keep_exact_match = True

# 最终输出Top 10
```

### **配置2：平衡模式（推荐）**

```python
# RRF融合Top 15
top_k = 15

# 质量过滤
dense_threshold = 0.70
sparse_top_n = 8
keep_exact_match = True

# 最终输出Top 10
```

### **配置3：召回优先（适合数据量小）**

```python
# RRF融合Top 10
top_k = 10

# 不过滤
# 直接Rerank
```

---

## 🔍 为什么不建议统一0.7阈值？

### **实际案例**

```
查询: "三清山周边美食"

Dense检索:
  ✅ 三清山 (0.82) - 保留
  ✅ 婺源 (0.71) - 保留
  ❌ 南昌美食 (0.68) - 过滤

Sparse检索:
  ❌ 景德镇美食 (IP=0.45) - 被过滤！但可能是最相关的！
  ❌ 上饶特色餐厅 (IP=0.38) - 被过滤！
  
结果：丢失了所有稀疏检索的美食结果！
```

**问题**：
- 稀疏检索的IP分值通常 < 0.7
- 但这些结果可能是关键词匹配度最高的
- 统一阈值会误杀这些结果

---

## ✅ 最终建议

### **如果数据量 < 1000条**
```python
方案C：不过滤
→ RRF融合Top 10 → Rerank Top 5
```

### **如果数据量 1000-10000条**
```python
方案A：RRF后过滤（推荐）
→ RRF融合Top 15 → 质量过滤 → Rerank Top 5
```

### **如果数据量 > 10000条**
```python
方案B：分路过滤
→ Dense>0.7 + Sparse>统计阈值 + Exact全部
→ RRF融合 → Rerank Top 5
```

---

## 🚀 我的建议

**不要在RRF前用统一阈值过滤！**

原因：
1. ✅ RRF设计目的就是解决不同分值范围的融合
2. ✅ 过滤应该在RRF后，基于多维度条件
3. ✅ 当前方案（RRF → Rerank）已经够好了

**如果一定要过滤，用方案A（RRF后多条件过滤）！**

---

要不要我帮你实现方案A的质量过滤？ 🤔
