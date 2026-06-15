import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'
import { useToast } from '../contexts/ToastContext'

function buildRecommendationsParams(filters, pageParam = 0) {
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
  params.set('limit', String(filters.limit || 50))
  params.set('offset', String(pageParam))
  return params
}

export function useRecommendations(filters) {
  const limit = filters.limit || 50

  const query = useInfiniteQuery({
    queryKey: ['recommendations', filters],
    queryFn: async ({ pageParam = 0 }) => {
      const params = buildRecommendationsParams(filters, pageParam)
      const { data } = await client.get(`/recommendations?${params.toString()}`)
      return data
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.offset + lastPage.items.length
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
  })

  const pages = query.data?.pages || []
  const items = pages.flatMap((page) => page.items) || []
  const total = pages[pages.length - 1]?.total || 0
  const hasNextPage = query.hasNextPage
  const fetchNextPage = query.fetchNextPage

  return {
    ...query,
    data: { items, total },
    hasNextPage,
    fetchNextPage,
  }
}

export function useSearch(q, filters = {}) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (filters.category && filters.category !== 'all') {
    if (filters.category === 'animation') {
      params.set('category', 'anime,cartoon')
    } else {
      params.set('category', filters.category)
    }
  }
  if (filters.yearMin) params.set('year_min', filters.yearMin)
  if (filters.yearMax) params.set('year_max', filters.yearMax)
  if (filters.offset) params.set('offset', String(filters.offset))
  if (filters.limit) params.set('limit', String(filters.limit))

  const query = useQuery({
    queryKey: ['search', q, filters],
    queryFn: async () => {
      const { data } = await client.get(`/search?${params.toString()}`)
      return data
    },
    enabled: Boolean(q && q.trim()),
  })

  const data = query.data
  const hasNextPage = data ? data.total > data.offset + data.items.length : false

  return {
    ...query,
    hasNextPage,
    fetchNextPage: () => {},
  }
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

export function useCollectionMissing(collectionId, enabled = true) {
  return useQuery({
    queryKey: ['dashboard', 'collection', collectionId, 'missing'],
    queryFn: async () => {
      const { data } = await client.get(`/dashboard/collections/${collectionId}/missing`)
      return data
    },
    enabled: Boolean(collectionId) && enabled,
  })
}

export function useAddCollectionToRadarr() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: async (collectionId) => {
      const { data } = await client.post(`/dashboard/collections/${collectionId}/add-to-radarr`)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['queue', 'radarr'] })
      const added = data?.added?.length || 0
      const failed = data?.failed?.length || 0
      if (added > 0) {
        addToast({ type: 'success', title: 'Radarr', message: `${added} movie(s) added` })
      }
      if (failed > 0) {
        addToast({ type: 'error', title: 'Radarr', message: `${failed} movie(s) failed` })
      }
      if (added === 0 && failed === 0) {
        addToast({ type: 'info', title: 'Radarr', message: 'No missing movies to add' })
      }
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Radarr', message: err?.response?.data?.detail || 'Failed to add collection' })
    },
  })
}

export function useMediaDetail(mediaId) {
  return useQuery({
    queryKey: ['media', mediaId],
    queryFn: async () => {
      const { data } = await client.get(`/media/${encodeURIComponent(mediaId)}`)
      return data
    },
    enabled: Boolean(mediaId),
  })
}

export function useQueueSonarr(enabled = true) {
  return useQuery({
    queryKey: ['queue', 'sonarr'],
    queryFn: async () => {
      const { data } = await client.get('/queue/sonarr')
      return data
    },
    refetchInterval: 5000,
    enabled,
  })
}

export function useQueueRadarr(enabled = true) {
  return useQuery({
    queryKey: ['queue', 'radarr'],
    queryFn: async () => {
      const { data } = await client.get('/queue/radarr')
      return data
    },
    refetchInterval: 5000,
    enabled,
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

export function useRemoveFromWishlist() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await client.delete(`/queue/wishlist/${id}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      addToast({ type: 'success', title: 'Wishlist', message: 'Item removed' })
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Wishlist', message: err?.response?.data?.detail || 'Failed to remove item' })
    },
  })
}

export function useSendWishlistToRadarr() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await client.post(`/queue/wishlist/${id}/radarr`)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      queryClient.invalidateQueries({ queryKey: ['queue', 'radarr'] })
      addToast({ type: 'success', title: 'Radarr', message: `${data.title || 'Movie'} added` })
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Radarr', message: err?.response?.data?.detail || 'Failed to add movie' })
    },
  })
}

export function useSendWishlistToSonarr() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await client.post(`/queue/wishlist/${id}/sonarr`)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      queryClient.invalidateQueries({ queryKey: ['queue', 'sonarr'] })
      addToast({ type: 'success', title: 'Sonarr', message: `${data.title || 'Series'} added` })
    },
    onError: (err) => {
      addToast({ type: 'error', title: 'Sonarr', message: err?.response?.data?.detail || 'Failed to add series' })
    },
  })
}

function buildWishlistPayload(items) {
  return items.map((item) => ({
    external_id: String(item.tmdb_id || item.anilist_id || item.tvdb_id || ''),
    title: item.title,
    category: item.category,
    poster_url: item.poster_url,
    tmdb_id: item.tmdb_id || null,
    tvdb_id: item.tvdb_id || null,
    anilist_id: item.anilist_id || null,
  }))
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
      const { data } = await client.post('/batch/wishlist', { items: buildWishlistPayload(items) })
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
