# 🐛 检索数量过少问题分析

## ❓ 问题

从日志看到：
```
[MilvusHybrid] Dense: 3 results  (预期: 10条)
[MilvusHybrid] Sparse: 3 results (预期: 10条)
[MilvusHybrid] Exact: 1 results  (正常)
```

**问题**：
1. 稠密检索只返回3条，而不是配置的10条
2. 稀疏检索也只返回3条
3. 数据库有510条数据，但检索结果太少

---

## 🔍 原因分析

### **1. 稀疏向量数据缺失**

**对比之前的日志**：
```
之前（使用fallback关键词匹配）:
- Dense: 6 results
- Sparse: 14 results  ← 关键词匹配成功
- Exact: 1 results

现在（使用真实稀疏向量）:
- Dense: 3 results
- Sparse: 3 results   ← 稀疏向量检索失败
- Exact: 1 results
```

**结论**：数据库中的`sparse_vector`字段可能为空或未生成。

### **2. 稠密检索也变少的原因**

可能原因：
- 查询向量质量问题
- 数据库中相似度>0.7的文档确实只有3条
- HNSW索引参数导致召回不足

---

## ✅ 已实施的修复

### **修复1：稀疏向量检索自动降级**

```python
# milvus_hybrid_client.py

if len(output) < top_k // 2:
    logger.warning(f"Sparse ANNS returned too few results, using fallback")
    return await self._search_sparse_fallback(query, top_k)
```

**效果**：
- 如果稀疏向量检索返回<5条（top_k=10的一半）
- 自动降级为关键词匹配（fallback）
- 保证至少有足够的稀疏检索结果

---

## 🔧 建议的解决方案

### **方案A：重新导入数据，生成稀疏向量（推荐）**

**问题**：当前数据可能没有稀疏向量

**解决**：
1. 重新运行文档导入流程
2. 确保`encode_sparse()`被调用
3. 稀疏向量写入Milvus的`sparse_vector`字段

**验证**：
```python
from pymilvus import Collection, connections
connections.connect(host="localhost", port=19530)
collection = Collection("travel_destinations")
collection.load()

# 查询一条数据
result = collection.query(
    expr="",
    output_fields=["name", "sparse_vector"],
    limit=1
)
print("稀疏向量:", result[0].get("sparse_vector"))

# 如果输出None或{} → 需要重新导入数据
# 如果输出{45: 0.8, 123: 0.6, ...} → 数据正常
```

### **方案B：临时使用fallback（当前已实施）**

**当前配置**：
- 稀疏向量检索失败 → 自动降级为关键词匹配
- 保证系统可用性

**效果**：
```
Dense: 3-6条（真实向量检索）
Sparse: 10-20条（关键词匹配fallback）
Exact: 1条
→ 总计有足够的结果进行RRF融合
```

### **方案C：调整HNSW搜索参数**

如果稠密检索结果也太少，可以调整：

```python
# settings.py
MILVUS_SEARCH_EF = 128  # 从64提高到128（更高召回，稍慢）
```

或者临时降低过滤阈值：

```python
DENSE_SCORE_THRESHOLD = 0.65  # 从0.7降到0.65
```

---

## 📊 数据库健康检查

### **检查1：数据总量**
```python
collection.num_entities  # 510条 ✅
```

### **检查2：稀疏向量覆盖率**
```python
# 检查有多少条数据有稀疏向量
results = collection.query(
    expr="",
    output_fields=["sparse_vector"],
    limit=100
)

has_sparse = sum(1 for r in results if r.get("sparse_vector"))
print(f"稀疏向量覆盖率: {has_sparse}/100")

# 如果<50% → 需要重新导入数据
```

### **检查3：向量维度**
```python
# 检查稠密向量维度是否正确
result = collection.query(
    expr="",
    output_fields=["dense_vector"],
    limit=1
)
print(f"稠密向量维度: {len(result[0]['dense_vector'])}")
# 应该是768维（bge-base-zh-v1.5）
```

---

## 🎯 立即行动

### **短期（当前已完成）**
✅ 稀疏检索自动降级
✅ 保证系统可用性

### **中期（本周完成）**
- [ ] 验证Milvus数据库中稀疏向量是否存在
- [ ] 如果不存在，重新导入数据
- [ ] 调整HNSW搜索参数提高召回

### **长期（优化方向）**
- [ ] 监控每次检索的返回数量
- [ ] 统计分析阈值的合理性
- [ ] 建立数据质量监控

---

## 🚀 测试步骤

1. **重启服务**
```bash
python backend/main.py
```

2. **查询"三清山"**

3. **观察日志**
```
预期看到：
[Milvus] Sparse ANNS returned 3 results
[Milvus] Sparse ANNS returned too few results (3 < 5), using fallback
[Milvus] Sparse fallback keywords: ['三清山']
[Milvus] Sparse fallback returned 15 results

→ 自动降级成功！
```

4. **对比结果**
```
之前: Dense(3) + Sparse(3) = 6条
现在: Dense(3) + Sparse(15 fallback) = 18条
→ 结果数量恢复正常！
```

---

## 📝 根本解决方法

**重新导入数据并生成稀疏向量**：

1. 运行文档导入流程
2. 确保调用`embedding_service.encode_sparse()`
3. 将稀疏向量写入Milvus

这样就能使用真正的稀疏向量检索，性能和准确性都更好！

---

**当前修复已完成，重启服务测试即可！** 🎉
