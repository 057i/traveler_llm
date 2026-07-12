# 问题修复总结

## 修复日期：2026-07-11

---

## 问题1：Province和City提取问题 ✅

### 问题描述
- City字段包含完整的"省+市"（如：`西藏自治区日喀则市`）
- Province字段为空或不正确

### 根本原因
虽然提示词要求LLM返回独立的`province`和`city`字段，但在`destination_extractor.py`的`_convert_graph_entity_to_destination`函数中，**没有将这两个字段添加到返回的字典中**。

### 修复方案
**文件**: `backend/app/services/destination_extractor.py:421-440`

添加了province和city字段的提取：
```python
return {
    'name': props['name'],
    'location': props['location'],
    'province': props.get('province', ''),  # ✅ 新增
    'city': props.get('city', ''),          # ✅ 新增
    'type': entity.get('type', 'Unknown'),
    # ... 其他字段
}
```

### 预期效果
- ✅ Province字段：`西藏自治区` 或 `浙江省`
- ✅ City字段：`日喀则市` 或 `嘉兴市`
- ✅ Location字段：保持完整地址

---

## 问题2：上传RAG文档后搜索不到 ✅

### 问题描述
用户上传了PDF文档（如西藏旅游攻略），提取了152个实体，但前端搜索"西藏旅游攻略"返回：
> "抱歉，没有找到相关的旅游信息"

### 根本原因
向量化节点（`node_vectorization.py`）仍在使用**ChromaDB**存储向量，而系统已经迁移到**Milvus**。

数据流程：
```
PDF上传 → 解析 → 实体提取 → [向量化到ChromaDB] ❌
                                        ↓
前端搜索 → [查询Milvus] ❌ 找不到数据
```

### 修复方案
**文件**: `backend/app/workflows/document_processing/nodes/node_vectorization.py:9-74`

将`vectorize_traditional`函数从ChromaDB改为Milvus：

**修复前**：
```python
from app.core.chroma_client import get_chroma_client
chroma_client = get_chroma_client()
chroma_client.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
```

**修复后**：
```python
from app.core.rag_engine import get_rag_engine
from app.models.schemas import Destination, Season, TravelType

rag_engine = get_rag_engine()

# 将实体转换为Destination对象
destinations = []
for entity in entities:
    if entity.get("type") == "Attraction":
        dest = Destination(
            name=entity.get("name", ""),
            location=entity.get("location", ""),
            description=entity.get("description", ""),
            # ... 其他字段映射
        )
        destinations.append(dest)

# 添加到Milvus
rag_engine.add_destinations(destinations=destinations, source_file=filename)
```

### 关键变化
1. **数据源统一**：PDF上传的实体现在存储到Milvus
2. **格式转换**：将图谱实体转换为Destination模型
3. **双向量生成**：自动生成稀疏+稠密向量

### 预期效果
- ✅ 上传PDF后，实体自动存入Milvus
- ✅ 前端搜索可以检索到新上传的数据
- ✅ 支持混合检索（稀疏+稠密）

---

## 测试建议

### 测试问题1（Province/City）
1. 重新上传一个旅游PDF文档
2. 检查日志输出：
   ```
   [Extract] 最终提取省份: 浙江省
   [Extract] 最终提取城市: 嘉兴市
   ```
3. 确认city不再包含省份前缀

### 测试问题2（搜索功能）
1. 上传PDF文档（如西藏旅游攻略.pdf）
2. 等待处理完成（查看日志确认存入Milvus）
3. 前端搜索关键词：
   - "西藏旅游"
   - "日喀则景点"
   - "珠穆朗玛峰"
4. 应该返回相关景点列表

---

## 相关文件清单

### 修改的文件
1. `backend/app/services/destination_extractor.py`
   - 添加province和city字段提取

2. `backend/app/workflows/document_processing/nodes/node_vectorization.py`
   - 将ChromaDB改为Milvus
   - 添加实体到Destination的转换逻辑

### 依赖关系
```
PDF上传
  ↓
destination_extractor.py (提取实体 + province/city)
  ↓
node_vectorization.py (存储到Milvus)
  ↓
rag_engine.py (Milvus混合检索)
  ↓
前端搜索 (返回结果)
```

---

## 回滚方案

如果需要回滚到ChromaDB：

```bash
cd backend/app/workflows/document_processing/nodes
git checkout HEAD node_vectorization.py
```

然后将`rag_engine.py`替换回ChromaDB版本：
```bash
cd backend/app/core
cp rag_engine_chromadb_backup.py rag_engine.py
```

---

## 注意事项

1. **数据迁移**：修复后，旧的ChromaDB数据不会自动迁移到Milvus
2. **重新上传**：建议重新上传所有PDF文档以确保数据一致性
3. **Milvus服务**：确保Milvus服务运行在localhost:19530

---

**修复完成时间**: 2026-07-11 17:15  
**影响范围**: PDF文档上传、实体提取、向量检索  
**测试状态**: 待测试
