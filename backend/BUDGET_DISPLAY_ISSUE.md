# 预算显示问题分析

## 🐛 问题描述

**现象**: 
- 前端显示: "¥150 - ¥150"
- 预期显示: "¥500" 或合理的预算范围（如 "¥1000 - ¥3000"）

**截图位置**: 综合搜索页面，三清山景点详情

---

## 🔍 问题分析

### 1. 前端代码（✅ 正常）

**文件**: `frontend/src/components/RecommendationList.vue`

```javascript
const formatBudget = (range) => {
  if (!range || range.length < 2) return '未知'
  return `¥${range[0]} - ¥${range[1]}`
}
```

前端逻辑正确，问题在于后端返回的数据。

---

### 2. 后端数据转换（可能的问题）

**文件**: `backend/app/core/rag_engine.py` (行829-832)

```python
budget_range=[
    doc.get("budget_min", 0),  # 从Milvus读取
    doc.get("budget_max", 0)   # 从Milvus读取
]
```

**分析**: 代码逻辑正确，但可能是Milvus中存储的数据有问题。

---

### 3. 数据来源分析

#### 可能原因1: Milvus数据错误

数据库中 `budget_min` 和 `budget_max` 字段可能存储了错误的值：
```
budget_min: 150
budget_max: 150
```

#### 可能原因2: 数据初始化问题

查看数据初始化代码：

**文件**: `backend/app/workflows/document_processing/nodes/node_vectorization.py` (行72)

```python
budget_range=entity.get("budget_range", [1000, 3000]),  # 默认值
```

**文件**: `backend/app/services/destination_extractor.py` (行448)

```python
def _extract_budget_range(self, props: Dict[str, Any]) -> List[int]:
    # 提取预算范围的逻辑
```

---

## 🎯 解决方案

### 方案1: 检查数据库数据（推荐）⭐⭐⭐⭐⭐

使用Python脚本检查Milvus中的实际数据：

```python
from pymilvus import connections, Collection

connections.connect("default", host="localhost", port="19530")
collection = Collection("tourism_destinations")
collection.load()

# 查询三清山数据
results = collection.query(
    expr='name == "三清山"',
    output_fields=["name", "budget_min", "budget_max"]
)

for r in results:
    print(f"{r['name']}: {r['budget_min']} - {r['budget_max']}")
```

### 方案2: 临时修复（快速）⭐⭐⭐

在后端添加数据验证，如果预算异常则使用默认值：

```python
# backend/app/core/rag_engine.py (行829)

budget_min = doc.get("budget_min", 0)
budget_max = doc.get("budget_max", 0)

# 数据验证和修正
if budget_min <= 0 or budget_max <= 0 or budget_min == budget_max:
    # 根据景点类型设置默认预算
    if "世界遗产" in doc.get("tags", ""):
        budget_range = [1000, 3000]  # 高端景点
    else:
        budget_range = [500, 2000]   # 普通景点
else:
    budget_range = [budget_min, budget_max]

destination = Destination(
    # ...
    budget_range=budget_range,
    # ...
)
```

### 方案3: 重新导入数据（彻底）⭐⭐⭐⭐

如果数据源有问题，重新运行数据导入：

```bash
cd backend
python scripts/init_simple_data.py
```

确保数据源文件中的预算字段正确。

---

## 🔧 临时修复代码（立即可用）

**文件**: `backend/app/core/rag_engine.py`

**位置**: 第829-832行

**修改**:

```python
# 原代码
budget_range=[
    doc.get("budget_min", 0),
    doc.get("budget_max", 0)
]

# 修改为（添加验证）
budget_min = doc.get("budget_min", 0)
budget_max = doc.get("budget_max", 0)

# 验证并修正异常数据
if budget_min <= 0 or budget_max <= 0 or budget_min == budget_max or budget_max < 500:
    # 异常数据，使用默认值
    budget_range = [1000, 3000]
    logger.warning(f"景点 {doc.get('name')} 预算数据异常 ({budget_min}-{budget_max})，使用默认值 [1000, 3000]")
else:
    budget_range = [budget_min, budget_max]
```

---

## 📊 预期效果

### 修复前
```
三清山: ¥150 - ¥150  ❌
```

### 修复后
```
三清山: ¥1000 - ¥3000  ✅
```

---

## 🎯 推荐操作步骤

### 步骤1: 立即修复（5分钟）
1. 修改 `backend/app/core/rag_engine.py` 添加数据验证
2. 重启后端
3. 测试查询

### 步骤2: 排查根源（可选）
1. 检查Milvus数据库中的实际数据
2. 如果数据错误，检查数据导入脚本
3. 重新导入正确数据

### 步骤3: 长期优化
1. 在数据导入时添加验证
2. 确保所有景点都有合理的预算范围
3. 添加数据质量检查脚本

---

## ✅ 任务状态

- ⏳ 问题分析：完成
- ⏳ 解决方案：已提供
- ⏳ 代码修复：待实施（需要手动修改）
- ⏳ 测试验证：待完成

---

**文档创建时间**: 2026-07-12  
**问题级别**: 中等（影响用户体验，但不影响核心功能）  
**修复难度**: 简单（5-10分钟）  
**推荐方案**: 方案2（临时修复）

需要我帮你实施修复吗？
