# 🔍 前端调试日志已添加

## ✅ 已完成

在`AIRecommend.vue`的complete事件监听器中添加了详细调试日志。

---

## 🚀 立即测试

### **1. 重启前端**
```bash
cd frontend
Ctrl+C (停止)
npm run dev (重启)
```

### **2. 完全清除浏览器缓存**
```
F12 → 应用/Application
→ 存储/Storage
→ 清除站点数据
```

### **3. 强制刷新**
```
Ctrl+Shift+R
```

### **4. 清空控制台**
```
F12 → Console
右键 → Clear console
```

### **5. 测试查询**
```
输入: "推荐一下三清山的旅游攻略"
点击发送
```

---

## ✅ 观察控制台输出

应该看到以下详细日志：

```
========== COMPLETE EVENT DEBUG ==========
Raw event data: {"event_type":"complete","message":"AI推荐完成","answer":"三清山旅游攻略推荐...","sources":[...],"timestamp":xxx}
Parsed data: {event_type: 'complete', message: 'AI推荐完成', answer: '三清山旅游攻略推荐...', sources: Array(3), timestamp: xxx}
data.answer: 三清山旅游攻略推荐...
data.answer type: string
data.answer length: 1586
data.sources: [{...}, {...}, {...}]
Condition result: true
==========================================
⏱️ [RECEIVE] complete at xxx | Delay: 34ms
📊 [SUMMARY] Workflow completed
✅ Condition passed, adding message
💡 Complete event contains answer: 1586 chars
📝 Messages array length after push: 2
推荐完成
```

---

## 🎯 诊断结果判断

### **情况A: 看到"✅ Condition passed"**

**说明**: 代码逻辑正确，数据有answer

**但页面还是不显示？**

可能原因：
1. messages数组已更新，但Vue渲染有问题
2. CSS隐藏了内容
3. 页面结构问题

**解决**: 检查Vue模板部分

### **情况B: 看到"❌ Condition failed"**

**说明**: answer是null、undefined或空字符串

**检查**:
1. Raw event data中是否有answer字段
2. answer的值是什么

### **情况C: 根本没有COMPLETE EVENT DEBUG日志**

**说明**: 前端代码未更新

**解决**:
1. 完全关闭浏览器，重新打开
2. 使用无痕模式测试
3. 确认前端服务器已重启

### **情况D: 有答案但messages数组未增加**

**说明**: push失败

**检查**: messages.value是否是响应式对象

---

## 📊 Network检查

同时检查Network EventStream：

```
F12 → Network → events/session_xxx → EventStream
```

找到complete事件，确认数据格式：
```json
{
  "event_type": "complete",
  "message": "AI推荐完成",
  "answer": "三清山旅游攻略推荐...",  ← 必须有
  "sources": [...],                   ← 必须有
  "timestamp": 1783930247.2274227
}
```

---

## 🔧 如果问题依然存在

### **方案1: 检查Vue模板**

确认消息渲染部分没有问题：
```vue
<div v-for="(msg, index) in messages" :key="index">
  <div v-if="msg.type === 'assistant'" class="assistant-message">
    <div class="answer-content" v-html="formatAnswer(msg.message)"></div>
  </div>
</div>
```

### **方案2: 手动添加测试消息**

在控制台执行：
```javascript
messages.value.push({
  type: 'assistant',
  message: '这是手动添加的测试消息',
  sources: [],
  nodes: []
})
```

如果显示了，说明Vue渲染正常，问题在事件处理。

### **方案3: 检查messages初始状态**

在控制台执行：
```javascript
console.log('messages.value:', messages.value)
console.log('messages.value length:', messages.value.length)
```

---

**现在重启前端，清除缓存，测试并观察详细日志！** 🔍
