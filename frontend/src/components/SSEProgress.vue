<template>
  <el-card class="sse-progress-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon class="rotating"><Loading /></el-icon>
        <span>实时推荐进度</span>
      </div>
    </template>

    <div class="progress-content">
      <!-- 当前状态 -->
      <div class="current-status">
        <el-tag :type="statusType" size="large" effect="dark">
          {{ currentMessage }}
        </el-tag>
      </div>

      <!-- 步骤进度 -->
      <el-steps :active="activeStep" align-center finish-status="success">
        <el-step title="RAG 检索" :description="`找到 ${stepCounts.rag} 个结果`" />
        <el-step title="GraphRAG 检索" :description="`找到 ${stepCounts.graph_rag} 个结果`" />
        <el-step title="RRF 融合" :description="`融合 ${stepCounts.rrf} 个结果`" />
        <el-step title="智能重排序" :description="`最终 ${stepCounts.rerank} 个推荐`" />
      </el-steps>

      <!-- 推荐结果预览 -->
      <div v-if="recommendations.length > 0" class="recommendations-preview">
        <el-divider>推荐结果</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="(rec, index) in recommendations"
            :key="index"
            :timestamp="`推荐 ${index + 1}`"
            placement="top"
          >
            <el-card>
              <h4>{{ rec.name }}</h4>
              <p class="reason">{{ rec.reason }}</p>
              <el-tag size="small">评分: {{ rec.score.toFixed(2) }}</el-tag>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { createSSERecommend } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  query: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['results'])

const currentMessage = ref('正在初始化...')
const activeStep = ref(0)
const stepCounts = ref({
  rag: 0,
  graph_rag: 0,
  rrf: 0,
  rerank: 0
})
const recommendations = ref([])
const isComplete = ref(false)
let reader = null
let abortController = null

const statusType = computed(() => {
  if (isComplete.value) return 'success'
  return 'info'
})

const stepMap = {
  rag: 0,
  graph_rag: 1,
  rrf: 2,
  rerank: 3
}

onMounted(() => {
  startSSE()
})

onUnmounted(() => {
  closeSSE()
})

const startSSE = async () => {
  try {
    const params = {
      query: props.query.query
    }

    // 只添加非空的参数
    if (props.query.budget != null && props.query.budget !== '') {
      params.budget = props.query.budget
    }
    if (props.query.season) {
      params.season = props.query.season
    }
    if (props.query.travelType) {
      params.travel_type = props.query.travelType
    }
    if (props.query.duration != null && props.query.duration !== '') {
      params.duration = props.query.duration
    }
    if (props.query.interests && props.query.interests.length > 0) {
      params.interests = props.query.interests
    }

    // 使用新的fetch方式
    abortController = new AbortController()
    reader = await createSSERecommend(params)

    // 读取SSE流
    await readSSEStream()
  } catch (error) {
    console.error('启动 SSE 失败:', error)
    ElMessage.error('无法启动推荐服务: ' + error.message)
  }
}

const readSSEStream = async () => {
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // 解码数据
      buffer += decoder.decode(value, { stream: true })

      // 按行分割
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留最后一个不完整的行

      // 处理每一行
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6))
            handleSSEMessage(data)
          } catch (error) {
            console.error('解析 SSE 消息失败:', line, error)
          }
        }
      }
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('SSE 读取错误:', error)
      ElMessage.error('推荐连接中断，请重试')
    }
  } finally {
    closeSSE()
  }
}

const handleSSEMessage = (data) => {
  switch (data.type) {
    case 'start':
      currentMessage.value = data.message
      break

    case 'progress':
      currentMessage.value = data.message
      if (data.step && stepMap[data.step] !== undefined) {
        activeStep.value = stepMap[data.step]
      }
      break

    case 'step_complete':
      if (data.step) {
        stepCounts.value[data.step] = data.count
        activeStep.value = stepMap[data.step] + 1
      }
      break

    case 'recommendation':
      recommendations.value.push(data)
      currentMessage.value = `正在推送第 ${data.index}/${data.total} 个推荐...`
      break

    case 'complete':
      currentMessage.value = data.message
      isComplete.value = true
      activeStep.value = 4
      ElMessage.success(data.message)
      emit('results', recommendations.value)
      closeSSE()
      break

    case 'error':
      currentMessage.value = data.message
      ElMessage.error(data.message)
      closeSSE()
      break
  }
}

const closeSSE = () => {
  if (reader) {
    reader.cancel()
    reader = null
  }
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}
</script>

<style scoped>
.sse-progress-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
  color: #667eea;
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

.progress-content {
  padding: 20px 0;
}

.current-status {
  text-align: center;
  margin-bottom: 30px;
}

.el-steps {
  margin: 30px 0;
}

.recommendations-preview {
  margin-top: 30px;
}

.recommendations-preview h4 {
  margin: 0 0 8px 0;
  color: #667eea;
  font-size: 16px;
}

.reason {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}
</style>
