# API路由语义化优化报告

## 优化时间
2026-07-11

## 优化目标
将API路由和文档描述优化为更加语义化、清晰易懂的形式，提升开发体验和API可读性。

---

## ✅ 已完成的优化

### 1. AI推荐 API（多智能体工作流）

**文件**: `backend/app/api/sse.py`

#### 修改前
```python
router = APIRouter(prefix="/api/sse", tags=["SSE"])

@router.post("/recommend")
async def sse_recommend(query_request: QueryRequest):
    """SSE 实时推荐 - 使用多智能体工作流"""
```

#### 修改后 ✅
```python
router = APIRouter(prefix="/api/ai-recommend", tags=["AI推荐（多智能体）"])

@router.post("/stream")
async def ai_recommend_stream(query_request: QueryRequest):
    """
    AI推荐 - 流式响应（使用多智能体工作流）
    
    技术栈：LangGraph + 多智能体编排
    
    Args:
        query_request: 查询请求
            - query: 用户查询内容
            - season: 旅行季节（可选）
            - budget: 预算（可选）
            - duration: 旅行天数（可选）
            - interests: 兴趣列表（可选）
    """
```

**优化点**:
- ✅ 路由从 `/api/sse/recommend` → `/api/ai-recommend/stream`
- ✅ 函数名从 `sse_recommend` → `ai_recommend_stream`
- ✅ 标签从 "SSE" → "AI推荐（多智能体）"
- ✅ 添加了详细的技术栈说明和参数文档

---

### 2. AI团队推荐 API（传统RAG流程）

**文件**: `backend/app/api/websocket.py`

#### 修改前
```python
router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 智能对话"""
```

#### 修改后 ✅
```python
router = APIRouter(prefix="/api/ai-team-recommend", tags=["AI团队推荐（传统RAG）"])

@router.websocket("/ws")
async def ai_team_recommend_websocket(websocket: WebSocket):
    """
    AI团队推荐 - WebSocket连接（使用传统RAG流程）
    
    技术栈：RAG → GraphRAG → RRF → Rerank
    
    流程：
    1. 接收用户查询
    2. RAG检索（向量数据库）
    3. GraphRAG检索（图数据库）
    4. RRF融合多源结果
    5. Rerank重排序
    6. 返回推荐结果
    
    消息格式：
    - 接收：{"query": "查询内容", "season": "夏季", ...}
    - 发送：{"type": "system|user|assistant|recommendations", "message": "...", ...}
    """
```

**优化点**:
- ✅ 路由从 `/ws/chat` → `/api/ai-team-recommend/ws`
- ✅ 函数名从 `websocket_chat` → `ai_team_recommend_websocket`
- ✅ 添加了路由前缀和标签
- ✅ 添加了详细的流程说明和消息格式文档

---

### 3. RRF融合推荐 API

**文件**: `backend/app/api/rrf.py`

#### 修改前
```python
router = APIRouter(prefix="/api/rrf", tags=["RRF"])

@router.post("/fuse")
async def rrf_fuse(request: RRFRequest):
    """RRF 融合推荐接口"""

@router.post("/recommend")
async def rrf_recommend(query_request: QueryRequest):
    """RRF 完整推荐流程（简化接口）"""
```

#### 修改后 ✅
```python
router = APIRouter(prefix="/api/rrf-recommend", tags=["RRF融合推荐"])

@router.post("/fuse")
async def rrf_fuse_results(request: RRFRequest):
    """
    RRF融合推荐 - 融合多源检索结果
    
    技术栈：RRF（Reciprocal Rank Fusion）
    
    功能：融合来自不同检索源的结果
    - RAG（向量检索）
    - GraphRAG（图检索）
    - 其他自定义源
    """

@router.post("/recommend")
async def rrf_full_recommend(query_request: QueryRequest):
    """
    RRF完整推荐流程
    
    技术栈：RAG → GraphRAG → RRF融合 → Rerank
    
    流程说明：
    1. RAG检索：从向量数据库检索相似景点
    2. GraphRAG检索：从图数据库检索关联景点
    3. RRF融合：使用倒数排名融合算法融合多源结果
    4. Rerank重排序：使用重排序模型优化最终排序
    """
```

**优化点**:
- ✅ 路由前缀从 `/api/rrf` → `/api/rrf-recommend`
- ✅ 标签从 "RRF" → "RRF融合推荐"
- ✅ 函数名优化：`rrf_fuse` → `rrf_fuse_results`，`rrf_recommend` → `rrf_full_recommend`
- ✅ 添加了详细的技术栈和流程说明

---

### 4. RAG文档管理 API

**文件**: `backend/app/api/documents.py`

#### 修改前
```python
router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(file: UploadFile):
    """上传 PDF 文档"""
```

#### 修改后 ✅
```python
router = APIRouter(prefix="/api/documents", tags=["RAG文档管理"])

@router.post("/upload")
async def upload_document(file: UploadFile):
    """
    上传文档并处理
    
    功能：
    1. 上传PDF文档
    2. 提取文本内容
    3. 生成向量嵌入
    4. 存储到ChromaDB
    5. 构建知识图谱（Neo4j）
    
    支持格式：PDF
    
    Args:
        file: 上传的PDF文件
    
    Returns:
        文档ID和处理任务ID
    """
```

**优化点**:
- ✅ 标签从 "Documents" → "RAG文档管理"
- ✅ 添加了详细的功能说明和处理流程
- ✅ 明确了支持的文件格式

---

## 📊 API路由对比表

### 修改前
| API功能 | 路由 | 函数名 | 标签 |
|---------|------|--------|------|
| AI推荐 | `/api/sse/recommend` | `sse_recommend` | SSE |
| AI团队推荐 | `/ws/chat` | `websocket_chat` | - |
| RRF融合 | `/api/rrf/fuse` | `rrf_fuse` | RRF |
| RRF完整推荐 | `/api/rrf/recommend` | `rrf_recommend` | RRF |
| 文档管理 | `/api/documents/*` | - | Documents |

### 修改后 ✅
| API功能 | 路由 | 函数名 | 标签 |
|---------|------|--------|------|
| AI推荐 | `/api/ai-recommend/stream` | `ai_recommend_stream` | AI推荐（多智能体） |
| AI团队推荐 | `/api/ai-team-recommend/ws` | `ai_team_recommend_websocket` | AI团队推荐（传统RAG） |
| RRF融合 | `/api/rrf-recommend/fuse` | `rrf_fuse_results` | RRF融合推荐 |
| RRF完整推荐 | `/api/rrf-recommend/recommend` | `rrf_full_recommend` | RRF融合推荐 |
| 文档管理 | `/api/documents/*` | - | RAG文档管理 |

---

## 🎯 优化原则

### 1. 语义化命名
- ✅ 路由名称清晰表达功能：`ai-recommend`、`ai-team-recommend`、`rrf-recommend`
- ✅ 函数名使用动词+名词结构：`ai_recommend_stream`、`rrf_fuse_results`
- ✅ 避免技术术语（如SSE）作为主要标识

### 2. 一致性
- ✅ 所有推荐API都使用 `/api/{feature}/` 结构
- ✅ 标签统一使用中文，括号内注明技术特点
- ✅ 文档字符串格式统一

### 3. 可发现性
- ✅ 标签分组清晰：按功能分类而非技术实现
- ✅ 文档字符串详细说明技术栈和流程
- ✅ 参数文档完整

### 4. RESTful风格
- ✅ 资源命名使用名词：`ai-recommend`、`documents`
- ✅ 操作使用HTTP方法：POST（创建/执行）
- ✅ 路径层级清晰：`/api/{resource}/{action}`

---

## 🔄 前端适配

### 需要更新的前端API调用

#### 1. AI推荐（ChatRecommend.vue）
```javascript
// 修改前
const response = await fetch('/api/sse/recommend', {...})

// 修改后
const response = await fetch('/api/ai-recommend/stream', {...})
```

#### 2. AI团队推荐（WebSocketChat.vue）
```javascript
// 修改前
const ws = new WebSocket('ws://localhost:8000/ws/chat')

// 修改后
const ws = new WebSocket('ws://localhost:8000/api/ai-team-recommend/ws')
```

#### 3. RRF推荐（RRFRecommend.vue）
```javascript
// 修改前
const response = await fetch('/api/rrf/recommend', {...})

// 修改后
const response = await fetch('/api/rrf-recommend/recommend', {...})
```

---

## 📝 API文档改进

### OpenAPI/Swagger文档优化

**访问地址**: http://localhost:8000/docs

**改进点**:
1. ✅ 标签分组更清晰
   - AI推荐（多智能体）
   - AI团队推荐（传统RAG）
   - RRF融合推荐
   - RAG文档管理

2. ✅ 每个端点都有详细的文档字符串
   - 功能说明
   - 技术栈
   - 流程步骤
   - 参数详解

3. ✅ 示例数据更完整
   - 请求参数示例
   - 响应格式说明

---

## ✅ 验证清单

- [x] AI推荐API路由优化
- [x] AI团队推荐API路由优化
- [x] RRF推荐API路由优化
- [x] 文档管理API优化
- [x] 文档字符串完善
- [x] 函数命名优化
- [x] 标签分组优化
- [ ] 前端API调用更新（待完成）
- [ ] API测试验证（待完成）

---

## 🚀 下一步

1. **更新前端API调用**
   - 修改所有API请求地址
   - 测试新的端点连接

2. **API测试**
   - 测试所有新端点
   - 验证WebSocket连接
   - 确认文档上传功能

3. **性能监控**
   - 添加API性能指标
   - 监控错误率

4. **文档完善**
   - 补充API使用示例
   - 添加错误码说明

---

## 📚 参考资料

- FastAPI最佳实践：https://fastapi.tiangolo.com/tutorial/path-params/
- RESTful API设计规范
- OpenAPI规范文档

---

## 总结

本次优化将所有API路由进行了语义化改造，使得：
1. ✅ 路由名称更清晰易懂
2. ✅ API文档更详细完整
3. ✅ 开发体验得到提升
4. ✅ 代码可维护性增强

后续需要同步更新前端API调用，确保整个系统正常运行。
