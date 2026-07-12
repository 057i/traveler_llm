<template>
  <div class="websocket-page">
    <el-card class="page-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI团队推荐</span>
          <el-tag type="info" size="small">实时连接</el-tag>
        </div>
      </template>

      <!-- WebSocket 聊天界面 -->
      <ChatInterface
        :use-chat-workflow="false"
        @recommendations="handleResults"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import ChatInterface from '@/components/ChatInterface.vue'

const recommendations = ref([])

const handleResults = (results) => {
  recommendations.value = results
}
</script>

<style scoped>
.websocket-page {
  width: 100%;
}

.page-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  height: calc(100vh - 60px);
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
  color: #409eff;
}
</style>
