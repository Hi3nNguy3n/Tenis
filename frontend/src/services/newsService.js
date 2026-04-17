import apiClient from './apiClient'

export const newsService = {
  getAllPosts(params = {}) {
    const searchParams = new URLSearchParams()
    if (params.skip) searchParams.append('skip', params.skip)
    if (params.limit) searchParams.append('limit', params.limit)
    if (params.search) searchParams.append('search', params.search)
    if (params.category) searchParams.append('category', params.category)

    const query = searchParams.toString()
    return apiClient.get(`/api/news?${query}`)
  },

  getPost(slugOrId) {
    return apiClient.get(`/api/news/${slugOrId}`)
  }
}

export default newsService
