import { describe, it, expect, beforeAll, afterAll, afterEach, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import client from '../api/client'

const server = setupServer()

describe('client 401 interceptor', () => {
  beforeAll(() => server.listen())
  afterEach(() => {
    server.resetHandlers()
    localStorage.clear()
  })
  afterAll(() => server.close())

  beforeEach(() => {
    const originalLocation = window.location
    delete window.location
    window.location = { ...originalLocation, assign: vi.fn(), pathname: '/discover' }
  })

  it('redirige vers /login sur une réponse 401', async () => {
    localStorage.setItem('mli_token', 'expired-token')
    server.use(
      http.get('/api/recommendations', () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      })
    )

    await expect(client.get('/recommendations')).rejects.toThrow()

    expect(localStorage.getItem('mli_token')).toBeNull()
    expect(window.location.assign).toHaveBeenCalledWith('/login')
  })

  it('ne redirige pas si on est déjà sur /login', async () => {
    window.location.pathname = '/login'
    server.use(
      http.post('/api/auth/login', () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      })
    )

    await expect(client.post('/auth/login', { username: 'x', password: 'y' })).rejects.toThrow()

    expect(window.location.assign).not.toHaveBeenCalled()
  })
})
