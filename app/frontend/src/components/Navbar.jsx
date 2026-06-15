import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Film, Compass, Activity, List, Heart, RotateCcw, Settings as SettingsIcon, LogOut, Sun, Moon } from 'lucide-react'
import { useBatchActions } from '../hooks/useMedia'
import { useTheme } from '../contexts/ThemeContext'
import SearchBar from './SearchBar'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Film },
  { path: '/activity', label: 'Activity', icon: Activity },
  { path: '/discover', label: 'Discover', icon: Compass },
  { path: '/queue', label: 'Queue', icon: List },
  { path: '/wishlist', label: 'Wishlist', icon: Heart },
  { path: '/settings', label: 'Settings', icon: SettingsIcon },
]

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { sync } = useBatchActions()
  const { theme, toggleTheme } = useTheme()
  const isAuthenticated = Boolean(localStorage.getItem('mli_token'))

  const searchQuery = location.pathname === '/discover' ? searchParams.get('q') || '' : ''

  const handleSearchChange = (value) => {
    if (location.pathname !== '/discover') {
      navigate(`/discover?q=${encodeURIComponent(value)}`)
      return
    }
    if (value) {
      setSearchParams({ q: value })
    } else {
      setSearchParams({})
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('mli_token')
    navigate('/login', { replace: true })
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-border">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2.5 group shrink-0">
          <div className="p-1.5 rounded-lg bg-accent/10 group-hover:bg-accent/20 transition-colors">
            <Film className="w-5 h-5 text-accent" />
          </div>
          <span className="font-bold text-lg tracking-tight">MLI</span>
        </Link>

        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-2 sm:px-3 py-2 rounded-lg text-sm font-medium transition-all focus-ring whitespace-nowrap ${
                  isActive
                    ? 'text-accent bg-accent/10'
                    : 'text-secondary hover:text-primary hover:bg-surface-elevated'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            )
          })}
        </div>

        <div className="flex-1 max-w-xs md:max-w-md hidden sm:block">
          <SearchBar
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search titles..."
          />
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-secondary hover:text-primary hover:bg-surface-elevated transition-colors focus-ring"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <button
            onClick={() => sync.mutate()}
            disabled={sync.isPending}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-secondary hover:text-primary hover:bg-surface-elevated transition-colors disabled:opacity-50 focus-ring"
          >
            <RotateCcw className={`w-4 h-4 ${sync.isPending ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>

          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors focus-ring"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          )}
        </div>
      </div>
    </nav>
  )
}
