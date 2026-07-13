# 🧪 测试指南 - 查看Milvus混合检索原始分值

## 📋 测试步骤

### **1. 重启后端服务**
```bash
cd backend
python main.py
```

### **2. 测试查询**
```bash
# 查询1: 精确查询（有实体）
输入: "三清山"

# 查询2: 模糊查询
输入: "推荐一下江西的旅游景点"

# 查询3: 附近查询
输入: "三清山附近有什么景点"
```

---

## 📊 预期日志输出格式

### **原始检索结果（3路）**
```
[MilvusHybrid] ============================================================
[MilvusHybrid] 📊 原始检索结果详情：
[MilvusHybrid] ============================================================

[MilvusHybrid] 🔵 稠密检索 Top 5:
  #1: 三清山               | Score=0.8524 | Source=milvus_dense
  #2: 南清园景区            | Score=0.7891 | Source=milvus_dense
  #3: 秀峰                 | Score=0.7234 | Source=milvus_dense
  #4: 婺源                 | Score=0.6892 | Source=milvus_dense
  #5: 龙虎山               | Score=0.6543 | Source=milvus_dense

[MilvusHybrid] 🟡 稀疏检索 Top 5:
  #1: 三清山               | Score=0.9200 | Source=milvus_sparse
  #2: 三清山风景区          | Score=0.7800 | Source=milvus_sparse
  #3: 南昌                 | Score=0.6500 | Source=milvus_sparse
  #4: 井冈山               | Score=0.5900 | Source=milvus_sparse
  #5: 庐山                 | Score=0.5200 | Source=milvus_sparse

[MilvusHybrid] 🟢 精确匹配结果:
  #1: 三清山               | Score=1.0000 (精确匹配满分) | Source=exact_match

[MilvusHybrid] ============================================================
```

### **RRF融合后结果**
```
[MilvusHybrid] ============================================================
[MilvusHybrid] 🔀 RRF融合后 Top 10:
[MilvusHybrid] ============================================================
  #1: 三清山               | RRF=0.016200 | OrigScore=1.0000 | Ranks[Dense=1, Sparse=1, Exact=1]
  #2: 南清园景区            | RRF=0.006500 | OrigScore=0.7891 | Ranks[Dense=2, Sparse=N/A, Exact=N/A]
  #3: 秀峰                 | RRF=0.006300 | OrigScore=0.7234 | Ranks[Dense=3, Sparse=N/A, Exact=N/A]
  #4: 三清山风景区          | RRF=0.005800 | OrigScore=0.7800 | Ranks[Dense=N/A, Sparse=2, Exact=N/A]
  #5: 婺源                 | RRF=0.005200 | OrigScore=0.6892 | Ranks[Dense=4, Sparse=N/A, Exact=N/A]
[MilvusHybrid] ============================================================
```

### **置信度详情**
```
[Confidence] 检索质量: 0.900
  - 精确匹配Top1: +0.5
  - 向量相似度: +0.2 (avg=0.75)
  - Top1来源类型: +0.2 (exact_match)

[Confidence] 结果覆盖: 0.800
  - 结果数量: +0.5 (10条)
  - 来源多样性: +0.3 (3种来源)

[Confidence] 排序稳定性: 0.700
  - Top1突出度: +0.4 (相对差距大)
  - 分数分布: +0.3 (方差适中)

[Confidence] 查询复杂度: 0.600
  - 查询长度: +0.2 (3字，较短)
  - 实体数量: +0.3 (1个实体)
  - 查询类型: +0.1 (精确查询)

[Confidence] 综合置信度: 0.860
```

---

## 🔍 关键观察点

### **1. 原始分值范围**
- **稠密检索**：0.6-0.9（Cosine相似度）
- **稀疏检索**：0.5-0.95（关键词匹配）
- **精确匹配**：1.0（满分）

### **2. RRF分值范围**
- Top1: 0.015-0.020
- Top5: 0.005-0.010
- Top10: 0.003-0.006

**注意**：RRF分值天然就很小，这是正常的！

### **3. 置信度计算**
应该看到4个维度的分数：
- 检索质量：0.3-0.9（有精确匹配会很高）
- 结果覆盖：0.4-0.8
- 排序稳定性：0.5-0.8
- 查询复杂度：0.3-0.7

---

## 🎯 预期结果

### **查询1: "三清山"**
```
✅ 稠密检索找到 "三清山"
✅ 稀疏检索找到 "三清山"
✅ 精确匹配找到 "三清山"
✅ RRF融合后Top1是 "三清山"
✅ 置信度 ≥ 0.85
✅ 不触发Tavily
```

### **查询2: "推荐江西的旅游景点"**
```
✅ 稠密检索找到相关景点
✅ 稀疏检索找到相关景点
❌ 精确匹配无结果（无实体精确匹配）
✅ RRF融合后有多个结果
✅ 置信度 0.5-0.7
⚠️ 可能触发Tavily（取决于结果质量）
```

### **查询3: "三清山附近有什么景点"**
```
✅ 稠密检索找到 "三清山"
✅ 稀疏检索找到 "三清山" + "附近" 相关
✅ 精确匹配找到 "三清山"
✅ needs_nearby_search: true
✅ Neo4j执行附近检索
✅ 置信度 ≥ 0.8
✅ 不触发Tavily
```

---

## 📝 日志文件位置

```
logs/app.log
```

可以用以下命令查看实时日志：
```bash
tail -f logs/app.log | grep -E "(MilvusHybrid|Confidence)"
```

---

## 🐛 如果没看到详细日志

检查 `config/settings.py`:
```python
LOG_LEVEL = "INFO"  # 确保是INFO级别
```

或者临时调整日志级别：
```bash
export LOG_LEVEL=DEBUG
python main.py
```

---

**重启服务后，发送查询，把日志发给我看！** 📊
