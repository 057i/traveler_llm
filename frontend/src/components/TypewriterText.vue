<template>
  <div class="typewriter" v-html="displayedHtml"></div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  speed: {
    type: Number,
    default: 30
  },
  autoStart: {
    type: Boolean,
    default: true
  }
})

// 配置 marked 选项
marked.setOptions({
  breaks: true,
  gfm: true,
})

// ✅ 修复：直接渲染完整 Markdown，不使用打字机效果
// 打字机效果与 Markdown HTML 渲染冲突，导致字符重复
const displayedHtml = computed(() => {
  if (!props.text) return ''

  try {
    // 直接渲染完整的 Markdown
    return marked.parse(props.text)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return props.text.replace(/\n/g, '<br>')
  }
})
</script>

<style scoped>
.typewriter {
  white-space: normal;
  word-break: break-word;
  line-height: 1.6;
}

/* Markdown 样式 */
.typewriter :deep(h1),
.typewriter :deep(h2),
.typewriter :deep(h3),
.typewriter :deep(h4),
.typewriter :deep(h5),
.typewriter :deep(h6) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.typewriter :deep(h1) { font-size: 1.8em; border-bottom: 2px solid #eee; padding-bottom: 8px; }
.typewriter :deep(h2) { font-size: 1.6em; border-bottom: 1px solid #eee; padding-bottom: 6px; }
.typewriter :deep(h3) { font-size: 1.4em; }
.typewriter :deep(h4) { font-size: 1.2em; }
.typewriter :deep(h5) { font-size: 1.1em; }
.typewriter :deep(h6) { font-size: 1em; color: #666; }

.typewriter :deep(p) {
  margin: 8px 0;
}

.typewriter :deep(ul),
.typewriter :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.typewriter :deep(li) {
  margin: 4px 0;
}

.typewriter :deep(strong) {
  font-weight: bold;
  color: #303133;
}

.typewriter :deep(em) {
  font-style: italic;
}

.typewriter :deep(code) {
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #e74c3c;
}

.typewriter :deep(pre) {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.typewriter :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.typewriter :deep(blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 16px;
  margin: 12px 0;
  color: #666;
}

.typewriter :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.typewriter :deep(a:hover) {
  text-decoration: underline;
}

.typewriter :deep(hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 16px 0;
}

.typewriter :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.typewriter :deep(th),
.typewriter :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.typewriter :deep(th) {
  background: #f4f4f5;
  font-weight: 600;
}
</style>
