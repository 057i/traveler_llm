<template>
  <el-card class="search-input-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><Search /></el-icon>
        <span>综合搜索</span>
        <el-tag type="warning" size="small">RAG多路检索+ 结构化筛选</el-tag>
      </div>
    </template>

    <el-form :model="form" label-width="100px" size="large">
      <el-form-item label="旅行需求">
        <el-input
          v-model="form.query"
          placeholder="例如：适合家庭旅游的海边城市"
          clearable
        >
          <template #prepend>
            <el-icon><ChatDotRound /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="预算范围">
            <div style="display: flex; align-items: center; gap: 10px; width: 100%;">
              <el-input-number
                v-model="form.budget_min"
                :min="0"
                :max="50000"
                :step="100"
                placeholder="最少"
              />
              <span>-</span>
              <el-input-number
                v-model="form.budget_max"
                :min="0"
                :max="50000"
                :step="100"
                placeholder="最多"
              />
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="季节">
            <el-select v-model="form.season" placeholder="选择季节" clearable style="width: 100%">
              <el-option label="春季" value="春季" />
              <el-option label="夏季" value="夏季" />
              <el-option label="秋季" value="秋季" />
              <el-option label="冬季" value="冬季" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="旅行类型">
            <el-select v-model="form.travel_type" placeholder="旅行类型" clearable style="width: 100%">
              <el-option label="家庭" value="家庭" />
              <el-option label="情侣" value="情侣" />
              <el-option label="朋友" value="朋友" />
              <el-option label="独自" value="独自" />
              <el-option label="商务" value="商务" />
            </el-select>
          </el-form-item>
        </el-col>
          <el-col :span="12">
          <el-form-item label="旅行天数">
            <el-input-number
              v-model="form.duration"
              :min="1"
              :max="30"
              placeholder="天数"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">


        <el-col :span="12">
          <el-form-item label="其他偏好">
            <el-select
              v-model="form.interests"
              multiple
              placeholder="选择偏好"
              style="width: 100%"
            >
              <el-option label="自然风光" value="自然" />
              <el-option label="历史文化" value="历史" />
              <el-option label="美食" value="美食" />
              <el-option label="摄影" value="摄影" />
              <el-option label="户外运动" value="户外" />
              <el-option label="休闲度假" value="休闲" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item>
        <el-button
          type="primary"
          size="large"
          :icon="Search"
          @click="handleSearch"
          :disabled="!form.query"
          style="width: 100%"
        >
          开始推荐
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive } from 'vue'
import { Search, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['search'])

const form = reactive({
  query: '',
  budget_min: null,
  budget_max: null,
  season: '',
  travel_type: '',  // 改为下划线命名，与后端一致
  duration: null,
  interests: []
})

const handleSearch = () => {
  if (!form.query.trim()) {
    ElMessage.warning('请输入旅行需求')
    return
  }

  emit('search', { ...form })
}
</script>

<style scoped>
.search-input-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  margin-bottom: 20px;
  height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
  color: #667eea;
}

.el-form {
  padding: 10px 0;
}
</style>
