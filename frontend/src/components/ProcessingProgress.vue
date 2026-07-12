<template>
  <div class="processing-progress">
    <div class="progress-header">
      <div class="doc-info">
        <el-icon><Document /></el-icon>
        <span class="filename">{{ currentFile }}</span>
      </div>
      <el-tag :type="getStatusType(status)">{{ status }}</el-tag>
    </div>

    <el-progress
      :percentage="progress"
      :status="progress === 100 ? 'success' : undefined"
      :stroke-width="20"
    >
      <span class="progress-text">{{ currentStep }}</span>
    </el-progress>

    <div class="steps-container">
      <div
        v-for="(step, index) in steps"
        :key="index"
        class="step-item"
        :class="{
          'active': step.status === 'processing',
          'completed': step.status === 'completed',
          'pending': step.status === 'pending'
        }"
      >
        <div class="step-icon">
          <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
          <el-icon v-else-if="step.status === 'processing'" class="rotating"><Loading /></el-icon>
          <el-icon v-else><Clock /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-title">{{ step.title }}</div>
          <div class="step-detail" v-if="step.detail">{{ step.detail }}</div>
        </div>
      </div>
    </div>

    <div class="log-container" v-if="logs.length > 0">
      <div class="log-header">
        <el-icon><ChatLineSquare /></el-icon>
        <span>处理日志</span>
      </div>
      <div class="log-content">
        <div v-for="(log, index) in logs" :key="index" class="log-item">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Document, Check, Loading, Clock, ChatLineSquare } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['complete', 'error'])

const currentFile = ref('')
const status = ref('处理中')
const progress = ref(0)
const currentStep = ref('正在初始化...')
const logs = ref([])

const steps = reactive([
  { title: '上传到 MinIO', status: 'pending', detail: '' },
  { title: 'PDF 解析 (MinerU)', status: 'pending', detail: '' },
  { title: '文本分块', status: 'pending', detail: '' },
  { title: '实体提取 (Qwen)', status: 'pending', detail: '' },
  { title: '向量化 (ChromaDB)', status: 'pending', detail: '' },
  { title: '知识图谱 (Neo4j)', status: 'pending', detail: '' }
])

let eventSource = null

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  closeSSE()
})

const connectSSE = () => {
  try {
    eventSource = new EventSource(`/api/documents/progress/${props.taskId}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleProgressUpdate(data)
      } catch (error) {
        console.error('解析 SSE 消息失败:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE 连接错误:', error)
      closeSSE()
      emit('error', '连接中断')
    }
  } catch (error) {
    console.error('启动 SSE 失败:', error)
    ElMessage.error('无法连接到处理服务')
  }
}

const closeSSE = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const handleProgressUpdate = (data) => {
  switch (data.type) {
    case 'start':
      status.value = '处理中'
      currentFile.value = data.filename || ''
      addLog(data.message)
      break

    case 'progress':
      progress.value = data.progress || 0
      currentStep.value = data.message || ''

      if (data.step !== undefined && data.step < steps.length) {
        // 更新步骤状态
        steps.forEach((step, index) => {
          if (index < data.step) {
            step.status = 'completed'
          } else if (index === data.step) {
            step.status = 'processing'
            step.detail = data.detail || ''
          } else {
            step.status = 'pending'
          }
        })
      }

      addLog(data.message)
      break

    case 'complete':
      status.value = '完成'
      progress.value = 100
      currentStep.value = '处理完成！'

      // 所有步骤标记为完成
      steps.forEach(step => {
        step.status = 'completed'
      })

      addLog(`✅ ${data.message}`)
      addLog(`📊 提取了 ${data.destinations_count || 0} 个景点`)

      setTimeout(() => {
        closeSSE()
        emit('complete', data)
      }, 2000)
      break

    case 'error':
      status.value = '失败'
      currentStep.value = data.message || '处理失败'
      addLog(`❌ ${data.message}`)

      closeSSE()
      emit('error', data.message)
      break
  }
}

const addLog = (message) => {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN')

  logs.value.push({
    time,
    message
  })

  // 限制日志数量
  if (logs.value.length > 100) {
    logs.value.shift()
  }
}

const getStatusType = (status) => {
  const typeMap = {
    '处理中': 'warning',
    '完成': 'success',
    '失败': 'danger'
  }
  return typeMap[status] || 'info'
}
</script>

<style scoped>
.processing-progress {
  padding: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.filename {
  color: #667eea;
}

.progress-text {
  font-size: 14px;
  color: #666;
}

.steps-container {
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s;
}

.step-item.active {
  background: #e1f3d8;
  border: 2px solid #67c23a;
}

.step-item.completed {
  background: #f0f9ff;
  border: 2px solid #409eff;
}

.step-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.step-item.pending .step-icon {
  color: #909399;
}

.step-item.active .step-icon {
  color: #67c23a;
}

.step-item.completed .step-icon {
  color: #409eff;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #333;
}

.step-detail {
  font-size: 12px;
  color: #666;
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

.log-container {
  margin-top: 30px;
  border-radius: 8px;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #67c23a;
}

.log-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-item {
  margin-bottom: 4px;
}

.log-time {
  color: #858585;
  margin-right: 8px;
}

.log-message {
  color: #d4d4d4;
}

/* 滚动条美化 */
.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #2d2d2d;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>
