export default function ScoreBadge({ score }) {
  let colorClass = 'bg-score-low text-background'
  if (score >= 80) colorClass = 'bg-score-high text-background'
  else if (score >= 60) colorClass = 'bg-score-mid text-background'

  return (
    <div className={`absolute top-2 left-2 px-2 py-0.5 rounded text-xs font-bold ${colorClass}`}>
      {score}
    </div>
  )
}
