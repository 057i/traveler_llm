# 节点事件发送修改清单

## 已完成
- [x] utils.py - 创建统一的事件发送函数
- [x] workflow_service.py - 删除旧的send_node_start_event函数
- [x] node_minio.py - 添加start和end事件

## 待修改

### node_pdf_parse.py
- [ ] 修改导入: `from ..utils import send_node_start, send_node_end`
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "parse", "PDF解析", 30, message

### node_chunking.py
- [ ] 修改导入: `from ..utils import send_node_start, send_node_end`
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "chunk", "文本分块", 45, message

### node_entity_extraction.py
- [ ] 修改导入: `from ..utils import send_node_start, send_node_end`
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "extract", "实体提取", 60, message

### node_vectorization.py (两个函数)
#### vectorize_traditional
- [ ] 修改导入: `from ..utils import send_node_start, send_node_end`
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "vectorize_traditional", "传统向量化", 75, message

#### vectorize_graph
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "vectorize_graph", "图向量化", 90, message

### node_finalize.py
- [ ] 修改导入: `from ..utils import send_node_start, send_node_end`
- [ ] 函数开始: 调用send_node_start
- [ ] 成功时: 调用send_node_end
- [ ] 传参: task_id, "finalize", "完成", 100, message
