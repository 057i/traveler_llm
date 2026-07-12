/**
 * Axios request wrapper
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// Create axios instance
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000
})

// Request interceptor
service.interceptors.request.use(
  config => {
    // Add custom headers here if needed
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  response => {
    const res = response.data
    return res
  },
  error => {
    console.error('Response error:', error)

    let message = '请求失败'

    if (error.response) {
      const status = error.response.status

      switch (status) {
        case 400:
          message = error.response.data.detail || '请求参数错误'
          break
        case 401:
          message = '未授权，请登录'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = error.response.data.detail || '服务器内部错误'
          break
        default:
          message = error.response.data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      message = '无法连接到服务器'
    } else {
      message = error.message
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
