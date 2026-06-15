import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import FilterBar from '../components/FilterBar'
import MediaGrid from '../components/MediaGrid'
import BatchActionBar from '../components/BatchActionBar'
import { useRecommendations, useSearch } from '../hooks/useMedia'

function parseIntParam(value) {
  if (!value) return undefined
  const n = parseInt(value, 10)
  return Number.isNaN(n) ? undefined : n
}

export default function Discover() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('q') || ''

  const [filters, setFilters] = useState({
    category: searchParams.get('category') || 'all',
    genre: parseIntParam(searchParams.get('genre')),
    yearMin: parseIntParam(searchParams.get('year_min')),
    yearMax: parseIntParam(searchParams.get('year_max')),
    ratingMin: searchParams.get('rating_min') ? parseFloat(searchParams.get('rating_min')) : undefined,
    hideInPlex: searchParams.get('hide_in_plex') !== 'false',
    hideMonitored: searchParams.get('hide_monitored') !== 'false',
    userId: searchParams.get('user_id') || undefined,
  })

  const recommendationsQuery = useRecommendations(filters)
  const searchQueryHook = useSearch(searchQuery, filters)

  const isSearchMode = Boolean(searchQuery.trim())
  const activeQuery = isSearchMode ? searchQueryHook : recommendationsQuery
  const { data, isLoading, hasNextPage, fetchNextPage } = activeQuery
  const items = data?.items || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6 animate-fade-in-up">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Discover</h1>
          <p className="text-secondary mt-1">
            {isSearchMode
              ? `Search results for "${searchQuery}"`
              : 'Explore personalized recommendations'}
          </p>
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      <MediaGrid
        items={items}
        isLoading={isLoading}
        hasNextPage={hasNextPage}
        fetchNextPage={fetchNextPage}
        searchQuery=""
      />

      <BatchActionBar items={items} />
    </div>
  )
}
