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
                  <el-collapse :model-value="msg.workflowExpanded ? ['workflow'] : []">
                    <el-collapse-item name="workflow">
                      <template #title>
                        <div class="workflow-title">
                          <el-icon><Operation /></el-icon>
                          <span>查看工作流执行详情 ({{ msg.nodes.length }}个节点)</span>
                          <!-- 显示工作流状态 -->
                          <el-tag
                            v-if="msg.workflowStatus === 'running'"
                            type="primary"
                            size="small"
                            style="margin-left: 8px;"
                          >
                            执行中
                          </el-tag>
                          <el-tag
                            v-else
                            type="success"
                            size="small"
                            style="margin-left: 8px;"
                          >
                            已完成
                          </el-tag>
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

                <!-- 附近推荐 -->
                <div v-if="msg.nearby_recommendations && msg.nearby_recommendations.length > 0" class="nearby-recommendations">
                  <el-collapse>
                    <el-collapse-item name="nearby">
                      <template #title>
                        <div style="display: flex; align-items: center; gap: 8px;">
                          <el-icon><LocationInformation /></el-icon>
                          <span>附近推荐 ({{ msg.nearby_recommendations.length }}条)</span>
                        </div>
                      </template>
                      <el-collapse accordion>
                        <el-collapse-item
                          v-for="(nearby, idx) in msg.nearby_recommendations"
                          :key="idx"
                          :title="`${nearby.name} ${nearby.city ? '- ' + nearby.city : ''}`"
                        >
                          <div class="source-content">
                            <p><strong>描述：</strong>{{ nearby.description || '无描述' }}</p>
                            <p v-if="nearby.category"><strong>类型：</strong>{{ nearby.category }}</p>
                            <p v-if="nearby.province || nearby.city">
                              <strong>位置：</strong>{{ nearby.province }}{{ nearby.city }}
                            </p>
                            <el-tag type="info" size="small">附近推荐</el-tag>
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
            <el-card shadow="hover" class="flow_card_wrapper">
              <template #header>
                <div class="progress-header">
                  <el-icon class="rotating"><Loading /></el-icon>
                  <span>工作流执行中</span>
                  <el-tag type="primary" size="small">
                    {{ executedNodes.length }}/{{ needs_web_search ? 7 : 6 }}
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
  Delete,
  LocationInformation
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
const needs_web_search = ref(false)
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
  query_rewriter: '🔍 查询分析',
  parallel_retrieval: '📊 混合检索',
  rrf_fusion: '🔀 结果融合',
  confidence_check: '📈 置信度检查',
  tavily_search: '🌐 网络搜索',
  rerank: '⭐ 智能重排',
  synthesizer: '✨ 答案生成'
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

    // 后端返回的是 history 字段，不是 messages
    if (response && response.history && Array.isArray(response.history)) {
      // 将历史记录转换为对话格式（用户查询 + AI回复）
      const historyMessages = []
      response.history.forEach(item => {
        // 添加用户查询
        if (item.query) {
          historyMessages.push({
            type: 'user',
            message: item.query,
            timestamp: item.timestamp
          })
        }

        // 添加AI回复
        if (item.answer) {
          historyMessages.push({
            type: 'assistant',
            message: item.answer,
            sources: item.sources || [],
            nearby_recommendations: item.nearby_recommendations || [],  // 新增：附近推荐
            nodes: [],
            workflowExpanded: false,
            workflowStatus: 'completed',
            timestamp: item.timestamp
          })
        }
      })

      messages.value = historyMessages
    } else {
      messages.value = []
    }

    console.log(`✅ 加载了 ${response.count} 条历史记录，转换为 ${messages.value.length} 条消息`)

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
const handleSend = async () => {
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

  // 关闭之前的SSE连接（如果存在）
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  // 用于存储后端返回的task_id
  let serverTaskId = null

  // 先发送查询请求，获取task_id
  try {
    const response = await fetch('/api/ai-recommend/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: userMessage,
        session_id: sessionId.value
      })
    })

    if (response.ok) {
      const result = await response.json()
      serverTaskId = result.task_id
      console.log(`[TASK_ID] 后端返回task_id: ${serverTaskId}`)
    } else {
      throw new Error('发送查询请求失败')
    }
  } catch (error) {
    console.error('发送查询失败:', error)
    messages.value.push({
      type: 'system',
      message: '发送请求失败'
    })
    isLoading.value = false
    return
  }

  // 等待一小段时间，确保后端清空旧事件
  await new Promise(resolve => setTimeout(resolve, 100))

  // 建立新的SSE连接
  const eventsUrl = `/api/ai-recommend/events/${sessionId.value}`
  eventSource = new EventSource(eventsUrl)

  console.log('连接SSE事件流:', eventsUrl)
  console.log('期望task_id:', serverTaskId)

  // 监听node_start事件
  eventSource.addEventListener('node_start', (event) => {
    const receiveTime = Date.now() / 1000
    const data = JSON.parse(event.data)
    const sendTime = data.timestamp || 0
    const delay = ((receiveTime - sendTime) * 1000).toFixed(0)

    // 使用task_id过滤
    if (serverTaskId && data.task_id && data.task_id !== serverTaskId) {
      console.log(`⏭️ [SKIP] task_id不匹配 node_start | 期望: ${serverTaskId}, 实际: ${data.task_id}`)
      return
    }

    console.log(`⏱️ [RECEIVE] node_start at ${receiveTime.toFixed(3)} | ${data.step_name} | Delay: ${delay}ms`)

    executedNodes.value.push({
      name: data.step_name || data.step,
      status: 'primary',
      icon: 'Loading',
      color: '#409eff',
      message: data.message || ''
    })

    scrollToBottom()
  })

  // 监听node_end事件
  eventSource.addEventListener('node_end', (event) => {
    const receiveTime = Date.now() / 1000
    const data = JSON.parse(event.data)
    const sendTime = data.timestamp || 0
    const delay = ((receiveTime - sendTime) * 1000).toFixed(0)

    // 使用task_id过滤
    if (serverTaskId && data.task_id && data.task_id !== serverTaskId) {
      console.log(`⏭️ [SKIP] task_id不匹配 node_end | 期望: ${serverTaskId}, 实际: ${data.task_id}`)
      return
    }

    console.log(`⏱️ [RECEIVE] node_end at ${receiveTime.toFixed(3)} | ${data.step_name} | Delay: ${delay}ms`)

    const lastNode = executedNodes.value[executedNodes.value.length - 1]
    if (lastNode) {
      lastNode.status = 'success'
      lastNode.icon = 'Check'
      lastNode.color = '#67c23a'
      lastNode.message = data.message || ''
    }

    scrollToBottom()
  })

  // 监听result事件
  eventSource.addEventListener('result', (event) => {
    const receiveTime = Date.now() / 1000
    const data = JSON.parse(event.data)
    const sendTime = data.timestamp || 0
    const delay = ((receiveTime - sendTime) * 1000).toFixed(0)

    // 使用task_id过滤
    if (serverTaskId && data.task_id && data.task_id !== serverTaskId) {
      console.log(`⏭️ [SKIP] task_id不匹配 result | 期望: ${serverTaskId}, 实际: ${data.task_id}`)
      return
    }

    console.log(`⏱️ [RECEIVE] result at ${receiveTime.toFixed(3)} | Answer: ${data.answer?.length || 0} chars | Delay: ${delay}ms`)

    // 添加AI回复
    messages.value.push({
      type: 'assistant',
      message: data.answer || '生成答案失败',
      sources: data.sources || [],
      nearby_recommendations: data.nearby_recommendations || [],
      nodes: [...executedNodes.value],
      workflowExpanded: false,
      workflowStatus: 'completed'
    })
    scrollToBottom()
  })

  // 监听complete事件
  eventSource.addEventListener('complete', (event) => {
    const receiveTime = Date.now() / 1000
    const data = JSON.parse(event.data)
    const sendTime = data.timestamp || 0
    const delay = ((receiveTime - sendTime) * 1000).toFixed(0)

    console.log(`⏱️ [RECEIVE] complete at ${receiveTime.toFixed(3)} | Delay: ${delay}ms`)
    console.log(`📊 [SUMMARY] Workflow completed`)

    // 结束加载状态并关闭连接
    isLoading.value = false

    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    ElMessage.success('推荐完成')
  })

  // 监听error事件
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

    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    scrollToBottom()
  })

  // 监听连接打开
  eventSource.onopen = () => {
    console.log('SSE连接已建立')
  }

  // 监听连接错误
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)

    if (isLoading.value) {
      messages.value.push({
        type: 'system',
        message: '连接服务器失败，请检查后端服务'
      })
      ElMessage.error('连接失败')

      isLoading.value = false
    }

    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    scrollToBottom()
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

/* 工作流进度样式 */
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
  font-size: 18px;
  animation: rotating 2s linear infinite;
}

:deep(.workflow-progress .flow_card_wrapper){
  width:100%!important
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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
  max-width: 95%;
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
