import { defineStore } from 'pinia'
import { apiClient } from '../services/apiClient'

export const useTournamentStore = defineStore('tournament', {
  state: () => ({
    tournaments: [],
    currentTournament: null,
    myRegistrations: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchTournaments(params = {}) {
      this.loading = true
      try {
        const query = new URLSearchParams(params).toString()
        this.tournaments = await apiClient.get(query ? `/api/tournaments/?${query}` : '/api/tournaments/')
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async fetchTournamentById(id) {
      this.loading = true
      try {
        this.currentTournament = await apiClient.get(`/api/tournaments/${id}`)
        return this.currentTournament
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.loading = false
      }
    },

    async registerForTournament(tournamentId, data) {
      this.loading = true
      try {
        // Assume API endpoint POST /api/registrations/
        return await apiClient.post('/api/registrations/', {
          tournament_id: tournamentId,
          ...data
        })
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchMyRegistrations() {
      this.loading = true
      try {
        // Backend endpoint: GET /api/registrations/my-registrations
        this.myRegistrations = await apiClient.get('/api/registrations/my-registrations')
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async confirmRegistrationPayment(registrationId) {
      this.loading = true
      try {
        // Backend endpoint: POST /api/registrations/{id}/confirm-payment
        return await apiClient.post(`/api/registrations/${registrationId}/confirm-payment`)
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.loading = false
      }
    },

    async cancelRegistration(registrationId) {
      this.loading = true
      try {
        // Backend endpoint: POST /api/registrations/{id}/cancel
        const data = await apiClient.post(`/api/registrations/${registrationId}/cancel`)
        await this.fetchMyRegistrations() // Refresh the list
        return data
      } catch (err) {
        this.error = err.message
        throw err
      } finally {
        this.loading = false
      }
    }
  }
})
