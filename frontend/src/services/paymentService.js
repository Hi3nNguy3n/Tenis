// d:\saigon-tennis-tour\frontend\src\services\paymentService.js
import { apiClient } from './apiClient'

export const paymentService = {
  async getAll(params) {
    return apiClient.get('/api/payments/list', { params })
  }
}
