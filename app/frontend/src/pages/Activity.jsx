import {
  Activity as ActivityIcon,
  Play,
  Pause,
  Loader2,
  Clock,
  Monitor,
  Smartphone,
  Tv,
  Tablet,
  Laptop,
  HelpCircle,
} from 'lucide-react'
import {
  useNowPlaying,
  useWatchHistory,
  useUsersStats,
  useTopWatched,
} from '../hooks/useActivity'

/* ─── Helpers ─── */

function formatDuration(minutes) {
  if (!minutes || minutes <= 0) return '0m'
  const h = Math.floor(minutes / 60)
  const m = Math.floor(minutes % 60)
  if (h > 0 && m > 0) return `${h}h ${m}m`
  if (h > 0) return `${h}h`
  return `${m}m`
}

function timeAgo(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)
  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHr < 24) return `${diffHr}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  return date.toLocaleDateString()
}

function getPlatformIcon(platform) {
  const p = (platform || '').toLowerCase()
  if (p.includes('tv') || p.includes('apple tv') || p.includes('roku') || p.includes('android tv')) return Tv
  if (p.includes('phone') || p.includes('android') || p.includes('ios')) return Smartphone
  if (p.includes('tablet') || p.includes('ipad')) return Tablet
  if (p.includes('laptop') || p.includes('mac') || p.includes('windows')) return Laptop
  if (p.includes('chrome') || p.includes('browser') || p.includes('web')) return Monitor
  return HelpCircle
}

function getStateBadge(state) {
  const s = (state || '').toLowerCase()
  if (s === 'playing')
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-400">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        Playing
      </span>
    )
  if (s === 'paused')
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-yellow-400">
        <span className="w-2 h-2 rounded-full bg-yellow-400" />
        Paused
      </span>
    )
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-orange-400">
      <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
      {s ? s.charAt(0).toUpperCase() + s.slice(1) : 'Unknown'}
    </span>
  )
}

/* ─── Skeletons ─── */

function NowPlayingSkeleton() {
  return (
    <div className="flex gap-4 overflow-x-auto pb-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="min-w-[280px] bg-surface border border-border rounded-lg p-4 animate-pulse"
        >
          <div className="h-4 bg-surface-elevated rounded w-1/2 mb-3" />
          <div className="h-5 bg-surface-elevated rounded w-3/4 mb-2" />
          <div className="h-2 bg-surface-elevated rounded w-full mb-2" />
          <div className="h-3 bg-surface-elevated rounded w-1/3" />
        </div>
      ))}
    </div>
  )
}

function HistorySkeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-10 bg-surface-elevated rounded" />
      ))}
    </div>
  )
}

function UserStatsSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-surface border border-border rounded-lg p-4 animate-pulse">
          <div className="h-5 bg-surface-elevated rounded w-1/2 mb-3" />
          <div className="h-4 bg-surface-elevated rounded w-3/4 mb-2" />
          <div className="h-2 bg-surface-elevated rounded w-full" />
        </div>
      ))}
    </div>
  )
}

function TopWatchedSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="bg-surface border border-border rounded-lg p-4 animate-pulse">
          <div className="h-5 bg-surface-elevated rounded w-3/4 mb-2" />
          <div className="h-4 bg-surface-elevated rounded w-1/2" />
        </div>
      ))}
    </div>
  )
}

/* ─── Section A: Now Playing ─── */

function NowPlayingSection() {
  const { data, isLoading } = useNowPlaying()
  const sessions = data?.sessions || []

  return (
    <section className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <Play className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-semibold">Now Playing</h2>
        <span className="text-xs text-secondary bg-surface-elevated px-2 py-0.5 rounded-full ml-auto">
          {isLoading ? '…' : `${sessions.length} session${sessions.length !== 1 ? 's' : ''}`}
        </span>
      </div>

      {isLoading ? (
        <NowPlayingSkeleton />
      ) : sessions.length === 0 ? (
        <p className="text-secondary text-sm">No active sessions.</p>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {sessions.map((session) => {
            const PlatformIcon = getPlatformIcon(session.platform)
            const title =
              session.media_type === 'episode' && session.grandparent_title
                ? `${session.grandparent_title} — ${session.title}`
                : session.title || 'Unknown'
            const percent = session.progress_percent || 0
            const duration = session.duration ? Math.round(session.duration / 60) : 0
            const remaining = session.duration && session.view_offset
              ? Math.round((session.duration - session.view_offset) / 60)
              : null

            return (
              <div
                key={session.session_key || session.id}
                className="min-w-[280px] max-w-[320px] flex-1 bg-surface-elevated border border-border rounded-lg p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PlatformIcon className="w-4 h-4 text-secondary" />
                    <span className="text-sm font-medium">{session.user || 'Unknown'}</span>
                  </div>
                  {getStateBadge(session.state)}
                </div>

                <div>
                  <p className="font-semibold leading-tight line-clamp-2" title={title}>
                    {title}
                  </p>
                  {session.media_type === 'episode' && session.parent_title && (
                    <p className="text-xs text-secondary mt-0.5">{session.parent_title}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent rounded-full transition-all"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-secondary">
                    <span>{percent}%</span>
                    <span>
                      {duration > 0 ? formatDuration(duration) : ''}
                      {remaining !== null && remaining > 0 ? ` · ${formatDuration(remaining)} left` : ''}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

/* ─── Section B: Watch History ─── */

function WatchHistorySection() {
  const { data, isLoading } = useWatchHistory(50)
  const history = data?.history || []

  return (
    <section className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-semibold">Watch History</h2>
        <span className="text-xs text-secondary bg-surface-elevated px-2 py-0.5 rounded-full ml-auto">
          Last 50
        </span>
      </div>

      {isLoading ? (
        <HistorySkeleton />
      ) : history.length === 0 ? (
        <p className="text-secondary text-sm">No watch history yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-secondary border-b border-border">
                <th className="pb-2 pr-4 font-medium">When</th>
                <th className="pb-2 pr-4 font-medium">User</th>
                <th className="pb-2 pr-4 font-medium">Title</th>
                <th className="pb-2 pr-4 font-medium">Duration</th>
                <th className="pb-2 font-medium">Completion</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, idx) => {
                const title =
                  item.media_type === 'episode' && item.grandparent_title
                    ? `${item.grandparent_title} — ${item.title}`
                    : item.title || 'Unknown'
                const percent = item.percent_complete || 0
                return (
                  <tr
                    key={item.id || idx}
                    className="border-b border-border/50 last:border-0 hover:bg-surface-elevated/50 transition-colors"
                  >
                    <td className="py-2.5 pr-4 text-secondary whitespace-nowrap">
                      {timeAgo(item.started_at)}
                    </td>
                    <td className="py-2.5 pr-4 font-medium whitespace-nowrap">{item.user || '—'}</td>
                    <td className="py-2.5 pr-4 max-w-xs truncate" title={title}>
                      {title}
                    </td>
                    <td className="py-2.5 pr-4 text-secondary whitespace-nowrap">
                      {formatDuration(item.duration_minutes)}
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-elevated rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent rounded-full"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                        <span className="text-xs text-secondary">{Math.round(percent)}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

/* ─── Section C: User Stats ─── */

function UserStatsSection() {
  const { data, isLoading } = useUsersStats()
  const users = data?.users || []

  const maxPlays = users.length > 0 ? Math.max(...users.map((u) => u.total_plays || 0), 1) : 1
  const maxTime = users.length > 0 ? Math.max(...users.map((u) => u.total_time_minutes || 0), 1) : 1

  return (
    <section className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <ActivityIcon className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-semibold">User Stats</h2>
      </div>

      {isLoading ? (
        <UserStatsSkeleton />
      ) : users.length === 0 ? (
        <p className="text-secondary text-sm">No user stats available.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {users.map((user) => {
            const plays = user.total_plays || 0
            const time = user.total_time_minutes || 0
            return (
              <div
                key={user.user_id || user.username}
                className="bg-surface-elevated border border-border rounded-lg p-4 space-y-3"
              >
                <p className="font-bold text-base">{user.username || 'Unknown'}</p>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-secondary">Plays</span>
                  <span className="font-semibold tabular-nums">{plays.toLocaleString()}</span>
                </div>
                <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent/80 rounded-full"
                    style={{ width: `${(plays / maxPlays) * 100}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-secondary">Watch time</span>
                  <span className="font-semibold tabular-nums">{formatDuration(time)}</span>
                </div>
                <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent/60 rounded-full"
                    style={{ width: `${(time / maxTime) * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

/* ─── Section D: Top Watched ─── */

function TopWatchedSection() {
  const { data, isLoading } = useTopWatched()
  const items = data?.items || []

  return (
    <section className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <ActivityIcon className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-semibold">Top Watched</h2>
        <span className="text-xs text-secondary bg-surface-elevated px-2 py-0.5 rounded-full ml-auto">
          Top 20
        </span>
      </div>

      {isLoading ? (
        <TopWatchedSkeleton />
      ) : items.length === 0 ? (
        <p className="text-secondary text-sm">No top watched data yet.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.slice(0, 20).map((item, idx) => {
            const title =
              item.media_type === 'episode' && item.grandparent_title
                ? `${item.grandparent_title} — ${item.title}`
                : item.title || 'Unknown'
            return (
              <div
                key={item.id || idx}
                className="bg-surface-elevated border border-border rounded-lg p-4 space-y-2 hover:border-accent/30 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium leading-tight line-clamp-2 flex-1" title={title}>
                    {title}
                  </p>
                  <span
                    className={`text-[10px] uppercase tracking-wide font-semibold px-1.5 py-0.5 rounded shrink-0 ${
                      item.media_type === 'movie'
                        ? 'bg-blue-500/10 text-blue-400'
                        : 'bg-purple-500/10 text-purple-400'
                    }`}
                  >
                    {item.media_type === 'episode' ? 'TV' : item.media_type || 'Movie'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-secondary">
                  <span>{item.play_count || 0} plays</span>
                  <span>{formatDuration(item.total_duration_minutes)}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

/* ─── Page ─── */

export default function Activity() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Activity</h1>
        <p className="text-secondary mt-1">Tautulli watch data and live sessions</p>
      </div>

      <NowPlayingSection />
      <WatchHistorySection />
      <UserStatsSection />
      <TopWatchedSection />
    </div>
  )
}
