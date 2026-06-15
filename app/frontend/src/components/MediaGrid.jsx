import { useMemo } from 'react'
import MediaCard from './MediaCard'
import LoadingSkeleton from './LoadingSkeleton'
import EmptyState from './EmptyState'
import { Search } from 'lucide-react'

export default function MediaGrid({ items, isLoading, hasNextPage, fetchNextPage, searchQuery = '' }) {
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items
    const q = searchQuery.toLowerCase()
    return items.filter((media) =>
      (media.title || '').toLowerCase().includes(q) ||
      (media.original_title || '').toLowerCase().includes(q)
    )
  }, [items, searchQuery])

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (!filteredItems || filteredItems.length === 0) {
    return (
      <EmptyState
        icon={Search}
        title={searchQuery ? 'No matches found' : 'No results found'}
        description={searchQuery ? 'Try a different search term.' : 'Adjust your filters to discover more content.'}
      />
    )
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
        {filteredItems.map((media, idx) => (
          <MediaCard key={media.id} media={media} index={idx} />
        ))}
      </div>

      {hasNextPage && (
        <div className="flex justify-center mt-8">
          <button
            onClick={fetchNextPage}
            className="px-6 py-2.5 rounded-lg bg-surface-elevated text-primary font-medium hover:bg-surface-hover border border-border transition-colors focus-ring"
          >
            Load more
          </button>
        </div>
      )}

    </>
  )
}
