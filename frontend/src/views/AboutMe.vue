<template>
  <div class="workspace-page">
    <!-- Header Section -->
    <div class="workspace-header project-intro">
      <div class="intro-icon">
        <Icon icon="mdi:compass-outline" style="font-size: 64px; color: #3b82f6;" />
      </div>
      <div class="header-content">
        <h1 class="header-title">
          智能旅行推荐系统
        </h1>
        <p class="header-description">
          基于 <strong>RAG + GraphRAG + RRF + Rerank</strong> 技术栈构建的智能旅游目的地推荐系统
        </p>
        <div class="header-features">
          <span class="feature-tag" >
            <Icon icon="mdi:database-search" />
            向量检索
          </span>
          <span class="feature-tag">
            <Icon icon="mdi:graph" />
            知识图谱
          </span>
          <span class="feature-tag" >
            <Icon icon="mdi:robot-happy" />
            AI推荐
          </span>
          <span class="feature-tag" >
            <Icon icon="mdi:file-document-multiple" />
            文档管理
          </span>
        </div>

        <!-- 预览提示 -->
        <div class="preview-notice">
          <Icon icon="mdi:information" style="font-size: 20px;" />
          <div class="notice-content">
            <strong>注意：</strong>因服务器配置不够，预览项目无法利用模型功能。
            <br />
            请转至
            <a href="https://github.com/057i/traveler_llm.git" target="_blank" class="github-link">
              <Icon icon="mdi:github" />
              GitHub仓库
            </a>
            clone 到本地运行以体验完整功能。
          </div>
        </div>
      </div>
    </div>

    <!-- Project Cards Section -->
    <div class="project-section">
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">{{ title }}</h2>
        </div>
        <div class="card-content">
          <div
            v-for="(item, index) in items"
            :key="item.title"
            :class="getCardClass(index)"
            class="project-card"
            @click="handleClick(item)"
          >
            <div class="project-header">
              <!-- Iconify Icon -->
              <span
                v-if="item.icon"
                class="iconify-icon"
                :style="{ color: item.color || '#000' }"
              >
                <Icon :icon="item.icon" :style="{ fontSize: '32px' }" />
              </span>
              <span class="project-title">{{ item.title }}</span>
            </div>
            <div class="project-content">
              {{ item.content }}
            </div>
            <div class="project-footer">
              <span>{{ item.group }}</span>
              <span>{{ item.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// ============ 接口定义 ============
interface WorkbenchProjectItem {
  color?: string;
  content: string;
  date: string;
  group: string;
  icon: string;
  title: string;
  url?: string;
}

interface Props {
  // 用户名
  username?: string;
  // 头像
  avatar?: string;
  // 卡片标题
  title?: string;
  // 项目列表
  items?: WorkbenchProjectItem[];
}

// ============ Props ============
const props = withDefaults(defineProps<Props>(), {
  username: '用户',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
  title: '我的技术栈',
  items: () => [
    {
      color: '#e18525',
      content: '没有什么才能比努力更重要。',
      date: '2026-06-01',
      group: '前端开发',
      icon: 'ion:logo-html5',
      title: 'Html5',
      url: 'https://developer.mozilla.org/zh-CN/docs/Web/HTML',
    },
    {
      color: '#EBD94E',
      content: '路是走出来的，而不是空想出来的。',
      date: '2026-06-01',
      group: '前端开发',
      icon: 'ion:logo-javascript',
      title: 'Js',
      url: 'https://developer.mozilla.org/zh-CN/docs/Web/JavaScript',
    },
    {
      color: '#3fb27f',
      content: '现在的你决定将来的你。',
      date: '2026-06-01',
      group: '前端开发',
      icon: 'ion:logo-vue',
      title: 'Vue',
      url: 'https://vuejs.org',
    },
    {
      color: '#3776ab',
      content: '简洁的语法，无限的可能。',
      date: '2026-04-04',
      group: '后端/模型应用开发',
      icon: 'devicon:python',
      title: 'Python',
      url: 'https://www.python.org',
    },
    {
      color: '#009688',
      content: '高性能API，让数据飞起来。',
      date: '2026-06-01',
      group: '后端',
      icon: 'logos:fastapi-icon',
      title: 'Fastapi',
      url: 'https://fastapi.tiangolo.com',
    },
    {
      color: '#00758f',
      content: '数据的可靠守护者，性能的极致追求。',
      date: '2026-06-01',
      group: '后端',
      icon: 'vscode-icons:file-type-mysql',
      title: 'Mysql',
      url: 'https://www.mysql.com',
    },
    {
      color: '#00a1ea',
      content: '向量检索的先锋，让相似度计算更快更准。',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'simple-icons:milvus',
      title: 'Milvus',
      url: 'https://milvus.io',
    },
    {
      color: '#dc244c',
      content: '高性能键值存储，让缓存飞起来。',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'logos:redis',
      title: 'Redis',
      url: 'https://redis.io',
    },
    {
      color: '#47a248',
      content: '文档数据库的王者，灵活存储万物互联。',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'vscode-icons:file-type-mongo',
      title: 'Mongodb',
      url: 'https://www.mongodb.com',
    },
    {
      color: '#1c3c3c',
      content: '让AI触手可及。',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'simple-icons:langchain',
      title: 'Langchain',
      url: 'https://www.langchain.com',
    },
    {
      color: '#1c3c3c',
      content: '让智能体拥有记忆。',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'simple-icons:langgraph',
      title: 'Langgraph',
      url: 'https://langchain-ai.github.io/langgraph',
    },
    {
      color: '#008cc1',
      content: '图数据库之光',
      date: '2026-06-01',
      group: '模型应用开发',
      icon: 'vscode-icons:file-type-light-neo4j',
      title: 'Neo4j',
      url: 'https://neo4j.com',
    },
  ],
});

// ============ Emits ============
const emit = defineEmits<{
  click: [item: WorkbenchProjectItem];
}>();

// ============ Methods ============
const navigateTo = (path: string) => {
  router.push(path);
};

const getCardClass = (index: number) => {
  const total = props.items.length;
  return {
    'border-r-0': index % 3 === 2,
    'border-b-0': index < 3,
    'pb-4': index > 2,
    'rounded-bl': index === total - 3,
    'rounded-br': index === total - 1,
  };
};

const handleClick = (item: WorkbenchProjectItem) => {
  emit('click', item);

  // 默认行为：如果有 URL，则打开链接
  if (item.url) {
    if (item.url.startsWith('http')) {
      window.open(item.url, '_blank');
    } else if (item.url.startsWith('/')) {
      // 如果是内部路由，可以在这里处理
      console.log('Navigate to:', item.url);
    }
  }
};
</script>

<style scoped>
/* ============ 页面布局 ============ */
.workspace-page {
  padding: 1.25rem;
  min-height: 100vh;
  background-color: var(--bg-color, #f5f5f5);
}

/* ============ Header 样式 ============ */
.workspace-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 0.75rem;
  padding: 3rem 2rem;
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
  color: white;
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

@media (min-width: 1024px) {
  .workspace-header {
    width: 90%;
  }
}

.project-intro {
  text-align: center;
}

.intro-icon {
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.header-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin-top: 0;
}

.header-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: white;
}

@media (min-width: 768px) {
  .header-title {
    font-size: 2.5rem;
  }
}

.header-description {
  color: rgba(255, 255, 255, 0.95);
  margin-top: 0.5rem;
  font-size: 1.125rem;
  line-height: 1.75;
  max-width: 800px;
}

.header-description strong {
  color: #fbbf24;
  font-weight: 600;
}

.header-features {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 1.5rem;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
  cursor: pointer;
  user-select: none;
}

.feature-tag:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-notice {
  margin-top: 2rem;
  padding: 1.25rem 1.5rem;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  text-align: left;
  max-width: 800px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notice-content {
  flex: 1;
  font-size: 0.9375rem;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.95);
}

.notice-content strong {
  color: #fbbf24;
  font-weight: 600;
}

.github-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #60a5fa;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}

.github-link:hover {
  color: #93c5fd;
  background: rgba(255, 255, 255, 0.1);
  text-decoration: underline;
}

/* ============ Project Section ============ */
.project-section {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
}

@media (min-width: 1024px) {
  .project-section {
    flex-direction: row;
  }
}

/* ============ Card 样式 ============ */
.card {
  background-color: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 0.75rem;
  overflow: hidden;
  width: 100%;
  margin-right: 1rem;
}

@media (min-width: 1024px) {
  .card {
    width: 90%;
  }
}

.card-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--foreground-color, #111827);
}

.card-content {
  display: flex;
  flex-wrap: wrap;
  padding: 0;
}

/* ============ Project Card 样式 ============ */
.project-card {
  width: 100%;
  border-right: 1px solid var(--border-color, #e5e7eb);
  border-top: 1px solid var(--border-color, #e5e7eb);
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.project-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

@media (min-width: 768px) {
  .project-card {
    width: 50%;
  }
}

@media (min-width: 1024px) {
  .project-card {
    width: 33.333333%;
  }
}

.project-card.border-r-0 {
  border-right: 0;
}

.project-card.border-b-0 {
  border-top: 0;
}

.project-card.rounded-bl {
  border-bottom-left-radius: 0.75rem;
}

.project-card.rounded-br {
  border-bottom-right-radius: 0.75rem;
}

/* ============ Project Card 内容 ============ */
.project-header {
  display: flex;
  align-items: center;
}

.iconify-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.project-card:hover .iconify-icon {
  transform: scale(1.1);
}

.project-title {
  margin-left: 1rem;
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--foreground-color, #111827);
}

.project-content {
  margin-top: 1rem;
  height: 2.5rem;
  color: var(--foreground-muted, #6b7280);
  font-size: 0.875rem;
  line-height: 1.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  color: var(--foreground-muted, #6b7280);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

/* ============ 暗色模式支持 ============ */
@media (prefers-color-scheme: dark) {
  .workspace-page {
    --bg-color: #0f172a;
  }

  .workspace-header,
  .card {
    --card-bg: #1e293b;
    --border-color: #334155;
    --foreground-color: #f1f5f9;
    --foreground-muted: #94a3b8;
  }
}

/* ============ 自定义 CSS 变量 ============ */
:root {
  --bg-color: #f5f5f5;
  --card-bg: #ffffff;
  --border-color: #e5e7eb;
  --foreground-color: #111827;
  --foreground-muted: #6b7280;
}
</style>
