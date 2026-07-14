<template>
  <div class="recommand">
    <!-- 搜索输入 -->
    <SearchInput @search="handleSearch" :loading="loading" />

    <!-- 搜索进度 -->
    <transition name="fade">
      <div v-if="loading" class="search-progress">
        <el-progress
          :percentage="progress"
          :color="progressColor"
          :stroke-width="8"
        />
        <p class="progress-message">{{ progressMessage }}</p>
        <p class="progress-detail">已找到 {{ recommendations.length }} 个结果</p>
      </div>
    </transition>

    <!-- 推荐结果 -->
    <transition-group name="slide-fade" tag="div">
      <RecommendationList
        v-if="recommendations.length > 0"
        :key="'results'"
        :recommendations="recommendations"
        :loading="false"
      />
    </transition-group>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SearchInput from '@/components/SearchInput.vue'
import RecommendationList from '@/components/RecommendationList.vue'
import { ElMessage } from 'element-plus'

const recommendations = ref([])
const loading = ref(false)
const progress = ref(0)
const progressMessage = ref('')

// 进度条颜色
const progressColor = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 }
]

const handleSearch = async (query) => {
  try {
    loading.value = true
    progress.value = 0
    progressMessage.value = '准备搜索...'
    recommendations.value = []

    // 构建筛选条件
    const filters = {}

    // 预算范围
    if (query.budget_min && query.budget_max) {
      filters.budget_range = [query.budget_min, query.budget_max]
    }

    // 天数范围（转换为区间：1天到用户输入的天数）
    if (query.duration) {
      filters.duration_range = [1, query.duration]
    }

    // 旅行类型
    if (query.travel_type) {
      filters.travel_type = query.travel_type
    }

    // 兴趣偏好
    if (query.interests && query.interests.length > 0) {
      filters.interests = query.interests
    }

    // 季节（后端暂未实现，但可以传递）
    if (query.season) {
      filters.season = query.season
    }

    console.log('搜索查询:', query)
    console.log('筛选条件:', filters)

    // 使用新的SSE流式搜索API
    const response = await fetch('/api/integrated-search/search/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query.query,
        filters: Object.keys(filters).length > 0 ? filters : null,
        top_k: 20
      })
    })

    if (!response.ok) {
      throw new Error('搜索请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let resultCount = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6))

          if (data.type === 'progress') {
            // 更新进度
            progress.value = data.progress
            progressMessage.value = data.message
          } else if (data.type === 'result') {
            // 转换数据格式为组件期望的结构
            const formattedResult = {
              name: data.data.name,
              destination: {
                name: data.data.name,
                location: data.data.city || data.data.province || '未知',
                description: data.data.description || '暂无描述',
                category: data.data.category || '景点',
                rating: data.data.rating || 4.5,
                best_season: ['春', '夏', '秋', '冬'],
                budget_range: [100, 500],
                features: data.data.category ? [data.data.category] : ['景点'] // 添加features字段
              },
              reason: `相关度：${data.data.score ? (data.data.score * 100).toFixed(0) : 0}%`,
              score: data.data.score || 0,
              source: data.data.source || 'RAG检索' // 添加source字段
            }

            recommendations.value.push(formattedResult)
            resultCount++

            // 微调进度（结果返回阶段）
            if (progress.value >= 90 && progress.value < 100) {
              progress.value = Math.min(99, 90 + resultCount)
            }
          } else if (data.type === 'complete') {
            progress.value = 100
            progressMessage.value = '搜索完成！'
            loading.value = false

            setTimeout(() => {
              ElMessage.success(`找到 ${resultCount} 个推荐景点`)
            }, 300)
          } else if (data.type === 'error') {
            console.error('Search error:', data.message)
            ElMessage.error('推荐搜索失败：' + data.message)
            loading.value = false
          }
        }
      }
    }

  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('推荐搜索失败，请重试')
    loading.value = false
    progress.value = 0
    progressMessage.value = ''
  }
}
</script>

<style scoped>
.recommand {
  width: 100%;
}

.search-progress {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin: 20px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.3s ease-in;
}

.progress-message {
  margin-top: 16px;
  font-size: 16px;
  color: #606266;
  text-align: center;
  font-weight: 500;
}

.progress-detail {
  margin-top: 8px;
  font-size: 14px;
  color: #909399;
  text-align: center;
}

/* 淡入动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 滑动淡入动画（结果列表） */
.slide-fade-enter-active {
  transition: all 0.4s ease;
}

.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
