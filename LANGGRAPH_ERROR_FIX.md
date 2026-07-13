# 🐛 LangGraph并发错误修复

## 错误信息

```
InvalidUpdateError: At key 'task_id': Can receive only one value per step.
Use an Annotated key to handle multiple values.
```

## 根本原因

### **并行节点问题**

在文档处理工作流中，有2个节点并行执行：
```python
# graph_builder.py
vectorize_traditional  # RAG向量化
vectorize_graph        # GraphRAG向量化
```

当两个节点同时完成并返回state时，LangGraph检测到`task_id`被同时更新2次，导致错误。

## 为什么会这样？

### **LangGraph并发规则**

1. **普通字段**（如`task_id: str`）：
   - 每个step只能有一个节点更新
   - 如果多个节点返回相同字段 → 错误

2. **Annotated字段**（如`errors: Annotated[List[str], add]`）：
   - 可以接受多个更新
   - 使用reducer（如`add`）合并值

3. **节点返回完整state**：
   - 如果节点返回`return state`
   - LangGraph认为所有字段都被更新
   - 包括`task_id`等不应该改变的字段

## 🔧 解决方案

### **方案A: 节点只返回修改的字段（推荐）**

```python
# 错误 ❌
async def vectorize_traditional(state: DocumentProcessingState):
    state["vector_success"] = True
    return state  # 返回完整state，包括task_id

# 正确 ✅
async def vectorize_traditional(state: DocumentProcessingState):
    return {
        "vector_success": True,
        # 只返回修改的字段，不返回task_id
    }
```

### **方案B: 改为串行执行（简单但慢）**

```python
# 不并行
self.graph.add_edge("extract_entities", "vectorize_traditional")
self.graph.add_edge("vectorize_traditional", "vectorize_graph")
self.graph.add_edge("vectorize_graph", "finalize")
```

### **方案C: 使用Annotated（复杂）**

```python
# state.py
from typing_extensions import Annotated
from operator import add

class DocumentProcessingState(TypedDict):
    # 改为列表，支持并发
    task_id: Annotated[List[str], add]
```

**但这不合理**，因为task_id应该是单一值。

---

## ✅ 推荐方案：方案A

修改所有节点，确保只返回修改的字段。

### **需要检查的节点**

```python
# nodes/__init__.py中的所有节点
- save_to_minio
- parse_pdf_mineru
- chunk_text
- extract_entities
- vectorize_traditional  ← 并行节点1
- vectorize_graph        ← 并行节点2
- finalize
```

### **检查模式**

```python
# 每个节点应该：
async def node_func(state: DocumentProcessingState):
    # 处理逻辑...
    
    # ✅ 只返回修改的字段
    return {
        "field1": value1,
        "field2": value2,
    }
    
    # ❌ 不要返回完整state
    # return state
```

---

## 🔍 快速诊断

运行此脚本检查所有节点：

```python
# check_nodes.py
import ast
import os

nodes_dir = "backend/app/workflows/document_processing/nodes/"

for filename in os.listdir(nodes_dir):
    if not filename.endswith('.py') or filename == '__init__.py':
        continue
    
    filepath = os.path.join(nodes_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 查找 "return state"
    if 'return state' in content and 'async def' in content:
        print(f"⚠️  {filename} 可能返回完整state")
```

---

## 📋 修复优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🟡 P2 | LangGraph错误 | 只影响文档导入 |
| 🟢 P3 | 不影响查询功能 | 可延后修复 |

**当前状态**：
- ✅ AI推荐功能正常
- ⚠️ 文档导入有错误（但MinerU也有问题）
- 建议：先确保查询功能正常，再修复文档导入

---

## 🚀 如果要立即修复

1. **检查并行节点**：
   ```bash
   # 查看这两个文件
   nodes/node_vectorization.py
   nodes/node_graphrag_vectorization.py
   ```

2. **确保只返回修改的字段**

3. **测试文档上传**

---

## 总结

- **错误原因**：并行节点同时更新task_id
- **推荐方案**：节点只返回修改的字段
- **优先级**：P2（不影响核心查询功能）
- **建议**：先确保查询正常，再修复文档导入

---

**当前可以暂时忽略这个错误，专注于测试AI推荐功能！** ✅
