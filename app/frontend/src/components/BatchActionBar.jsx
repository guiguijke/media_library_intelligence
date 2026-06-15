import { Film, Tv, Heart, X } from 'lucide-react'
import { useSelection } from '../contexts/SelectionContext'
import { useBatchActions } from '../hooks/useMedia'
import { useMemo } from 'react'

export default function BatchActionBar({ items = [] }) {
  const { selected, clear } = useSelection()
  const { sendToRadarr, sendToSonarr, addToWishlist } = useBatchActions()

  const selectedItems = useMemo(() => {
    return items.filter((item) => selected.has(item.id))
  }, [items, selected])

  const count = selected.size
  if (count === 0) return null

  const estimatedSize = count * 2.5

  const handleRadarr = () => {
    const ids = selectedItems
      .filter((i) => i.category === 'movie' || i.category === 'cartoon')
      .map((i) => i.tmdb_id)
      .filter(Boolean)
    if (ids.length) sendToRadarr.mutate(ids)
  }

  const handleSonarr = () => {
    const ids = selectedItems
      .filter((i) => i.category === 'series' || i.category === 'anime')
      .map((i) => i.tmdb_id)
      .filter(Boolean)
    if (ids.length) sendToSonarr.mutate(ids)
  }

  const handleWishlist = () => {
    const payload = selectedItems.map((i) => ({
      tmdb_id: i.tmdb_id,
      anilist_id: i.anilist_id,
      title: i.title,
      category: i.category,
      poster_url: i.poster_url,
    }))
    if (payload.length) addToWishlist.mutate(payload)
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4 animate-fade-in-up">
      <div className="bg-surface-elevated/95 backdrop-blur-xl border border-border rounded-2xl shadow-2xl px-5 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="px-2.5 py-1 rounded-lg bg-accent text-accent-foreground text-sm font-bold">
            {count}
          </div>
          <span className="text-sm text-secondary">
            {count === 1 ? 'item selected' : 'items selected'}
          </span>
          <span className="text-xs text-muted hidden sm:inline">
            ~{estimatedSize.toFixed(0)} GB estimated
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRadarr}
            disabled={sendToRadarr.isPending}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface text-primary text-sm font-medium border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 focus-ring"
          >
            <Film className="w-4 h-4" />
            <span className="hidden sm:inline">Radarr</span>
          </button>
          <button
            onClick={handleSonarr}
            disabled={sendToSonarr.isPending}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface text-primary text-sm font-medium border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 focus-ring"
          >
            <Tv className="w-4 h-4" />
            <span className="hidden sm:inline">Sonarr</span>
          </button>
          <button
            onClick={handleWishlist}
            disabled={addToWishlist.isPending}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface text-primary text-sm font-medium border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 focus-ring"
          >
            <Heart className="w-4 h-4" />
            <span className="hidden sm:inline">Wishlist</span>
          </button>
          <button
            onClick={clear}
            className="p-2 rounded-lg text-secondary hover:text-primary hover:bg-surface transition-colors focus-ring"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
