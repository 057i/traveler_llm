<template>
  <div class="workflow-progress">
    <!-- 进度概览 -->
    <div class="progress-header">
      <div class="progress-info">
        <el-icon class="file-icon"><Document /></el-icon>
        <div class="file-info">
          <div class="filename">{{ filename }}</div>
          <div class="status-text">{{ statusText }}</div>
        </div>
      </div>
      <div class="progress-bar-container">
        <el-progress
          :percentage="progress"
          :status="progressStatus"
          :stroke-width="12"
        />
      </div>
    </div>

    <!-- 工作流图 - 新的7步流程 -->
    <div class="workflow-graph">
      <svg class="workflow-svg" viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg">
        <!-- 定义渐变和滤镜 -->
        <defs>
          <linearGradient id="processing-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#409EFF;stop-opacity:0.3" />
            <stop offset="50%" style="stop-color:#409EFF;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#409EFF;stop-opacity:0.3" />
          </linearGradient>

          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <!-- 连接线 -->
        <!-- PDF解析 -> 上传MinIO -->
        <line x1="180" y1="60" x2="320" y2="60" :class="['link', getLinkClass('minio_upload')]" />

        <!-- 上传MinIO → 文本分块 -->
        <path d="M 350 90 Q 350 125, 250 130" :class="['link', 'curved', getLinkClass('chunk')]" fill="none" />

        <!-- 文本分块 → 实体提取 -->
        <line x1="280" y1="160" x2="460" y2="160" :class="['link', getLinkClass('extract')]" />

        <!-- 实体提取 → 传统向量化 -->
        <path d="M 490 190 Q 370 235, 250 250" :class="['link', 'curved', getLinkClass('vectorize_traditional')]" fill="none" />

        <!-- 实体提取 → 图向量化 -->
        <path d="M 490 190 Q 490 235, 490 250" :class="['link', 'curved', getLinkClass('vectorize_graph')]" fill="none" />

        <!-- 两种向量化到完成 -->
        <path d="M 250 310 Q 310 350, 340 390" :class="['link', 'curved', getLinkClass('finalize')]" fill="none" />
        <path d="M 490 310 Q 430 350, 400 390" :class="['link', 'curved', getLinkClass('finalize')]" fill="none" />

        <!-- 节点 -->
        <!-- 第一行：PDF解析 -> 上传MinIO -->
        <g class="node" :class="getNodeClass('parse')">
          <circle cx="150" cy="60" r="30" class="node-bg" />
          <circle cx="150" cy="60" r="28" class="node-circle" />
          <g v-if="steps.parse === 'completed'" class="status-icon">
            <text x="150" y="67" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.parse === 'processing'" class="status-icon">
            <circle cx="150" cy="60" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="150" y="95" class="node-label">PDF解析</text>
        </g>

        <g class="node" :class="getNodeClass('minio_upload')">
          <circle cx="350" cy="60" r="30" class="node-bg" />
          <circle cx="350" cy="60" r="28" class="node-circle" />
          <g v-if="steps.minio_upload === 'completed'" class="status-icon">
            <text x="350" y="67" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.minio_upload === 'processing'" class="status-icon">
            <circle cx="350" cy="60" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="350" y="95" class="node-label">上传MinIO</text>
        </g>

        <!-- 第二行：文本分块 -> 实体提取 -->
        <g class="node" :class="getNodeClass('chunk')">
          <circle cx="250" cy="160" r="30" class="node-bg" />
          <circle cx="250" cy="160" r="28" class="node-circle" />
          <g v-if="steps.chunk === 'completed'" class="status-icon">
            <text x="250" y="167" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.chunk === 'processing'" class="status-icon">
            <circle cx="250" cy="160" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="250" y="195" class="node-label">文本分块</text>
        </g>

        <g class="node" :class="getNodeClass('extract')">
          <circle cx="490" cy="160" r="30" class="node-bg" />
          <circle cx="490" cy="160" r="28" class="node-circle" />
          <g v-if="steps.extract === 'completed'" class="status-icon">
            <text x="490" y="167" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.extract === 'processing'" class="status-icon">
            <circle cx="490" cy="160" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="490" y="195" class="node-label">实体提取</text>
        </g>

        <!-- 第三行 -->
        <g class="node" :class="getNodeClass('vectorize_traditional')">
          <circle cx="250" cy="280" r="30" class="node-bg" />
          <circle cx="250" cy="280" r="28" class="node-circle" />
          <g v-if="steps.vectorize_traditional === 'completed'" class="status-icon">
            <text x="250" y="287" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.vectorize_traditional === 'processing'" class="status-icon">
            <circle cx="250" cy="280" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="250" y="310" class="node-label">传统向量化</text>
          <text x="250" y="325" class="node-sublabel">Milvus</text>
        </g>

        <g class="node" :class="getNodeClass('vectorize_graph')">
          <circle cx="490" cy="280" r="30" class="node-bg" />
          <circle cx="490" cy="280" r="28" class="node-circle" />
          <g v-if="steps.vectorize_graph === 'completed'" class="status-icon">
            <text x="490" y="287" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.vectorize_graph === 'processing'" class="status-icon">
            <circle cx="490" cy="280" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="490" y="310" class="node-label">图向量化</text>
          <text x="490" y="325" class="node-sublabel">Neo4j</text>
        </g>

        <!-- 第四行：完成节点 -->
        <g class="node" :class="getNodeClass('finalize')">
          <circle cx="370" cy="390" r="35" class="node-bg" />
          <circle cx="370" cy="390" r="33" class="node-circle" />
          <g v-if="steps.finalize === 'completed'" class="status-icon">
            <text x="370" y="397" class="check-icon">✓</text>
          </g>
          <g v-else-if="steps.finalize === 'processing'" class="status-icon">
            <circle cx="370" cy="390" r="8" fill="white" opacity="0.9" />
          </g>
          <text x="370" y="430" class="node-label finish-label">完成</text>
        </g>
      </svg>
    </div>

    <!-- 处理日志 -->
    <div v-if="logs.length > 0" class="logs-section">
      <div class="logs-header" @click="logsExpanded = !logsExpanded">
        <el-icon><Document /></el-icon>
        <span>处理日志</span>
        <el-icon class="expand-icon" :class="{ expanded: logsExpanded }">
          <ArrowDown />
        </el-icon>
      </div>
      <transition name="fade">
        <div v-show="logsExpanded" class="logs-content">
          <div v-for="(log, index) in logs" :key="index" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </transition>
    </div>

    <!-- 错误信息 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      :closable="false"
      style="margin-top: 16px;"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  Document,
  ArrowDown
} from '@element-plus/icons-vue'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  filename: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['complete'])

const progress = ref(0)
const statusText = ref('等待处理...')
const errorMessage = ref('')
const completed = ref(false)
const logsExpanded = ref(false)

const steps = ref({
  parse: 'pending',           // 1. PDF解析
  minio_upload: 'pending',    // 2. 上传MinIO（新增）
  chunk: 'pending',           // 3. 文本分块
  extract: 'pending',         // 4. 实体提取
  vectorize_traditional: 'pending',  // 5. 传统向量化
  vectorize_graph: 'pending',        // 6. 图向量化
  finalize: 'pending'         // 7. 完成
})

const logs = ref([])
let eventSource = null

const progressStatus = computed(() => {
  if (errorMessage.value) return 'exception'
  if (completed.value) return 'success'
  return undefined
})

// 获取节点样式类
const getNodeClass = (stepId) => {
  const status = steps.value[stepId] || 'pending'
  return status
}

// 获取连接线样式类
const getLinkClass = (stepId) => {
  const status = steps.value[stepId] || 'pending'
  return status
}

const addLog = (message) => {
  const now = new Date()
  logs.value.push({
    time: now.toLocaleTimeString('zh-CN'),
    message
  })
}

const updateStepStatus = (stepId, status) => {
  console.log(`[WorkflowProgress] 更新步骤 ${stepId} 状态为 ${status}`)
  if (steps.value.hasOwnProperty(stepId)) {
    // 使用 Vue 3 的响应式 API 强制更新
    steps.value = {
      ...steps.value,
      [stepId]: status
    }
  }
}

const connectSSE = () => {
  if (!props.taskId) return

  const url = `/api/documents/progress/${props.taskId}`
  eventSource = new EventSource(url)

  eventSource.onopen = () => {
    console.log('[WorkflowProgress] SSE 连接已建立')
    addLog('开始处理文档...')
  }

  // 监听默认 message 事件（详细日志）
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log('[WorkflowProgress] 收到 message 事件:', data)

    // 如果有 message 字段，添加到日志
    if (data.message) {
      addLog(data.message)
    }
  }

  eventSource.addEventListener('start', (event) => {
    const data = JSON.parse(event.data)
    statusText.value = data.message || '开始处理...'
    addLog(data.message)
  })

  eventSource.addEventListener('progress', (event) => {
    const data = JSON.parse(event.data)
    console.log('[WorkflowProgress] 收到 progress 事件:', data)

    if (data.progress !== undefined) {
      progress.value = data.progress
    }

    if (data.step) {
      console.log(`[WorkflowProgress] 更新步骤 ${data.step} 为 processing`)
      updateStepStatus(data.step, 'processing')
      statusText.value = data.message || '处理中...'
    }
  })

  eventSource.addEventListener('node_start', (event) => {
    const data = JSON.parse(event.data)
    console.log('[Workflow] NODE_START:', data)

    if (data.step) {
      console.log(`[Workflow] 节点开始: ${data.step} - ${data.step_name}`)
      updateStepStatus(data.step, 'processing')
    }

    if (data.progress !== undefined) {
      progress.value = data.progress
    }

    if (data.message) {
      statusText.value = data.message
      addLog(`${data.step_name || data.step}: ${data.message}`)
    }
  })

  eventSource.addEventListener('node_end', (event) => {
    const data = JSON.parse(event.data)
    console.log('[Workflow] NODE_END:', data)

    if (data.step) {
      console.log(`[Workflow] 节点完成: ${data.step} - ${data.step_name}`)
      updateStepStatus(data.step, 'completed')
    }

    if (data.progress !== undefined) {
      progress.value = data.progress
    }

    if (data.message) {
      statusText.value = data.message
      addLog(`${data.step_name || data.step}: ${data.message}`)
    }
  })

  eventSource.addEventListener('complete', (event) => {
    const data = JSON.parse(event.data)

    completed.value = true
    progress.value = 100
    statusText.value = '处理完成！'

    addLog('文档处理完成！')

    // 标记所有步骤为完成
    Object.keys(steps.value).forEach(key => {
      if (steps.value[key] !== 'failed') {
        steps.value[key] = 'completed'
      }
    })

    // 通知父组件刷新
    emit('complete')

    eventSource.close()
  })

  eventSource.addEventListener('error', (event) => {
    try {
      const data = JSON.parse(event.data)
      errorMessage.value = data.message || '处理失败'
      statusText.value = '处理失败'
      addLog(`错误: ${errorMessage.value}`)

      // 标记当前处理的步骤为失败
      Object.keys(steps.value).forEach(key => {
        if (steps.value[key] === 'processing') {
          steps.value[key] = 'failed'
        }
      })

      eventSource.close()
    } catch (e) {
      console.error('[WorkflowProgress] 错误事件解析失败:', e)
    }
  })

  eventSource.onerror = (error) => {
    console.error('[WorkflowProgress] SSE 连接错误:', error)

    if (eventSource.readyState === EventSource.CLOSED) {
      console.log('[WorkflowProgress] SSE 连接已关闭')
    } else {
      errorMessage.value = '连接服务器失败'
      statusText.value = '连接失败'
      addLog('连接服务器失败，请刷新重试')
      eventSource.close()
    }
  }
}

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<style scoped>
.workflow-progress {
  padding: 24px;
  background: #ffffff;
  border-radius: 8px;
}

.progress-header {
  margin-bottom: 24px;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.file-icon {
  font-size: 32px;
  color: #409eff;
}

.file-info {
  flex: 1;
}

.filename {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.status-text {
  font-size: 14px;
  color: #909399;
}

.progress-bar-container {
  width: 100%;
}

.workflow-graph {
  width: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.workflow-svg {
  width: 100%;
  height: auto;
}

/* 连接线样式 */
.link {
  stroke-width: 3;
  transition: all 0.4s ease;
}

.link.pending {
  stroke: #DCDFE6;
  stroke-dasharray: 5, 5;
  animation: dash 20s linear infinite;
}

.link.processing {
  stroke: #E6A23C;
  stroke-width: 4;
  filter: drop-shadow(0 0 8px rgba(230, 162, 60, 0.6));
  animation: pulse 1.5s ease-in-out infinite;
}

.link.completed {
  stroke: #67C23A;
  stroke-width: 3;
  filter: drop-shadow(0 0 6px rgba(103, 194, 58, 0.4));
}

.link.failed {
  stroke: #F56C6C;
  stroke-width: 3;
}

.link.curved {
  stroke-linecap: round;
}

@keyframes dash {
  to {
    stroke-dashoffset: -100;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 节点样式 */
.node {
  cursor: pointer;
  transition: all 0.3s ease;
}

.node:hover .node-bg {
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
}

.node:hover .node-circle {
  transform: scale(1.08);
  transform-origin: center;
  transform-box: fill-box;
}

.node-bg {
  fill: white;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.08));
  transition: all 0.3s ease;
}

.node-circle {
  transition: all 0.4s ease;
  transform-origin: center;
  transform-box: fill-box;
}

.node.pending .node-circle {
  fill: #E4E7ED;
  stroke: #DCDFE6;
  stroke-width: 2;
}

.node.processing .node-circle {
  fill: #409EFF;
  stroke: #3A8EE6;
  stroke-width: 3;
  animation: glow 1.5s ease-in-out infinite;
}

.node.completed .node-circle {
  fill: #67C23A;
  stroke: #5DAF34;
  stroke-width: 2;
}

.node.failed .node-circle {
  fill: #F56C6C;
  stroke: #E55656;
  stroke-width: 2;
}

/* 状态图标 */
.status-icon {
  pointer-events: none;
}

.check-icon {
  font-size: 24px;
  font-weight: bold;
  fill: white;
  text-anchor: middle;
  dominant-baseline: middle;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes glow {
  0%, 100% {
    filter: drop-shadow(0 0 8px rgba(64, 158, 255, 0.6));
  }
  50% {
    filter: drop-shadow(0 0 16px rgba(64, 158, 255, 0.9));
  }
}

@keyframes checkmark {
  0% {
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.node-label {
  fill: #606266;
  font-size: 13px;
  font-weight: 500;
  text-anchor: middle;
  pointer-events: none;
}

.node-label.finish-label {
  font-size: 16px;
  font-weight: 600;
}

.node-sublabel {
  fill: #909399;
  font-size: 11px;
  text-anchor: middle;
  pointer-events: none;
}

.node:hover .node-circle {
  transform: scale(1.05);
}

.logs-section {
  margin-top: 24px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.logs-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
  color: #303133;
}

.logs-header:hover {
  background: #e4e7ed;
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.logs-content {
  max-height: 300px;
  overflow-y: auto;
  background: #fafafa;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 8px 16px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  border-bottom: 1px solid #e4e7ed;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  white-space: nowrap;
}

.log-message {
  color: #606266;
  flex: 1;
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s;
}

.fade-enter-from, .fade-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
