import { useState } from 'react'
import MediaCard from './MediaCard'
import MediaModal from './MediaModal'
import LoadingSkeleton from './LoadingSkeleton'

export default function MediaGrid({ items, isLoading, hasNextPage, fetchNextPage }) {
  const [selectedMedia, setSelectedMedia] = useState(null)

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-20 text-secondary">
        No results found.
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
        {items.map((media) => (
          <MediaCard key={media.id} media={media} onClick={setSelectedMedia} />
        ))}
      </div>

      {hasNextPage && (
        <div className="flex justify-center mt-8">
          <button
            onClick={fetchNextPage}
            className="px-6 py-2.5 rounded-md bg-surface-elevated text-primary font-medium hover:bg-border transition-colors"
          >
            Load more
          </button>
        </div>
      )}

      {selectedMedia && (
        <MediaModal media={selectedMedia} onClose={() => setSelectedMedia(null)} />
      )}
    </>
  )
}
