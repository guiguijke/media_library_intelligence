import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ImageOff } from 'lucide-react'
import { useSelection } from '../contexts/SelectionContext'
import ScoreBadge from './ScoreBadge'

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

export default function MediaCard({ media, onClick, index = 0 }) {
  const navigate = useNavigate()
  const { toggle, isSelected } = useSelection()
  const [imgLoaded, setImgLoaded] = useState(false)
  const [imgError, setImgError] = useState(false)
  const selected = isSelected(media.id)

  const handleClick = () => {
    if (onClick) {
      onClick(media)
      return
    }
    navigate(`/media/${encodeURIComponent(media.id)}`)
  }

  const posterUrl = media.poster_url
    ? (media.poster_url.startsWith('http') ? media.poster_url : `https://image.tmdb.org/t/p/w500${media.poster_url}`)
    : null

  return (
    <div
      className="group relative rounded-xl overflow-hidden bg-surface cursor-pointer card-glow animate-fade-in-up"
      style={{ animationDelay: `${index * 40}ms` }}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
    >
      {/* Poster */}
      <div className="aspect-[2/3] relative bg-surface-elevated">
        {posterUrl && !imgError ? (
          <img
            src={posterUrl}
            alt={media.title}
            loading="lazy"
            onLoad={() => setImgLoaded(true)}
            onError={() => setImgError(true)}
            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
              imgLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-muted">
            <ImageOff className="w-10 h-10 mb-2 opacity-50" />
            <span className="text-xs text-center px-4 line-clamp-2">{media.title}</span>
          </div>
        )}

        {/* Gradient overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity" />

        {/* Score badge */}
        <ScoreBadge score={media.score} />

        {/* Checkbox */}
        <div
          className="absolute top-2 right-2 z-10"
          onClick={(e) => {
            e.stopPropagation()
            toggle(media.id)
          }}
        >
          <div
            className={`w-7 h-7 rounded-lg border-2 flex items-center justify-center transition-all backdrop-blur-sm ${
              selected
                ? 'bg-accent border-accent'
                : 'bg-black/40 border-white/40 hover:border-white'
            }`}
          >
            {selected && <Check className="w-4 h-4 text-accent-foreground" />}
          </div>
        </div>

        {/* Hover overlay info */}
        <div className="absolute inset-0 flex flex-col justify-end p-3 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-y-2 group-hover:translate-y-0">
          <h3 className="font-semibold text-sm line-clamp-2 text-white drop-shadow-md">{media.title}</h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-white/80">
            <span>{media.year}</span>
            <span>•</span>
            <span>⭐ {media.vote_average?.toFixed(1) || '—'}</span>
          </div>
        </div>
      </div>

      {/* Category badge */}
      <div className="absolute bottom-2 left-2">
        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold shadow-sm ${categoryStyles[media.category] || 'bg-black/70 text-white'}`}>
          {categoryLabels[media.category] || media.category}
        </span>
      </div>
    </div>
  )
}
