# 🔍 SSE页面消失问题诊断

## 问题现象

1. SSE连接完成后，页面内容消失
2. 工作流程节点不见了
3. AI答案没有显示

---

## 问题原因分析

### **原因1: executedNodes被清空**

在`complete`和`error`事件中：
```javascript
executedNodes.value = []  // ← 这会清空所有节点
```

**影响**: 页面上的工作流程显示消失

### **原因2: result事件可能没有触发**

如果`result`事件在`complete`之后才到达，消息就不会显示。

### **原因3: SSE连接异常关闭**

从日志看到：
```
[SSE] Connection closed for session: session_xxx
```

如果连接异常关闭，`onerror`会被触发，导致页面清空。

---

## 🔧 修复方案

### **修复1: 不要清空executedNodes**

让工作流程保留在页面上：

```javascript
// 监听complete事件
eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data)
  console.log('推荐完成:', data)

  isLoading.value = false
  // executedNodes.value = []  // ← 注释掉，保留节点显示

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  ElMessage.success('推荐完成')
})
```

### **修复2: 确保result事件在complete之前**

后端已经添加了延迟：
```python
redis_client.publish(...)  # 发送result
await asyncio.sleep(0.1)   # 等待
await send_complete_event(...)  # 发送complete
```

### **修复3: 添加调试日志**

在前端添加更多日志：

```javascript
eventSource.addEventListener('result', (event) => {
  const data = JSON.parse(event.data)
  console.log('🎯 收到AI答案:', data)
  console.log('🎯 answer长度:', data.answer?.length)
  console.log('🎯 sources数量:', data.sources?.length)

  messages.value.push({
    type: 'assistant',
    message: data.answer || '生成答案失败',
    sources: data.sources || [],
    nodes: [...executedNodes.value]  // 保存当前的节点
  })
  
  console.log('🎯 messages数组长度:', messages.value.length)
  scrollToBottom()
})
```

---

## 🚀 立即修复

### **步骤1: 修改前端Vue代码**

```vue
// frontend/src/views/AIRecommend.vue

// 找到complete事件处理
eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data)
  console.log('推荐完成:', data)

  isLoading.value = false
  // 不要清空executedNodes，保留工作流显示
  // executedNodes.value = []  // ← 注释掉

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  ElMessage.success('推荐完成')
})

// 找到error事件处理
eventSource.addEventListener('error', (event) => {
  console.error('SSE错误:', event)

  if (event.data) {
    try {
      const data = JSON.parse(event.data)
      messages.value.push({
        type: 'system',
        message: `错误: ${data.message || '推荐失败'}`
      })
      ElMessage.error(data.message || '推荐失败')
    } catch (e) {
      console.error('解析错误消息失败')
    }
  }

  isLoading.value = false
  // 不要清空executedNodes
  // executedNodes.value = []  // ← 注释掉

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  scrollToBottom()
})

// 找到onerror处理
eventSource.onerror = (error) => {
  console.error('SSE连接错误:', error)

  if (isLoading.value) {
    messages.value.push({
      type: 'system',
      message: '连接服务器失败，请检查后端服务'
    })
    ElMessage.error('连接失败')

    isLoading.value = false
    // 不要清空executedNodes
    // executedNodes.value = []  // ← 注释掉
  }

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  scrollToBottom()
}
```

### **步骤2: 重启前端**

```bash
# 停止前端
Ctrl+C

# 重启
npm run dev
```

### **步骤3: 测试**

1. 刷新浏览器 (Ctrl+Shift+R)
2. 打开控制台 (F12)
3. 发起查询
4. 观察日志和页面

---

## 🔍 调试检查清单

### **后端日志检查**

```
✓ [Synthesizer] LLM Generated Answer:
✓ [Synthesizer] Generated answer: 1586 characters
✓ [AIRecommend] Result event sent
✓ [AIRecommend] Workflow completed
```

### **前端控制台检查**

```
✓ 连接SSE事件流: /api/ai-recommend/events/session_xxx
✓ 节点开始: {step: "rewrite", ...}
✓ 节点完成: {step: "rewrite", ...}
✓ 🎯 收到AI答案: {answer: "...", sources: [...]}  ← 关键
✓ 🎯 answer长度: 1586
✓ 🎯 sources数量: 3
✓ 🎯 messages数组长度: 2
✓ 推荐完成: {message: "AI推荐完成"}
```

### **前端页面检查**

```
✓ 工作流程节点仍然显示
✓ AI推荐内容正确显示
✓ 参考来源列表显示
✓ 没有错误消息
```

---

## 📊 事件顺序验证

**正确的顺序**:
```
1. node_start (多次)
2. node_end (多次)
3. result → 显示答案 ← 关键
4. complete → 关闭连接
```

**错误的顺序** (导致问题):
```
1. node_start
2. node_end
3. complete → 清空节点、关闭连接
4. result → 太晚了，连接已关闭
```

---

## 🎯 最终验证

**页面应该显示**:

```
[用户消息]
推荐一下三清山的旅游攻略

[AI回复]
三清山旅游攻略推荐

玉京峰景区是三清山的最高峰，海拔1819米...
女神峰是三清山最具代表性的景观...
三清山作为中国道教名山...

▼ 查看工作流执行详情 (8个节点)  ← 应该保留
  ✓ 查询分析 - 完成
  ✓ 混合检索 - 完成
  ✓ 附近检索 - 完成
  ...

▼ 参考来源 (3条)
  来源1: 玉京峰景区 - 相关度: 85.1%
  来源2: 女神 - 相关度: 82.3%
  来源3: 三清山 - 相关度: 74.2%
```

---

**现在立即修改前端代码，注释掉3处`executedNodes.value = []`！** 🚀
