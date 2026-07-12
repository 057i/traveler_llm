/**
 * Documents API
 */
import request from '@/utils/request'

/**
 * Get documents list
 */
export function listDocuments(params) {
  return request({
    url: '/api/documents/list',
    method: 'get',
    params
  })
}

/**
 * Get document statistics
 */
export function getStatistics() {
  return request({
    url: '/api/documents/statistics',
    method: 'get'
  })
}

/**
 * Delete document
 */
export function deleteDocument(docId) {
  return request({
    url: `/api/documents/${docId}`,
    method: 'delete'
  })
}

/**
 * Get document detail
 */
export function getDocument(docId) {
  return request({
    url: `/api/documents/${docId}`,
    method: 'get'
  })
}
