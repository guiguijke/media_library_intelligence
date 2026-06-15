export default function ScoreBadge({ score }) {
  let colorClass = 'bg-score-low/90 text-white'
  if (score >= 80) colorClass = 'bg-score-high/90 text-white'
  else if (score >= 60) colorClass = 'bg-score-mid/90 text-black'

  return (
    <div className={`absolute top-2 left-2 px-2 py-0.5 rounded-md text-xs font-bold shadow-sm backdrop-blur-sm ${colorClass}`}>
      {score ?? '—'}
    </div>
  )
}
