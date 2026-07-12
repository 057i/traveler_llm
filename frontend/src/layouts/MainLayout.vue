<template>
  <div class="layout-container">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <el-icon><Menu /></el-icon>
        <span>智能旅行推荐</span>
      </div>

      <el-menu
        :default-active="currentRoute"
        class="sidebar-menu"
        @select="handleMenuSelect"
        router
      >
        <!-- 动态生成菜单 -->
        <template v-for="route in menuRoutes" :key="route.path">
          <!-- 菜单组（带子菜单） -->
          <el-sub-menu v-if="route.children && route.meta?.isGroup" :index="route.path">
            <template #title>
              <el-icon><component :is="route.meta.icon" /></el-icon>
              <span>{{ route.meta.title }}</span>
            </template>

            <el-menu-item
              v-for="child in route.children"
              :key="child.path"
              :index="child.path"
            >
              <el-icon><component :is="child.meta.icon" /></el-icon>
              <span>{{ child.meta.title }}</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 普通菜单项 -->
          <el-menu-item v-else :index="route.path">
            <el-icon><component :is="route.meta.icon" /></el-icon>
            <span>{{ route.meta.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>

      <!-- 底部状态指示 -->
      <div class="sidebar-footer">
        <div class="mode-indicator">
          <div :class="['indicator-dot', `mode-sse`]"></div>
          <span class="indicator-text">{{ getCurrentModeName() }}</span>
        </div>
      </div>
    </aside>

    <!-- 右侧内容区域 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Menu,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const currentRoute = computed(() => route.path)

// 从路由配置中提取菜单项
const menuRoutes = computed(() => {
  const routes = router.options.routes
  const mainRoute = routes.find(r => r.path === '/')

  if (!mainRoute || !mainRoute.children) {
    return []
  }

  // 过滤掉隐藏的菜单项
  return mainRoute.children.filter(route => {
    return route.meta && !route.meta.hideInMenu
  })
})

const handleMenuSelect = (index) => {
  router.push(index)
}

const getCurrentModeName = () => {
  return route.meta?.title || '未选择'
}
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  gap: 0;
}

/* 左侧导航栏 */
.sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 1000;
}

.sidebar-header {
  padding: 24px 20px;
  color: white;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-header .el-icon {
  font-size: 24px;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  overflow-y: auto;
}

.el-menu {
  background-color: transparent !important;
}

/* 子菜单样式 */
.sidebar-menu .el-sub-menu {
  background: transparent !important;
}

.sidebar-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 16px;
  padding: 16px 20px !important;
  margin: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s;
  height: auto !important;
  line-height: 1.5;
  background: transparent !important;
}

.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
}

.sidebar-menu :deep(.el-sub-menu.is-opened .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

/* 子菜单列表容器 */
.sidebar-menu :deep(.el-menu--inline) {
  background: rgba(0, 0, 0, 0.1) !important;
  margin: 0 12px 8px 12px;
  border-radius: 8px;
  padding: 4px 0;
}

.sidebar-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  padding: 16px 20px;
  margin: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s;
  height: auto;
  line-height: 1.5;
  background: transparent !important;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-1px) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-1px) !important;
}

/* submenu 内的菜单项选中样式 */
.sidebar-menu .el-sub-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-1px) !important;
}

.sidebar-menu .el-sub-menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-1px) !important;
}

.sidebar-menu .el-menu-item .el-icon {
  font-size: 20px;
  margin-right: 12px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.mode-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.indicator-dot.mode-sse {
  background: #67c23a;
  box-shadow: 0 0 10px rgba(103, 194, 58, 0.6);
}

.indicator-dot.mode-rrf {
  background: #e6a23c;
  box-shadow: 0 0 10px rgba(230, 162, 60, 0.6);
}

.indicator-dot.mode-chat {
  background: #9c27b0;
  box-shadow: 0 0 10px rgba(156, 39, 176, 0.6);
}

.indicator-dot.mode-websocket {
  background: #409eff;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.6);
}

.indicator-dot.mode-document {
  background: #f56c6c;
  box-shadow: 0 0 10px rgba(245, 108, 108, 0.6);
}

.indicator-text {
  color: white;
  font-size: 13px;
  font-weight: 500;
  flex: 1;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

/* 右侧内容区域 */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 20px;
  min-height: 100vh;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条美化 */
.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
