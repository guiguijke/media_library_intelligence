import { useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export function useCancelTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (taskId) => {
      const { data } = await client.post(`/tasks/${taskId}/cancel`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
