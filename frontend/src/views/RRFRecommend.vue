<template>
  <div class="rrf-page">


      <!-- 搜索输入 -->
      <SearchInput @search="handleSearch" />

      <!-- 推荐结果 -->
      <RecommendationList
        v-if="recommendations.length > 0"
        :recommendations="recommendations"
        :loading="loading"
      />
<!--    </el-card>-->
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Connection } from '@element-plus/icons-vue'
import SearchInput from '@/components/SearchInput.vue'
import RecommendationList from '@/components/RecommendationList.vue'
import { integratedSearchWithDiversity } from '@/api'
import { ElMessage } from 'element-plus'

const recommendations = ref([])
const loading = ref(false)

const handleSearch = async (query) => {
  try {
    loading.value = true
    recommendations.value = []

    // 构建query对象，只包含有值的字段
    const queryObj = {
      query: query.query
    }

    if (query.budget) queryObj.budget = query.budget
    if (query.season) queryObj.season = query.season
    if (query.travel_type) queryObj.travel_type = query.travel_type
    if (query.duration) queryObj.duration = query.duration
    if (query.interests && query.interests.length > 0) {
      queryObj.interests = query.interests
    }

    const requestData = {
      query: queryObj,
      models: ['rag'],  // 临时只使用RAG，不使用graph_rag
      weights: {
        rag: 1.0  // 100%权重给RAG
      }
    }

    const response = await integratedSearchWithDiversity(requestData, {
      alpha: 0.7,
      top_k: 5
    })

    if (response.status === 'success') {
      recommendations.value = response.results
      ElMessage.success(`找到 ${response.results.length} 个推荐景点`)
    }
  } catch (error) {
    console.error('RRF 搜索失败:', error)
    ElMessage.error('推荐搜索失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.recommend {
  width: 100%;
}

.page-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
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
  color: #e6a23c;
}
</style>
