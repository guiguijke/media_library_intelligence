import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Film, Loader2 } from 'lucide-react'
import client from '../api/client'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await client.post('/auth/login', {
        username,
        password,
      })
      const { access_token } = response.data
      localStorage.setItem('mli_token', access_token)
      navigate('/', { replace: true })
    } catch (err) {
      const message = err.response?.data?.detail || 'Invalid credentials or server error.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 animate-fade-in-up">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center">
          <div className="p-3 rounded-2xl bg-accent/10 animate-pulse-glow">
            <Film className="w-10 h-10 text-accent" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-primary">Media Library Intelligence</h1>
          <p className="mt-1 text-sm text-secondary">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 bg-surface border border-border rounded-2xl p-8 shadow-lg">
          <div className="space-y-2">
            <label htmlFor="username" className="block text-sm font-medium text-primary">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
              placeholder="Enter your username"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-primary">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
              placeholder="Enter your password"
            />
          </div>

          {error && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent text-accent-foreground font-medium hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Signing in…
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
