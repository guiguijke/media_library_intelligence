import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import Login from '../pages/Login'

const server = setupServer()

function renderLogin() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        initialEntries={['/login']}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div data-testid="dashboard">Dashboard</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Login', () => {
  beforeAll(() => server.listen())
  afterEach(() => {
    server.resetHandlers()
    localStorage.clear()
  })
  afterAll(() => server.close())

  it('soumet le formulaire et redirige vers le dashboard en cas de succès', async () => {
    server.use(
      http.post('/api/auth/login', async () => {
        return HttpResponse.json({ access_token: 'fake-token' })
      })
    )

    renderLogin()

    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(localStorage.getItem('mli_token')).toBe('fake-token')
    })
    expect(screen.getByTestId('dashboard')).toBeInTheDocument()
  })

  it('affiche un message d’erreur si le login échoue', async () => {
    server.use(
      http.post('/api/auth/login', async () => {
        return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
      })
    )

    renderLogin()

    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument()
    expect(localStorage.getItem('mli_token')).toBeNull()
  })
})
