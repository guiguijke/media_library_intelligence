import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'
import { useToast } from '../contexts/ToastContext'

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
  if (filters.userId) params.set('user_id', filters.userId)

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

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await client.get('/activity/users')
      return data?.users || []
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
    refetchInterval: 5000,
  })
}

export function useQueueRadarr() {
  return useQuery({
    queryKey: ['queue', 'radarr'],
    queryFn: async () => {
      const { data } = await client.get('/queue/radarr')
      return data
    },
    refetchInterval: 5000,
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
  const { addToast } = useToast()

  const sendToRadarr = useMutation({
    mutationFn: async (ids) => {
      const { data } = await client.post('/batch/radarr', { ids })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['queue', 'radarr'] })
      const added = data?.added?.length || 0
      const failed = data?.failed?.length || 0
      if (added > 0) {
        addToast({ type: 'success', title: 'Radarr', message: `${added} movie(s) added` })
      }
      if (failed > 0) {
        addToast({ type: 'error', title: 'Radarr', message: `${failed} movie(s) failed` })
      }
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Radarr', message: err?.response?.data?.detail || 'Failed to add movies' })
    },
  })

  const sendToSonarr = useMutation({
    mutationFn: async (ids) => {
      const { data } = await client.post('/batch/sonarr', { ids })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['queue', 'sonarr'] })
      const added = data?.added?.length || 0
      const failed = data?.failed?.length || 0
      if (added > 0) {
        addToast({ type: 'success', title: 'Sonarr', message: `${added} series added` })
      }
      if (failed > 0) {
        addToast({ type: 'error', title: 'Sonarr', message: `${failed} series failed` })
      }
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Sonarr', message: err?.response?.data?.detail || 'Failed to add series' })
    },
  })

  const addToWishlist = useMutation({
    mutationFn: async (items) => {
      const { data } = await client.post('/batch/wishlist', { items })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      const count = data?.added || data?.count || 0
      addToast({ type: 'success', title: 'Wishlist', message: `${count} item(s) added` })
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Wishlist', message: err?.response?.data?.detail || 'Failed to add items' })
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
