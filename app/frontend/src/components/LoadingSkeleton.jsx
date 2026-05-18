export default function LoadingSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="aspect-[2/3] bg-surface-elevated rounded-lg" />
          <div className="mt-2 h-4 bg-surface-elevated rounded w-3/4" />
          <div className="mt-1 h-3 bg-surface-elevated rounded w-1/2" />
        </div>
      ))}
    </div>
  )
}
