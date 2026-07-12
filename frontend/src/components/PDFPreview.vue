<template>
  <el-dialog
    v-model="visible"
    :title="`预览: ${filename}`"
    width="80%"
    top="5vh"
    :close-on-click-modal="false"
    class="pdf-preview-dialog"
  >
    <div class="pdf-preview-container">
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-button-group>
          <el-button
            :icon="ZoomOut"
            @click="zoomOut"
            :disabled="scale <= 0.5"
          >
            缩小
          </el-button>
          <el-button @click="resetZoom">
            {{ Math.round(scale * 100) }}%
          </el-button>
          <el-button
            :icon="ZoomIn"
            @click="zoomIn"
            :disabled="scale >= 2.0"
          >
            放大
          </el-button>
        </el-button-group>

        <div class="page-control">
          <el-button
            :icon="ArrowLeft"
            @click="prevPage"
            :disabled="currentPage <= 1"
          >
            上一页
          </el-button>
          <span class="page-info">
            第 {{ currentPage }} / {{ totalPages }} 页
          </span>
          <el-button
            :icon="ArrowRight"
            @click="nextPage"
            :disabled="currentPage >= totalPages"
          >
            下一页
          </el-button>
        </div>

        <el-button :icon="Download" @click="downloadPDF">
          下载
        </el-button>
      </div>

      <!-- PDF 渲染区域 -->
      <div class="pdf-viewer" v-loading="loading">
        <canvas
          ref="pdfCanvas"
          :style="{
            transform: `scale(${scale})`,
            transformOrigin: 'top center'
          }"
        ></canvas>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import {
  ZoomIn,
  ZoomOut,
  ArrowLeft,
  ArrowRight,
  Download
} from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import { ElMessage } from 'element-plus'

// 配置 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  documentId: {
    type: String,
    required: true
  },
  filename: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const pdfCanvas = ref(null)
const pdfDoc = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadPDF()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

watch(currentPage, () => {
  if (pdfDoc.value) {
    renderPage(currentPage.value)
  }
})

const loadPDF = async () => {
  try {
    loading.value = true

    // 构建 PDF URL（从后端获取）
    const pdfUrl = `/api/documents/${props.documentId}/download`

    // 加载 PDF 文档
    const loadingTask = pdfjsLib.getDocument(pdfUrl)
    pdfDoc.value = await loadingTask.promise

    totalPages.value = pdfDoc.value.numPages
    currentPage.value = 1

    // 渲染第一页
    await nextTick()
    await renderPage(1)

    loading.value = false
    ElMessage.success('PDF 加载成功')

  } catch (error) {
    console.error('加载 PDF 失败:', error)
    ElMessage.error('PDF 加载失败')
    loading.value = false
    visible.value = false
  }
}

const renderPage = async (pageNum) => {
  if (!pdfDoc.value || !pdfCanvas.value) return

  try {
    loading.value = true

    const page = await pdfDoc.value.getPage(pageNum)
    const viewport = page.getViewport({ scale: 1.5 })

    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')

    canvas.height = viewport.height
    canvas.width = viewport.width

    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }

    await page.render(renderContext).promise
    loading.value = false

  } catch (error) {
    console.error('渲染页面失败:', error)
    loading.value = false
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const zoomIn = () => {
  if (scale.value < 2.0) {
    scale.value = Math.min(scale.value + 0.1, 2.0)
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(scale.value - 0.1, 0.5)
  }
}

const resetZoom = () => {
  scale.value = 1.0
}

const downloadPDF = () => {
  const link = document.createElement('a')
  link.href = `/api/documents/${props.documentId}/download`
  link.download = props.filename
  link.click()
  ElMessage.success('开始下载')
}
</script>

<style scoped>
.pdf-preview-dialog {
  --el-dialog-padding-primary: 0;
}

.pdf-preview-container {
  display: flex;
  flex-direction: column;
  height: 80vh;
  background: #f5f5f5;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  gap: 16px;
  flex-wrap: wrap;
}

.page-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-info {
  font-size: 14px;
  color: #606266;
  min-width: 120px;
  text-align: center;
}

.pdf-viewer {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #525252;
}

.pdf-viewer canvas {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  background: white;
  transition: transform 0.2s ease;
}

/* 滚动条美化 */
.pdf-viewer::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.pdf-viewer::-webkit-scrollbar-track {
  background: #3a3a3a;
}

.pdf-viewer::-webkit-scrollbar-thumb {
  background: #666;
  border-radius: 5px;
}

.pdf-viewer::-webkit-scrollbar-thumb:hover {
  background: #888;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
  }

  .page-control {
    width: 100%;
    justify-content: center;
  }
}
</style>
