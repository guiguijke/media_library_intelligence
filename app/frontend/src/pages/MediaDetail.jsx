import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Heart,
  Film,
  Tv,
  ImageOff,
  Star,
  Calendar,
  Clock,
  MonitorPlay,
  ExternalLink,
} from 'lucide-react'
import { useMediaDetail } from '../hooks/useMedia'
import { useBatchActions } from '../hooks/useMedia'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'

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

export default function MediaDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: media, isLoading, error } = useMediaDetail(id)
  const { sendToRadarr, sendToSonarr, addToWishlist } = useBatchActions()

  const handleAdd = () => {
    if (!media?.tmdb_id) return
    if (media.category === 'movie' || media.category === 'cartoon') {
      sendToRadarr.mutate([media.tmdb_id])
    } else if (media.category === 'series' || media.category === 'anime') {
      sendToSonarr.mutate([media.tmdb_id])
    }
  }

  const handleWishlist = () => {
    if (!media) return
    addToWishlist.mutate([
      {
        tmdb_id: media.tmdb_id,
        tvdb_id: media.tvdb_id,
        anilist_id: media.anilist_id,
        title: media.title,
        category: media.category,
        poster_url: media.poster_url,
      },
    ])
  }

  const trailer = media?.videos?.find((v) => v.site === 'YouTube' && v.type === 'Trailer')
  const posterUrl = media?.poster_url
    ? media.poster_url.startsWith('http')
      ? media.poster_url
      : `https://image.tmdb.org/t/p/w500${media.poster_url}`
    : null
  const backdropUrl = media?.backdrop_url
    ? media.backdrop_url.startsWith('http')
      ? media.backdrop_url
      : `https://image.tmdb.org/t/p/original${media.backdrop_url}`
    : null

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-6 animate-fade-in-up">
        <LoadingSkeleton count={6} />
      </div>
    )
  }

  if (error || !media) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-6 animate-fade-in-up">
        <EmptyState
          icon={ImageOff}
          title="Media not found"
          description="The requested title could not be loaded."
          action={
            <button
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground hover:bg-accent/90 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Go back
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="animate-fade-in-up">
      {/* Backdrop header */}
      <div className="relative h-64 sm:h-80 lg:h-96 overflow-hidden">
        {backdropUrl ? (
          <img
            src={backdropUrl}
            alt={media.title}
            className="w-full h-full object-cover opacity-40"
          />
        ) : (
          <div className="w-full h-full bg-surface-elevated" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
        <div className="absolute top-4 left-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/40 backdrop-blur-sm text-white hover:bg-black/60 transition-colors focus-ring"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 pb-12">
        <div className="flex flex-col md:flex-row gap-6 -mt-32 sm:-mt-40 relative z-10">
          {/* Poster */}
          <div className="shrink-0 mx-auto md:mx-0">
            <ImageWithFallback
              src={posterUrl}
              alt={media.title}
              className="w-48 sm:w-56 aspect-[2/3] rounded-2xl shadow-2xl border border-border object-cover"
            />
          </div>

          {/* Info */}
          <div className="flex-1 pt-4">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`px-2.5 py-0.5 rounded-lg text-xs font-bold ${categoryStyles[media.category] || 'bg-surface-elevated text-primary'}`}
              >
                {categoryLabels[media.category] || media.category}
              </span>
              {media.year && (
                <span className="flex items-center gap-1 text-sm text-secondary">
                  <Calendar className="w-3.5 h-3.5" />
                  {media.year}
                </span>
              )}
              {media.runtime && (
                <span className="flex items-center gap-1 text-sm text-secondary">
                  <Clock className="w-3.5 h-3.5" />
                  {media.runtime} min
                </span>
              )}
              {media.number_of_seasons && (
                <span className="text-sm text-secondary">
                  {media.number_of_seasons} season{media.number_of_seasons > 1 ? 's' : ''}
                  {media.number_of_episodes ? ` • ${media.number_of_episodes} episodes` : ''}
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold mt-3">{media.title}</h1>
            {media.original_title && media.original_title !== media.title && (
              <p className="text-secondary mt-1">{media.original_title}</p>
            )}

            <div className="flex items-center gap-4 mt-4">
              {media.vote_average && (
                <div className="flex items-center gap-1.5 text-yellow-400">
                  <Star className="w-5 h-5 fill-current" />
                  <span className="font-bold text-lg">{media.vote_average.toFixed(1)}</span>
                  {media.vote_count && (
                    <span className="text-sm text-secondary">({media.vote_count.toLocaleString()} votes)</span>
                  )}
                </div>
              )}
              {media.popularity && (
                <div className="text-sm text-secondary">
                  Popularity: <span className="text-primary font-medium">{Math.round(media.popularity)}</span>
                </div>
              )}
            </div>

            {media.genres && media.genres.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {media.genres.map((g) => (
                  <span
                    key={g}
                    className="px-3 py-1 rounded-full bg-accent/10 text-accent text-sm font-medium"
                  >
                    {g}
                  </span>
                ))}
              </div>
            )}

            {media.overview && (
              <div className="mt-6">
                <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-2">Overview</h2>
                <p className="text-primary/90 leading-relaxed">{media.overview}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3 mt-6">
              {media.category === 'movie' || media.category === 'cartoon' ? (
                <button
                  onClick={handleAdd}
                  disabled={!media.tmdb_id || sendToRadarr.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50 focus-ring"
                >
                  <Film className="w-4 h-4" />
                  Add to Radarr
                </button>
              ) : (
                <button
                  onClick={handleAdd}
                  disabled={!media.tmdb_id || sendToSonarr.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50 focus-ring"
                >
                  <Tv className="w-4 h-4" />
                  Add to Sonarr
                </button>
              )}
              <button
                onClick={handleWishlist}
                disabled={addToWishlist.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-elevated text-primary font-semibold border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 focus-ring"
              >
                <Heart className="w-4 h-4" />
                Wishlist
              </button>
            </div>

            {/* Watch providers */}
            {media.watch_providers && media.watch_providers.length > 0 && (
              <div className="mt-6">
                <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-2">
                  Available on
                </h2>
                <div className="flex flex-wrap gap-2">
                  {media.watch_providers.map((provider) => (
                    <span
                      key={provider}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-surface-elevated border border-border text-sm"
                    >
                      <MonitorPlay className="w-3.5 h-3.5 text-muted" />
                      {provider}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Trailer */}
        {trailer && (
          <div className="mt-10">
            <h2 className="text-xl font-bold mb-4">Trailer</h2>
            <div className="aspect-video rounded-2xl overflow-hidden border border-border">
              <iframe
                width="100%"
                height="100%"
                src={`https://www.youtube.com/embed/${trailer.key}`}
                title={trailer.name}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        )}

        {/* Cast */}
        {media.cast && media.cast.length > 0 && (
          <div className="mt-10">
            <h2 className="text-xl font-bold mb-4">Cast</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {media.cast.map((person) => (
                <div
                  key={person.id}
                  className="bg-surface border border-border rounded-xl overflow-hidden"
                >
                  <ImageWithFallback
                    src={person.profile_path}
                    alt={person.name}
                    className="w-full aspect-[2/3] object-cover"
                  />
                  <div className="p-3">
                    <p className="font-medium text-sm truncate">{person.name}</p>
                    <p className="text-xs text-secondary truncate">{person.character}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Similar */}
        {media.similar && media.similar.length > 0 && (
          <div className="mt-10">
            <h2 className="text-xl font-bold mb-4">Similar titles</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {media.similar.map((sim) => (
                <Link
                  key={sim.id}
                  to={`/media/tmdb-${sim.id}`}
                  className="group rounded-xl overflow-hidden bg-surface border border-border hover:border-accent/50 transition-colors"
                >
                  <ImageWithFallback
                    src={
                      sim.poster_url?.startsWith('http')
                        ? sim.poster_url
                        : `https://image.tmdb.org/t/p/w500${sim.poster_url}`
                    }
                    alt={sim.title}
                    className="w-full aspect-[2/3] object-cover transition-transform group-hover:scale-105"
                  />
                  <div className="p-2.5">
                    <p className="text-sm font-medium line-clamp-2">{sim.title}</p>
                    {sim.year && <p className="text-xs text-secondary mt-0.5">{sim.year}</p>}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
