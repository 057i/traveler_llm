<template>
  <el-card class="chat-interface-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><ChatDotRound /></el-icon>
        <span>智能对话推荐</span>
        <el-tag :type="connected ? 'success' : 'danger'" size="small">
          {{ connected ? '已连接' : '未连接' }}
        </el-tag>
      </div>
    </template>

    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesRef">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.type]"
        >
          <div v-if="msg.type === 'system'" class="system-message">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ msg.message }}</span>
          </div>

          <div v-else-if="msg.type === 'user'" class="user-message">
            <div class="message-content">{{ msg.message }}</div>
            <el-avatar :size="32" class="avatar">我</el-avatar>
          </div>

          <div v-else-if="msg.type === 'assistant'" class="assistant-message">
            <el-avatar :size="32" class="avatar">AI</el-avatar>
            <div class="message-content">
              <div class="agent-header" @click="msg.collapsed = !msg.collapsed">
                <el-tag size="small" type="success" v-if="msg.agent">
                  {{ msg.agent }}
                </el-tag>
                <el-icon class="collapse-icon" :class="{ expanded: !msg.collapsed }">
                  <ArrowRight />
                </el-icon>
                <span class="thinking-text" v-if="msg.isStreaming">正在思考...</span>
                <span class="complete-text" v-else>已完成</span>
              </div>

              <el-collapse-transition>
                <div v-show="!msg.collapsed" class="message-text">
                  <TypewriterText
                    :text="msg.message"
                    :speed="msg.typingSpeed || 30"
                    :autoStart="!msg.collapsed"
                  />
                </div>
              </el-collapse-transition>
            </div>
          </div>

          <div v-else-if="msg.type === 'progress'" class="progress-message">
            <el-icon class="rotating"><Loading /></el-icon>
            <span>{{ msg.message }}</span>
          </div>

          <div v-else-if="msg.type === 'result'" class="result-message">
            <div class="result-header">
              <el-icon><SuccessFilled /></el-icon>
              <span>{{ msg.message }}</span>
            </div>
            <div class="result-count">
              找到 {{ msg.recommendations?.length || 0 }} 个推荐
            </div>
          </div>
        </div>
      </div>

      <!-- 建议问题 -->
      <div v-if="suggestions.length > 0" class="suggestions">
        <el-tag
          v-for="(suggestion, index) in suggestions"
          :key="index"
          @click="sendMessage(suggestion)"
          style="cursor: pointer; margin-right: 8px; margin-bottom: 8px;"
        >
          {{ suggestion }}
        </el-tag>
      </div>

      <!-- 输入框 -->
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          placeholder="输入您的旅行需求..."
          @keyup.enter="handleSend"
          :disabled="!connected"
        >
          <template #append>
            <el-button
              :icon="Position"
              @click="handleSend"
              :disabled="!connected || !inputMessage.trim()"
              type="primary"
            >
              发送
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ChatDotRound,
  InfoFilled,
  Loading,
  SuccessFilled,
  Position,
  ArrowRight
} from '@element-plus/icons-vue'
import { createWebSocket, chatRecommend } from '@/api'
import { ElMessage } from 'element-plus'
import TypewriterText from './TypewriterText.vue'

const props = defineProps({
  useChatWorkflow: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['recommendations'])

const connected = ref(false)
const messages = ref([])
const inputMessage = ref('')
const suggestions = ref([])
const messagesRef = ref(null)
const sessionId = ref(`session_${Date.now()}`)
let ws = null

onMounted(() => {
  if (props.useChatWorkflow) {
    // 使用智能聊天工作流，不需要 WebSocket
    connected.value = true
    addMessage('system', '智能聊天推荐已启动，支持多路(rag+graphrag+hyde_search)召回+RRF+Rerank精排')
  } else {
    // 使用 WebSocket 模式
    connectWebSocket()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})

const connectWebSocket = () => {
  try {
    ws = createWebSocket()

    ws.onopen = () => {
      connected.value = true
      ElMessage.success('WebSocket 连接成功')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      ElMessage.error('WebSocket 连接错误')
    }

    ws.onclose = () => {
      connected.value = false
      ElMessage.warning('WebSocket 连接已断开')
    }
  } catch (error) {
    console.error('创建 WebSocket 失败:', error)
    ElMessage.error('无法连接到服务器')
  }
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

// 当前流式响应的临时消息
const currentStreamMessage = ref(null)
const currentAgent = ref(null)
const progressMessages = ref([])  // 追踪进度消息的索引

const handleWebSocketMessage = (data) => {
  switch (data.type) {
    case 'system':
      messages.value.push({
        type: 'system',
        message: data.message
      })
      if (data.suggestions) {
        suggestions.value = data.suggestions
      }
      if (data.agents) {
        // 显示智能体团队信息
        const agentInfo = data.agents.map(a => `${a.name}: ${a.description}`).join('\n')
        console.log('智能体团队:', agentInfo)
      }
      break

    case 'status':
    case 'progress':
      // 添加进度消息，并记录索引
      const progressIndex = messages.value.length
      messages.value.push({
        type: 'progress',
        message: data.message
      })
      progressMessages.value.push(progressIndex)
      break

    case 'agent_switch':
      // 智能体切换
      currentAgent.value = data.agent

      // 添加进度消息
      const switchIndex = messages.value.length
      messages.value.push({
        type: 'progress',
        message: data.message
      })
      progressMessages.value.push(switchIndex)

      // 准备新的流式消息（默认折叠）
      currentStreamMessage.value = {
        type: 'assistant',
        agent: data.agent,
        message: '',
        isStreaming: true,
        collapsed: true,  // 默认折叠
        typingSpeed: 30
      }
      messages.value.push(currentStreamMessage.value)
      break

    case 'agent_status':
      // 助手状态更新
      if (data.status === 'started') {
        // 助手开始 - 确保消息存在且状态为 thinking
        if (currentStreamMessage.value && currentStreamMessage.value.agent === data.agent) {
          currentStreamMessage.value.isStreaming = true
        }
      } else if (data.status === 'completed') {
        // 助手完成 - 更新状态为 completed
        // 查找该助手的消息并更新状态
        const agentMessage = messages.value.find(
          m => m.type === 'assistant' && m.agent === data.agent && m.isStreaming === true
        )
        if (agentMessage) {
          agentMessage.isStreaming = false
          agentMessage.collapsed = false  // 完成后展开
        }
      }
      break

    case 'stream':
      // 流式内容
      if (currentStreamMessage.value) {
        currentStreamMessage.value.message += data.content
      } else {
        // 如果没有当前消息，创建一个新的（主智能体直接回复）
        currentStreamMessage.value = {
          type: 'assistant',
          agent: data.agent || '智能助手',
          message: data.content,
          isStreaming: true,
          collapsed: false,  // 主智能体直接回复时不折叠
          typingSpeed: 20
        }
        messages.value.push(currentStreamMessage.value)
      }
      break

    case 'complete':
      // 流式完成 - 自动展开并开始打字机效果
      if (currentStreamMessage.value) {
        currentStreamMessage.value.isStreaming = false
        currentStreamMessage.value.collapsed = false  // 完成后自动展开
        currentStreamMessage.value.typingSpeed = 20   // 最终回复用稍快的速度
      }

      // 移除所有进度消息
      if (progressMessages.value.length > 0) {
        // 从后往前删除，避免索引变化
        progressMessages.value.sort((a, b) => b - a).forEach(index => {
          if (index < messages.value.length && messages.value[index].type === 'progress') {
            messages.value.splice(index, 1)
          }
        })
        progressMessages.value = []
      }

      currentStreamMessage.value = null
      currentAgent.value = null
      break

    case 'result':
      messages.value.push({
        type: 'result',
        message: data.message,
        recommendations: data.recommendations
      })
      if (data.recommendations) {
        emit('recommendations', data.recommendations)
      }
      break

    case 'suggestion':
      if (data.suggestions) {
        suggestions.value = data.suggestions
      }
      break

    case 'error':
      ElMessage.error(data.message)
      break
  }

  scrollToBottom()
}

const handleSend = () => {
  if (!inputMessage.value.trim()) return
  sendMessage(inputMessage.value)
  inputMessage.value = ''
}

const sendMessage = async (message) => {
  if (!connected.value) {
    ElMessage.warning('服务未连接')
    return
  }

  // 添加用户消息到界面
  addMessage('user', message)

  if (props.useChatWorkflow) {
    // 使用智能聊天工作流 API
    try {
      addMessage('progress', '正在分析您的需求...')

      const response = await chatRecommend({
        session_id: sessionId.value,
        message: message,
        history: messages.value
          .filter(m => m.type === 'user' || m.type === 'assistant')
          .map(m => ({
            role: m.type === 'user' ? 'user' : 'assistant',
            content: m.message
          }))
      })

      // 移除进度消息
      messages.value = messages.value.filter(m => m.type !== 'progress')

      // 添加 AI 回复
      addMessage('assistant', response.answer)

      // 显示推荐结果
      if (response.recommendations && response.recommendations.length > 0) {
        addMessage('result', '为您找到以下推荐', response.recommendations)
        emit('recommendations', response.recommendations)
      }

      // 显示元数据（可选）
      if (response.metadata && response.metadata.need_hyde) {
        addMessage('system', '💡 已启用 HyDE 兜底策略提升结果质量')
      }

      scrollToBottom()

    } catch (error) {
      console.error('聊天推荐失败:', error)
      messages.value = messages.value.filter(m => m.type !== 'progress')
      ElMessage.error('推荐失败，请重试')
    }
  } else {
    // 使用 WebSocket 模式
    const data = {
      message: message,
      preferences: {}
    }

    ws.send(JSON.stringify(data))
    scrollToBottom()
  }
}

const addMessage = (type, message, recommendations = null) => {
  messages.value.push({
    type,
    message,
    recommendations
  })
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-interface-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
  color: #667eea;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.message {
  margin-bottom: 16px;
}

.system-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #e1f3d8;
  border-radius: 4px;
  color: #67c23a;
  font-size: 14px;
}

.user-message,
.assistant-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-content {
  max-width: 70%;
  flex: 1;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
  user-select: none;
}

.agent-header:hover {
  background: #e0f2fe;
}

.collapse-icon {
  transition: transform 0.3s;
  color: #409eff;
}

.collapse-icon.expanded {
  transform: rotate(90deg);
}

.thinking-text {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.complete-text {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.message-text {
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  background: white;
  border-radius: 4px;
  margin-top: 8px;
  border-left: 3px solid #409eff;
}

.streaming-cursor {
  display: inline-block;
  margin-left: 4px;
  color: #409eff;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50%, 100% { opacity: 1; }
  25%, 75% { opacity: 0; }
}

.user-message {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
}

.user-message .message-content {
  background: #667eea;
  color: white;
}

.assistant-message .message-content {
  background: white;
  color: #333;
  border: 1px solid #e0e0e0;
}

.progress-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f0f2f5;
  border-radius: 4px;
  color: #909399;
  font-size: 14px;
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

.result-message {
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 2px solid #67c23a;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #67c23a;
  font-weight: 600;
  margin-bottom: 8px;
}

.result-count {
  color: #666;
  font-size: 14px;
}

.suggestions {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.input-container {
  margin-top: auto;
  flex-shrink: 0;
}

.avatar {
  flex-shrink: 0;
}
</style>
