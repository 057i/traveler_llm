# RAG数据扩展方案 - 方案A增强版

## 🎯 方案定义

在方案A基础上，添加旅行类型和季节字段，共5个扩展字段：

### 新增字段列表

| 字段名 | 类型 | 说明 | 示例 | 筛选方式 |
|--------|------|------|------|----------|
| `estimated_budget` | INT32 | 人均预算（元） | 300 | 范围筛选 |
| `recommended_days` | INT32 | 推荐天数 | 2 | 范围筛选 |
| `tags` | ARRAY[VARCHAR] | 标签 | ["自然风光", "摄影"] | 交集匹配 |
| `travel_type` | VARCHAR | 旅行类型 | "自然风光" | 精确匹配 |
| `best_season` | ARRAY[VARCHAR] | 最佳季节 | ["春", "秋"] | 包含匹配 |

---

## 🔍 预算检索问题与解决方案

### 问题分析

**预算是数值范围筛选，不是向量检索！**

用户输入：`budget_range: [100, 500]`
期望结果：返回预算在100-500元之间的景点

### 解决方案：标量字段过滤

Milvus支持两种筛选方式：

#### 方式1：后端内存过滤（当前方式）
```python
# 先检索，再在Python中过滤
results = await milvus_client._search_dense(vector, top_k=100)

# 内存中过滤预算
filtered = [r for r in results if 100 <= r.get('estimated_budget', 0) <= 500]
```

**优点：** 实现简单
**缺点：** 需要检索更多结果，浪费性能

#### 方式2：Milvus标量过滤（推荐）
```python
# 在Milvus查询时就过滤
results = milvus_client.collection.search(
    data=[dense_vector],
    anns_field="dense_vector",
    param={"metric_type": "COSINE", "params": {"ef": 64}},
    limit=top_k,
    expr="estimated_budget >= 100 && estimated_budget <= 500",  # 👈 Milvus过滤表达式
    output_fields=["name", "city", "estimated_budget", ...]
)
```

**优点：** 性能好，在数据库层过滤
**缺点：** 需要修改检索逻辑

---

## 📐 完整实施方案

### Step 1: 修改Milvus Schema

**文件：`app/core/milvus_hybrid_client.py`**

```python
def _create_collection(self):
    """创建collection schema"""
    fields = [
        # 原有字段
        FieldSchema(name="destination_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="province", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="city", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="full_text", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
        
        # ========== 新增字段 ==========
        FieldSchema(name="estimated_budget", dtype=DataType.INT32),           # 预算
        FieldSchema(name="recommended_days", dtype=DataType.INT32),           # 天数
        FieldSchema(name="travel_type", dtype=DataType.VARCHAR, max_length=50),  # 类型
        FieldSchema(name="tags", dtype=DataType.ARRAY, 
                   element_type=DataType.VARCHAR, max_capacity=20, max_length=50),  # 标签
        FieldSchema(name="best_season", dtype=DataType.ARRAY,
                   element_type=DataType.VARCHAR, max_capacity=4, max_length=20),   # 季节
        
        # 向量字段
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dense_dim),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR)
    ]
    
    schema = CollectionSchema(fields, description="Travel destinations with extended fields")
    
    # 创建collection
    collection = Collection(self.collection_name, schema)
    
    # 创建索引
    collection.create_index(
        field_name="dense_vector",
        index_params={
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 256}
        }
    )
    
    collection.create_index(
        field_name="sparse_vector",
        index_params={
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "IP"
        }
    )
    
    # 👉 为数值字段创建标量索引（加速过滤）
    collection.create_index(
        field_name="estimated_budget",
        index_params={"index_type": "STL_SORT"}
    )
    
    collection.create_index(
        field_name="recommended_days",
        index_params={"index_type": "STL_SORT"}
    )
    
    return collection
```

---

### Step 2: 修改检索方法（支持Milvus过滤）

**文件：`app/services/integrated_search_service.py`**

```python
async def _search_milvus(
    self,
    query: str,
    entities: List[str],
    top_k: int,
    filters: Optional[Dict[str, Any]] = None  # 👈 新增filters参数
) -> List[Dict[str, Any]]:
    """Milvus混合检索（支持Milvus层过滤）"""
    try:
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client
        from app.core.embedding_service import get_embedding_service

        if not self.milvus_client:
            self.milvus_client = get_milvus_hybrid_client()
        if not self.embedding_service:
            self.embedding_service = get_embedding_service()

        # 构建Milvus过滤表达式
        expr = self._build_milvus_expr(filters)

        # 1. 稠密检索（带过滤）
        dense_vector = self.embedding_service.encode(query, normalize_embeddings=True)
        dense_results = await self.milvus_client._search_dense(
            dense_vector, 
            top_k=top_k,
            expr=expr  # 👈 传入过滤表达式
        )

        # 2. 稀疏检索（带过滤）
        sparse_results = await self.milvus_client._search_sparse(
            query, 
            top_k=top_k,
            expr=expr  # 👈 传入过滤表达式
        )

        # 3. 精确匹配
        exact_results = []
        if entities:
            for entity in entities[:5]:
                try:
                    # 精确匹配也应用过滤
                    entity_expr = f'name == "{entity}"'
                    if expr:
                        entity_expr = f'{entity_expr} && {expr}'
                    
                    entity_results = self.milvus_client.collection.query(
                        expr=entity_expr,
                        output_fields=[
                            "name", "province", "city", "category", "description", "rating",
                            "estimated_budget", "recommended_days", "travel_type", 
                            "tags", "best_season"
                        ],
                        limit=3
                    )
                    for r in entity_results:
                        exact_results.append({
                            'name': r.get('name'),
                            'city': r.get('city'),
                            'province': r.get('province'),
                            'category': r.get('category'),
                            'description': r.get('description'),
                            'rating': r.get('rating', 0),
                            'estimated_budget': r.get('estimated_budget', 0),
                            'recommended_days': r.get('recommended_days', 1),
                            'travel_type': r.get('travel_type', ''),
                            'tags': r.get('tags', []),
                            'best_season': r.get('best_season', []),
                            'score': 1.0
                        })
                except Exception as e:
                    logger.warning(f"Exact match for '{entity}' failed: {e}")

        # 4. 合并去重
        seen = set()
        merged = []
        for r in exact_results + dense_results + sparse_results:
            name = r.get('name')
            if name and name not in seen:
                seen.add(name)
                merged.append(r)

        # 质量过滤
        filtered = [r for r in merged if r.get('score', 0) >= 0.7]

        logger.success(f"Milvus search: {len(filtered)} results")
        return filtered

    except Exception as e:
        logger.error(f"Milvus search failed: {e}")
        return []

def _build_milvus_expr(self, filters: Optional[Dict[str, Any]]) -> str:
    """构建Milvus过滤表达式"""
    if not filters:
        return ""
    
    conditions = []
    
    # 预算范围
    if filters.get("budget_range"):
        min_b, max_b = filters["budget_range"]
        conditions.append(f"estimated_budget >= {min_b} && estimated_budget <= {max_b}")
    
    # 天数范围
    if filters.get("duration_range"):
        min_d, max_d = filters["duration_range"]
        conditions.append(f"recommended_days >= {min_d} && recommended_days <= {max_d}")
    
    # 旅行类型（精确匹配）
    if filters.get("travel_type"):
        travel_type = filters["travel_type"]
        conditions.append(f'travel_type == "{travel_type}"')
    
    # 季节（数组包含）
    if filters.get("season"):
        season = filters["season"]
        conditions.append(f'array_contains(best_season, "{season}")')
    
    # 兴趣标签（数组交集）
    if filters.get("interests"):
        # Milvus数组交集较复杂，这里用内存过滤
        # 暂不加入expr，后续在Python中过滤
        pass
    
    # 组合条件
    if conditions:
        return " && ".join(conditions)
    
    return ""
```

---

### Step 3: 修改search_stream方法

**文件：`app/services/integrated_search_service.py`**

```python
async def search_stream(...):
    # ...
    
    # Step 2: 多路RAG检索（传入filters）
    milvus_results, neo4j_results = await asyncio.gather(
        self._search_milvus(query, entities, top_k, filters),  # 👈 传入filters
        self._search_neo4j(entities),
        return_exceptions=True
    )
    
    # ...
    
    # Step 4: 结构化筛选（只处理Milvus无法处理的筛选）
    if filters and filters.get("interests"):
        # 只对兴趣标签进行内存过滤（Milvus表达式不支持复杂数组操作）
        interests = set(filters["interests"])
        fused_results = [
            r for r in fused_results
            if interests & set(r.get('tags', []))
        ]
```

---

### Step 4: 更新Milvus检索方法（支持expr参数）

**文件：`app/core/milvus_hybrid_client.py`**

```python
async def _search_dense(
    self, 
    dense_vector: List[float], 
    top_k: int = 20,
    expr: str = ""  # 👈 新增参数
) -> List[Dict[str, Any]]:
    """稠密向量检索（支持过滤表达式）"""
    try:
        dense_search_params = {
            "metric_type": "COSINE",
            "params": {"ef": settings.MILVUS_SEARCH_EF}
        }

        # 构建搜索参数
        search_params = {
            "data": [dense_vector],
            "anns_field": "dense_vector",
            "param": dense_search_params,
            "limit": top_k,
            "output_fields": [
                "name", "province", "city", "category", "description", "rating",
                "estimated_budget", "recommended_days", "travel_type", 
                "tags", "best_season"
            ]
        }
        
        # 如果有过滤表达式，添加expr参数
        if expr:
            search_params["expr"] = expr
            logger.info(f"[Milvus] Dense search with filter: {expr}")

        results = self.collection.search(**search_params)

        # 格式化结果
        output = []
        for hits in results:
            for hit in hits:
                output.append({
                    'name': hit.entity.get('name'),
                    'city': hit.entity.get('city'),
                    'province': hit.entity.get('province'),
                    'category': hit.entity.get('category'),
                    'description': hit.entity.get('description'),
                    'rating': hit.entity.get('rating', 0),
                    'estimated_budget': hit.entity.get('estimated_budget', 0),
                    'recommended_days': hit.entity.get('recommended_days', 1),
                    'travel_type': hit.entity.get('travel_type', ''),
                    'tags': hit.entity.get('tags', []),
                    'best_season': hit.entity.get('best_season', []),
                    'score': hit.distance
                })

        logger.info(f"[Milvus] Dense search returned {len(output)} results")
        return output

    except Exception as e:
        logger.error(f"[Milvus] Dense search failed: {e}")
        return []

async def _search_sparse(
    self, 
    query: str, 
    top_k: int = 20,
    expr: str = ""  # 👈 新增参数
) -> List[Dict[str, Any]]:
    """稀疏向量检索（支持过滤表达式）"""
    # ... 类似_search_dense的修改
```

---

### Step 5: 数据准备

**扩展CSV格式：`data/destinations_extended.csv`**

```csv
destination_id,name,province,city,category,description,rating,estimated_budget,recommended_days,travel_type,tags,best_season
1,三清山,江西省,上饶市,世界自然遗产,世界自然遗产、世界地质公园...,4.7,300,2,自然风光,"自然风光,摄影,徒步","春,秋"
2,婺源,江西省,上饶市,古村落,中国最美乡村...,4.6,200,2,历史文化,"古村,油菜花,摄影","春,秋"
3,庐山,江西省,九江市,名山,避暑胜地...,4.8,400,3,自然风光,"避暑,名山,历史","夏,秋"
4,景德镇,江西省,景德镇市,文化,陶瓷之都...,4.5,150,1,历史文化,"陶瓷,文化,购物","春,夏,秋,冬"
5,龙虎山,江西省,鹰潭市,道教名山,道教发源地...,4.6,250,2,历史文化,"道教,漂流,自然","春,夏,秋"
```

---

## 📋 实施步骤总结

1. ✅ **备份现有数据**
2. ✅ **修改Milvus Schema** - 添加5个字段
3. ✅ **修改检索方法** - 支持expr过滤
4. ✅ **准备扩展数据** - CSV补充新字段
5. ✅ **删除旧Collection** - `collection.drop()`
6. ✅ **创建新Collection** - 包含新字段
7. ✅ **上传新数据** - 导入扩展数据
8. ✅ **测试验证** - 完整测试所有筛选

---

## 🎯 预期效果

### 筛选示例
```python
# 用户输入
filters = {
    "budget_range": [100, 500],
    "duration_range": [1, 2],
    "travel_type": "自然风光",
    "season": "春",
    "interests": ["摄影"]
}

# Milvus层过滤（高性能）
expr = "estimated_budget >= 100 && estimated_budget <= 500 && recommended_days >= 1 && recommended_days <= 2 && travel_type == '自然风光' && array_contains(best_season, '春')"

# Python内存过滤（只处理interests）
filtered = [r for r in results if "摄影" in r.get('tags', [])]
```

---

**准备开始实施吗？** 🚀
