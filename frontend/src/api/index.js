import axios from 'axios'

// 根据环境变量决定API基础URL
// 生产环境使用环境变量，开发环境使用相对路径（通过Vite代理）
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// WebSocket基础URL（用于AI团队推荐）
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ||
  (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// RAG 推荐
export const ragSearch = (params) => {
  return api.get('/rag/search', { params })
}

// GraphRAG 推荐
export const graphRagSearch = (params) => {
  return api.get('/graph_rag/search', { params })
}

// 综合搜索
export const integratedSearch = (data) => {
  return api.post('/integrated-search/search', data)
}

// 综合搜索（带多样性）
export const integratedSearchWithDiversity = (data, params) => {
  return api.post('/integrated-search/search_with_diversity', data, { params })
}

// Rerank 重排序
export const rerank = (data) => {
  return api.post('/rerank/rerank', data)
}

// Rerank 带解释
export const rerankWithExplanation = (data) => {
  return api.post('/rerank/rerank_with_explanation', data)
}

// SSE 推荐（使用POST + fetch处理SSE流）
export const createSSERecommend = async (params) => {
  // 过滤掉 null、undefined 和空字符串
  const cleanParams = {}
  Object.keys(params).forEach(key => {
    if (params[key] != null && params[key] !== '') {
      cleanParams[key] = params[key]
    }
  })

  // 使用POST方法，使用baseURL
  const url = `${baseURL}/ai-recommend/stream`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(cleanParams)
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.body.getReader()
}

// WebSocket 连接
export const createWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/api/ai-team-recommend/ws`)
}

// 智能聊天推荐
export const chatRecommend = (data) => {
  return api.post('/chat/recommend', data)
}

// ==================== AI推荐 - Redis缓存相关 ====================

// 获取聊天历史
export const getChatHistory = (sessionId, limit = 50) => {
  return api.get(`/ai-recommend/history/${sessionId}`, { params: { limit } })
}

// 获取实时进度
export const getProgress = (sessionId) => {
  return api.get(`/ai-recommend/progress/${sessionId}`)
}

// 清除聊天历史
export const clearChatHistory = (sessionId) => {
  return api.delete(`/ai-recommend/history/${sessionId}`)
}

// 健康检查
export const healthCheck = () => {
  return api.get('/ai-recommend/health')
}

// ==================== AI团队推荐历史记录 ====================

// 获取AI团队推荐聊天历史
export const getTeamChatHistory = (sessionId, limit = 50) => {
  return api.get(`/team-recommend-ws/history/${sessionId}`, { params: { limit } })
}

// 清除AI团队推荐聊天历史
export const clearTeamChatHistory = (sessionId) => {
  return api.delete(`/team-recommend-ws/history/${sessionId}`)
}

// ==================== 文档管理 API ====================

// 获取文档列表
export const listDocuments = (params) => {
  return api.get('/documents/list', { params })
}

// 删除文档
export const deleteDocument = (documentId) => {
  return api.delete(`/documents/${documentId}`)
}

// 获取文档详情
export const getDocumentDetail = (documentId) => {
  return api.get(`/documents/${documentId}`)
}

// 重新处理文档
export const reprocessDocument = (documentId) => {
  return api.post(`/documents/${documentId}/reprocess`)
}

// 获取统计数据
export const getStatistics = () => {
  return api.get('/documents/statistics')
}

export default api
