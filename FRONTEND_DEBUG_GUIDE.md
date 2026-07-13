# 🔍 前端显示问题诊断指南

## 当前问题

前端显示"AI推荐完成"而不是推荐内容。

---

## 诊断步骤

### **步骤1: 确认前端已刷新**

**重要！** 必须完全刷新页面加载新代码：

```
方法1: 强制刷新
  Windows: Ctrl + Shift + R
  Mac: Cmd + Shift + R

方法2: 清除缓存
  1. F12打开开发者工具
  2. 右键点击刷新按钮
  3. 选择"清空缓存并硬性重新加载"

方法3: 重启前端开发服务器
  1. 停止 npm run dev (Ctrl+C)
  2. 重新运行 npm run dev
  3. 打开新标签页访问
```

### **步骤2: 检查浏览器控制台**

**操作**: 按F12打开开发者工具，查看Console标签

**应该看到**:
```javascript
连接SSE事件流: /api/ai-recommend/events/session_xxx
节点开始: {step: "rewrite", ...}
节点完成: {step: "rewrite", ...}
...
收到AI答案: {answer: "三清山旅游攻略...", sources: [...]}  // ← 关键
推荐完成: {message: "AI推荐完成"}
```

**如果没有"收到AI答案"**:
- 说明前端没有收到result事件
- 或者前端代码没有更新

### **步骤3: 检查Network标签**

**操作**: F12 → Network标签 → 发起查询

**查找**: `events/session_xxx` 请求

**查看事件流**:
```
event: node_start
data: {...}

event: node_end
data: {...}

event: result        ← 应该有这个
data: {"type":"result","answer":"三清山旅游攻略...","sources":[...]}

event: complete
data: {...}
```

**如果没有result事件**:
- 后端可能没有发送
- 检查后端日志是否有"Result event sent"

---

## 快速解决方案

### **方案1: 强制刷新前端 (最简单)**

```bash
# 1. 完全关闭浏览器
# 2. 重新打开
# 3. 访问 http://localhost:5173
# 4. Ctrl+Shift+R 强制刷新
# 5. 测试查询
```

### **方案2: 重启前端服务**

```bash
# 停止前端服务
Ctrl+C

# 清除node_modules/.vite缓存
rm -rf node_modules/.vite  # Linux/Mac
Remove-Item -Recurse -Force node_modules\.vite  # PowerShell

# 重启
npm run dev
```

### **方案3: 验证代码更新**

查看前端源码是否包含result事件监听：

```javascript
// 按F12 → Sources → AIRecommend.vue
// 搜索 "addEventListener('result'"
// 应该能找到:
eventSource.addEventListener('result', (event) => {
  const data = JSON.parse(event.data)
  console.log('收到AI答案:', data)
  ...
})
```

---

## 临时调试方案

### **添加调试日志**

如果刷新后还是不行，可以添加更多日志：

```javascript
// 在前端添加通用消息监听
eventSource.onmessage = (event) => {
  console.log('[DEBUG] 收到任何消息:', event)
  const data = JSON.parse(event.data)
  console.log('[DEBUG] 数据:', data)
}
```

### **检查事件名称**

后端发送的事件名可能不是`result`，检查：

```javascript
// 监听所有事件类型
eventSource.addEventListener('message', (event) => {
  console.log('[DEBUG] message事件:', event.data)
})

// 或者添加error监听
eventSource.addEventListener('error', (err) => {
  console.error('[DEBUG] SSE错误:', err)
})
```

---

## 常见问题

### **Q1: 刷新后还是显示"AI推荐完成"**

**可能原因**:
1. 浏览器缓存太强，没有加载新代码
2. 前端开发服务器没有重新编译
3. result事件确实没发送

**解决**:
```bash
# 完全重启前端
1. 关闭所有浏览器标签
2. Ctrl+C 停止npm dev
3. 删除 .vite 缓存
4. npm run dev
5. 新标签页打开
```

### **Q2: 控制台没有"收到AI答案"日志**

**说明**: 前端没有收到result事件

**检查**:
1. Network标签是否有result事件
2. 后端日志是否有"Result event sent"
3. 前端代码是否有addEventListener('result')

### **Q3: 控制台有"收到AI答案"但没显示**

**说明**: 事件收到了，但渲染有问题

**检查**:
1. data.answer是否有值
2. messages数组是否正确push
3. v-html是否正确渲染

---

## 最终验证

**完全重启所有服务**:

```bash
# 1. 停止后端
Ctrl+C

# 2. 停止前端
Ctrl+C

# 3. 启动后端
cd backend
python main.py

# 4. 启动前端
cd frontend
npm run dev

# 5. 新浏览器标签打开
http://localhost:5173

# 6. 强制刷新
Ctrl+Shift+R

# 7. 测试
输入: "推荐一下三清山的旅游攻略"
```

---

## 预期最终效果

**前端显示**:
```
AI助手

三清山旅游攻略推荐

玉京峰景区是三清山的最高峰，海拔1819米，是观赏云海、
日出的绝佳地点。站在峰顶，可以俯瞰整个三清山的壮丽
景色，感受大自然的鬼斧神工。

女神峰是三清山最具代表性的景观之一，形似一位婀娜多姿
的少女，因此得名"东方女神"。这里是摄影爱好者的天堂，
不同的角度和光线下，女神峰展现出不同的魅力。

三清山作为中国道教名山和世界自然遗产，拥有独特的花岗岩
峰林地貌和丰富的道教文化遗产...

📚 参考来源 (3条)
▼ 玉京峰景区
  三清山最高峰...
```

---

**现在按照步骤1强制刷新前端，然后测试！** 🚀
