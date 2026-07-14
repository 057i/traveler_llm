import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import AIRecommend from '@/views/AIRecommend.vue'
import AITeamRecommend from '@/views/AITeamRecommend.vue'
import Recommend from '@/views/Recommend.vue'
import DocumentManager from '@/views/DocumentManager.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/recommend',
    children: [
      // 推荐模式
      {
        path: 'recommend-mode',
        name: 'RecommendMode',
        meta: {
          title: '推荐模式',
          icon: 'Grid',
          hideInMenu: false,
          isGroup: true, // 标记为菜单组
        },
        children: [

          {
            path: '/ai_recommend',
            name: 'AIRecommend',
            component: AIRecommend,
            meta: {
              title: 'AI推荐',
              icon: 'ChatLineSquare',
              hideInMenu: false,
              description: '基于LangGraph的智能推荐'
            }
          },
          {
            path: '/ai_team_recommend',
            name: 'AITeamRecommend',
            component: AITeamRecommend,
            meta: {
              title: 'AI团队推荐',
              icon: 'ChatDotRound',
              hideInMenu: false,
              description: '多智能体协作推荐'
            }
          },
          {
            path: '/recommend',
            name: 'Recommend',
            component: Recommend,
            meta: {
              title: '综合搜索',
              icon: 'Connection',
              hideInMenu: false,
              description: 'RAG多路检索 + 结构化筛选'
            }
          },
        ]
      },
      // 文档管理
      {
        path: '/documents',
        name: 'DocumentManager',
        component: DocumentManager,
        meta: {
          title: 'RAG文档管理',
          icon: 'Document',
          hideInMenu: false,
          description: '管理知识库文档'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能旅行推荐系统`
  }
  next()
})

export default router
