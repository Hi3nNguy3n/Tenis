// d:\saigon-tennis-tour\frontend\src\services\playerService.js
import { apiClient } from './apiClient'

export const playerService = {
  async getAll(params) {
    return apiClient.get('/api/players/list', { params })
  },
  async update(id, data) {
    return apiClient.put(`/api/players/${id}`, data)
  }
}
