<template>
  <div class="chat-page">
    <el-card class="page-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>AI团队推荐</span>
          <el-tag type="success" size="small">多智能体协作</el-tag>

          <!-- 清除历史按钮 -->
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
              <el-avatar :size="32" style="background: #67c23a;">我</el-avatar>
            </div>

            <!-- AI消息 -->
            <div v-else-if="msg.type === 'assistant'" class="assistant-message">
              <el-avatar :size="32" style="background: #67c23a;">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="message-content">
                <!-- 智能体执行记录 - 时间轴样式 -->
                <div v-if="msg.agent_logs && msg.agent_logs.length > 0" class="agent-timeline">
                  <div class="timeline-header">
                    <el-icon><Operation /></el-icon>
                    <span>智能体协作流程</span>
                    <el-tag size="small" type="success">{{ msg.agent_logs.length }}个智能体</el-tag>
                  </div>

                  <el-timeline class="custom-timeline">
                    <el-timeline-item
                      v-for="(log, idx) in msg.agent_logs"
                      :key="idx"
                      :type="log.status === 'completed' ? 'success' : 'primary'"
                      :icon="log.status === 'completed' ? 'Check' : 'Clock'"
                      :size="'large'"
                    >
                      <div class="timeline-card">
                        <div class="timeline-card-header">
                          <div class="agent-info">
                            <span class="agent-icon">{{ getAgentIcon(log.agent) }}</span>
                            <strong class="agent-name">{{ translateAgentName(log.agent) }}</strong>
                          </div>
                          <el-tag
                            :type="log.status === 'completed' ? 'success' : 'info'"
                            size="small"
                            effect="dark"
                          >
                            {{ log.status === 'completed' ? '✓ 完成' : '⏳ 进行中' }}
                          </el-tag>
                        </div>
                        <div v-if="log.summary" class="timeline-card-body">
                          {{ log.summary }}
                        </div>
                        <div v-if="log.result_count !== undefined" class="timeline-card-footer">
                          <el-icon><Document /></el-icon>
                          <span>检索结果: {{ log.result_count }}条</span>
                        </div>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                </div>

                <!-- 答案内容 -->
                <div class="answer-section">
                  <div class="answer-header">
                    <el-icon><Star /></el-icon>
                    <span>推荐方案</span>
                  </div>
                  <div class="answer-content" v-html="formatAnswer(msg.message)"></div>
                </div>

                <!-- 来源 -->
                <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
                  <el-collapse>
                    <el-collapse-item>
                      <template #title>
                        <div class="collapse-title">
                          <el-icon><Document /></el-icon>
                          <span>参考来源 ({{ msg.sources.length }}条)</span>
                        </div>
                      </template>
                      <div class="sources-grid">
                        <div
                          v-for="(source, idx) in msg.sources"
                          :key="idx"
                          class="source-card"
                        >
                          <div class="source-header">
                            <span class="source-number">{{ idx + 1 }}</span>
                            <strong>{{ source.name || source.title || '未命名景点' }}</strong>
                          </div>
                          <div class="source-body">
                            <p class="source-location" v-if="source.location">
                              <el-icon><Location /></el-icon>
                              {{ source.location }}
                            </p>
                            <p class="source-description">
                              {{ source.description || source.content || '无描述' }}
                            </p>
                            <div v-if="source.tags && source.tags.length > 0" class="source-tags">
                              <el-tag
                                v-for="tag in source.tags"
                                :key="tag"
                                size="small"
                                type="info"
                              >
                                {{ tag }}
                              </el-tag>
                            </div>
                          </div>
                          <div class="source-footer">
                            <span class="source-score">相关度: {{ (source.score * 100).toFixed(1) }}%</span>
                          </div>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 元数据 -->
                <div v-if="msg.metadata" class="metadata">
                  <el-tag size="small" type="info">
                    <el-icon><Setting /></el-icon>
                    {{ msg.metadata.workflow === 'knowledge_base_only' ? '知识库模式' : '完整规划模式' }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 系统消息 -->
            <div v-else-if="msg.type === 'system'" class="system-message">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ msg.message }}</span>
            </div>
          </div>

          <!-- 实时进度显示 -->
          <div v-if="isLoading" class="progress-panel">
            <div class="progress-header">
              <el-icon class="rotating"><Loading /></el-icon>
              <span>AI团队协作中...</span>
            </div>
            <div class="progress-content">
              <el-steps :active="activeAgentStep" align-center finish-status="success">
                <el-step
                  v-for="(step, idx) in agentSteps"
                  :key="idx"
                  :title="step.agent"
                  :description="step.message"
                  :icon="step.status === 'completed' ? 'Check' : step.status === 'running' ? 'Loading' : 'Clock'"
                />
              </el-steps>
              <div class="current-progress">
                {{ currentProgress }}
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷问题 -->
        <div v-if="!isLoading && messages.length === 0" class="suggestions">
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
            type="success"
            @click="handleSend"
            :loading="isLoading"
            :disabled="!inputMessage.trim()"
            size="large"
          >
            <el-icon><Position /></el-icon>
            {{ isLoading ? '团队协作中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Position,
  Document,
  InfoFilled,
  Loading,
  Operation,
  Check,
  Clock,
  Star,
  Location,
  Setting,
  Delete
} from '@element-plus/icons-vue'
import { getChatHistory, clearChatHistory } from '@/api/index'

// Session ID
const sessionId = ref('')

// WebSocket连接
let ws = null

// 响应式数据
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const historyLoading = ref(false)
const currentProgress = ref('')
const messagesRef = ref(null)
const agentSteps = ref([])
const activeAgentStep = ref(0)

// 快捷问题
const suggestions = [
  '推荐三清山3天旅游攻略',
  '去婺源看油菜花的最佳时间',
  '南昌周边适合周末游的景点',
  '江西有哪些特色美食'
]

// 获取智能体图标
const getAgentIcon = (agentName) => {
  const iconMap = {
    '主智能体': '🎯',
    'RAG知识库助手': '📚',
    '图RAG知识库助手': '🗺️',
    '行程规划师': '📅',
    '交通助手': '🚗',
    '美食助手': '🍜',
    '预算专家': '💰',
    '查询重写助手': '🔍',
    // 英文名称映射
    'Team Manager': '🎯',
    'RAG Knowledge Assistant': '📚',
    'RAG Assistant': '📚',
    'Graph RAG Assistant': '🗺️',
    'Itinerary Planner': '📅',
    'Transport Assistant': '🚗',
    'Food Assistant': '🍜',
    'Budget Expert': '💰',
    'Query Rewriter': '🔍'
  }
  return iconMap[agentName] || '🤖'
}

// 将英文Agent名称翻译为中文
const translateAgentName = (agentName) => {
  const nameMap = {
    'Team Manager': '主智能体',
    'RAG Knowledge Assistant': 'RAG知识库助手',
    'RAG Assistant': 'RAG知识库助手',
    'Graph RAG Assistant': '图RAG知识库助手',
    'Itinerary Planner': '行程规划师',
    'Transport Assistant': '交通助手',
    'Food Assistant': '美食助手',
    'Budget Expert': '预算专家',
    'Query Rewriter': '查询重写助手',
    '查询重写助手': '查询重写助手'
  }
  return nameMap[agentName] || agentName
}

// 初始化
onMounted(() => {
  // 生成或获取session ID
  sessionId.value = localStorage.getItem('ai_team_session_id') || generateSessionId()
  localStorage.setItem('ai_team_session_id', sessionId.value)

  console.log('Team Session ID:', sessionId.value)

  // 加载历史消息
  loadChatHistory()
})

// 清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

// 生成Session ID
function generateSessionId() {
  return 'team_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// 加载聊天历史
async function loadChatHistory() {
  historyLoading.value = true
  try {
    const response = await getChatHistory(sessionId.value, 50)

    console.log('历史记录响应:', response)

    // 验证响应数据
    if (!response || !response.messages || !Array.isArray(response.messages)) {
      console.warn('历史记录格式错误或为空:', response)
      messages.value = []
      return
    }

    messages.value = response.messages.map(msg => {
      // 确保每条消息都有正确的结构
      return {
        type: msg.type || 'user',
        message: msg.content || msg.message || '',
        timestamp: msg.timestamp,
        sources: (msg.metadata?.sources || []),
        agent_logs: (msg.metadata?.agent_logs || [])
      }
    })

    console.log(`✅ 加载了 ${response.count || messages.value.length} 条历史消息`)

    nextTick(() => {
      scrollToBottom()
    })

  } catch (error) {
    console.error('加载聊天历史失败:', error)
    messages.value = []
    // Redis未启动时不报错
  } finally {
    historyLoading.value = false
  }
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

  // 滚动到底部
  scrollToBottom()

  // 开始AI团队推荐（传递session_id）
  startTeamRecommend(userMessage)
}

// 快捷问题点击
const handleSuggestionClick = (suggestion) => {
  inputMessage.value = suggestion
  handleSend()
}

// 开始AI团队推荐（使用WebSocket实时推送）
const startTeamRecommend = (query) => {
  isLoading.value = true
  currentProgress.value = '🤖 AI团队启动中...'
  agentSteps.value = []
  activeAgentStep.value = 0

  // 构建历史对话（最近3轮）
  const chatHistory = messages.value
    .slice(-6)
    .filter(msg => msg.type !== 'system')
    .map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.message
    }))

  // 使用WebSocket连接
  ws = new WebSocket('ws://localhost:8000/api/team-recommend-ws/stream')

  ws.onopen = () => {
    console.log('✅ WebSocket已连接')
    ws.send(JSON.stringify({
      query: query,
      session_id: sessionId.value,  // 使用正确的session_id
      chat_history: chatHistory
    }))
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('✅ 收到WebSocket消息:', data.type, data)
      handleStreamMessage(data)
    } catch (e) {
      console.error('❌ 解析消息失败:', e)
    }
  }

  ws.onerror = (error) => {
    console.error('❌ WebSocket错误:', error)
    messages.value.push({
      type: 'system',
      message: '连接服务器失败，请检查后端服务是否启动'
    })
    isLoading.value = false
    currentProgress.value = ''
    agentSteps.value = []
    ws.close()
  }

  ws.onclose = () => {
    console.log('WebSocket已关闭')
  }
}

// 处理流式消息
const handleStreamMessage = (data) => {
  console.log('处理消息:', data.type, data)

  switch (data.type) {
    case 'start':
      currentProgress.value = data.message
      break

    case 'node_start':
      // 节点开始 - 添加新步骤
      const stepName = data.step_name || data.step || 'Unknown Step'
      const existingStartStep = agentSteps.value.find(s => s.agent === stepName)

      if (!existingStartStep) {
        agentSteps.value.push({
          agent: stepName,
          status: 'running',
          message: data.message || '处理中...'
        })
      }

      currentProgress.value = data.message || `[${stepName}] 处理中...`
      scrollToBottom()
      break

    case 'node_end':
      // 节点完成 - 更新步骤状态
      const completedStepName = data.step_name || data.step || 'Unknown Step'
      const existingEndStep = agentSteps.value.find(s => s.agent === completedStepName)

      if (existingEndStep) {
        existingEndStep.status = 'completed'
        existingEndStep.message = data.message || '完成'
      } else {
        // 如果没找到，添加一个已完成的步骤
        agentSteps.value.push({
          agent: completedStepName,
          status: 'completed',
          message: data.message || '完成'
        })
      }

      activeAgentStep.value = agentSteps.value.filter(s => s.status === 'completed').length
      currentProgress.value = data.message || `[${completedStepName}] 完成`
      scrollToBottom()
      break

    case 'progress':
      // 进度更新消息 - 更新步骤
      const agentName = data.agent || 'Unknown Agent'
      const translatedName = translateAgentName(agentName)
      const existingStep = agentSteps.value.find(s => s.agent === agentName)

      if (existingStep) {
        existingStep.status = data.status || 'running'
        existingStep.message = data.detail || data.message || ''
      } else {
        agentSteps.value.push({
          agent: agentName,
          status: data.status || 'running',
          message: data.detail || data.message || ''
        })
      }

      if (data.status === 'completed') {
        activeAgentStep.value = agentSteps.value.filter(s => s.status === 'completed').length
      }

      currentProgress.value = data.message || `[${translatedName}] 处理中...`
      scrollToBottom()
      break

    case 'answer':
      // 添加AI回复消息
      const answer = data.answer || '抱歉，没有找到相关的旅游信息。'

      console.log('收到答案，agent_logs:', data.agent_logs)

      messages.value.push({
        type: 'assistant',
        message: answer,
        sources: data.sources || [],
        metadata: data.metadata || {},
        agent_logs: data.agent_logs || []
      })

      nextTick(() => {
        scrollToBottom()
      })
      break

    case 'complete':
      console.log('团队推荐完成')
      isLoading.value = false
      currentProgress.value = ''
      agentSteps.value = []
      ElMessage.success(data.message || '团队推荐完成')
      break

    case 'error':
      console.error('收到错误消息:', data.message)
      isLoading.value = false
      currentProgress.value = ''
      agentSteps.value = []
      messages.value.push({
        type: 'system',
        message: `错误: ${data.message}`
      })
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
  color: #67c23a;
}

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
  gap: 20px;
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
  max-width: 70%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
  border-radius: 12px;
  line-height: 1.6;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.assistant-message {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  gap: 12px;
  max-width: 100%;
}

.assistant-message .message-content {
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
}

/* 智能体时间轴 */
.agent-timeline {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.timeline-header .el-icon {
  font-size: 20px;
  color: #67c23a;
}

.custom-timeline {
  margin-top: 20px;
}

.timeline-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  border-left: 3px solid #67c23a;
}

.timeline-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-icon {
  font-size: 20px;
}

.agent-name {
  font-size: 15px;
  color: #303133;
}

.timeline-card-body {
  color: #606266;
  font-size: 14px;
  margin: 8px 0;
  line-height: 1.6;
}

.timeline-card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

/* 答案区域 */
.answer-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px 12px 20px 40px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.answer-header .el-icon {
  color: #f59e0b;
  font-size: 20px;
}

.answer-content {
  line-height: 1.8;
  color: #303133;
}

.answer-content h3 {
  margin: 16px 0 8px;
  color: #67c23a;
  font-size: 16px;
}

.answer-content li {
  margin-left: 20px;
  margin-bottom: 8px;
}

/* 来源区域 */
.sources-section {
  margin-top: 16px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  padding: 0 16px;
}
:deep(.el-collapse-item__content){
  padding: 0 16px 16px;
}

.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.source-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e0e0e0;
  transition: all 0.3s;
}

.source-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.source-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #67c23a;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.source-body {
  margin-bottom: 12px;
}

.source-location {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.source-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.source-footer {
  display: flex;
  justify-content: flex-end;
}

.source-score {
  color: #67c23a;
  font-size: 12px;
  font-weight: 600;
}

/* 实时进度面板 */
.progress-panel {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
  color: #67c23a;
}

.progress-content {
  padding: 16px 0;
}

.current-progress {
  margin-top: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.system-message {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
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

.metadata {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.input-container {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: white;
}

.suggestions {
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  border-bottom: 1px solid #e0e0e0;
  background: #fff;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s;
  padding: 8px 16px;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
