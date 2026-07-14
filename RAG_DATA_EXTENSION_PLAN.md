# 综合搜索结构化筛选 - 数据字段扩展方案

## 🔍 当前问题分析

### 前端传递的筛选条件
```json
{
  "query": "三清山",
  "filters": {
    "budget_range": [100, 500],
    "duration_range": [1, 2],
    "travel_type": "秋季",
    "season": "秋季",
    "interests": ["美食"]
  }
}
```

### 后端筛选逻辑
```python
# 当前只实现了 travel_type 筛选
if filters.get("travel_type"):
    filtered = [r for r in filtered if r.get('category') == travel_type]
```

### 数据库现有字段
```
Milvus Collection字段：
- destination_id
- name
- province
- city
- category
- description
- full_text
- rating
- dense_vector (768维)
- sparse_vector
```

**问题：缺少预算、天数、季节、标签等字段！**

---

## 🎯 解决方案

### 方案1：扩展Milvus字段（推荐）

#### 1.1 新增字段设计

在Milvus中添加以下字段：

```python
# app/core/milvus_hybrid_client.py - 扩展字段

class MilvusHybridClient:
    def _create_collection(self):
        fields = [
            # ... 现有字段 ...
            
            # 新增字段
            FieldSchema(name="estimated_budget", dtype=DataType.INT32),        # 预估预算（元）
            FieldSchema(name="recommended_days", dtype=DataType.INT32),        # 推荐天数
            FieldSchema(name="best_seasons", dtype=DataType.ARRAY, 
                       element_type=DataType.VARCHAR, max_capacity=4),        # 最佳季节数组
            FieldSchema(name="tags", dtype=DataType.ARRAY,
                       element_type=DataType.VARCHAR, max_capacity=20),       # 标签数组
            FieldSchema(name="suitable_for", dtype=DataType.ARRAY,
                       element_type=DataType.VARCHAR, max_capacity=10),       # 适合人群
            FieldSchema(name="difficulty_level", dtype=DataType.VARCHAR, 
                       max_length=20),                                         # 难度等级
        ]
```

#### 1.2 字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `estimated_budget` | INT32 | 人均预算（元） | 300 |
| `recommended_days` | INT32 | 推荐游玩天数 | 2 |
| `best_seasons` | ARRAY[VARCHAR] | 最佳游览季节 | ["春", "秋"] |
| `tags` | ARRAY[VARCHAR] | 特征标签 | ["自然风光", "摄影", "徒步"] |
| `suitable_for` | ARRAY[VARCHAR] | 适合人群 | ["家庭", "情侣", "朋友"] |
| `difficulty_level` | VARCHAR | 游玩难度 | "简单", "中等", "困难" |

---

### 方案2：数据准备与上传

#### 2.1 扩展CSV数据格式

**原始CSV格式：**
```csv
destination_id,name,category,province,city,description,location,...
```

**扩展后CSV格式：**
```csv
destination_id,name,category,province,city,description,estimated_budget,recommended_days,best_seasons,tags,suitable_for,difficulty_level
1,三清山,自然风光,江西省,上饶市,世界自然遗产...,300,2,"春,秋","自然风光,摄影,徒步","家庭,情侣,朋友",中等
2,婺源,古村落,江西省,上饶市,中国最美乡村...,200,2,"春,秋","古村,油菜花,摄影","家庭,情侣",简单
```

#### 2.2 数据示例

| 景点 | 预算 | 天数 | 季节 | 标签 | 适合人群 | 难度 |
|------|------|------|------|------|----------|------|
| 三清山 | 300 | 2 | 春,秋 | 自然风光,摄影,徒步 | 家庭,情侣,朋友 | 中等 |
| 婺源 | 200 | 2 | 春,秋 | 古村,油菜花,摄影 | 家庭,情侣 | 简单 |
| 庐山 | 400 | 3 | 夏,秋 | 避暑,名山,历史 | 家庭,朋友 | 中等 |
| 景德镇 | 150 | 1 | 全年 | 陶瓷,文化,购物 | 家庭,朋友,独自 | 简单 |
| 龙虎山 | 250 | 2 | 春,夏,秋 | 道教,漂流,自然 | 家庭,朋友 | 中等 |

---

### 方案3：修改后端筛选逻辑

#### 3.1 更新 `integrated_search_service.py`

```python
def _apply_filters(self, results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """应用结构化筛选"""
    filtered = results
    
    # 1. 预算筛选
    if filters.get("budget_range"):
        min_budget, max_budget = filters["budget_range"]
        filtered = [
            r for r in filtered
            if min_budget <= r.get('estimated_budget', 0) <= max_budget
        ]
        logger.info(f"[Filter] Budget filter: {len(filtered)} results")
    
    # 2. 天数筛选
    if filters.get("duration_range"):
        min_days, max_days = filters["duration_range"]
        filtered = [
            r for r in filtered
            if min_days <= r.get('recommended_days', 1) <= max_days
        ]
        logger.info(f"[Filter] Duration filter: {len(filtered)} results")
    
    # 3. 季节筛选
    if filters.get("season"):
        season = filters["season"]
        filtered = [
            r for r in filtered
            if season in r.get('best_seasons', [])
        ]
        logger.info(f"[Filter] Season filter: {len(filtered)} results")
    
    # 4. 标签/兴趣筛选
    if filters.get("interests"):
        interests = set(filters["interests"])
        filtered = [
            r for r in filtered
            if interests & set(r.get('tags', []))
        ]
        logger.info(f"[Filter] Interests filter: {len(filtered)} results")
    
    # 5. 人群筛选（如果travel_type映射到suitable_for）
    if filters.get("travel_type"):
        travel_type = filters["travel_type"]
        filtered = [
            r for r in filtered
            if travel_type in r.get('suitable_for', [])
        ]
        logger.info(f"[Filter] Travel type filter: {len(filtered)} results")
    
    return filtered
```

#### 3.2 更新Milvus检索方法

```python
async def _search_milvus(self, query: str, entities: List[str], top_k: int):
    # ... 现有检索逻辑 ...
    
    # 查询时包含新字段
    entity_results = self.milvus_client.collection.query(
        expr=f'name == "{entity}"',
        output_fields=[
            "name", "province", "city", "category", "description", "rating",
            "estimated_budget",      # 新增
            "recommended_days",      # 新增
            "best_seasons",          # 新增
            "tags",                  # 新增
            "suitable_for",          # 新增
            "difficulty_level"       # 新增
        ],
        limit=3
    )
```

---

### 方案4：数据上传脚本修改

#### 4.1 扩展上传脚本

**文件：`scripts/upload_extended_data.py`**

```python
"""
扩展字段数据上传脚本
"""
import pandas as pd
from app.core.milvus_hybrid_client import get_milvus_hybrid_client
from app.core.embedding_service import get_embedding_service

def upload_extended_data(csv_file: str):
    """上传扩展字段的景点数据"""
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    milvus_client = get_milvus_hybrid_client()
    embedding_service = get_embedding_service()
    
    for idx, row in df.iterrows():
        # 生成向量
        text = f"{row['name']} {row['description']}"
        dense_vector = embedding_service.encode(text, normalize_embeddings=True)
        sparse_vector = embedding_service.encode_sparse(text)
        
        # 解析数组字段
        best_seasons = row['best_seasons'].split(',') if pd.notna(row['best_seasons']) else []
        tags = row['tags'].split(',') if pd.notna(row['tags']) else []
        suitable_for = row['suitable_for'].split(',') if pd.notna(row['suitable_for']) else []
        
        # 准备数据
        data = {
            "destination_id": row['destination_id'],
            "name": row['name'],
            "province": row['province'],
            "city": row['city'],
            "category": row['category'],
            "description": row['description'],
            "rating": float(row.get('rating', 4.5)),
            "estimated_budget": int(row.get('estimated_budget', 200)),
            "recommended_days": int(row.get('recommended_days', 1)),
            "best_seasons": best_seasons,
            "tags": tags,
            "suitable_for": suitable_for,
            "difficulty_level": row.get('difficulty_level', '中等'),
            "dense_vector": dense_vector.tolist(),
            "sparse_vector": sparse_vector
        }
        
        # 插入Milvus
        milvus_client.collection.insert([data])
        
        if (idx + 1) % 10 == 0:
            print(f"Uploaded {idx + 1} records...")
    
    print(f"✅ Total uploaded: {len(df)} records")

if __name__ == "__main__":
    upload_extended_data("data/destinations_extended.csv")
```

---

## 📋 实施步骤

### Step 1: 准备扩展数据
- [ ] 创建 `data/destinations_extended.csv`
- [ ] 补充现有景点的扩展字段
- [ ] 预算、天数、季节、标签等

### Step 2: 修改Milvus Schema
- [ ] 备份现有数据
- [ ] 删除旧Collection
- [ ] 创建新Collection（包含扩展字段）
- [ ] 重新上传数据

### Step 3: 更新后端代码
- [ ] 修改 `milvus_hybrid_client.py` - 添加字段定义
- [ ] 修改 `integrated_search_service.py` - 完善筛选逻辑
- [ ] 修改检索方法 - 返回新字段

### Step 4: 测试验证
- [ ] 测试预算筛选
- [ ] 测试天数筛选
- [ ] 测试季节筛选
- [ ] 测试兴趣标签筛选

---

## 💡 快速实施建议

### 最小化方案（快速上线）
1. **只添加3个关键字段**：
   - `estimated_budget` (预算)
   - `recommended_days` (天数)
   - `tags` (标签数组)

2. **手动补充核心景点数据**：
   - 三清山、婺源、庐山等前20个热门景点

3. **先实现预算和天数筛选**：
   - 这两个最实用

### 完整方案（长期规划）
1. 添加所有6个扩展字段
2. 补充完整数据
3. 实现所有筛选维度
4. 添加更多智能推荐逻辑

---

**需要我帮你实施哪个方案？** 🚀
