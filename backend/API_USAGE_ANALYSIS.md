# 🔍 前端API使用分析报告

## 📋 后端API端点清单（10个文件）

### 现有的API文件
1. `ai_recommend.py` - AI推荐（SSE）
2. `chat.py` - 智能聊天
3. `documents.py` - 文档管理
4. `graph_rag.py` - 图RAG检索
5. `rag.py` - RAG检索
6. `rerank.py` - 重排序
7. `rrf.py` - RRF融合
8. `smart_recommend.py` - 智能推荐
9. `team_recommend.py` - 团队推荐
10. `team_recommend_ws.py` - 团队推荐（WebSocket）

---

## ✅ 前端正在使用的API

### 1. AI推荐相关 ✅
```javascript
// AI推荐（SSE流式）
POST /api/ai-recommend/stream

// AI推荐历史记录
GET /api/ai-recommend/history/{session_id}
DELETE /api/ai-recommend/history/{session_id}
```

### 2. AI团队推荐相关 ✅
```javascript
// WebSocket连接
WS /api/ai-team-recommend/ws

// 历史记录（推测，与AI推荐类似）
GET /api/team-recommend/history/{session_id}
DELETE /api/team-recommend/history/{session_id}
```

### 3. 文档管理相关 ✅
```javascript
// 文档列表
GET /api/documents/list

// 文档统计
GET /api/documents/statistics

// 上传文档
POST /api/documents/upload

// 删除文档
DELETE /api/documents/{docId}

// 下载文档
GET /api/documents/{docId}/download

// 处理进度（SSE）
GET /api/documents/progress/{taskId}
```

---

## ⚠️ 前端未使用的API（可能）

### 1. rag.py ⚠️
```python
# RAG检索
GET /api/rag/search
```
**状态**: ❌ 前端未找到直接调用
**用途**: RAG向量检索
**建议**: 检查是否被其他服务内部调用

### 2. graph_rag.py ⚠️
```python
# 图RAG检索
GET /api/graph_rag/search
```
**状态**: ❌ 前端未找到直接调用
**用途**: 图数据库检索
**建议**: 检查是否被其他服务内部调用

### 3. rrf.py ⚠️
```python
# RRF融合
POST /api/rrf-recommend/fuse
POST /api/rrf-recommend/fuse_with_diversity
```
**状态**: ❌ 前端未找到直接调用
**用途**: 多源结果融合
**建议**: 检查是否被其他服务内部调用

### 4. rerank.py ⚠️
```python
# 重排序
POST /api/rerank/rerank
POST /api/rerank/rerank_with_explanation
```
**状态**: ❌ 前端未找到直接调用
**用途**: 语义重排序
**建议**: 检查是否被其他服务内部调用

### 5. chat.py ⚠️
```python
# 智能聊天
POST /api/chat/recommend
```
**状态**: ❌ 前端未找到直接调用
**用途**: 聊天式推荐
**建议**: 可能是早期功能，已被AI推荐替代

### 6. smart_recommend.py ⚠️
```python
# 智能推荐
POST /api/smart-recommend/recommend
```
**状态**: ❌ 前端未找到直接调用
**用途**: 智能推荐（功能不明）
**建议**: 可能是早期功能，已被AI推荐替代

### 7. team_recommend.py ⚠️
```python
# 团队推荐（非WebSocket）
POST /api/team-recommend/recommend
```
**状态**: ❌ 前端未找到直接调用
**用途**: 团队推荐API版本
**说明**: 前端只使用WebSocket版本

---

## 🔍 深度分析

### API调用链分析

#### 前端直接调用的API（3个）✅
1. **ai_recommend.py** - 前端直接使用（SSE）
2. **team_recommend_ws.py** - 前端直接使用（WebSocket）
3. **documents.py** - 前端直接使用

#### 可能被工作流内部调用的API（4个）⚠️
这些API可能不是直接暴露给前端，而是被后端工作流内部调用：

1. **rag.py** - 被AI推荐工作流调用
2. **graph_rag.py** - 被AI推荐工作流调用
3. **rrf.py** - 被RRF推荐服务调用
4. **rerank.py** - 被AI推荐工作流调用

#### 可能已废弃的API（3个）❌
1. **chat.py** - 早期聊天功能，已被AI推荐替代
2. **smart_recommend.py** - 功能不明，可能已废弃
3. **team_recommend.py** - 非WebSocket版本，已被WebSocket替代

---

## 📊 建议清理方案

### 方案A: 保守方案（推荐）⭐
**保留所有API**，因为：
1. rag.py、graph_rag.py、rrf.py、rerank.py 可能被后端工作流内部调用
2. 需要进一步验证才能确定是否可删除

**执行**:
- 先检查这些API是否被后端服务调用
- 添加日志追踪API使用情况
- 运行1-2天后根据日志决定

### 方案B: 激进方案（需验证）⚠️
**删除以下API**:
1. ❌ `chat.py` - 已被AI推荐替代
2. ❌ `smart_recommend.py` - 功能重复
3. ❌ `team_recommend.py` - 已有WebSocket版本

**保留**:
- ✅ `rag.py` - 可能被内部调用
- ✅ `graph_rag.py` - 可能被内部调用
- ✅ `rrf.py` - 可能被内部调用
- ✅ `rerank.py` - 可能被内部调用

---

## 🔎 验证步骤

### 步骤1: 检查后端服务调用
```bash
# 搜索这些API是否被后端服务调用
cd backend
grep -r "from app.api.rag import" .
grep -r "from app.api.graph_rag import" .
grep -r "from app.api.rrf import" .
grep -r "from app.api.rerank import" .
grep -r "from app.api.chat import" .
grep -r "from app.api.smart_recommend import" .
```

### 步骤2: 添加访问日志
在每个可疑API中添加：
```python
@router.get("/xxx")
async def xxx():
    logger.warning(f"⚠️ API被调用: /api/xxx - 请检查是否还需要")
    # ...
```

### 步骤3: 运行并观察
- 运行后端1-2天
- 查看日志，看哪些API被调用
- 未被调用的API可以删除

---

## 📋 需要进一步检查的文件

### 检查是否有内部调用
```
app/workflows/ai_recommend/
app/services/
main.py
```

---

**分析时间**: 2026-07-12  
**建议**: 先执行验证步骤，再决定是否删除

需要我帮你检查这些API是否被后端内部调用吗？
