import { useState } from 'react'
import { Tv, Film, Loader2, Download, CheckCircle, AlertCircle, Clock, HardDrive } from 'lucide-react'
import { useQueueSonarr, useQueueRadarr } from '../hooks/useMedia'
import EmptyState from '../components/EmptyState'
import ShimmerSkeleton from '../components/ShimmerSkeleton'

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function Poster({ src, alt, type }) {
  const [error, setError] = useState(false)
  if (!src || error) {
    return (
      <div className="w-12 h-[72px] bg-surface-elevated rounded-lg shrink-0 flex items-center justify-center border border-border">
        {type === 'sonarr' ? <Tv className="w-5 h-5 text-muted" /> : <Film className="w-5 h-5 text-muted" />}
      </div>
    )
  }
  return (
    <img
      src={src}
      alt={alt}
      className="w-12 h-[72px] object-cover rounded-lg shrink-0 border border-border"
      onError={() => setError(true)}
    />
  )
}

function QueueList({ items, type }) {
  if (!items || items.length === 0) {
    return (
      <EmptyState
        icon={type === 'sonarr' ? Tv : Film}
        title="The queue is empty"
        description={`No active ${type === 'sonarr' ? 'Sonarr' : 'Radarr'} downloads right now.`}
      />
    )
  }

  return (
    <div className="space-y-3 stagger-children">
      {items.map((item) => {
        const posterUrl = item.poster_url
          ? (item.poster_url.startsWith('http') ? item.poster_url : `https://image.tmdb.org/t/p/w200${item.poster_url}`)
          : null

        let statusIcon = <Loader2 className="w-4 h-4 animate-spin" />
        let statusColor = 'text-accent'
        let statusLabel = item.status
        if (item.status === 'completed' || item.status === 'importing') {
          statusIcon = <CheckCircle className="w-4 h-4" />
          statusColor = 'text-score-high'
        } else if (item.status === 'downloading') {
          statusIcon = <Download className="w-4 h-4" />
          statusColor = 'text-score-mid'
        } else if (item.status === 'failed') {
          statusIcon = <AlertCircle className="w-4 h-4" />
          statusColor = 'text-score-low'
        } else if (item.status === 'queued' || item.status === 'added') {
          statusIcon = <Clock className="w-4 h-4" />
          statusColor = 'text-secondary'
        }

        const showProgress = item.status === 'downloading' || item.status === 'importing'
        const totalSize = item.size || 0
        const leftSize = item.sizeleft || 0
        const doneSize = totalSize - leftSize

        return (
          <div
            key={item.id}
            className="flex items-center gap-4 p-3 bg-surface border border-border rounded-xl card-glow"
          >
            <Poster src={posterUrl} alt={item.title} type={type} />
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate">{item.title}</h3>
              <div className="flex items-center gap-2 text-xs text-secondary mt-0.5">
                {item.year && <span>{item.year}</span>}
                {item.quality && (
                  <span className="px-1.5 py-0.5 bg-surface-elevated rounded-md text-[10px] border border-border">
                    {item.quality}
                  </span>
                )}
                {item.protocol && (
                  <span className="px-1.5 py-0.5 bg-surface-elevated rounded-md text-[10px] uppercase border border-border">
                    {item.protocol}
                  </span>
                )}
              </div>
            </div>
            <div className={`flex items-center gap-2 text-sm font-medium ${statusColor}`}>
              {statusIcon}
              <span className="hidden sm:inline capitalize">{statusLabel}</span>
            </div>
            {showProgress && (
              <div className="w-28 sm:w-40 space-y-1">
                <div className="h-1.5 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all"
                    style={{ width: `${Math.min(item.progress, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] text-secondary">
                  <span>{Math.round(item.progress)}%</span>
                  {totalSize > 0 && (
                    <span className="flex items-center gap-0.5">
                      <HardDrive className="w-3 h-3" />
                      {formatBytes(doneSize)} / {formatBytes(totalSize)}
                    </span>
                  )}
                </div>
                {item.timeleft && (
                  <p className="text-[10px] text-secondary text-right">{item.timeleft} left</p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function Queue() {
  const [tab, setTab] = useState('sonarr')
  const { data: sonarrData, isLoading: sonarrLoading } = useQueueSonarr(tab === 'sonarr')
  const { data: radarrData, isLoading: radarrLoading } = useQueueRadarr(tab === 'radarr')

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-2xl font-bold">Queue</h1>
        <p className="text-secondary mt-1">Track Sonarr and Radarr downloads</p>
      </div>

      <div className="flex items-center gap-2 bg-surface border border-border rounded-xl p-1 w-fit">
        <button
          onClick={() => setTab('sonarr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focus-ring ${
            tab === 'sonarr'
              ? 'bg-surface-elevated text-primary shadow-sm'
              : 'text-secondary hover:text-primary'
          }`}
        >
          <Tv className="w-4 h-4" />
          Sonarr
        </button>
        <button
          onClick={() => setTab('radarr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focus-ring ${
            tab === 'radarr'
              ? 'bg-surface-elevated text-primary shadow-sm'
              : 'text-secondary hover:text-primary'
          }`}
        >
          <Film className="w-4 h-4" />
          Radarr
        </button>
      </div>

      {tab === 'sonarr' && (
        sonarrLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <ShimmerSkeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : (
          <QueueList items={sonarrData || []} type="sonarr" />
        )
      )}

      {tab === 'radarr' && (
        radarrLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <ShimmerSkeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : (
          <QueueList items={radarrData || []} type="radarr" />
        )
      )}
    </div>
  )
}
