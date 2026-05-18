import { SlidersHorizontal } from 'lucide-react'

const categories = [
  { key: 'all', label: 'All' },
  { key: 'movie', label: 'Movies' },
  { key: 'series', label: 'TV Shows' },
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

export default function FilterBar({ filters, onChange }) {
  const update = (key, value) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <div className="space-y-4">
      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => {
          const active = filters.category === cat.key
          return (
            <button
              key={cat.key}
              onClick={() => update('category', cat.key)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                active
                  ? 'bg-accent text-background'
                  : 'bg-surface-elevated text-secondary hover:text-primary'
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

        {/* Genre */}
        <select
          value={filters.genre || ''}
          onChange={(e) => update('genre', e.target.value ? parseInt(e.target.value) : undefined)}
          className="bg-surface-elevated text-primary text-sm rounded-md px-3 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-accent"
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
            className="w-20 bg-surface-elevated text-primary text-sm rounded-md px-2 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <span className="text-secondary">-</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.yearMax || ''}
            onChange={(e) => update('yearMax', e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-20 bg-surface-elevated text-primary text-sm rounded-md px-2 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-accent"
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
            className="w-16 bg-surface-elevated text-primary text-sm rounded-md px-2 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        {/* Toggles */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <div
            className={`w-9 h-5 rounded-full relative transition-colors ${
              filters.hideInPlex ? 'bg-accent' : 'bg-surface-elevated border border-border'
            }`}
            onClick={() => update('hideInPlex', !filters.hideInPlex)}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                filters.hideInPlex ? 'translate-x-4' : 'translate-x-0.5'
              }`}
            />
          </div>
          <span className="text-xs text-secondary">Hide Plex</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <div
            className={`w-9 h-5 rounded-full relative transition-colors ${
              filters.hideMonitored ? 'bg-accent' : 'bg-surface-elevated border border-border'
            }`}
            onClick={() => update('hideMonitored', !filters.hideMonitored)}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                filters.hideMonitored ? 'translate-x-4' : 'translate-x-0.5'
              }`}
            />
          </div>
          <span className="text-xs text-secondary">Hide monitored</span>
        </label>
      </div>
    </div>
  )
}
