import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import FilterBar from '../components/FilterBar'
import MediaGrid from '../components/MediaGrid'
import BatchActionBar from '../components/BatchActionBar'
import { useRecommendations, useSearch } from '../hooks/useMedia'

export default function Discover() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('q') || ''

  const [filters, setFilters] = useState({
    category: 'all',
    genre: undefined,
    yearMin: undefined,
    yearMax: undefined,
    ratingMin: undefined,
    hideInPlex: true,
    hideMonitored: true,
    userId: undefined,
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
