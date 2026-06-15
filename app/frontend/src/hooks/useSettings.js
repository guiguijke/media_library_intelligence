import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data } = await client.get('/settings')
      return data
    },
  })
}

export function useRawSettings() {
  return useQuery({
    queryKey: ['settings', 'raw'],
    queryFn: async () => {
      const { data } = await client.get('/settings')
      return data
    },
  })
}

export function useSaveSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (values) => {
      const payload = {}
      values.forEach(item => {
        payload[item.key] = item.value
      })
      const { data } = await client.put('/settings', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}
