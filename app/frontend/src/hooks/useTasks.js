import { useQuery } from '@tanstack/react-query'
import client from '../api/client'

export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const { data } = await client.get('/tasks')
      return data
    },
    refetchInterval: 2000,
  })
}
