export default function ShimmerSkeleton({ className }) {
  return (
    <div
      className={`animate-shimmer bg-surface-elevated/60 rounded-lg ${className}`}
      aria-hidden="true"
    />
  )
}
