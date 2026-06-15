import { useQuery } from '@tanstack/react-query'
import client from '../api/client'

export function useNowPlaying() {
  return useQuery({
    queryKey: ['activity', 'now'],
    queryFn: async () => {
      const { data } = await client.get('/activity/now')
      return data
    },
    refetchInterval: 5000,
  })
}

export function useWatchHistory(length = 100) {
  return useQuery({
    queryKey: ['activity', 'history', length],
    queryFn: async () => {
      const { data } = await client.get(`/activity/history?length=${length}`)
      return data
    },
  })
}

export function useUsers() {
  return useQuery({
    queryKey: ['activity', 'users'],
    queryFn: async () => {
      const { data } = await client.get('/activity/users')
      return data?.users || []
    },
  })
}

export function useUsersStats() {
  return useQuery({
    queryKey: ['activity', 'users', 'stats'],
    queryFn: async () => {
      const { data } = await client.get('/activity/users/stats')
      return data
    },
  })
}

export function useTopWatched() {
  return useQuery({
    queryKey: ['activity', 'top'],
    queryFn: async () => {
      const { data } = await client.get('/activity/top')
      return data
    },
  })
}
