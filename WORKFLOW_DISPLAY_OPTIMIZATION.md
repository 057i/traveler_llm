# ✅ 工作流展示优化完成

## 优化方案

### **核心改进**

1. **执行中自动展开** - 工作流正在执行时，自动展开显示实时进度
2. **完成后自动折叠** - 工作流完成后，自动折叠节省空间
3. **手动展开/折叠** - 用户可以随时点击展开查看详情
4. **状态标签显示** - 清晰显示"执行中"或"已完成"状态
5. **独立的进度消息** - 执行期间显示独立的进度消息，完成后替换为答案

---

## 实现细节

### **1. 添加状态属性**

每条消息现在包含：
```javascript
{
  type: 'assistant' | 'workflow',  // 消息类型
  message: '...',
  sources: [...],
  nodes: [...],
  workflowExpanded: true/false,    // 是否展开
  workflowStatus: 'running' | 'completed'  // 工作流状态
}
```

### **2. 执行流程**

**开始时**:
```javascript
// 添加占位的工作流消息（自动展开）
messages.value.push({
  type: 'workflow',
  message: '',
  nodes: [],
  workflowExpanded: true,      // 自动展开
  workflowStatus: 'running'    // 执行中
})
```

**执行中**:
```javascript
// node_start/node_end时更新占位消息的nodes
const workflowMsg = messages.value.find(m => m.type === 'workflow')
if (workflowMsg) {
  workflowMsg.nodes = [...executedNodes.value]
}
```

**完成时**:
```javascript
// 移除占位消息
const workflowMsgIndex = messages.value.findIndex(m => m.type === 'workflow')
if (workflowMsgIndex !== -1) {
  messages.value.splice(workflowMsgIndex, 1)
}

// 添加最终答案（自动折叠）
messages.value.push({
  type: 'assistant',
  message: data.answer,
  sources: data.sources,
  nodes: [...executedNodes.value],
  workflowExpanded: false,      // 自动折叠
  workflowStatus: 'completed'   // 已完成
})
```

### **3. 模板结构**

**工作流执行中消息** (type='workflow'):
```vue
<div class="workflow-progress">
  <el-icon class="is-loading"><Loading /></el-icon>
  <span>正在生成推荐...</span>
</div>

<el-collapse :model-value="['workflow']">  <!-- 自动展开 -->
  <el-collapse-item name="workflow">
    <template #title>
      工作流执行详情 (X个节点)
      <el-tag type="primary">执行中</el-tag>
    </template>
    <!-- 实时节点进度 -->
  </el-collapse-item>
</el-collapse>
```

**AI回复消息** (type='assistant'):
```vue
<div class="answer-content">答案内容</div>

<el-collapse :model-value="[]">  <!-- 自动折叠 -->
  <el-collapse-item name="workflow">
    <template #title>
      查看工作流执行详情 (X个节点)
      <el-tag type="success">已完成</el-tag>
    </template>
    <!-- 历史节点记录 -->
  </el-collapse-item>
</el-collapse>
```

### **4. CSS样式**

```css
.workflow-progress {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #409eff;
}

.workflow-progress .el-icon {
  animation: rotating 2s linear infinite;
}
```

---

## 用户体验

### **执行中**
```
┌─────────────────────────────────────┐
│ [AI头像]                            │
│                                     │
│  ⟳ 正在生成推荐...                  │
│                                     │
│  ▼ 工作流执行详情 (5个节点) [执行中] │
│    ✓ 查询分析 - 完成                │
│    ✓ 混合检索 - 完成                │
│    ⟳ 置信度检查 - 进行中            │
│    • 网络搜索 - 等待                │
│    • 答案生成 - 等待                │
└─────────────────────────────────────┘
```

### **完成后**
```
┌─────────────────────────────────────┐
│ [AI头像]                            │
│                                     │
│  三清山旅游攻略推荐                 │
│                                     │
│  玉京峰景区是三清山的最高峰...      │
│  女神峰是三清山最具代表性的景观...  │
│                                     │
│  ▶ 查看工作流执行详情 (8个节点) [已完成] ← 折叠
│                                     │
│  ▼ 参考来源 (3条)                   │
│    来源1: 玉京峰景区                │
│    来源2: 女神                      │
│    来源3: 三清山                    │
└─────────────────────────────────────┘
```

### **手动展开后**
```
┌─────────────────────────────────────┐
│  ▼ 查看工作流执行详情 (8个节点) [已完成]
│    ✓ 查询分析 - 完成                │
│    ✓ 混合检索 - 完成                │
│    ✓ 附近检索 - 完成                │
│    ✓ 置信度检查 - 完成              │
│    ✓ 网络搜索 - 完成                │
│    ✓ 结果融合 - 完成                │
│    ✓ 智能重排 - 完成                │
│    ✓ 答案生成 - 完成                │
└─────────────────────────────────────┘
```

---

## 优势

1. **清晰的状态反馈** - 用户随时知道系统在做什么
2. **不干扰阅读** - 完成后自动折叠，专注于答案
3. **可追溯性** - 可以随时展开查看执行过程
4. **性能友好** - 不依赖loading状态，独立管理
5. **视觉吸引力** - 旋转的加载图标，蓝色的进度条

---

## 🚀 测试步骤

### **1. 保存并刷新**
```
前端会自动热重载
或手动 Ctrl+Shift+R
```

### **2. 测试查询**
```
输入: "推荐一下三清山的旅游攻略"
```

### **3. 观察变化**

**执行中**:
- 应该看到"正在生成推荐..."提示
- 工作流自动展开
- 节点实时更新
- "执行中"标签

**完成后**:
- 工作流自动折叠
- 显示AI答案
- "已完成"标签
- 可以手动展开查看

---

## 📝 技术要点

1. **响应式状态管理** - 使用find和splice高效更新
2. **Vue的model-value** - 动态控制collapse展开状态
3. **消息类型区分** - workflow和assistant分别渲染
4. **实时更新机制** - 节点事件触发UI更新
5. **CSS动画** - 旋转加载图标提升体验

---

**🎉 优化完成！刷新前端测试！** 🚀
