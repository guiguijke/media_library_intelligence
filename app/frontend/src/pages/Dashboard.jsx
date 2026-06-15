import { Film, Tv, Clapperboard, Baby, TrendingUp, RotateCcw, Clock, Sparkles } from 'lucide-react'
import { useDashboardStats, useRecommendations, useBatchActions } from '../hooks/useMedia'
import MediaCard from '../components/MediaCard'
import MediaModal from '../components/MediaModal'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import { useState } from 'react'

const statConfig = [
  { label: 'Movies', key: 'movies', icon: Film, gradient: 'from-blue-500/20 to-blue-600/5', iconColor: 'text-blue-400' },
  { label: 'TV Shows', key: 'series', icon: Tv, gradient: 'from-purple-500/20 to-purple-600/5', iconColor: 'text-purple-400' },
  { label: 'Anime', key: 'anime', icon: Clapperboard, gradient: 'from-pink-500/20 to-pink-600/5', iconColor: 'text-pink-400' },
  { label: 'Cartoons', key: 'cartoons', icon: Baby, gradient: 'from-orange-500/20 to-orange-600/5', iconColor: 'text-orange-400' },
]

function StatCard({ stat, value, index }) {
  const Icon = stat.icon
  return (
    <div
      className="relative overflow-hidden rounded-xl border border-border bg-surface p-4 card-glow animate-fade-in-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-60`} />
      <div className="relative flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-surface-elevated ${stat.iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <span className="text-2xl font-bold tabular-nums">{value}</span>
          <p className="text-sm text-secondary">{stat.label}</p>
        </div>
      </div>
    </div>
  )
}

function SectionCard({ icon: Icon, title, subtitle, children, delay = 0 }) {
  return (
    <div
      className="bg-surface border border-border rounded-xl p-5 animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-5 h-5 text-accent" />}
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
        {subtitle && <span className="text-xs text-secondary bg-surface-elevated px-2 py-0.5 rounded-full">{subtitle}</span>}
      </div>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: recs, isLoading: recsLoading } = useRecommendations({ category: 'all' })
  const { sync } = useBatchActions()
  const [selectedMedia, setSelectedMedia] = useState(null)

  const topRecommendations = recs?.items?.slice(0, 10) || []
  const hasTrends = stats?.trends && stats.trends.length > 0
  const hasRecommendations = topRecommendations.length > 0

  const trends = stats?.trends || []
  const maxTrend = hasTrends ? Math.max(...trends.map((t) => t.count), 1) : 1

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-secondary mt-1">Overview of your library and recommendations</p>
        </div>
        {stats?.last_synced && (
          <div className="flex items-center gap-1.5 text-xs text-secondary bg-surface border border-border rounded-lg px-3 py-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Last synced: {stats.last_synced}</span>
          </div>
        )}
      </div>

      {/* Stats */}
      {statsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-surface rounded-xl p-4 animate-pulse border border-border">
              <div className="h-8 bg-surface-elevated rounded w-1/2" />
              <div className="h-4 bg-surface-elevated rounded w-3/4 mt-2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {statConfig.map((s, idx) => (
            <StatCard key={s.key} stat={s} value={stats?.[s.key] || 0} index={idx} />
          ))}
        </div>
      )}

      {/* Saga Completion */}
      <SectionCard title="Saga Completion" delay={100}>
        {stats?.incomplete_collections && stats.incomplete_collections.length > 0 ? (
          <div className="space-y-3">
            {stats.incomplete_collections.map((col) => (
              <div key={col.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-elevated">
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
      </SectionCard>

      {/* Trends */}
      <SectionCard icon={TrendingUp} title="Watch Trends" delay={150}>
        {hasTrends ? (
          <div className="space-y-3">
            {trends.map((t) => (
              <div key={t.genre} className="flex items-center gap-3">
                <span className="w-24 text-sm text-secondary text-right shrink-0">{t.genre}</span>
                <div className="flex-1 h-7 bg-surface-elevated rounded-lg overflow-hidden relative">
                  <div
                    className="h-full bg-accent/80 rounded-lg transition-all"
                    style={{ width: `${(t.count / maxTrend) * 100}%` }}
                  />
                  <span className="absolute inset-0 flex items-center px-3 text-xs font-medium text-primary mix-blend-difference">
                    {t.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-secondary text-sm">No watch data yet. Run a Tautulli sync to see trends.</p>
        )}
      </SectionCard>

      {/* Top recommendations */}
      <div className="animate-fade-in-up" style={{ animationDelay: '200ms' }}>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-accent" />
          <h2 className="text-lg font-semibold">Priority Recommendations</h2>
        </div>
        {recsLoading ? (
          <LoadingSkeleton count={5} />
        ) : hasRecommendations ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
            {topRecommendations.map((media, idx) => (
              <MediaCard key={media.id} media={media} onClick={setSelectedMedia} index={idx} />
            ))}
          </div>
        ) : (
          <div className="bg-surface border border-border rounded-xl p-8 text-center">
            <EmptyState
              icon={Sparkles}
              title="No recommendations yet"
              description="Run a sync to fetch classics and generate personalized recommendations."
              action={
                <button
                  onClick={() => sync.mutate()}
                  disabled={sync.isPending}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-accent text-accent-foreground hover:bg-accent/90 focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <RotateCcw className={`w-4 h-4 ${sync.isPending ? 'animate-spin' : ''}`} />
                  {sync.isPending ? 'Syncing...' : 'Run Sync'}
                </button>
              }
            />
          </div>
        )}
      </div>

      {selectedMedia && (
        <MediaModal media={selectedMedia} onClose={() => setSelectedMedia(null)} />
      )}
    </div>
  )
}
