<template>
  <div class="document-manager">
    <el-card class="header-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>文档管理中心</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="3">
          <el-statistic title="总文档数" :value="statistics.totalDocs">
            <template #prefix>
              <el-icon><Folder /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="总省份数" :value="statistics.totalProvinces || 0">
            <template #prefix>
              <el-icon><Location /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="总城市数" :value="statistics.totalCities || 0">
            <template #prefix>
              <el-icon><LocationInformation /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="总景点数" :value="statistics.totalDestinations">
            <template #prefix>
              <el-icon><LocationInformation /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="文本RAG" :value="statistics.textRAG || 0">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
            <template #suffix>
              <span style="font-size: 12px; color: #909399;">条</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="3">
          <el-statistic title="图RAG" :value="statistics.graphRAG || 0">
            <template #prefix>
              <el-icon><Connection /></el-icon>
            </template>
            <template #suffix>
              <span style="font-size: 12px; color: #909399;">节点</span>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div>
            <el-icon><List /></el-icon>
            <span>文档列表</span>
            <span style="color: #df1515;font-size: 14px;font-weight: 300;">
              （tips:上传文档为避免失败请等待完成后再离开）
            </span>
          </div>
          <div style="display: flex; gap: 10px;">
            <el-button
              type="primary"
              @click="uploadDialogVisible = true"
            >
              <el-icon><Upload /></el-icon>
              上传文档
            </el-button>
            <el-button
              @click="refreshList"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="documents"
        style="width: 100%"
        :loading="loading"
        stripe
        row-key="task_id"
        :expand-row-keys="expandedRows"
        @expand-change="handleExpandChange"
      >
        <!-- 展开列 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div v-if="row.status!='completed'" class="progress-detail">
              <WorkflowProgress :task-id="row.task_id" :filename="row.filename" @complete="handleProcessComplete" />
            </div>
            <div v-else class="no-progress">
              <el-empty description="无处理进度信息" :image-size="60" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="filename" label="文档名称" min-width="200">
          <template #default="{ row }">
            <div class="doc-name">
              <el-icon><Document /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="province" label="省份" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.province" type="primary" effect="plain">
              <el-icon><Location /></el-icon>
              {{ row.province }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="city" label="城市" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.city" type="info">{{ row.city }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="destinations_count" label="提取景点数" width="100" align="center">
          <template #default="{ row }">
          {{row.destinations_count}}
          </template>
        </el-table-column>

        <el-table-column prop="pages_count" label="页数" width="100" align="center" />

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success">
              <el-icon><Check /></el-icon>
              完成
            </el-tag>
            <el-tag v-else-if="row.status === 'processing'" type="warning">
              <el-icon><Loading /></el-icon>
              处理中
            </el-tag>
            <el-tag v-else-if="row.status === 'pending'" type="info">
              <el-icon><Clock /></el-icon>
              排队中
            </el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">
              <el-icon><Close /></el-icon>
              失败
            </el-tag>
            <el-tag v-else type="info">未知</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="upload_time" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.upload_time) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="viewDocument(row)"
              :disabled="row.status === 'processing'"
            >
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button
              type="danger"
              link
              @click="deleteDocument(row)"
              :disabled="row.status === 'processing'"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传 PDF 文档"
      width="600px"
      @close="handleUploadDialogClose"
    >
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :action="uploadUrl"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :on-progress="handleUploadProgress"
        :on-change="handleFileChange"
        :file-list="fileList"
        :auto-upload="false"
        accept=".pdf"
        multiple
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽 PDF 文件到这里，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持格式：PDF (最大 100MB)，支持批量上传<br>
            <span style="color: #67C23A;">✓ 自动执行传统向量化（ChromaDB）和图向量化（Neo4j）</span>
          </div>
        </template>
      </el-upload>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button @click="clearFiles">清空</el-button>
          <el-button
            type="primary"
            @click="submitUpload"
            :loading="uploading"
            :disabled="fileList.length === 0"
          >
            开始上传 ({{ fileList.length }} 个文件)
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Folder,
  LocationInformation,
  MapLocation,
  DataAnalysis,
  List,
  Upload,
  Refresh,
  Check,
  Loading,
  Clock,
  Close,
  View,
  Delete,
  UploadFilled,
  Location,
  Connection
} from '@element-plus/icons-vue'
import { listDocuments, deleteDocument as deleteDocumentApi, getStatistics } from '@/api/documents'
import WorkflowProgress from '@/components/WorkflowProgress.vue'

// 统计数据
const statistics = ref({
  totalDocs: 0,
  totalDestinations: 0,
  totalCities: 0,
  chromaCount: 0,
  neo4jNodeCount: 0,
  neo4jRelCount: 0
})

// 文档列表
const documents = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 展开的行
const expandedRows = ref([])

// 上传相关
const uploadDialogVisible = ref(false)
const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const uploadUrl = '/api/documents/upload'

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const data = await getStatistics()
    statistics.value = data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取文档列表
const fetchDocuments = async () => {
  loading.value = true
  try {
    const response = await listDocuments({
      page: currentPage.value,
      page_size: pageSize.value
    })
    documents.value = response.documents
    total.value = response.total

    // 自动展开处理中的文档
    expandedRows.value = documents.value
      .filter(doc => doc.status === 'processing' || doc.status === 'pending')
      .map(doc => doc.task_id)
  } catch (error) {
    ElMessage.error('获取文档列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  fetchDocuments()
  fetchStatistics()
}

// 处理分页变化
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchDocuments()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchDocuments()
}

// 处理展开/折叠
const handleExpandChange = (row, expandedRowsData) => {
  // 使用task_id作为key
  expandedRows.value = expandedRowsData.map(r => r.task_id)
}

// 上传前验证
const beforeUpload = (file) => {
  const isPdf = file.type === 'application/pdf'
  const isLt100M = file.size / 1024 / 1024 < 100

  if (!isPdf) {
    ElMessage.error('只能上传 PDF 文件！')
    return false
  }
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过 100MB！')
    return false
  }
  return true
}

const handleFileChange = (file, fileListParam) => {
  fileList.value = fileListParam
}

const submitUpload = () => {
  uploading.value = true
  uploadRef.value.submit()
}

const clearFiles = () => {
  uploadRef.value.clearFiles()
  fileList.value = []
}

const handleUploadSuccess = (response, file) => {
  console.log('[Upload] Response:', response)

  ElMessage.success(`${file.name} 上传成功！`)

  uploading.value = false
  uploadDialogVisible.value = false
  clearFiles()

  // 立即处理新文档：创建临时对象并展开，触发SSE连接
  const taskId = response.task_id
  if (taskId) {
    // 创建临时文档对象
    const tempDoc = {
      task_id: taskId,
      filename: file.name,
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      destinations_count: 0,
      pages_count: 0,
      province: '-',
      city: '-'
    }

    // 添加到文档列表顶部
    documents.value.unshift(tempDoc)
    // 不要增加total，因为后端会返回正确的total

    // 立即展开该文档（触发WorkflowProgress挂载和SSE连接）
    expandedRows.value = [taskId]

    console.log('[Upload] Immediately expanded task:', taskId)
  }

  // 延迟刷新完整列表（更新真实数据，替换临时对象）
  setTimeout(async () => {
    await fetchDocuments()
    await fetchStatistics()
  }, 1000)
}

const handleUploadError = (error, file) => {
  ElMessage.error(`${file.name} 上传失败：${error.message}`)
  uploading.value = false
}

const handleUploadProgress = (event, file) => {
  console.log('上传进度:', event.percent, file.name)
}

const handleProcessComplete = () => {
  // 文档处理完成后刷新列表
  fetchDocuments()
  fetchStatistics()
}

const handleUploadDialogClose = () => {
  clearFiles()
  uploading.value = false
}

// 查看文档
const viewDocument = (row) => {
  // 直接从列表数据中读取查看URL
  const viewUrl = row.view_url || row.minio_public_url

  if (viewUrl) {
    // 在新窗口中打开文档
    window.open(viewUrl, '_blank')
  } else {
    ElMessage.warning('该文档暂无查看链接，请重新上传')
  }
}

// 删除文档
const deleteDocument = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${row.filename}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 使用task_id作为文档ID
    await deleteDocumentApi(row.task_id)
    ElMessage.success('删除成功')
    fetchDocuments()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchDocuments()
  fetchStatistics()
})
</script>

<style scoped>
.document-manager {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-detail {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.no-progress {
  padding: 20px;
  text-align: center;
}

.upload-demo {
  width: 100%;
}

.el-icon--upload {
  font-size: 67px;
  color: #409eff;
  margin: 40px 0 16px;
}

.el-upload__text {
  font-size: 14px;
  color: #606266;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
}

:deep(.el-table__expanded-cell) {
  padding: 0 !important;
}
</style>
