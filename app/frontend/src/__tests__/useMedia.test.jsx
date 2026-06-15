import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { useRecommendations } from '../hooks/useMedia'

const server = setupServer()

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useRecommendations', () => {
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  it('récupère les recommandations en fonction des filtres', async () => {
    const mockData = {
      items: [
        { id: 1, title: 'Inception', category: 'movie' },
        { id: 2, title: 'Attack on Titan', category: 'anime' },
      ],
      total: 2,
    }

    server.use(
      http.get('/api/recommendations', ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('category')).toBe('movie')
        expect(url.searchParams.get('rating_min')).toBe('7')
        return HttpResponse.json(mockData)
      })
    )

    const { result } = renderHook(
      () => useRecommendations({ category: 'movie', ratingMin: 7 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockData)
  })

  it('mappe la catégorie animation vers anime,cartoon', async () => {
    server.use(
      http.get('/api/recommendations', ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('category')).toBe('anime,cartoon')
        return HttpResponse.json({ items: [], total: 0 })
      })
    )

    const { result } = renderHook(
      () => useRecommendations({ category: 'animation' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({ items: [], total: 0 })
  })
})
