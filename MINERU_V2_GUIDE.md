# 🆕 MinerU V2 客户端使用指南

## ✅ 已完成

### **1. 创建新的MinerU客户端**
- 文件：`backend/app/core/mineru_client_v2.py`
- 使用你提供的Token和API URL
- 完整的三步流程实现
- 详细的日志和错误处理

### **2. 创建测试脚本**
- 文件：`backend/test_mineru_v2.py`
- 自动查找PDF文件测试
- 保存结果到文件

---

## 📋 新实现特点

### **完整的三步流程**

```python
Step 1: 上传文件
  ↓ 获取预签名URL
  ↓ 上传PDF到URL
  ↓ 返回batch_id

Step 2: 轮询进度
  ↓ 定期查询状态（每3秒）
  ↓ state: queue → processing → done
  ↓ 最多等待10分钟

Step 3: 提取结果
  ↓ 从响应中提取markdown
  ↓ 尝试多个字段名
  ↓ 返回结果
```

### **增强的日志**

```python
[MinerU] 上传文件: xxx.pdf
[MinerU] 获取到batch_id: xxx
[MinerU] [10s] 轮询响应: 200
[MinerU] [10s] 当前状态: processing
[MinerU] [90s] 解析完成
[MinerU] ========== 提取解析结果 ==========
[MinerU] 结果keys: ['state', 'markdown', 'pages_count', ...]
[MinerU] markdown: 23247 字符
[MinerU] Markdown前500字符: ...
[MinerU] ======================================
```

### **完善的错误处理**

- ✅ 超时控制（默认600秒）
- ✅ 网络错误重试
- ✅ 状态检查（done/failed/processing）
- ✅ 详细错误信息

---

## 🔧 环境配置

### **在.env文件中添加**

```bash
# MinerU API配置
MINERU_API_TOKEN=eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxMzIwMDk5NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc4MTE2NTYzMSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiODliOTM1OGEtN2Y1ZS00MDRhLWE1YTItYTJhYWFiZjNlZDgzIiwiZW1haWwiOiIiLCJleHAiOjE3ODg5NDE2MzF9.R9eAgDi5v5sm2y6-EFIWaEajKhCUhlm9bXcHhLNemrbzBQPtH6fm1D-64RepfwJrSLZamatrhJKIXb5_bUntAg
MINERU_BASE_URL=https://mineru.net/api/v4
```

---

## 🧪 测试步骤

### **1. 准备测试PDF**

```bash
# 确保有测试PDF文件
ls backend/data/uploads/*.pdf
```

### **2. 运行测试**

```bash
cd backend
python test_mineru_v2.py
```

### **3. 查看结果**

测试成功后会：
- 在控制台显示详细日志
- 保存结果到 `test_mineru_result.md`

---

## 📊 预期输出

### **成功的情况**

```
[MinerU] Initialized with base_url: https://mineru.net/api/v4
[MinerU] 开始上传文件: test.pdf
[MinerU] 获取到batch_id: xxx
[MinerU] 文件上传成功
[MinerU] 开始轮询进度: batch_id=xxx
[MinerU] [3s] 轮询响应: 200
[MinerU] [3s] 当前状态: queue
[MinerU] [6s] 当前状态: processing
[MinerU] [90s] 解析完成
[MinerU] ========== 提取解析结果 ==========
[MinerU] 结果keys: ['state', 'markdown', 'pages_count']
[MinerU] markdown: 23247 字符
[MinerU] Markdown前200字符: # 标题\n\n内容...
[MinerU] ======================================
✅ Markdown长度: 23247 字符
✅ Raw text长度: 20000 字符
✅ 页数: 14
✅ 结果已保存到: test_mineru_result.md
```

---

## 🔄 集成到现有系统

### **修改node_pdf_parse.py**

```python
# 在文件开头导入
from app.core.mineru_client_v2 import get_mineru_client_v2

# 修改step2_call_mineru_api
def step2_call_mineru_api(file_path: str) -> dict:
    """使用V2客户端"""
    try:
        client = get_mineru_client_v2()
        result = client.parse_by_file(file_path, timeout=600)
        return result
    except Exception as e:
        logger.error(f"[PDF] MinerU V2调用失败: {e}")
        raise
```

### **修改step3_extract_markdown**

```python
def step3_extract_markdown(result: dict, state_pages_count: int) -> tuple:
    """从V2结果提取数据"""
    # V2直接返回markdown字段
    markdown_text = result.get('markdown', '')
    pages_count = result.get('pages_count', state_pages_count)
    
    logger.info(f"[PDF] 提取Markdown: {len(markdown_text)} 字符")
    logger.info(f"[PDF] 页数: {pages_count}")
    
    return markdown_text, pages_count
```

---

## 🆚 对比旧实现

| 特性 | 旧实现 | 新实现V2 |
|------|--------|---------|
| **API版本** | SDK包装 | 直接HTTP |
| **日志详细度** | 🟡 基础 | 🟢 详细 |
| **错误处理** | 🟡 基础 | 🟢 完善 |
| **超时控制** | ❌ 无 | ✅ 有 |
| **调试信息** | 🟡 少 | 🟢 多 |
| **字段提取** | 🟡 单一 | 🟢 多重尝试 |
| **可维护性** | 🟡 中等 | 🟢 高 |

---

## 🎯 下一步

### **1. 等待测试结果**
- 查看测试日志
- 确认是否能正确提取markdown

### **2. 如果测试成功**
- 替换现有的mineru_client.py
- 或与现有实现共存

### **3. 如果测试失败**
- 根据日志调整字段名
- 检查API响应格式

---

## 📝 测试检查清单

- [ ] 能成功上传文件
- [ ] 能获取batch_id
- [ ] 能正确轮询状态
- [ ] 能提取到markdown内容
- [ ] markdown长度>0
- [ ] 日志信息完整清晰

---

## 🚀 当前状态

**正在运行测试...**

测试脚本已在后台运行，将会：
1. 上传PDF到MinerU
2. 轮询解析进度
3. 提取并保存结果

预计耗时：1-2分钟

---

**测试完成后，查看日志确定是否成功！** 🔍
