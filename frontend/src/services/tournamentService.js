// d:\saigon-tennis-tour\frontend\src\services\tournamentService.js
import { apiClient } from './apiClient'

export const tournamentService = {
  async getAll(params) {
    return apiClient.get('/api/tournaments', { params })
  },
  async getById(id) {
    return apiClient.get(`/api/tournaments/${id}`)
  },
  async create(data) {
    return apiClient.post('/api/tournaments', data)
  },
  async update(id, data) {
    return apiClient.put(`/api/tournaments/${id}`, data)
  },
  async delete(id) {
    return apiClient.request(`/api/tournaments/${id}`, { method: 'DELETE' })
  },
  async getStats() {
    return apiClient.get('/api/tournaments/summary/stats')
  },
  async getMatches(tournamentId) {
    return apiClient.get(`/api/tournaments/${tournamentId}/matches`)
  },
  async generateDraw(tournamentId) {
    return apiClient.post(`/api/tournaments/${tournamentId}/generate-draw`)
  },
  async getPublicBracket(tournamentId) {
    return apiClient.get(`/api/tournaments/${tournamentId}/public-bracket`)
  }
}
