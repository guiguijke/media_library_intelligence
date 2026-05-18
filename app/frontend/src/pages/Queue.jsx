import { useState } from 'react'
import { Tv, Film, Loader2, Download, CheckCircle, AlertCircle, Clock, HardDrive } from 'lucide-react'
import { useQueueSonarr, useQueueRadarr } from '../hooks/useMedia'

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function QueueList({ items, type }) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-16 text-secondary">
        <p>The queue is empty.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
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
            className="flex items-center gap-4 p-3 bg-surface border border-border rounded-lg"
          >
            {posterUrl ? (
              <img
                src={posterUrl}
                alt={item.title}
                className="w-12 h-[72px] object-cover rounded-md shrink-0"
              />
            ) : (
              <div className="w-12 h-[72px] bg-surface-elevated rounded-md shrink-0 flex items-center justify-center">
                {type === 'sonarr' ? <Tv className="w-5 h-5 text-secondary" /> : <Film className="w-5 h-5 text-secondary" />}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate">{item.title}</h3>
              <div className="flex items-center gap-2 text-xs text-secondary mt-0.5">
                {item.year && <span>{item.year}</span>}
                {item.quality && (
                  <span className="px-1.5 py-0.5 bg-surface-elevated rounded text-[10px]">
                    {item.quality}
                  </span>
                )}
                {item.protocol && (
                  <span className="px-1.5 py-0.5 bg-surface-elevated rounded text-[10px] uppercase">
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
  const { data: sonarrData, isLoading: sonarrLoading } = useQueueSonarr()
  const { data: radarrData, isLoading: radarrLoading } = useQueueRadarr()

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Queue</h1>
        <p className="text-secondary mt-1">Track Sonarr and Radarr downloads</p>
      </div>

      <div className="flex items-center gap-2 bg-surface border border-border rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab('sonarr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'sonarr'
              ? 'bg-surface-elevated text-primary'
              : 'text-secondary hover:text-primary'
          }`}
        >
          <Tv className="w-4 h-4" />
          Sonarr
        </button>
        <button
          onClick={() => setTab('radarr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'radarr'
              ? 'bg-surface-elevated text-primary'
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
              <div key={i} className="h-16 bg-surface animate-pulse rounded-lg" />
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
              <div key={i} className="h-16 bg-surface animate-pulse rounded-lg" />
            ))}
          </div>
        ) : (
          <QueueList items={radarrData || []} type="radarr" />
        )
      )}
    </div>
  )
}
