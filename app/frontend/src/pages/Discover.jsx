import { useState } from 'react'
import FilterBar from '../components/FilterBar'
import MediaGrid from '../components/MediaGrid'
import BatchActionBar from '../components/BatchActionBar'
import { useRecommendations } from '../hooks/useMedia'

export default function Discover() {
  const [filters, setFilters] = useState({
    category: 'all',
    genre: undefined,
    yearMin: undefined,
    yearMax: undefined,
    ratingMin: undefined,
    hideInPlex: true,
    hideMonitored: true,
  })

  const { data, isLoading, hasNextPage, fetchNextPage } = useRecommendations(filters)
  const items = data?.items || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Discover</h1>
        <p className="text-secondary mt-1">Explore personalized recommendations</p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      <MediaGrid
        items={items}
        isLoading={isLoading}
        hasNextPage={hasNextPage}
        fetchNextPage={fetchNextPage}
      />

      <BatchActionBar />
    </div>
  )
}
