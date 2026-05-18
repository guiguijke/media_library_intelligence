import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export function usePlexLibraries() {
  return useQuery({
    queryKey: ['plex', 'libraries'],
    queryFn: async () => {
      const { data } = await client.get('/plex/libraries')
      return data
    },
  })
}

export function usePlexMappings() {
  return useQuery({
    queryKey: ['plex', 'mappings'],
    queryFn: async () => {
      const { data } = await client.get('/plex/mappings')
      return data
    },
  })
}

export function useSavePlexMappings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (mappings) => {
      const { data } = await client.post('/plex/mappings', mappings)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plex', 'mappings'] })
    },
  })
}
