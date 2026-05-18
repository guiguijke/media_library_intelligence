import { Link, useLocation } from 'react-router-dom'
import { Film, Compass, Activity, List, Heart, RotateCcw, Settings as SettingsIcon } from 'lucide-react'
import { useBatchActions } from '../hooks/useMedia'

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
  const { sync } = useBatchActions()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/90 backdrop-blur border-b border-border">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Film className="w-6 h-6 text-accent" />
          <span className="font-bold text-lg tracking-tight">MLI</span>
        </Link>

        <div className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
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

        <button
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
          className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-secondary hover:text-primary hover:bg-surface-elevated transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-4 h-4 ${sync.isPending ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Sync</span>
        </button>
      </div>
    </nav>
  )
}
