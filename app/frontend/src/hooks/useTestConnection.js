import { useMutation } from '@tanstack/react-query'
import client from '../api/client'

export function useTestConnection() {
  return useMutation({
    mutationFn: async (service) => {
      const { data } = await client.get(`/test/${service}`)
      return data
    },
  })
}
