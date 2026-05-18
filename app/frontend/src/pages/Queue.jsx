import { useState } from 'react'
import { Tv, Film, Loader2, Download, CheckCircle } from 'lucide-react'
import { useQueueSonarr, useQueueRadarr } from '../hooks/useMedia'

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
        if (item.status === 'completed') {
          statusIcon = <CheckCircle className="w-4 h-4" />
          statusColor = 'text-score-high'
        } else if (item.status === 'downloading') {
          statusIcon = <Download className="w-4 h-4" />
          statusColor = 'text-score-mid'
        }

        return (
          <div
            key={item.id}
            className="flex items-center gap-4 p-3 bg-surface border border-border rounded-lg"
          >
            {posterUrl ? (
              <img
                src={posterUrl}
                alt={item.title}
                className="w-12 h-18 object-cover rounded-md shrink-0"
              />
            ) : (
              <div className="w-12 h-[72px] bg-surface-elevated rounded-md shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate">{item.title}</h3>
              <p className="text-sm text-secondary">{item.year}</p>
            </div>
            <div className={`flex items-center gap-2 text-sm font-medium ${statusColor}`}>
              {statusIcon}
              <span className="hidden sm:inline capitalize">{item.status}</span>
            </div>
            {item.progress !== undefined && item.progress !== null && (
              <div className="w-24 sm:w-32">
                <div className="h-1.5 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all"
                    style={{ width: `${Math.min(item.progress, 100)}%` }}
                  />
                </div>
                <p className="text-[10px] text-secondary text-right mt-0.5">
                  {Math.round(item.progress)}%
                </p>
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
          <QueueList items={sonarrData?.items || []} type="sonarr" />
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
          <QueueList items={radarrData?.items || []} type="radarr" />
        )
      )}
    </div>
  )
}
