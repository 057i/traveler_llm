# 🎨 前端集成指南 - AI推荐功能

**日期**: 2026-07-11  
**后端状态**: ✅ 完成  
**前端状态**: 待实现

---

## 📋 需要修改的前端文件

### 1. 创建AI推荐页面
**文件**: `frontend/src/views/AIRecommend.vue`

```vue
<template>
  <div class="ai-recommend-container">
    <div class="header">
      <h1>🤖 AI智能推荐</h1>
      <p>基于知识图谱和AI的智能旅游推荐</p>
    </div>

    <!-- 输入区域 -->
    <div class="input-section">
      <el-input
        v-model="userQuery"
        placeholder="例如：推荐一下三清山的旅游攻略"
        :rows="3"
        type="textarea"
        @keyup.ctrl.enter="handleSubmit"
      />
      <el-button 
        type="primary" 
        @click="handleSubmit"
        :loading="isLoading"
        :disabled="!userQuery.trim()"
      >
        {{ isLoading ? '推荐中...' : '获取推荐' }}
      </el-button>
    </div>

    <!-- 进度显示 -->
    <div v-if="isLoading" class="progress-section">
      <el-timeline>
        <el-timeline-item
          v-for="(node, index) in executedNodes"
          :key="index"
          :type="node.status"
          :icon="node.icon"
        >
          <div class="node-info">
            <strong>{{ node.name }}</strong>
            <p v-if="node.message">{{ node.message }}</p>
            <el-tag v-if="node.data" size="small">{{ node.data }}</el-tag>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 结果显示 -->
    <div v-if="result" class="result-section">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>🎯 推荐结果</span>
            <el-button 
              text 
              @click="copyResult"
              icon="DocumentCopy"
            >
              复制
            </el-button>
          </div>
        </template>

        <div class="answer-content" v-html="formatAnswer(result.answer)"></div>

        <!-- 来源列表 -->
        <div v-if="result.sources && result.sources.length > 0" class="sources">
          <h4>📚 参考来源</h4>
          <el-collapse>
            <el-collapse-item
              v-for="(source, index) in result.sources"
              :key="index"
              :title="`来源 ${index + 1}: ${source.title || '无标题'}`"
            >
              <p>{{ source.content || '无内容' }}</p>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

const userQuery = ref('');
const isLoading = ref(false);
const executedNodes = ref([]);
const result = ref(null);

// 节点名称映射
const nodeNameMap = {
  query_rewriter: '📝 问题重写',
  parallel_retrieval: '🔍 并行检索',
  rrf_fusion: '🔀 RRF融合',
  confidence_check: '📊 置信度检查',
  tavily_search: '🌐 网络搜索',
  rerank: '⭐ 精排',
  synthesizer: '✨ 结果润色'
};

const handleSubmit = () => {
  if (!userQuery.value.trim()) {
    ElMessage.warning('请输入问题');
    return;
  }

  isLoading.value = true;
  executedNodes.value = [];
  result.value = null;

  // 创建EventSource连接
  const apiUrl = `http://localhost:8000/api/ai-recommend/stream`;
  
  // 使用POST需要特殊处理，这里简化为GET（实际项目中需要处理POST+SSE）
  // 或者使用fetch + ReadableStream
  
  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: userQuery.value,
      session_id: `session-${Date.now()}`
    })
  }).then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          isLoading.value = false;
          return;
        }

        const text = decoder.decode(value);
        const lines = text.split('\n');

        lines.forEach(line => {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEMessage(data);
            } catch (e) {
              console.error('解析SSE消息失败:', e);
            }
          }
        });

        read();
      });
    }

    read();
  }).catch(error => {
    isLoading.value = false;
    ElMessage.error('请求失败: ' + error.message);
  });
};

const handleSSEMessage = (data) => {
  switch (data.type) {
    case 'start':
      ElMessage.success(data.message);
      break;

    case 'node_start':
      executedNodes.value.push({
        name: nodeNameMap[data.node] || data.node,
        status: 'primary',
        icon: 'Loading',
        message: '',
        data: ''
      });
      break;

    case 'progress':
      const lastNode = executedNodes.value[executedNodes.value.length - 1];
      if (lastNode) {
        lastNode.message = data.message;
      }
      break;

    case 'node_complete':
      const completeNode = executedNodes.value[executedNodes.value.length - 1];
      if (completeNode) {
        completeNode.status = 'success';
        completeNode.icon = 'Check';
        completeNode.data = JSON.stringify(data.data);
      }
      break;

    case 'result':
      result.value = {
        answer: data.answer,
        sources: data.sources || []
      };
      break;

    case 'complete':
      isLoading.value = false;
      ElMessage.success(data.message);
      break;

    case 'error':
      isLoading.value = false;
      ElMessage.error(data.message);
      break;
  }
};

const formatAnswer = (text) => {
  // 简单的Markdown格式化
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');
};

const copyResult = () => {
  if (result.value) {
    navigator.clipboard.writeText(result.value.answer);
    ElMessage.success('已复制到剪贴板');
  }
};
</script>

<style scoped>
.ai-recommend-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.input-section {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.input-section .el-input {
  flex: 1;
}

.progress-section {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.node-info {
  padding: 8px 0;
}

.result-section {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.answer-content {
  line-height: 1.8;
  margin-bottom: 20px;
}

.sources {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
</style>
```

---

### 2. 更新路由配置
**文件**: `frontend/src/router/index.js`

添加路由：
```javascript
{
  path: '/ai-recommend',
  name: 'AIRecommend',
  component: () => import('../views/AIRecommend.vue'),
  meta: {
    title: 'AI智能推荐'
  }
}
```

---

### 3. 更新导航栏
**文件**: `frontend/src/components/NavBar.vue` (或主导航组件)

添加菜单项：
```vue
<el-menu-item index="/ai-recommend">
  <el-icon><MagicStick /></el-icon>
  <span>AI智能推荐</span>
</el-menu-item>
```

---

## 🚀 启动和测试

### 后端启动
```bash
cd backend
python main.py
```

### 前端启动
```bash
cd frontend
npm run dev
```

### 测试后端
```bash
cd backend
python test_ai_recommend.py
```

---

## 📡 API调用示例

### 方式1: Fetch + ReadableStream (推荐)
```javascript
const response = await fetch('http://localhost:8000/api/ai-recommend/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: '三清山', session_id: 'xxx' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  // 处理SSE消息...
}
```

### 方式2: EventSource (仅GET)
```javascript
// 注意：EventSource只支持GET，需要后端提供GET接口
const eventSource = new EventSource(
  'http://localhost:8000/api/ai-recommend/stream?query=三清山'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 处理消息...
};
```

---

## 🎨 UI优化建议

1. **进度可视化**: 使用el-timeline展示节点执行进度
2. **结果格式化**: 支持Markdown渲染
3. **来源展示**: 使用el-collapse折叠展示来源
4. **复制功能**: 一键复制推荐结果
5. **历史记录**: 保存用户查询历史
6. **评分功能**: 允许用户对推荐结果评分

---

**准备就绪！可以开始前端开发了！** 🎉
