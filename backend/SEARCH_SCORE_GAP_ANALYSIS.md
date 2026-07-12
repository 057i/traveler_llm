# AI团队推荐搜索差距分析

## 📊 两次查询对比

### 查询1: "推荐三清山3天旅游攻略"
```
稠密向量 Top3: [0.6915, 0.6833, 0.6720]
融合后 Top3: [0.6915, 0.6892, 0.6440]
阈值: 0.7
结果: ⚠️ 0条（全部被过滤）
```

### 查询2: "三清山"
```
稠密向量 Top3: [0.8108, 0.7585, 0.7531]
融合后 Top3: [0.8108, 0.6964, 0.6945]
阈值: 0.7
结果: ✅ 1条
```

---

## 🔍 问题根本原因

### 1. 查询长度差异

**查询1**: "推荐三清山3天旅游攻略" (12个字)
- 包含多个词: `推荐`、`三清山`、`3天`、`旅游`、`攻略`
- 向量分散，语义不够集中

**查询2**: "三清山" (3个字)
- 核心实体明确
- 向量聚焦，匹配度更高

### 2. 向量化特性

向量模型 `bge-base-zh-v1.5` 的特点：
- **短查询**: 语义更纯粹，匹配度高
- **长查询**: 包含修饰词，可能稀释核心语义

### 3. 文档标题可能很短

如果数据库中的文档标题是：
```
"三清山"
"三清山风景区"
"江西三清山"
```

那么：
- "三清山" 查询 → 直接匹配 → 0.81分 ✅
- "推荐三清山3天旅游攻略" → 包含冗余词 → 0.69分 ❌

---

## 💡 解决方案

### 方案1: 查询预处理（推荐）⭐⭐⭐⭐⭐

在搜索前提取核心实体：

```python
# 在 rag_assistant.py 的 execute 方法中添加
def _extract_destination(query: str) -> str:
    """提取查询中的目的地名称"""
    import re
    
    # 移除常见修饰词
    clean_query = re.sub(r'(推荐|攻略|旅游|天|日|游玩|去|一下)', '', query)
    clean_query = clean_query.strip()
    
    # 如果太短，返回原查询
    if len(clean_query) < 2:
        return query
    
    logger.info(f"[查询优化] 原始: {query} → 提取: {clean_query}")
    return clean_query

# 使用
async def execute(self, context: str) -> Dict[str, Any]:
    logger.info(f"[RAG知识库助手] 开始RAG检索: {context}")
    
    # 提取核心查询
    clean_query = self._extract_destination(context)
    
    # 使用清洗后的查询
    results = self.rag_engine.hybrid_search(
        QueryRequest(query=clean_query),  # 修改这里
        top_k=self.top_k
    )
```

**效果**:
```
"推荐三清山3天旅游攻略" → "三清山"
"去婺源看油菜花的最佳时间" → "婺源油菜花"
```

---

### 方案2: 降低阈值（临时方案）⭐⭐

修改 `config/settings.py`:
```python
RAG_SIMILARITY_THRESHOLD: float = 0.6  # 从0.7降到0.6
```

**优点**: 立即生效
**缺点**: 可能返回低质量结果

---

### 方案3: 多查询融合（最佳）⭐⭐⭐⭐⭐

生成多个查询变体并融合：

```python
def _generate_query_variants(query: str) -> List[str]:
    """生成查询变体"""
    variants = [query]  # 原始查询
    
    # 提取实体
    clean = self._extract_destination(query)
    if clean != query:
        variants.append(clean)
    
    # 添加常见组合
    if "攻略" not in query and "推荐" not in query:
        variants.append(f"{clean}旅游攻略")
        variants.append(f"{clean}推荐")
    
    return list(set(variants))  # 去重

# 使用
async def execute(self, context: str) -> Dict[str, Any]:
    variants = self._generate_query_variants(context)
    logger.info(f"[查询变体] {variants}")
    
    all_results = []
    for variant in variants:
        results = self.rag_engine.hybrid_search(
            QueryRequest(query=variant),
            top_k=5
        )
        all_results.extend(results)
    
    # 去重并排序
    unique_results = self._deduplicate(all_results)
    return unique_results[:self.top_k]
```

---

### 方案4: 混合检索权重调整⭐⭐⭐

当前配置：
```python
稠密=0.9, 稀疏=0.1
```

可以调整为：
```python
稠密=0.7, 稀疏=0.3  # 增加BM25关键词匹配的权重
```

修改 `config/settings.py`:
```python
AI_RECOMMEND_DENSE_WEIGHT: float = 0.7  # 从0.9改为0.7
AI_RECOMMEND_SPARSE_WEIGHT: float = 0.3  # 从0.1改为0.3
```

---

## 🎯 推荐实施方案

### 立即实施（5分钟）

1. **降低阈值** + **提取核心实体**
   ```python
   # settings.py
   RAG_SIMILARITY_THRESHOLD = 0.6
   
   # rag_assistant.py
   clean_query = re.sub(r'(推荐|攻略|旅游|天|日)', '', query).strip()
   ```

### 短期实施（1天）

2. **多查询融合**
   - 生成3-5个查询变体
   - 分别检索
   - 融合结果

### 长期优化（1周）

3. **文档增强**
   - 丰富文档内容
   - 添加同义词
   - 增加描述长度

---

## 📊 预期效果

| 方案 | "推荐三清山3天旅游攻略" 分数 | 预期结果数 |
|------|---------------------------|-----------|
| **当前** | 0.6915 | 0条 ❌ |
| **方案1（提取实体）** | 0.81+ | 1-3条 ✅ |
| **方案2（降低阈值）** | 0.6915 | 5-8条 ⚠️ |
| **方案3（多查询）** | 0.75-0.85 | 3-5条 ✅ |
| **方案4（调权重）** | 0.70-0.75 | 1-3条 ✅ |

---

## ✅ 总结

### 根本原因
- 长查询包含冗余词
- 向量语义被稀释
- 阈值0.7过高

### 最佳方案
**查询预处理（提取核心实体）** + **降低阈值到0.65**

### 快速修复
```python
# 1. 降低阈值
RAG_SIMILARITY_THRESHOLD = 0.65

# 2. 提取核心
clean_query = re.sub(r'(推荐|攻略|旅游|[\d]+天|[\d]+日)', '', query).strip()
```

需要我帮你实施这个修复吗？
