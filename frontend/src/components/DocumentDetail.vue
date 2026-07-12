<template>
  <div class="document-detail">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="文档名称">
        {{ document.filename }}
      </el-descriptions-item>

      <el-descriptions-item label="文件大小">
        {{ formatFileSize(document.file_size) }}
      </el-descriptions-item>

      <el-descriptions-item label="页数">
        {{ document.pages }} 页
      </el-descriptions-item>

      <el-descriptions-item label="城市">
        <el-tag v-if="document.city">{{ document.city }}</el-tag>
        <span v-else>-</span>
      </el-descriptions-item>

      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(document.status)">
          {{ getStatusText(document.status) }}
        </el-tag>
      </el-descriptions-item>

      <el-descriptions-item label="提取景点数">
        <el-tag v-if="document.destinations_count > 0" type="success">
          {{ document.destinations_count }} 个
        </el-tag>
        <span v-else>-</span>
      </el-descriptions-item>

      <el-descriptions-item label="上传时间">
        {{ formatFullTime(document.upload_time) }}
      </el-descriptions-item>

      <el-descriptions-item label="处理时间">
        {{ document.process_time ? document.process_time + 's' : '-' }}
      </el-descriptions-item>

      <el-descriptions-item label="MinIO 路径" :span="2">
        <el-input
          :value="document.minio_path"
          readonly
          size="small"
        >
          <template #append>
            <el-button @click="copyPath">复制</el-button>
          </template>
        </el-input>
      </el-descriptions-item>
    </el-descriptions>

    <div v-if="document.destinations && document.destinations.length > 0" class="destinations-section">
      <el-divider content-position="left">
        <el-icon><LocationInformation /></el-icon>
        提取的景点 ({{ document.destinations.length }})
      </el-divider>

      <el-table :data="document.destinations" stripe max-height="400">
        <el-table-column prop="name" label="景点名称" min-width="150" />
        <el-table-column prop="location" label="位置" min-width="150" />
        <el-table-column prop="tags" label="标签" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag"
              size="small"
              style="margin-right: 4px"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rating" label="评分" width="100" align="center" />
      </el-table>
    </div>

    <div v-if="document.error_message" class="error-section">
      <el-alert
        title="处理错误"
        type="error"
        :description="document.error_message"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup>
import { LocationInformation } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  document: {
    type: Object,
    required: true
  }
})

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`
}

const formatFullTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'processing': 'warning',
    'pending': 'info',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'completed': '完成',
    'processing': '处理中',
    'pending': '排队中',
    'failed': '失败'
  }
  return textMap[status] || status
}

const copyPath = () => {
  navigator.clipboard.writeText(props.document.minio_path)
  ElMessage.success('已复制到剪贴板')
}
</script>

<style scoped>
.document-detail {
  padding: 20px;
}

.destinations-section {
  margin-top: 30px;
}

.error-section {
  margin-top: 20px;
}
</style>
