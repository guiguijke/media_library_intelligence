import { SlidersHorizontal, Users } from 'lucide-react'
import { useUsers } from '../hooks/useActivity'

const categories = [
  { key: 'all', label: 'All' },
  { key: 'movie', label: 'Movies' },
  { key: 'series', label: 'TV Shows' },
  { key: 'anime', label: 'Anime' },
  { key: 'animation', label: 'Animation' },
]

const genres = [
  { id: 28, name: 'Action' },
  { id: 12, name: 'Adventure' },
  { id: 16, name: 'Animation' },
  { id: 35, name: 'Comedy' },
  { id: 80, name: 'Crime' },
  { id: 99, name: 'Documentary' },
  { id: 18, name: 'Drama' },
  { id: 10751, name: 'Family' },
  { id: 14, name: 'Fantasy' },
  { id: 36, name: 'History' },
  { id: 27, name: 'Horror' },
  { id: 10402, name: 'Music' },
  { id: 9648, name: 'Mystery' },
  { id: 10749, name: 'Romance' },
  { id: 878, name: 'Science Fiction' },
  { id: 53, name: 'Thriller' },
  { id: 10752, name: 'War' },
  { id: 37, name: 'Western' },
]

function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer select-none">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-5 rounded-full transition-colors focus-ring ${
          checked ? 'bg-accent' : 'bg-surface-elevated border border-border'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-3.5 h-3.5 rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-0'
          }`}
        />
      </button>
      <span className="text-xs text-secondary">{label}</span>
    </label>
  )
}

export default function FilterBar({ filters, onChange }) {
  const update = (key, value) => {
    onChange({ ...filters, [key]: value })
  }
  const { data: users } = useUsers()

  return (
    <div className="space-y-4 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => {
          const active = filters.category === cat.key
          return (
            <button
              key={cat.key}
              onClick={() => update('category', cat.key)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all focus-ring ${
                active
                  ? 'bg-accent text-accent-foreground shadow-sm'
                  : 'bg-surface-elevated text-secondary hover:text-primary hover:bg-surface-hover'
              }`}
            >
              {cat.label}
            </button>
          )
        })}
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-secondary" />
          <span className="text-sm text-secondary font-medium">Filters</span>
        </div>

        {/* User */}
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-secondary" />
          <select
            value={filters.userId || ''}
            onChange={(e) => update('userId', e.target.value || undefined)}
            className="bg-surface-elevated text-primary text-sm rounded-lg px-3 py-1.5 border border-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
          >
            <option value="">All users</option>
            {(users || []).map((u) => (
              <option key={u.user_id} value={u.user_id}>{u.username}</option>
            ))}
          </select>
        </div>

        {/* Genre */}
        <select
          value={filters.genre || ''}
          onChange={(e) => update('genre', e.target.value ? parseInt(e.target.value) : undefined)}
          className="bg-surface-elevated text-primary text-sm rounded-lg px-3 py-1.5 border border-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
        >
          <option value="">All genres</option>
          {genres.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>

        {/* Year range */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondary">Year</span>
          <input
            type="number"
            placeholder="Min"
            value={filters.yearMin || ''}
            onChange={(e) => update('yearMin', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-20 bg-surface-elevated text-primary text-sm rounded-lg px-2 py-1.5 border border-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
          />
          <span className="text-secondary">-</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.yearMax || ''}
            onChange={(e) => update('yearMax', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-20 bg-surface-elevated text-primary text-sm rounded-lg px-2 py-1.5 border border-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
          />
        </div>

        {/* Rating min */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondary">Min Rating</span>
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            placeholder="0"
            value={filters.ratingMin || ''}
            onChange={(e) => update('ratingMin', e.target.value ? parseFloat(e.target.value) : undefined)}
            className="w-16 bg-surface-elevated text-primary text-sm rounded-lg px-2 py-1.5 border border-border focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
          />
        </div>

        {/* Toggles */}
        <Toggle checked={filters.hideInPlex} onChange={(v) => update('hideInPlex', v)} label="Hide Plex" />
        <Toggle checked={filters.hideMonitored} onChange={(v) => update('hideMonitored', v)} label="Hide monitored" />
      </div>
    </div>
  )
}
