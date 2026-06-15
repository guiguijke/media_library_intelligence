import { useState } from 'react'
import { X, Heart, Tv, Film, ImageOff } from 'lucide-react'
import { useBatchActions } from '../hooks/useMedia'

const categoryLabels = {
  movie: 'Movie',
  series: 'TV Show',
  anime: 'Anime',
  cartoon: 'Cartoon',
}

const categoryStyles = {
  movie: 'bg-blue-500/90 text-white',
  series: 'bg-purple-500/90 text-white',
  anime: 'bg-pink-500/90 text-white',
  cartoon: 'bg-orange-500/90 text-white',
}

function ImageWithFallback({ src, alt, className }) {
  const [error, setError] = useState(false)
  if (!src || error) {
    return (
      <div className={`bg-surface-elevated flex items-center justify-center ${className}`}>
        <ImageOff className="w-12 h-12 text-muted" />
      </div>
    )
  }
  return <img src={src} alt={alt} className={className} onError={() => setError(true)} />
}

export default function MediaModal({ media, onClose }) {
  const { sendToRadarr, sendToSonarr, addToWishlist } = useBatchActions()

  const isMovie = media.category === 'movie' || media.category === 'cartoon'
  const isSeries = media.category === 'series' || media.category === 'anime'
  const canAddToArr = Boolean(media.tmdb_id)

  const handleAdd = () => {
    if (!canAddToArr) return
    if (isMovie) {
      sendToRadarr.mutate([media.tmdb_id])
    } else if (isSeries) {
      sendToSonarr.mutate([media.tmdb_id])
    }
  }

  const handleWishlist = () => {
    addToWishlist.mutate([
      {
        tmdb_id: media.tmdb_id,
        anilist_id: media.anilist_id,
        title: media.title,
        category: media.category,
        poster_url: media.poster_url,
      },
    ])
  }

  const backdropUrl = media.backdrop_url
    ? (media.backdrop_url.startsWith('http') ? media.backdrop_url : `https://image.tmdb.org/t/p/original${media.backdrop_url}`)
    : null
  const posterUrl = media.poster_url
    ? (media.poster_url.startsWith('http') ? media.poster_url : `https://image.tmdb.org/t/p/w500${media.poster_url}`)
    : null

  let scoreColor = 'text-score-low'
  if (media.score >= 80) scoreColor = 'text-score-high'
  else if (media.score >= 60) scoreColor = 'text-score-mid'

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 animate-fade-in-up">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-surface rounded-2xl shadow-2xl border border-border">
        {/* Backdrop */}
        <div className="relative h-48 sm:h-64 overflow-hidden rounded-t-2xl">
          <ImageWithFallback
            src={backdropUrl}
            alt=""
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/60 to-transparent" />
          <button
            onClick={onClose}
            className="absolute top-3 right-3 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors focus-ring"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 pb-6 -mt-20 sm:-mt-24 relative flex flex-col sm:flex-row gap-6">
          {/* Poster */}
          <div className="shrink-0 mx-auto sm:mx-0">
            <ImageWithFallback
              src={posterUrl}
              alt={media.title}
              className="w-40 sm:w-48 aspect-[2/3] rounded-xl shadow-lg border border-border object-cover"
            />
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0 pt-2">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold">{media.title}</h2>
                {media.original_title && media.original_title !== media.title && (
                  <p className="text-sm text-secondary mt-0.5">{media.original_title}</p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 mt-3 text-sm text-secondary">
              <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${categoryStyles[media.category] || 'bg-surface-elevated text-primary'}`}>
                {categoryLabels[media.category] || media.category}
              </span>
              <span>{media.year}</span>
              <span>•</span>
              <span>⭐ {media.vote_average?.toFixed(1)} ({media.vote_count?.toLocaleString()} votes)</span>
            </div>

            {media.genres && media.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {media.genres.map((g) => (
                  <span key={g} className="px-2.5 py-0.5 rounded-full bg-accent/10 text-accent text-xs font-medium">
                    {g}
                  </span>
                ))}
              </div>
            )}

            {/* Score */}
            <div className="mt-4 p-3 rounded-xl bg-surface-elevated border border-border">
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold tabular-nums ${scoreColor}`}>{media.score}</span>
                <span className="text-xs text-secondary uppercase tracking-wider">Relevance Score</span>
              </div>
              {media.score_reason && (
                <p className="text-sm text-secondary mt-1">Recommended because: {media.score_reason}</p>
              )}
            </div>

            {(media.synopsis || media.overview) && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-1">Synopsis</h3>
                <p className="text-sm leading-relaxed text-primary/90">{media.synopsis || media.overview}</p>
              </div>
            )}

            {/* Trailer */}
            {media.trailer_key && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-2">Trailer</h3>
                <div className="aspect-video rounded-xl overflow-hidden border border-border">
                  <iframe
                    width="100%"
                    height="100%"
                    src={`https://www.youtube.com/embed/${media.trailer_key}`}
                    title="Trailer"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3 mt-6">
              <button
                onClick={handleAdd}
                disabled={!canAddToArr || sendToRadarr.isPending || sendToSonarr.isPending}
                title={canAddToArr ? '' : 'Missing TMDb ID'}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50 focus-ring"
              >
                {isMovie ? <Film className="w-4 h-4" /> : <Tv className="w-4 h-4" />}
                Add to {isMovie ? 'Radarr' : 'Sonarr'}
              </button>
              <button
                onClick={handleWishlist}
                disabled={addToWishlist.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-elevated text-primary font-semibold border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 focus-ring"
              >
                <Heart className="w-4 h-4" />
                Wishlist
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-border text-secondary font-medium hover:text-primary hover:bg-surface-elevated transition-colors focus-ring"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
