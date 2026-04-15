// d:\saigon-tennis-tour\frontend\src\services\courtService.js
import { apiClient } from './apiClient'

export const courtService = {
  async getAll(params) {
    return apiClient.get('/api/courts', { params })
  },
  async create(data) {
    return apiClient.post('/api/courts', data)
  },
  async update(id, data) {
    return apiClient.put(`/api/courts/${id}`, data)
  },
  async delete(id) {
    return apiClient.request(`/api/courts/${id}`, { method: 'DELETE' })
  }
}
