# 🚀 方案B实施文档：稀疏+稠密向量都存ChromaDB

**日期**: 2026-07-11  
**方案**: B - 稀疏+稠密向量都持久化到ChromaDB  
**状态**: 已完成开发，待测试

---

## 📋 方案B架构

### 存储结构

```python
# ChromaDB存储内容

document = "江西省上饶市 三清山"  # 短文本，用于生成稠密向量

embedding = [0.123, 0.456, ..., 0.789]  # 768维稠密向量（自动生成）

metadata = {
    # 基础字段
    'name': '三清山',
    'location': '江西省上饶市',
    'description': '三清山是道教名山...',
    'tags': '自然风光,道教文化,登山,摄影',
    'features': '世界自然遗产,奇峰怪石,...',
    'rating': 4.8,
    
    # 稀疏向量（TF-IDF，JSON序列化）
    'sparse_vector': '{
        "三清山": 2.156,
        "江西省": 1.823,
        "道教": 1.654,
        "奇峰": 1.432,
        "怪石": 1.398,
        ...
    }',
    
    # 文件信息
    'source_file': 'sanqingshan.json',
    'file_path': '/data/destinations/sanqingshan.json',
    
    # 完整数据
    'full_data': '{"name":"三清山",...}'
}
```

---

## 🎯 核心优势

### vs 方案A（BM25内存索引）

| 特性 | 方案A | 方案B |
|------|-------|-------|
| **稀疏向量存储** | 内存（重启丢失） | ChromaDB持久化 ✅ |
| **重启后** | 需重建索引 | 自动加载 ✅ |
| **大数据量** | 启动慢 | 无影响 ✅ |
| **实现复杂度** | 简单 | 中等 |
| **内存占用** | 额外占用 | 无额外占用 ✅ |

### 检索流程

```
用户查询: "三清山旅游攻略"
    ↓
1. 稠密向量检索
   - ChromaDB自动用Embedding查询
   - 匹配document: "江西省上饶市 三清山"
   - 返回相似度: 0.85
    ↓
2. 稀疏向量检索
   - 查询分词: ["三清山", "旅游", "攻略"]
   - 生成TF-IDF查询向量
   - 从metadata读取所有文档的sparse_vector
   - 计算余弦相似度
   - 返回相似度: 0.92
    ↓
3. RRF融合
   - alpha=0.5: 稀疏50% + 稠密50%
   - 融合分数: 0.88
    ↓
返回结果: 三清山（融合分数0.88）
```

---

## 📝 已完成的文件

### 1. `rag_engine_planB.py` - 核心引擎
- ✅ `SparseVectorGenerator`: TF-IDF稀疏向量生成器
- ✅ `HybridRAGEngine`: 混合检索引擎
- ✅ `add_destinations()`: 同时存储稀疏+稠密
- ✅ `hybrid_search()`: 混合检索
- ✅ `_dense_search()`: 稠密向量检索
- ✅ `_sparse_search()`: 稀疏向量检索（从metadata读取）
- ✅ `_rrf_fusion()`: RRF融合算法

### 2. `test_planB.py` - 测试脚本
- ✅ 初始化引擎
- ✅ 添加测试数据
- ✅ 测试混合检索
- ✅ 对比不同alpha值
- ✅ 验证存储结构

---

## 🚀 实施步骤

### 步骤1: 安装依赖
```powershell
cd E:\大模型开发\代码\网站\travel_proj
.venv\Scripts\activate
pip install jieba
```

### 步骤2: 备份原引擎
```powershell
cd backend\app\core
copy rag_engine.py rag_engine_backup_$(Get-Date -Format "yyyyMMdd_HHmmss").py
```

### 步骤3: 替换为方案B
```powershell
copy rag_engine_planB.py rag_engine.py
```

### 步骤4: 清空ChromaDB
```powershell
cd E:\大模型开发\代码\网站\travel_proj\backend

# 清空集合
..\\.venv\Scripts\python.exe -c "import chromadb; client = chromadb.HttpClient(host='localhost', port=8088, headers={'X-Chroma-Token': '..123456'}); client.delete_collection('travel_destinations'); print('集合已删除')"
```

### 步骤5: 测试方案B
```powershell
..\\.venv\Scripts\python.exe test_planB.py
```

**预期输出**:
```
✓ 引擎初始化完成
✓ 数据添加成功
  - 稠密向量: 已自动生成并存储
  - 稀疏向量: 已计算并存储到metadata
  - 稀疏向量示例维度: 45

查询: '三清山旅游攻略'
  1. 三清山 (江西省上饶市)
     相似度: 0.880
     来源: hybrid_planB

查询: '道教名山'
  1. 三清山 (江西省上饶市)
     相似度: 0.856
  2. 龙虎山 (江西省鹰潭市)
     相似度: 0.845
```

### 步骤6: 重新导入生产数据
```powershell
# 修改import_test_data.py，使用方案B引擎
..\\.venv\Scripts\python.exe import_test_data.py
```

### 步骤7: 重启后端
```powershell
# 停止
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force

# 清理缓存
Get-ChildItem "E:\大模型开发\代码\网站\travel_proj\backend" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 启动
cd E:\大模型开发\代码\网站\travel_proj\backend
Start-Process -FilePath "..\\.venv\Scripts\python.exe" -ArgumentList "main.py" -WindowStyle Hidden
```

### 步骤8: 前端测试
访问: http://localhost:5173/ai-recommend
测试查询:
- "三清山旅游攻略"
- "道教文化名山"
- "江西避暑胜地"

---

## 📊 预期效果

### 查询类型 vs 相似度

| 查询类型 | 示例 | 稠密检索 | 稀疏检索 | 融合(α=0.5) |
|---------|------|----------|----------|-------------|
| **精确名称** | "三清山" | 0.85 | 0.95 | **0.90** ✅ |
| **城市** | "上饶市旅游" | 0.78 | 0.88 | **0.83** ✅ |
| **关键词** | "道教文化" | 0.72 | 0.91 | **0.82** ✅ |
| **语义** | "适合避暑的山" | 0.85 | 0.65 | **0.75** ✅ |

### alpha参数建议

```python
# 精确匹配场景（景点名称、城市名）
alpha = 0.3  # 更依赖稀疏向量

# 平衡场景（一般查询）
alpha = 0.5  # 稀疏+稠密各50%

# 语义理解场景（概念性查询）
alpha = 0.7  # 更依赖稠密向量
```

---

## ⚠️ 注意事项

### 1. 稀疏向量存储大小
- 每个景点的稀疏向量: 约1-2KB（JSON）
- 1000个景点: 约1-2MB
- 存在metadata中，不影响Embedding检索性能

### 2. TF-IDF训练
- 需要在`add_destinations`时训练
- 一次性训练，后续无需重训练
- 适合静态数据集

### 3. 性能影响
- **稠密检索**: ChromaDB原生支持，速度快 ⚡
- **稀疏检索**: 需要遍历所有文档的metadata，速度较慢 🐢
- **优化**: 可以缓存稀疏向量到内存（首次加载时）

### 4. 与方案A对比
- **优点**: 持久化，重启无需重建
- **缺点**: 稀疏检索速度略慢（需遍历metadata）

---

## 🔧 可选优化

### 优化1: 缓存稀疏向量
```python
class HybridRAGEngine:
    def __init__(self):
        ...
        self.sparse_cache = {}  # 缓存 {doc_id: sparse_vector}
    
    def _load_sparse_cache(self):
        """首次启动时加载所有稀疏向量到内存"""
        collection = self.vectorstore._collection
        all_docs = collection.get(include=['metadatas'])
        
        for i, meta in enumerate(all_docs['metadatas']):
            doc_id = all_docs['ids'][i]
            sparse_json = meta.get('sparse_vector', '{}')
            self.sparse_cache[doc_id] = json.loads(sparse_json)
```

### 优化2: 动态alpha
```python
def adaptive_alpha(query: str) -> float:
    """根据查询类型动态调整alpha"""
    # 短查询（1-2个词）-> 更依赖稀疏
    if len(query) <= 5:
        return 0.3
    
    # 长查询（概念性）-> 更依赖稠密
    elif len(query) > 15:
        return 0.7
    
    # 中等查询 -> 平衡
    else:
        return 0.5
```

---

## ✅ 测试检查清单

- [ ] jieba已安装
- [ ] 原rag_engine.py已备份
- [ ] rag_engine_planB.py已替换为rag_engine.py
- [ ] ChromaDB集合已清空
- [ ] test_planB.py运行成功
- [ ] 稀疏向量已存储到metadata
- [ ] 混合检索返回正确结果
- [ ] 相似度分数合理（>0.7）
- [ ] 后端已重启
- [ ] 前端测试通过

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `rag_engine_planB.py` | 方案B实现 ✅ |
| `test_planB.py` | 测试脚本 ✅ |
| `rag_engine_hybrid.py` | 方案A（内存BM25） |
| `rag_engine_backup.py` | 原引擎备份 |

---

## 🎉 总结

**方案B的核心价值**:
1. ✅ **持久化**: 稀疏+稠密向量都存ChromaDB
2. ✅ **无需重建**: 重启后自动加载
3. ✅ **易维护**: 所有数据在一个地方
4. ✅ **可扩展**: metadata可存更多信息

**适用场景**:
- ✅ 生产环境（需要持久化）
- ✅ 大数据量（避免启动时重建索引）
- ✅ 多实例部署（所有实例共享ChromaDB）

**准备好了吗？执行步骤1开始实施方案B！** 🚀
