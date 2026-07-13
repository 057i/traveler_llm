# ✅ 工作流展示优化 - 简化版

## 问题

之前的方案创建了独立的workflow消息，导致显示了两个工作流。

---

## 新方案（简化）

**不创建独立的workflow消息**，而是：
1. 只在assistant消息中显示工作流
2. 通过`workflowExpanded`控制展开/折叠
3. 完成后自动折叠

---

## 实现

### **消息结构**

```javascript
{
  type: 'assistant',
  message: 'AI回答内容',
  sources: [...],
  nodes: [...],
  workflowExpanded: false,    // false=折叠，true=展开
  workflowStatus: 'completed' // 'running'=执行中, 'completed'=已完成
}
```

### **模板**

```vue
<el-collapse :model-value="msg.workflowExpanded ? ['workflow'] : []">
  <el-collapse-item name="workflow">
    <template #title>
      查看工作流执行详情 (X个节点)
      <el-tag :type="msg.workflowStatus === 'running' ? 'primary' : 'success'">
        {{ msg.workflowStatus === 'running' ? '执行中' : '已完成' }}
      </el-tag>
    </template>
    <!-- 节点列表 -->
  </el-collapse-item>
</el-collapse>
```

### **行为**

- **完成后**: `workflowExpanded: false` → 自动折叠
- **用户可以**: 点击标题手动展开/折叠

---

## 效果

### **AI回复显示**
```
[AI头像]
三清山旅游攻略推荐

玉京峰景区是三清山的最高峰...

▶ 查看工作流执行详情 (8个节点) [已完成]  ← 折叠
▼ 参考来源 (3条)
```

### **手动展开后**
```
▼ 查看工作流执行详情 (8个节点) [已完成]  ← 展开
  ✓ 查询分析 - 完成
  ✓ 混合检索 - 完成
  ...
```

---

## 优势

1. **简单直接** - 不需要占位消息
2. **无重复显示** - 只有一个工作流
3. **自动折叠** - 完成后自动收起
4. **可手动控制** - 用户可以展开查看

---

## 🚀 测试

**刷新前端**:
```
Ctrl+Shift+R
```

**测试查询**:
```
输入: "推荐一下三清山的旅游攻略"
```

**预期**:
- AI答案显示
- 工作流自动折叠
- 点击可展开查看

---

**🎉 简化版完成！刷新测试！** 🚀
