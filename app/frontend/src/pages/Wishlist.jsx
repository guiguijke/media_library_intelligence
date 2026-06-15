import { useState } from 'react'
import { Heart, Trash2, Compass, ImageOff, Monitor, Film } from 'lucide-react'
import {
  useWishlist,
  useRemoveFromWishlist,
  useSendWishlistToRadarr,
  useSendWishlistToSonarr,
} from '../hooks/useMedia'
import MediaModal from '../components/MediaModal'
import EmptyState from '../components/EmptyState'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { Link } from 'react-router-dom'

function ImageWithFallback({ src, alt, className }) {
  const [error, setError] = useState(false)
  if (!src || error) {
    return (
      <div className={`bg-surface-elevated flex items-center justify-center ${className}`}>
        <ImageOff className="w-8 h-8 text-muted" />
      </div>
    )
  }
  return <img src={src} alt={alt} className={className} onError={() => setError(true)} />
}

const isMovieCategory = (category) => category === 'movie' || category === 'cartoon'
const isSeriesCategory = (category) => category === 'series' || category === 'anime'

export default function Wishlist() {
  const { data, isLoading } = useWishlist()
  const removeFromWishlist = useRemoveFromWishlist()
  const sendToRadarr = useSendWishlistToRadarr()
  const sendToSonarr = useSendWishlistToSonarr()
  const [selectedMedia, setSelectedMedia] = useState(null)

  const items = data?.items || []

  const handleRemove = (item) => {
    if (!item.id) return
    removeFromWishlist.mutate(item.id)
  }

  const handleAddToRadarr = (e, item) => {
    e.stopPropagation()
    if (!item.id) return
    sendToRadarr.mutate(item.id)
  }

  const handleAddToSonarr = (e, item) => {
    e.stopPropagation()
    if (!item.id) return
    sendToSonarr.mutate(item.id)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-2xl font-bold">Wishlist</h1>
        <p className="text-secondary mt-1">Items to add later</p>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={8} />
      ) : items.length === 0 ? (
        <div className="bg-surface border border-border rounded-xl">
          <EmptyState
            icon={Heart}
            title="Your wishlist is empty"
            description="Save movies and shows you want to watch later."
            action={
              <Link
                to="/discover"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-accent text-accent-foreground hover:bg-accent/90 transition-colors"
              >
                <Compass className="w-4 h-4" />
                Discover content
              </Link>
            }
          />
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 stagger-children">
          {items.map((item, idx) => {
            const posterUrl = item.poster_url
              ? (item.poster_url.startsWith('http') ? item.poster_url : `https://image.tmdb.org/t/p/w500${item.poster_url}`)
              : null

            return (
              <div
                key={item.id || item.tmdb_id}
                className="group relative rounded-xl overflow-hidden bg-surface cursor-pointer card-glow animate-fade-in-up"
                style={{ animationDelay: `${idx * 40}ms` }}
                onClick={() => setSelectedMedia(item)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setSelectedMedia(item)
                  }
                }}
              >
                <div className="aspect-[2/3] relative bg-surface-elevated">
                  <ImageWithFallback
                    src={posterUrl}
                    alt={item.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                  <div className="absolute inset-0 flex flex-col justify-end p-3 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-y-2 group-hover:translate-y-0">
                    <h3 className="font-semibold text-sm line-clamp-2 text-white drop-shadow-md">{item.title}</h3>
                  </div>
                  <div className="absolute top-2 right-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all">
                    {isMovieCategory(item.category) && (
                      <button
                        onClick={(e) => handleAddToRadarr(e, item)}
                        disabled={sendToRadarr.isPending}
                        className="p-1.5 rounded-full bg-black/50 text-white hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50 focus-ring"
                        title="Add to Radarr"
                      >
                        <Film className="w-4 h-4" />
                      </button>
                    )}
                    {isSeriesCategory(item.category) && (
                      <button
                        onClick={(e) => handleAddToSonarr(e, item)}
                        disabled={sendToSonarr.isPending}
                        className="p-1.5 rounded-full bg-black/50 text-white hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50 focus-ring"
                        title="Add to Sonarr"
                      >
                        <Monitor className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRemove(item)
                      }}
                      disabled={removeFromWishlist.isPending}
                      className="p-1.5 rounded-full bg-black/50 text-white hover:bg-red-500/80 transition-all disabled:opacity-50 focus-ring"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {selectedMedia && (
        <MediaModal media={selectedMedia} onClose={() => setSelectedMedia(null)} />
      )}
    </div>
  )
}
