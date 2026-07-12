# Redis缓存系统 - 前后端完整对接指南

## ✅ 已完成的工作

### 后端部分（已完成）

#### 1. 核心服务（4个文件）
- ✅ `app/core/redis_client.py` - Redis连接管理
- ✅ `app/services/chat_history.py` - 聊天记录服务
- ✅ `app/services/progress_tracker.py` - 进度追踪服务
- ✅ `app/services/__init__.py` - 服务导出

#### 2. API接口（已添加到 `app/api/ai_recommend.py`）
- ✅ `GET /api/ai-recommend/history/{session_id}` - 获取聊天历史
- ✅ `GET /api/ai-recommend/progress/{session_id}` - 获取实时进度
- ✅ `DELETE /api/ai-recommend/history/{session_id}` - 清除聊天历史
- ✅ `GET /api/ai-recommend/health` - 健康检查

### 前端部分（已完成）

#### 1. API调用函数（已添加到 `frontend/src/api/index.js`）
- ✅ `getChatHistory(sessionId, limit)` - 获取历史
- ✅ `getProgress(sessionId)` - 获取进度
- ✅ `clearChatHistory(sessionId)` - 清除历史
- ✅ `healthCheck()` - 健康检查

---

## 🚀 使用示例

### 1. 生成Session ID

在前端组件中生成唯一的session ID：

```javascript
// 在 AIRecommend.vue 的 setup() 中添加
import { ref, onMounted } from 'vue'
import { getChatHistory, getProgress, clearChatHistory } from '@/api/index'

// 生成或获取session ID
const sessionId = ref('')

onMounted(() => {
  // 从localStorage获取或生成新的
  sessionId.value = localStorage.getItem('ai_recommend_session_id') || generateSessionId()
  localStorage.setItem('ai_recommend_session_id', sessionId.value)
  
  // 加载历史消息
  loadChatHistory()
})

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}
```

---

### 2. 加载聊天历史

```javascript
// 加载聊天历史
async function loadChatHistory() {
  try {
    const response = await getChatHistory(sessionId.value, 50)
    
    // 将历史消息添加到消息列表
    messages.value = response.messages.map(msg => ({
      type: msg.type,
      message: msg.content,
      timestamp: msg.timestamp,
      ...msg.metadata
    }))
    
    console.log(`加载了 ${response.count} 条历史消息`)
    
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
}
```

---

### 3. 轮询进度（实时进度追踪）

```javascript
// 轮询进度
let progressTimer = null

function startProgressPolling() {
  // 每500ms轮询一次
  progressTimer = setInterval(async () => {
    try {
      const progress = await getProgress(sessionId.value)
      
      if (progress.error) {
        // 进度不存在，停止轮询
        stopProgressPolling()
        return
      }
      
      // 更新进度UI
      updateProgressUI(progress)
      
      // 如果完成，停止轮询
      if (progress.status === 'completed' || progress.status === 'failed') {
        stopProgressPolling()
      }
      
    } catch (error) {
      console.error('获取进度失败:', error)
    }
  }, 500)
}

function stopProgressPolling() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

function updateProgressUI(progress) {
  // 更新进度条
  currentProgress.value = progress.progress * 100
  
  // 更新当前节点
  currentNode.value = progress.current_node
  
  // 更新消息
  statusMessage.value = progress.message
  
  // 更新节点状态
  executedNodes.value = Object.keys(progress.nodes).filter(
    node => progress.nodes[node] === 'completed'
  )
}
```

---

### 4. 清除聊天历史

```javascript
// 清除聊天历史
async function handleClearHistory() {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有聊天记录吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await clearChatHistory(sessionId.value)
    
    // 清空前端消息列表
    messages.value = []
    
    ElMessage.success('聊天历史已清除')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除历史失败:', error)
      ElMessage.error('清除失败')
    }
  }
}
```

---

### 5. 在发送消息时传递session ID

```javascript
// 修改handleSend函数
const handleSend = () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    type: 'user',
    message: userMessage
  })

  scrollToBottom()
  isLoading.value = true
  executedNodes.value = []
  currentProgress.value = 0

  // 创建SSE连接时传递session_id
  const apiUrl = `/api/ai-recommend/stream?query=${encodeURIComponent(userMessage)}&session_id=${sessionId.value}`
  
  eventSource = new EventSource(apiUrl)
  
  // 开始轮询进度
  startProgressPolling()
  
  // ... 其他代码
}
```

---

## 📱 完整的Vue组件集成示例

```vue
<template>
  <div class="chat-page">
    <el-card class="page-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><MagicStick /></el-icon>
          <span>AI智能推荐</span>
          <el-tag type="primary" size="small">LangGraph工作流</el-tag>
          
          <!-- 新增：清除历史按钮 -->
          <el-button 
            type="danger" 
            size="small" 
            @click="handleClearHistory"
            style="margin-left: auto;"
          >
            清除历史
          </el-button>
        </div>
      </template>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesRef">
        <!-- 历史消息加载提示 -->
        <div v-if="historyLoading" class="loading-hint">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载历史消息中...</span>
        </div>
        
        <!-- 消息列表 -->
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.type]">
          <!-- 消息内容 -->
        </div>
      </div>

      <!-- 新增：实时进度显示 -->
      <div v-if="isLoading" class="progress-panel">
        <el-progress 
          :percentage="currentProgress" 
          :status="progressStatus"
          :stroke-width="8"
        />
        <div class="progress-info">
          <span class="current-node">{{ nodeNameMap[currentNode] || currentNode }}</span>
          <span class="progress-message">{{ statusMessage }}</span>
        </div>
        <div class="nodes-status">
          <el-tag 
            v-for="node in Object.keys(nodeNameMap)" 
            :key="node"
            :type="getNodeTagType(node)"
            size="small"
            style="margin: 2px;"
          >
            {{ nodeNameMap[node] }}
          </el-tag>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          placeholder="请输入您的旅游需求..."
          @keyup.enter="handleSend"
          :disabled="isLoading"
        >
          <template #append>
            <el-button 
              type="primary" 
              @click="handleSend"
              :loading="isLoading"
            >
              发送
            </el-button>
          </template>
        </el-input>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Loading } from '@element-plus/icons-vue'
import { getChatHistory, getProgress, clearChatHistory } from '@/api/index'

// Session ID
const sessionId = ref('')

// 消息列表
const messages = ref([])
const historyLoading = ref(false)

// 进度相关
const isLoading = ref(false)
const currentProgress = ref(0)
const currentNode = ref('')
const statusMessage = ref('')
const executedNodes = ref([])
let progressTimer = null

// 节点名称映射
const nodeNameMap = {
  query_rewriter: '📝 问题重写',
  parallel_retrieval: '🔍 并行检索',
  rrf_fusion: '🔀 RRF融合',
  confidence_check: '📊 置信度检查',
  tavily_search: '🌐 网络搜索',
  rerank: '⭐ 精排优化',
  synthesizer: '✨ 结果润色'
}

// 节点状态
const nodeStatus = ref({})

// 初始化
onMounted(() => {
  // 生成或获取session ID
  sessionId.value = localStorage.getItem('ai_recommend_session_id') || generateSessionId()
  localStorage.setItem('ai_recommend_session_id', sessionId.value)
  
  console.log('Session ID:', sessionId.value)
  
  // 加载历史消息
  loadChatHistory()
})

// 清理
onUnmounted(() => {
  stopProgressPolling()
})

// 生成Session ID
function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// 加载聊天历史
async function loadChatHistory() {
  historyLoading.value = true
  try {
    const response = await getChatHistory(sessionId.value, 50)
    
    messages.value = response.messages.map(msg => ({
      type: msg.type,
      message: msg.content,
      timestamp: msg.timestamp,
      ...msg.metadata
    }))
    
    console.log(`✅ 加载了 ${response.count} 条历史消息`)
    
  } catch (error) {
    console.error('加载聊天历史失败:', error)
    // 如果Redis未启动，不报错，正常使用
  } finally {
    historyLoading.value = false
  }
}

// 开始进度轮询
function startProgressPolling() {
  stopProgressPolling() // 先停止之前的
  
  progressTimer = setInterval(async () => {
    try {
      const progress = await getProgress(sessionId.value)
      
      if (progress.error) {
        return
      }
      
      // 更新进度
      currentProgress.value = (progress.progress || 0) * 100
      currentNode.value = progress.current_node || ''
      statusMessage.value = progress.message || ''
      nodeStatus.value = progress.nodes || {}
      
      // 如果完成，停止轮询
      if (progress.status === 'completed' || progress.status === 'failed') {
        stopProgressPolling()
      }
      
    } catch (error) {
      // 忽略错误，继续轮询
    }
  }, 500)
}

// 停止进度轮询
function stopProgressPolling() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// 获取节点标签类型
function getNodeTagType(node) {
  const status = nodeStatus.value[node]
  if (status === 'completed') return 'success'
  if (status === 'running') return 'warning'
  if (status === 'failed') return 'danger'
  return 'info'
}

// 清除历史
async function handleClearHistory() {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有聊天记录吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await clearChatHistory(sessionId.value)
    messages.value = []
    
    ElMessage.success('聊天历史已清除')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除历史失败:', error)
      ElMessage.error('清除失败')
    }
  }
}

// 发送消息（修改版，传递session_id）
const handleSend = () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    type: 'user',
    message: userMessage
  })

  isLoading.value = true
  currentProgress.value = 0
  nodeStatus.value = {}

  // 传递session_id
  const apiUrl = `/api/ai-recommend/stream?query=${encodeURIComponent(userMessage)}&session_id=${sessionId.value}`
  
  eventSource = new EventSource(apiUrl)
  
  // 开始轮询进度
  startProgressPolling()
  
  // 监听消息
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleSSEMessage(data)
    } catch (e) {
      console.error('解析SSE消息失败:', e)
    }
  }
  
  eventSource.onerror = (event) => {
    console.error('SSE连接错误:', event)
    isLoading.value = false
    stopProgressPolling()
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }
}

// 处理SSE消息
function handleSSEMessage(data) {
  // 根据消息类型处理
  // ... 现有代码
}
</script>

<style scoped>
.progress-panel {
  margin: 20px 0;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 14px;
}

.current-node {
  font-weight: bold;
  color: #409eff;
}

.progress-message {
  color: #666;
}

.nodes-status {
  margin-top: 10px;
}

.loading-hint {
  text-align: center;
  padding: 20px;
  color: #999;
}

.loading-hint .el-icon {
  font-size: 24px;
  margin-right: 8px;
}
</style>
```

---

## 📊 完整流程

```
用户打开页面
    ↓
1. 生成/获取 session_id
    ↓
2. 加载聊天历史（Redis）
    ↓
3. 用户输入问题
    ↓
4. 发送SSE请求（带session_id）
    ↓
5. 后端保存用户消息到Redis
    ↓
6. 开始进度轮询
    ↓
7. 后端更新进度到Redis
    ↓
8. 前端轮询显示进度
    ↓
9. 后端保存AI回复到Redis
    ↓
10. 前端显示结果
    ↓
11. 停止进度轮询
```

---

## 🔧 配置Redis

### 安装Redis
```bash
pip install redis
```

### 配置文件 (`backend/config/settings.py`)
```python
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0
REDIS_PASSWORD: str = ""
```

---

## ✅ 测试步骤

1. **启动Redis**
   ```bash
   # Windows: 启动Redis服务
   # Linux/Mac:
   redis-server
   ```

2. **测试API**
   ```bash
   # 健康检查
   curl http://localhost:8000/api/ai-recommend/health
   
   # 应返回: {"status": "ok", "redis": true}
   ```

3. **前端测试**
   - 打开浏览器控制台
   - 查看Session ID
   - 发送消息
   - 刷新页面，历史消息应该加载
   - 观察进度实时更新

---

## 📝 注意事项

1. **Redis未启动时**：系统仍然正常工作，只是没有历史记录和进度追踪

2. **Session ID管理**：
   - 存储在localStorage
   - 刷新页面保持会话
   - 清除localStorage会创建新会话

3. **进度轮询**：
   - 500ms轮询一次
   - 完成后自动停止
   - 组件卸载时清理

4. **历史消息**：
   - 默认加载最近50条
   - 7天自动过期
   - 支持手动清除

---

**文档完成时间**: 2026-07-12  
**状态**: ✅ 后端API完成，✅ 前端API完成，⏳ Vue组件集成待测试
