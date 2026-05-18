import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export function useRecommendations(filters) {
  const params = new URLSearchParams()
  if (filters.category && filters.category !== 'all') {
    if (filters.category === 'animation') {
      params.set('category', 'anime,cartoon')
    } else {
      params.set('category', filters.category)
    }
  }
  if (filters.genre) params.set('genre', filters.genre)
  if (filters.yearMin) params.set('year_min', filters.yearMin)
  if (filters.yearMax) params.set('year_max', filters.yearMax)
  if (filters.ratingMin) params.set('rating_min', filters.ratingMin)
  if (filters.hideInPlex) params.set('hide_in_plex', 'true')
  if (filters.hideMonitored) params.set('hide_monitored', 'true')

  return useQuery({
    queryKey: ['recommendations', filters],
    queryFn: async () => {
      const { data } = await client.get(`/recommendations?${params.toString()}`)
      return data
    },
  })
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const { data } = await client.get('/dashboard/stats')
      return data
    },
  })
}

export function useQueueSonarr() {
  return useQuery({
    queryKey: ['queue', 'sonarr'],
    queryFn: async () => {
      const { data } = await client.get('/queue/sonarr')
      return data
    },
  })
}

export function useQueueRadarr() {
  return useQuery({
    queryKey: ['queue', 'radarr'],
    queryFn: async () => {
      const { data } = await client.get('/queue/radarr')
      return data
    },
  })
}

export function useWishlist() {
  return useQuery({
    queryKey: ['wishlist'],
    queryFn: async () => {
      const { data } = await client.get('/wishlist')
      return data
    },
  })
}

export function useBatchActions() {
  const queryClient = useQueryClient()

  const sendToRadarr = useMutation({
    mutationFn: async (ids) => {
      const { data } = await client.post('/batch/radarr', { ids })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue', 'radarr'] })
    },
  })

  const sendToSonarr = useMutation({
    mutationFn: async (ids) => {
      const { data } = await client.post('/batch/sonarr', { ids })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue', 'sonarr'] })
    },
  })

  const addToWishlist = useMutation({
    mutationFn: async (items) => {
      const { data } = await client.post('/batch/wishlist', { items })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
    },
  })

  const sync = useMutation({
    mutationFn: async () => {
      const { data } = await client.post('/sync/trigger')
      return data
    },
  })

  return { sendToRadarr, sendToSonarr, addToWishlist, sync }
}
