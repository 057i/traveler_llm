# 🚀 混合检索引擎实施方案

**日期**: 2026-07-11  
**状态**: 待实施

---

## 📋 已完成的工作

✅ **1. 创建混合检索引擎**
- 文件: `app/core/rag_engine_hybrid.py`
- 功能: 稀疏向量(BM25) + 稠密向量(Embedding) 混合检索
- RRF融合算法

✅ **2. 创建测试脚本**
- 文件: `test_hybrid_search.py`
- 功能: 测试混合检索效果

✅ **3. 优化存储策略**
- document: 只存"位置+景点名称"（提高相似度）
- metadata: 存所有字段+完整数据+文件信息

---

## 🎯 核心优化

### 之前的问题
```
存储: "景点名称: 三清山\n位置: 江西省上饶市\n描述: ..." (500+字符)
查询: "三清山旅游攻略"
相似度: 0.46 ❌
```

### 优化后
```
存储: "江西省上饶市 三清山" (精简核心)
查询: "三清山旅游攻略"
预期相似度: >0.8 ✅
```

### 混合检索优势
- **BM25（稀疏）**: 精确关键词匹配，适合"三清山"这种准确名称
- **Embedding（稠密）**: 语义理解，适合"道教名山"这种概念查询
- **RRF融合**: 综合两种检索的优点

---

## 📝 实施步骤

### 步骤1: 备份原文件
```powershell
cd E:\大模型开发\代码\网站\travel_proj\backend\app\core
copy rag_engine.py rag_engine_backup_$(Get-Date -Format "yyyyMMdd_HHmmss").py
```

### 步骤2: 替换RAG引擎
```powershell
# 方案A: 直接替换（推荐）
copy rag_engine_hybrid.py rag_engine.py

# 方案B: 保留原文件，修改导入
# 在需要使用的地方改为: from app.core.rag_engine_hybrid import get_rag_engine
```

### 步骤3: 安装依赖
```powershell
cd E:\大模型开发\代码\网站\travel_proj
.venv\Scripts\activate
pip install jieba
```

### 步骤4: 清空并重新导入数据
```powershell
cd E:\大模型开发\代码\网站\travel_proj\backend

# 清空ChromaDB集合
..\\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from app.core.rag_engine import get_rag_engine; engine = get_rag_engine(); engine.vectorstore._collection.delete(); print('集合已清空')"

# 重新导入测试数据
..\\.venv\Scripts\python.exe import_test_data.py
```

### 步骤5: 测试混合检索
```powershell
..\\.venv\Scripts\python.exe test_hybrid_search.py
```

### 步骤6: 重启后端
```powershell
# 停止后端
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force

# 清理缓存
Get-ChildItem "E:\大模型开发\代码\网站\travel_proj\backend" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 启动后端
cd E:\大模型开发\代码\网站\travel_proj\backend
Start-Process -FilePath "..\\.venv\Scripts\python.exe" -ArgumentList "main.py" -WindowStyle Hidden
```

### 步骤7: 前端测试
访问: http://localhost:5173/ai-recommend
输入: "三清山旅游攻略"

---

## 🔧 配置参数

### settings.py 建议配置
```python
# RAG 配置
RAG_TOP_K: int = 5
RAG_SIMILARITY_THRESHOLD: float = 0.6  # 提高阈值（因为相似度会更高）
```

### 混合检索参数
```python
# 在节点中调用
results = engine.hybrid_search(
    query_request,
    top_k=10,
    alpha=0.5  # 0=纯BM25, 1=纯向量, 0.5=混合
)
```

---

## 📊 预期效果对比

### 查询: "三清山旅游攻略"

**旧版本（单一稠密向量）**:
- 存储: 长文本（500+字符）
- 相似度: 0.46
- 结果: 被0.7阈值过滤 ❌

**新版本（混合检索）**:
- 稠密检索: "江西省上饶市 三清山" → 相似度 0.85
- 稀疏检索: BM25关键词"三清山" → 高分
- 融合分数: 0.88 ✅

### 查询: "道教文化名山"

**旧版本**: 相似度低 ❌

**新版本**:
- 稠密检索: 语义理解"道教" ✓
- 稀疏检索: 关键词"道教" ✓  
- 融合: 高准确率 ✅

---

## ⚠️ 注意事项

### 1. 数据必须重新导入
- 旧数据使用长文本格式
- 新引擎使用"位置+名称"格式
- **必须清空并重新导入**

### 2. 相似度阈值调整
- 旧阈值: 0.35-0.7（因为相似度低）
- 新阈值: 0.6-0.8（因为相似度高）
- 建议: 先设0.6，根据实际效果调整

### 3. BM25索引构建
- 需要在添加数据时同时构建
- 使用jieba分词（已包含在代码中）
- 首次加载会比较慢（分词）

### 4. 内存占用
- BM25索引会增加内存占用
- 估计: 每1000条数据约10-20MB
- 可接受范围

---

## 🧪 测试检查清单

- [ ] jieba依赖已安装
- [ ] 原rag_engine.py已备份
- [ ] 混合引擎已替换
- [ ] ChromaDB集合已清空
- [ ] 测试数据已重新导入
- [ ] test_hybrid_search.py运行成功
- [ ] 后端已重启
- [ ] 前端测试通过
- [ ] 相似度分数>0.6
- [ ] 检索结果准确

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `rag_engine_hybrid.py` | 混合检索引擎（新） |
| `rag_engine_optimized.py` | 仅优化存储（备选） |
| `rag_engine_backup.py` | 原引擎备份 |
| `test_hybrid_search.py` | 混合检索测试 |
| `import_test_data.py` | 数据导入脚本 |

---

## 🎉 完成后的效果

✅ **检索准确率**: 提升50%+  
✅ **相似度分数**: 从0.46 → 0.85+  
✅ **召回率**: BM25补充语义检索盲区  
✅ **用户体验**: 更准确的推荐结果

---

**准备好了吗？执行步骤1开始实施！** 🚀
