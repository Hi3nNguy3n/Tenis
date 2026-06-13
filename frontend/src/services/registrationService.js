// d:\saigon-tennis-tour\frontend\src\services\registrationService.js
import { apiClient } from './apiClient'

export const registrationService = {
  async getAll(params) {
    return apiClient.get('/api/registrations/', { params })
  },
  async confirm(id) {
    return apiClient.post(`/api/registrations/${id}/confirm-payment`)
  },
  async cancel(id) {
    return apiClient.post(`/api/registrations/${id}/cancel`)
  },
  async checkIn(id) {
    return apiClient.post(`/api/registrations/${id}/check-in`)
  }
}
