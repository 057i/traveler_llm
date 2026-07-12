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
            :icon="Delete"
          >
            清除历史
          </el-button>
        </div>
      </template>

      <div class="chat-container">
        <!-- 历史加载提示 -->
        <div v-if="historyLoading" class="loading-hint">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载历史消息中...</span>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesRef">
          <!-- 用户消息 -->
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.type]"
          >
            <!-- 用户消息 -->
            <div v-if="msg.type === 'user'" class="user-message">
              <div class="message-content">{{ msg.message }}</div>
              <el-avatar :size="32" style="background: #409eff;">我</el-avatar>
            </div>

            <!-- AI消息 -->
            <div v-else-if="msg.type === 'assistant'" class="assistant-message">
              <el-avatar :size="32" style="background: #9c27b0;">AI</el-avatar>
              <div class="message-content">
                <div class="answer-content" v-html="formatAnswer(msg.message)"></div>

                <!-- 执行节点 -->
                <div v-if="msg.nodes && msg.nodes.length > 0" class="workflow-details">
                  <el-collapse>
                    <el-collapse-item>
                      <template #title>
                        <div class="workflow-title">
                          <el-icon><Operation /></el-icon>
                          <span>查看工作流执行详情 ({{ msg.nodes.length }}个节点)</span>
                        </div>
                      </template>
                      <el-timeline>
                        <el-timeline-item
                          v-for="(node, idx) in msg.nodes"
                          :key="idx"
                          :type="node.status"
                          :icon="node.icon"
                          :color="node.color"
                        >
                          <div class="node-info">
                            <div class="node-title">
                              <strong>{{ node.name }}</strong>
                              <el-tag
                                :type="node.status === 'success' ? 'success' : 'primary'"
                                size="small"
                              >
                                {{ node.status === 'success' ? '完成' : '进行中' }}
                              </el-tag>
                            </div>
                            <p v-if="node.message" class="node-message">{{ node.message }}</p>
                          </div>
                        </el-timeline-item>
                      </el-timeline>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 来源 -->
                <div v-if="msg.sources && msg.sources.length > 0" class="sources">
                  <el-collapse>
                    <el-collapse-item name="sources">
                      <template #title>
                        <div style="display: flex; align-items: center; gap: 8px;">
                          <el-icon><Document /></el-icon>
                          <span>参考来源 ({{ msg.sources.length }}条)</span>
                        </div>
                      </template>
                      <el-collapse accordion>
                        <el-collapse-item
                          v-for="(source, idx) in msg.sources"
                          :key="idx"
                          :title="`来源 ${idx + 1}: ${source.name || source.title || '未命名景点'} - 相关度: ${(source.score * 100).toFixed(1)}%`"
                        >
                          <div class="source-content">
                            <p><strong>描述：</strong>{{ source.description || source.content || '无描述' }}</p>
                            <p v-if="source.tags && source.tags.length > 0">
                              <strong>标签：</strong>
                              <el-tag v-for="tag in source.tags" :key="tag" size="small" style="margin-right: 5px;">{{ tag }}</el-tag>
                            </p>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>

            <!-- 系统消息 -->
            <div v-else-if="msg.type === 'system'" class="system-message">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ msg.message }}</span>
            </div>
          </div>

          <!-- 工作流进度 -->
          <div v-if="isLoading" class="workflow-progress">
            <el-card shadow="hover">
              <template #header>
                <div class="progress-header">
                  <el-icon class="rotating"><Loading /></el-icon>
                  <span>工作流执行中</span>
                  <el-tag type="primary" size="small">
                    {{ executedNodes.length }}/7
                  </el-tag>
                </div>
              </template>

              <el-timeline>
                <el-timeline-item
                  v-for="(node, index) in executedNodes"
                  :key="index"
                  :type="node.status"
                  :icon="node.icon"
                  :color="node.color"
                >
                  <div class="node-info">
                    <div class="node-title">
                      <strong>{{ node.name }}</strong>
                      <el-tag
                        :type="node.status === 'success' ? 'success' : 'primary'"
                        size="small"
                      >
                        {{ node.status === 'success' ? '完成' : '进行中' }}
                      </el-tag>
                    </div>
                    <p v-if="node.message" class="node-message">{{ node.message }}</p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </div>
        </div>

        <!-- 快捷问题 -->
        <div v-if="!isLoading" class="suggestions">
          <el-tag
            v-for="(suggestion, index) in suggestions"
            :key="index"
            @click="handleSuggestionClick(suggestion)"
            class="suggestion-tag"
          >
            {{ suggestion }}
          </el-tag>
        </div>

        <!-- 输入框 -->
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            type="text"
            placeholder="输入您的旅行需求，例如：推荐一下三清山的旅游攻略..."
            @keyup.enter="handleSend"
            :disabled="isLoading"
            class="fixed-input"
          />
          <el-button
            type="primary"
            @click="handleSend"
            :loading="isLoading"
            :disabled="!inputMessage.trim()"
            size="large"
          >
            <el-icon><Position /></el-icon>
            {{ isLoading ? '推荐中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  Position,
  Document,
  InfoFilled,
  Loading,
  Operation,
  Delete
} from '@element-plus/icons-vue'
import { getChatHistory, clearChatHistory } from '@/api/index'

// Session ID
const sessionId = ref('')

// 响应式数据
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const historyLoading = ref(false)
const executedNodes = ref([])
const messagesRef = ref(null)
let eventSource = null

// 快捷问题
const suggestions = [
  '推荐一下三清山的旅游攻略',
  '去婺源看油菜花的最佳时间',
  '南昌周边适合周末游的景点',
  '江西有哪些特色美食'
]

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
  if (eventSource) {
    eventSource.close()
  }
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

    // 将历史消息转换为前端格式
    messages.value = response.messages.map(msg => ({
      type: msg.type,
      message: msg.content,
      timestamp: msg.timestamp,
      sources: msg.metadata?.sources || [],
      nodes: msg.metadata?.nodes || []
    }))

    console.log(`✅ 加载了 ${response.count} 条历史消息`)

    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })

  } catch (error) {
    console.error('加载聊天历史失败:', error)
    // 如果Redis未启动，不报错，正常使用
  } finally {
    historyLoading.value = false
  }
}

// 进度轮询已移除，使用SSE实时接收进度信息

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

// 处理建议点击
const handleSuggestionClick = (suggestion) => {
  inputMessage.value = suggestion
  handleSend()
}

// 发送消息
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

  // 创建SSE连接，传递session_id
  const apiUrl = `/api/ai-recommend/stream?query=${encodeURIComponent(userMessage)}&session_id=${sessionId.value}`

  eventSource = new EventSource(apiUrl)

  console.log('EventSource已创建:', apiUrl)

  // 监听消息
  eventSource.onmessage = (event) => {
    console.log('收到EventSource消息:', event.data)
    try {
      const data = JSON.parse(event.data)
      handleSSEMessage(data)
    } catch (e) {
      console.error('解析SSE消息失败:', e, 'raw data:', event.data)
    }
  }

  // 监听打开
  eventSource.onopen = (event) => {
    console.log('EventSource连接已打开')
  }

  // 监听错误
  eventSource.onerror = (event) => {
    console.error('SSE连接错误:', event)
    messages.value.push({
      type: 'system',
      message: '连接服务器失败，请检查后端服务是否启动'
    })
    isLoading.value = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    scrollToBottom()
  }
}

// 处理SSE消息
const handleSSEMessage = (data) => {
  console.log('收到SSE消息:', data.type, data)

  switch (data.type) {
    case 'start':
      console.log('推荐开始:', data.message)
      break

    case 'node_start':
      executedNodes.value.push({
        name: nodeNameMap[data.node] || data.node,
        status: 'primary',
        icon: 'Loading',
        color: '#409eff',
        message: ''
      })
      scrollToBottom()
      break

    case 'progress':
      const lastNode = executedNodes.value[executedNodes.value.length - 1]
      if (lastNode) {
        lastNode.message = data.message
      }
      break

    case 'node_complete':
      const completeNode = executedNodes.value[executedNodes.value.length - 1]
      if (completeNode) {
        completeNode.status = 'success'
        completeNode.icon = 'Check'
        completeNode.color = '#67c23a'
      }
      break

    case 'result':
      console.log('收到结果消息:', data.answer ? '有答案' : '无答案', 'sources:', data.sources?.length)

      const answer = data.answer || '抱歉，没有找到相关的旅游信息。'

      const newMessage = {
        type: 'assistant',
        message: answer,
        sources: data.sources || [],
        nodes: [...executedNodes.value]
      }

      console.log('添加消息到messages数组:', newMessage)
      messages.value.push(newMessage)

      nextTick(() => {
        scrollToBottom()
      })
      break

    case 'complete':
      console.log('推荐完成')
      isLoading.value = false

      nextTick(() => {
        executedNodes.value = []
      })

      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
      ElMessage.success(data.message || '推荐完成')
      break

    case 'error':
      console.error('收到错误消息:', data.message)
      isLoading.value = false
      executedNodes.value = []
      messages.value.push({
        type: 'system',
        message: `错误: ${data.message}`
      })
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
      ElMessage.error(data.message)
      scrollToBottom()
      break

    default:
      console.warn('未知消息类型:', data.type)
  }
}

// 格式化答案
const formatAnswer = (text) => {
  if (!text) return ''

  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/#{1,6}\s+(.*?)(<br>|$)/g, '<h3>$1</h3>')
    .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>')
    .replace(/\d+\.\s+(.*?)(<br>|$)/g, '<li>$1</li>')
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
/* 保持原有样式 */
.chat-page {
  width: 100%;
  height: 100%;
}

.page-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 20px;
}

.card-header .el-icon {
  font-size: 24px;
  color: #9c27b0;
}

/* 新增：历史加载提示 */
.loading-hint {
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-hint .el-icon {
  font-size: 20px;
}

/* 进度状态消息样式已移除 */

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 100%;
  box-sizing: border-box;
}

.message {
  animation: fadeIn 0.3s;
  max-width: 100%;
  box-sizing: border-box;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  gap: 12px;
}

.user-message .message-content {
  max-width: 80%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  line-height: 1.6;
  box-sizing: border-box;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.assistant-message {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  gap: 12px;
  max-width: 100%;
  box-sizing: border-box;
}

.assistant-message .message-content {
  max-width: 100%;
  width: 100%;
  padding: 16px 16px 16px 36px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  line-height: 1.8;
  box-sizing: border-box;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.answer-content {
  margin-bottom: 16px;
}

.answer-content h3 {
  margin: 20px 0 10px;
  color: #409eff;
}

.answer-content li {
  margin-left: 20px;
  margin-bottom: 8px;
}

.workflow-details {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  font-weight: 500;
}

.system-message {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
}

.workflow-progress {
  margin: 20px 0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.node-info {
  padding: 8px 0;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.node-message {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.sources {
  margin-top: 20px;
}

.source-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  color: #606266;
}

.input-container {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background: white;
}

.suggestions {
  padding: 10px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  border-bottom: 1px solid #e0e0e0;
  background: #fff;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
