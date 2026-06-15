import ShimmerSkeleton from './ShimmerSkeleton'

export default function LoadingSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="space-y-3">
          <ShimmerSkeleton className="aspect-[2/3] w-full" />
          <ShimmerSkeleton className="h-4 w-3/4" />
          <ShimmerSkeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  )
}
