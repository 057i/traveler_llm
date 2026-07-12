<template>
  <div class="sse-page">
    <el-card class="page-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Lightning /></el-icon>
          <span>SSE 实时推荐</span>
          <el-tag type="success" size="small">实时流式</el-tag>
        </div>
      </template>

      <!-- 搜索输入 -->
      <SearchInput @search="handleSearch" />

      <!-- SSE 进度展示 -->
      <SSEProgress
        v-if="showSSE"
        :query="searchQuery"
        @results="handleSSEResults"
      />

      <!-- 推荐结果 -->
      <RecommendationList
        v-if="recommendations.length > 0"
        :recommendations="recommendations"
        :loading="loading"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Lightning } from '@element-plus/icons-vue'
import SearchInput from '@/components/SearchInput.vue'
import SSEProgress from '@/components/SSEProgress.vue'
import RecommendationList from '@/components/RecommendationList.vue'

const searchQuery = ref(null)
const showSSE = ref(false)
const recommendations = ref([])
const loading = ref(false)

const handleSearch = async (query) => {
  searchQuery.value = query
  recommendations.value = []
  showSSE.value = true
}

const handleSSEResults = (results) => {
  recommendations.value = results
  showSSE.value = false
  loading.value = false
}
</script>

<style scoped>
.sse-page {
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
  color: #67c23a;
}
</style>
