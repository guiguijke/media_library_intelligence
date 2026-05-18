import { Film, Tv, Clapperboard, Baby, HardDrive, TrendingUp, RotateCcw, Clock } from 'lucide-react'
import { useDashboardStats, useRecommendations, useBatchActions } from '../hooks/useMedia'
import MediaCard from '../components/MediaCard'
import MediaModal from '../components/MediaModal'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useState } from 'react'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: recs, isLoading: recsLoading } = useRecommendations({ category: 'all' })
  const { sync } = useBatchActions()
  const [selectedMedia, setSelectedMedia] = useState(null)

  const topRecommendations = recs?.items?.slice(0, 10) || []
  const hasTrends = stats?.trends && stats.trends.length > 0
  const hasRecommendations = topRecommendations.length > 0

  const statCards = [
    { label: 'Movies', value: stats?.movies || 0, icon: Film, color: 'text-accent' },
    { label: 'TV Shows', value: stats?.series || 0, icon: Tv, color: 'text-accent' },
    { label: 'Anime', value: stats?.anime || 0, icon: Clapperboard, color: 'text-accent' },
    { label: 'Cartoons', value: stats?.cartoons || 0, icon: Baby, color: 'text-accent' },
    { label: 'Disk Space', value: stats?.disk_usage ? `${(stats.disk_usage / 1e12).toFixed(1)} TB` : '0 TB', icon: HardDrive, color: 'text-accent' },
  ]

  const trends = stats?.trends || []
  const maxTrend = hasTrends ? Math.max(...trends.map((t) => t.count), 1) : 1

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-secondary mt-1">Overview of your library and recommendations</p>
        </div>
        {stats?.last_synced && (
          <div className="flex items-center gap-1.5 text-xs text-secondary bg-surface border border-border rounded-md px-3 py-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Last synced: {stats.last_synced}</span>
          </div>
        )}
      </div>

      {/* Stats */}
      {statsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-surface rounded-lg p-4 animate-pulse">
              <div className="h-8 bg-surface-elevated rounded w-1/2" />
              <div className="h-4 bg-surface-elevated rounded w-3/4 mt-2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {statCards.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.label} className="bg-surface border border-border rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <Icon className={`w-5 h-5 ${s.color}`} />
                  <span className="text-2xl font-bold tabular-nums">{s.value}</span>
                </div>
                <p className="text-sm text-secondary mt-1">{s.label}</p>
              </div>
            )
          })}
        </div>
      )}

      {/* Completion de sagas */}
      <div className="bg-surface border border-border rounded-lg p-5">
        <h2 className="text-lg font-semibold mb-4">Saga Completion</h2>
        {stats?.incomplete_collections && stats.incomplete_collections.length > 0 ? (
          <div className="space-y-3">
            {stats.incomplete_collections.map((col) => (
              <div key={col.id} className="flex items-center justify-between p-3 rounded-md bg-surface-elevated">
                <div>
                  <p className="font-medium">{col.name}</p>
                  <p className="text-sm text-secondary">{col.owned} / {col.total} movies</p>
                </div>
                <div className="w-32 h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full"
                    style={{ width: `${(col.owned / col.total) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-secondary text-sm">No incomplete sagas detected.</p>
        )}
      </div>

      {/* Trends */}
      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-accent" />
          <h2 className="text-lg font-semibold">Watch Trends</h2>
        </div>
        {hasTrends ? (
          <div className="space-y-3">
            {trends.map((t) => (
              <div key={t.genre} className="flex items-center gap-3">
                <span className="w-20 text-sm text-secondary text-right shrink-0">{t.genre}</span>
                <div className="flex-1 h-6 bg-surface-elevated rounded-md overflow-hidden relative">
                  <div
                    className="h-full bg-accent/80 rounded-md transition-all"
                    style={{ width: `${(t.count / maxTrend) * 100}%` }}
                  />
                  <span className="absolute inset-0 flex items-center px-2 text-xs font-medium text-primary mix-blend-difference">
                    {t.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-secondary text-sm">No watch data yet. Run a Tautulli sync to see trends.</p>
        )}
      </div>

      {/* Top recommendations */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Priority Recommendations</h2>
        {recsLoading ? (
          <LoadingSkeleton count={5} />
        ) : hasRecommendations ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
            {topRecommendations.map((media) => (
              <MediaCard key={media.id} media={media} onClick={setSelectedMedia} />
            ))}
          </div>
        ) : (
          <div className="bg-surface border border-border rounded-lg p-6 text-center space-y-3">
            <p className="text-secondary text-sm">
              No recommendations yet. Run a sync to fetch classics and generate recommendations.
            </p>
            <button
              onClick={() => sync.mutate()}
              disabled={sync.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-accent text-black hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCcw className={`w-4 h-4 ${sync.isPending ? 'animate-spin' : ''}`} />
              {sync.isPending ? 'Syncing...' : 'Run Sync'}
            </button>
          </div>
        )}
      </div>

      {selectedMedia && (
        <MediaModal media={selectedMedia} onClose={() => setSelectedMedia(null)} />
      )}
    </div>
  )
}
