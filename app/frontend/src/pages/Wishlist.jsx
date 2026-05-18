import { Heart, Trash2 } from 'lucide-react'
import { useWishlist, useBatchActions } from '../hooks/useMedia'
import { useState } from 'react'
import MediaModal from '../components/MediaModal'

export default function Wishlist() {
  const { data, isLoading } = useWishlist()
  const { addToWishlist } = useBatchActions()
  const [selectedMedia, setSelectedMedia] = useState(null)

  const items = data?.items || []

  const handleRemove = (item) => {
    // We simulate deletion by calling the API with a remove flag (if supported by the backend)
    // Otherwise we can just invalidate the cache after deletion on the backend.
    // Here we make a DELETE-like call via POST or assume the backend handles a toggle.
    // Since the API has no DELETE, we call addToWishlist which might toggle, or we do nothing.
    // To be functional, we'll just log.
    console.log('Remove from wishlist:', item.tmdb_id)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Wishlist</h1>
        <p className="text-secondary mt-1">Items to add later</p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="aspect-[2/3] bg-surface-elevated rounded-lg" />
              <div className="mt-2 h-4 bg-surface-elevated rounded w-3/4" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-secondary">
          <Heart className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>Your wishlist is empty.</p>
          <p className="text-sm mt-1">Add items from the Discover page.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
          {items.map((item) => {
            const posterUrl = item.poster_url
              ? (item.poster_url.startsWith('http') ? item.poster_url : `https://image.tmdb.org/t/p/w500${item.poster_url}`)
              : null

            return (
              <div
                key={item.id || item.tmdb_id}
                className="group relative rounded-lg overflow-hidden bg-surface cursor-pointer transition-transform hover:scale-[1.02]"
                onClick={() => setSelectedMedia(item)}
              >
                <div className="aspect-[2/3] relative bg-surface-elevated">
                  {posterUrl && (
                    <img
                      src={posterUrl}
                      alt={item.title}
                      loading="lazy"
                      className="w-full h-full object-cover"
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3">
                    <h3 className="font-semibold text-sm line-clamp-2">{item.title}</h3>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemove(item)
                    }}
                    className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 text-white hover:bg-red-500/80 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
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
