// d:\saigon-tennis-tour\frontend\src\services\playerService.js
import { apiClient } from './apiClient'

export const playerService = {
  async getAll(params) {
    return apiClient.get('/api/players/list', { params })
  },
  async update(id, data) {
    return apiClient.put(`/api/players/${id}`, data)
  },
  async getRankings(params) {
    return apiClient.get('/api/players/rankings', { params })
  },
  async getMatchHistory() {
    return apiClient.get('/api/players/me/history')
  },
  async getMatchHistoryAdmin(playerId) {
    return apiClient.get(`/api/players/${playerId}/history`)
  },
  async getTournamentsAdmin(playerId) {
    return apiClient.get(`/api/players/${playerId}/tournaments`)
  },
  async updateMe(data) {
    return apiClient.put('/api/players/me', data)
  },
  async uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    // Note: apiClient.post handles JSON by default, for multipart/form-data we pass includeJson: false
    return apiClient.post('/api/players/me/avatar', formData, { includeJson: false })
  },
  async delete(id) {
    return apiClient.request(`/api/players/${id}`, { method: 'DELETE' })
  },
  async getDeleted(params) {
    return apiClient.get('/api/players/deleted', { params })
  },
  async restore(id) {
    return apiClient.post(`/api/players/${id}/restore`)
  }
}
