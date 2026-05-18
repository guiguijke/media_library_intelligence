import { useState } from 'react'
import { Check } from 'lucide-react'
import { useSelection } from '../contexts/SelectionContext'
import ScoreBadge from './ScoreBadge'

const categoryLabels = {
  movie: 'Movie',
  series: 'TV Show',
  anime: 'Anime',
  cartoon: 'Cartoon',
}

export default function MediaCard({ media, onClick }) {
  const { toggle, isSelected } = useSelection()
  const [imgLoaded, setImgLoaded] = useState(false)
  const selected = isSelected(media.id)

  const posterUrl = media.poster_url
    ? (media.poster_url.startsWith('http') ? media.poster_url : `https://image.tmdb.org/t/p/w500${media.poster_url}`)
    : null

  return (
    <div
      className="group relative rounded-lg overflow-hidden bg-surface cursor-pointer transition-transform hover:scale-[1.02]"
      onClick={() => onClick?.(media)}
    >
      {/* Poster */}
      <div className="aspect-[2/3] relative bg-surface-elevated">
        {posterUrl && (
          <img
            src={posterUrl}
            alt={media.title}
            loading="lazy"
            onLoad={() => setImgLoaded(true)}
            className={`w-full h-full object-cover transition-opacity duration-300 ${
              imgLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

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
            className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
              selected
                ? 'bg-accent border-accent'
                : 'bg-black/50 border-white/50 hover:border-white'
            }`}
          >
            {selected && <Check className="w-3.5 h-3.5 text-background" />}
          </div>
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3">
          <h3 className="font-semibold text-sm line-clamp-2">{media.title}</h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-secondary">
            <span>{media.year}</span>
            <span>•</span>
            <span>⭐ {media.vote_average?.toFixed(1) || '—'}</span>
          </div>
        </div>
      </div>

      {/* Category badge */}
      <div className="absolute bottom-2 left-2">
        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-black/70 text-white backdrop-blur">
          {categoryLabels[media.category] || media.category}
        </span>
      </div>
    </div>
  )
}
