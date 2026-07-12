# Document Processing Workflow - 模块化架构

## 📁 目录结构

```
app/workflows/document_processing/
├── __init__.py              # 包入口
├── state.py                 # 工作流状态定义
├── graph_builder.py         # 工作流图构建器
├── nodes/                   # 节点目录
│   ├── __init__.py         # 节点包入口
│   ├── node_minio.py       # MinIO 存储节点
│   ├── node_pdf_parse.py   # PDF 解析节点 (MinerU + PyPDF)
│   ├── node_chunking.py    # 文本分块节点
│   ├── node_entity_extraction.py  # 实体提取节点 (Qwen + Neo4j)
│   ├── node_vectorization.py      # 向量化节点 (ChromaDB + Neo4j)
│   └── node_finalize.py    # 最终化节点
└── README.md               # 本文档
```

## 🔄 工作流程

```
1. MinIO 存储
   ├─ save_to_minio (主路径)
   └─ minio_fallback (降级)
        ↓
2. PDF 解析
   ├─ parse_pdf_mineru (MinerU, 主路径)
   └─ parse_pdf_pypdf (PyPDF, 降级)
        ↓
3. 文本分块
   └─ chunk_text
        ↓
4. 实体提取 + GraphRAG
   ├─ extract_entities (Qwen 提取 + 自动存入 Neo4j)
   └─ extract_fallback (降级)
        ↓
5. 传统向量化
   ├─ vectorize_traditional (ChromaDB)
   └─ vector_fallback (降级)
        ↓
6. 图向量化
   ├─ vectorize_graph (Neo4j)
   └─ graph_vector_fallback (降级)
        ↓
7. 完成
   └─ finalize
```

## 🎯 核心特性

### 1. 模块化设计
- **单一职责**：每个节点只负责一个明确的任务
- **易于测试**：可以独立测试每个节点
- **易于扩展**：添加新节点无需修改现有代码

### 2. 容错机制
- **Fallback 降级**：每个关键步骤都有降级方案
- **错误隔离**：某个节点失败不会导致整个流程崩溃
- **错误收集**：所有错误记录在 `state["error_messages"]`

### 3. GraphRAG 集成
- **自动提取**：使用增强的 prompt 提取 9 种实体、17 种关系
- **自动存储**：提取后立即存入 Neo4j
- **跨文档合并**：通过 `entity_id` 自动合并相同实体
- **统计追踪**：记录创建了多少实体和关系

## 📝 使用方法

### 方法 1: 使用兼容层（推荐）

```python
from app.core.workflow_engine_v2 import get_workflow_engine

engine = get_workflow_engine()
result = await engine.process_document(
    task_id="task_001",
    filename="travel_guide.pdf",
    file_content=pdf_bytes
)

print(f"提取了 {result['destinations_count']} 个景点")
print(f"创建了 {result['graph_entities_count']} 个图谱实体")
print(f"创建了 {result['graph_relationships_count']} 个关系")
```

### 方法 2: 直接使用工作流图

```python
from app.workflows.document_processing import (
    build_document_processing_graph,
    DocumentProcessingState
)

# 构建工作流图
workflow = build_document_processing_graph()

# 初始化状态
initial_state: DocumentProcessingState = {
    "task_id": "task_001",
    "filename": "guide.pdf",
    "file_content": pdf_bytes,
    # ... 其他字段
}

# 运行工作流
final_state = await workflow.ainvoke(initial_state)
```

### 方法 3: 单独测试节点

```python
from app.workflows.document_processing.nodes import extract_entities

# 准备测试状态
test_state = {
    "task_id": "test",
    "filename": "test.pdf",
    "parsed_text": "京都的清水寺是著名的景点...",
    # ...
}

# 测试节点
result_state = await extract_entities(test_state)
print(f"提取了 {len(result_state['entities'])} 个实体")
```

## 🔧 自定义节点

### 添加新节点

1. 在 `nodes/` 目录创建新文件 `node_xxx.py`
2. 定义节点函数：

```python
from loguru import logger
from ..state import DocumentProcessingState

async def your_custom_node(state: DocumentProcessingState) -> DocumentProcessingState:
    """你的自定义节点"""
    logger.info("[YourNode] Starting custom processing")
    
    try:
        # 你的处理逻辑
        result = do_something(state)
        
        state["your_field"] = result
        state["your_success"] = True
        logger.success("[YourNode] Completed")
        
    except Exception as e:
        logger.error(f"[YourNode] Failed: {e}")
        state["your_success"] = False
        state["error_messages"].append(f"Your node failed: {e}")
    
    return state
```

3. 在 `nodes/__init__.py` 中导出
4. 在 `graph_builder.py` 中添加到工作流图

### 自定义降级逻辑

在 `graph_builder.py` 的条件判断函数中修改：

```python
def _check_your_result(self, state: DocumentProcessingState) -> str:
    """自定义检查逻辑"""
    if state.get("your_success") and some_other_condition:
        return "success"
    return "fallback"
```

## 📊 状态字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | str | 任务唯一标识 |
| `filename` | str | 文件名 |
| `file_content` | bytes | 文件内容 |
| `status` | str | 工作流状态 (pending/processing/completed/failed) |
| `progress` | int | 进度百分比 (0-100) |
| `parsed_text` | str | 解析后的文本 |
| `pages` | int | 页数 |
| `text_chunks` | List[str] | 文本块列表 |
| `entities` | List[Dict] | 提取的实体列表（扁平格式） |
| `destinations_count` | int | 景点数量 |
| `graph_entities_count` | int | 图谱实体数量 |
| `graph_relationships_count` | int | 图谱关系数量 |
| `error_messages` | List[str] | 错误消息列表 |

## 🐛 调试技巧

### 1. 查看工作流图

```python
from app.workflows.document_processing import build_document_processing_graph

workflow = build_document_processing_graph()

# 查看图结构
print(workflow.get_graph().draw_ascii())
```

### 2. 启用详细日志

在 `nodes/` 中的任何节点添加详细日志：

```python
logger.debug(f"[Debug] Current state: {state}")
```

### 3. 断点测试

在特定节点设置断点，检查状态：

```python
async def extract_entities(state: DocumentProcessingState):
    # 在这里设置断点
    import pdb; pdb.set_trace()
    
    # 检查状态
    print(f"Parsed text length: {len(state['parsed_text'])}")
    # ...
```

## 🎓 最佳实践

1. **保持节点纯函数**：节点函数只修改 state，不产生副作用
2. **错误处理**：总是捕获异常并记录到 `error_messages`
3. **日志规范**：使用 `[NodeName]` 前缀标记日志来源
4. **状态验证**：在节点开始时验证必需的输入字段
5. **向后兼容**：添加新字段时提供默认值

## 📦 迁移指南

### 从旧版本迁移

旧版本使用单一的 `workflow_engine.py`，新版本使用模块化结构。迁移步骤：

1. **API 保持兼容**：使用 `workflow_engine_v2.py` 作为兼容层
2. **逐步替换**：在 API 层逐步替换为新的导入
3. **测试验证**：确保所有功能正常

```python
# 旧版本
from app.core.workflow_engine import WorkflowEngine

# 新版本（兼容层）
from app.core.workflow_engine_v2 import get_workflow_engine
engine = get_workflow_engine()

# 新版本（直接使用）
from app.workflows.document_processing import build_document_processing_graph
```

## 🚀 性能优化

- **并行处理**：未来可以使用 LangGraph 的并行能力同时处理多个块
- **缓存机制**：在节点中添加缓存避免重复处理
- **流式输出**：使用 `workflow.astream()` 实现流式处理

## 📚 相关文档

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [项目整体架构](../../README.md)
- [Neo4j GraphRAG 设计](../../docs/graphrag_design.md)
