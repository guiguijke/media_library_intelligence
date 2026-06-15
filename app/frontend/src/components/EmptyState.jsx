export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 sm:py-24 px-4 text-center animate-fade-in-up">
      {Icon && (
        <div className="p-4 rounded-2xl bg-surface-elevated text-muted mb-5">
          <Icon className="w-10 h-10" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-primary">{title}</h3>
      {description && <p className="mt-1.5 text-sm text-secondary max-w-sm">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
