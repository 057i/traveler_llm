<template>
  <el-card class="recommendation-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><List /></el-icon>
        <span>推荐结果 ({{ recommendations.length }})</span>
      </div>
    </template>

    <el-row :gutter="20" v-loading="loading">
      <el-col
        v-for="(rec, index) in recommendations"
        :key="index"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="8"
      >
        <el-card class="destination-card" shadow="hover" @click="showDetail(rec)">
          <template #header>
            <div class="destination-header">
              <h3>{{ rec.name }}</h3>
            </div>
          </template>

          <div class="destination-content">
            <div class="info-item">
              <el-icon><Location /></el-icon>
              <span class="ellipsis">{{ rec.destination.location }}</span>
            </div>

            <div class="description">
              {{ rec.destination.description }}
            </div>

            <div class="reason">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ rec.reason }}</span>
            </div>

            <el-divider />

            <div class="meta-info">
              <div class="meta-item">
                <el-icon><Calendar /></el-icon>
                <span>{{ formatSeasons(rec.destination.best_season) }}</span>
              </div>
              <div class="meta-item">
                <el-icon><Money /></el-icon>
                <span>{{ formatBudget(rec.destination.budget_range) }}</span>
              </div>
              <div class="meta-item">
                <el-icon><Star /></el-icon>
                <span>{{ rec.destination.rating.toFixed(2) }}</span>
              </div>
            </div>

            <div class="features">
              <h4>特色景点</h4>
              <div class="feature-tags">
                <el-tag
                  v-for="(feature, idx) in rec.destination.features.slice(0, 3)"
                  :key="idx"
                  size="small"
                  type="success"
                  effect="plain"
                >
                  {{ feature }}
                </el-tag>
                <el-tag v-if="rec.destination.features.length > 3" size="small" type="info">
                  +{{ rec.destination.features.length - 3 }}
                </el-tag>
              </div>
            </div>

            <div class="source">
              <el-tag size="small" type="warning">
                来源: {{ rec.source }}
              </el-tag>
            </div>

            <div class="view-detail">
              <el-link type="primary" :underline="false">
                <el-icon><View /></el-icon>
                查看详情
              </el-link>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && recommendations.length === 0" description="暂无推荐结果" />

    <!-- 详情弹窗 -->
    <el-dialog v-if="detailVisible"
      v-model="detailVisible"
      :title="currentDetail?.name"
      width="800px"
      center
      destroy-on-close
      append-to-body
      class="recommand_detail_dialog"
    >
      <div v-if="currentDetail" class="detail-content">
        <!-- 图片展示 -->
        <div v-if="currentDetail.destination.image_url" class="detail-image">
          <el-image
            :src="currentDetail.destination.image_url"
            fit="cover"
            style="width: 100%; height: 300px; border-radius: 8px;"
          >
            <template #error>
              <div class="image-slot">
                <el-icon><Picture /></el-icon>
                <span>暂无图片</span>
              </div>
            </template>
          </el-image>
        </div>

        <!-- 基本信息 -->
        <el-descriptions :column="2" border style="margin-top: 20px;">
          <el-descriptions-item label="位置">
            <el-icon><Location /></el-icon>
            {{ currentDetail.destination.location }}
          </el-descriptions-item>
          <el-descriptions-item label="评分">
            <el-icon><Star /></el-icon>
            {{ currentDetail.destination.rating.toFixed(2) }} / 5.0
          </el-descriptions-item>
          <el-descriptions-item label="预算区间">
            <el-icon><Money /></el-icon>
            {{ formatBudget(currentDetail.destination.budget_range) }}
          </el-descriptions-item>
          <el-descriptions-item label="最佳季节">
            <el-icon><Calendar /></el-icon>
            {{ formatSeasons(currentDetail.destination.best_season) }}
          </el-descriptions-item>
          <el-descriptions-item label="适合人群" :span="2">
            <el-tag
              v-for="type in currentDetail.destination.suitable_for"
              :key="type"
              size="small"
              type="primary"
              effect="plain"
              style="margin-right: 8px;"
            >
              {{ type }}
            </el-tag>
            <span v-if="!currentDetail.destination.suitable_for || currentDetail.destination.suitable_for.length === 0">
              全部人群
            </span>
          </el-descriptions-item>

          <el-descriptions-item label="数据来源" :span="2">
            <el-tag size="small" type="warning">{{ currentDetail.source }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 描述 -->
        <el-divider content-position="left">景点介绍</el-divider>
        <p class="detail-description">{{ currentDetail.destination.description }}</p>

        <!-- 推荐理由 -->
        <el-divider content-position="left">推荐理由</el-divider>
        <el-alert
          :title="currentDetail.reason"
          type="info"
          :closable="false"
          show-icon
        />

        <!-- 标签 -->
        <el-divider content-position="left">景点标签</el-divider>
        <div class="detail-tags">
          <el-tag
            v-for="tag in currentDetail.destination.tags"
            :key="tag"
            type="info"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ tag }}
          </el-tag>
          <span v-if="!currentDetail.destination.tags || currentDetail.destination.tags.length === 0" class="empty-hint">
            暂无标签
          </span>
        </div>

        <!-- 特色景点 -->
        <el-divider content-position="left">特色景点</el-divider>
        <div class="detail-features">
          <el-tag
            v-for="feature in currentDetail.destination.features"
            :key="feature"
            type="success"
            effect="plain"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ feature }}
          </el-tag>
          <span v-if="!currentDetail.destination.features || currentDetail.destination.features.length === 0" class="empty-hint">
            暂无特色景点
          </span>
        </div>
      </div>

      <template #footer>
        <div style="text-align: right;">
          <el-button @click="detailVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { List, Location, InfoFilled, Calendar, Money, Star, View, Picture } from '@element-plus/icons-vue'

defineProps({
  recommendations: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const detailVisible = ref(false)
const currentDetail = ref(null)

const showDetail = (rec) => {
  currentDetail.value = rec
  detailVisible.value = true
}

const formatSeasons = (seasons) => {
  if (!seasons || seasons.length === 0) return '全年适宜'
  return seasons.join('、')
}

const formatBudget = (range) => {
  if (!range || range.length < 2) return '未知'
  return `¥${range[0]} - ¥${range[1]}`
}

const getScoreColor = (score) => {
  if (score >= 0.7) return '#67c23a'
  if (score >= 0.5) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.recommendation-list-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
  color: #667eea;
}

.destination-card {
  margin-bottom: 20px;
  height: 480px; /* 固定高度 */
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
  cursor: pointer;
}

.destination-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.destination-card :deep(.el-card__header) {
  flex-shrink: 0;
}

.destination-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.destination-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.destination-header h3 {
  margin: 0;
  font-size: 20px;
  color: #667eea;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.destination-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #666;
}

.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.description {
  margin: 12px 0;
  color: #333;
  line-height: 1.6;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 限制两行 */
  -webkit-box-orient: vertical;
}

.reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #f0f2f5;
  border-radius: 4px;
  margin: 12px 0;
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 限制两行 */
  -webkit-box-orient: vertical;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  margin: 12px 0;
  flex-shrink: 0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #666;
}

.features {
  margin: 12px 0;
  flex-shrink: 0;
}

.features h4 {
  font-size: 14px;
  margin: 0 0 8px 0;
  color: #333;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source {
  margin-top: auto;
  text-align: right;
  flex-shrink: 0;
}

.view-detail {
  text-align: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
}

/* 详情弹窗样式 */
.detail-content {
  height: 100%;
}

.detail-image {
  margin-bottom: 20px;
}

.image-slot {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}

.image-slot .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.detail-description {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  text-indent: 2em;
}

.detail-tags,
.detail-features {
  display: flex;
  flex-wrap: wrap;
}

.empty-hint {
  color: #909399;
  font-size: 14px;
  font-style: italic;
}

/* 弹窗样式优化 */
:deep(.el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  margin-top: 15vh !important;  /* 距离顶部15%，让弹窗居中显示 */
}

:deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}
</style>
