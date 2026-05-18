import { useEffect, useRef, useState } from 'react'
import { useTasks } from '../hooks/useTasks'
import { CheckCircle, XCircle, Loader2, Zap } from 'lucide-react'

export default function TaskMonitor() {
  const { data: tasks } = useTasks()
  const prevTasksRef = useRef([])
  const [toasts, setToasts] = useState([])

  const activeTasks = (tasks || []).filter((t) => t.status === 'running')
  const hasActive = activeTasks.length > 0

  useEffect(() => {
    if (!tasks) {
      prevTasksRef.current = []
      return
    }

    const prevRunning = prevTasksRef.current.filter((t) => t.status === 'running')
    const currentRunningIds = new Set(
      (tasks || []).filter((t) => t.status === 'running').map((t) => t.task_id)
    )

    const completed = prevRunning.filter((t) => !currentRunningIds.has(t.task_id))

    completed.forEach((t) => {
      const success = t.status === 'success'
      const toast = {
        id: `${t.task_id}-${Date.now()}`,
        name: t.task_name || 'Task',
        success,
        message: success ? 'Completed successfully' : t.message || 'Failed',
      }
      setToasts((prev) => [...prev, toast])
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== toast.id))
      }, 4000)
    })

    prevTasksRef.current = tasks
  }, [tasks])

  return (
    <>
      {/* Main progress overlay - always visible during sync */}
      {hasActive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl p-8 w-full max-w-md shadow-2xl mx-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-accent/10 rounded-lg">
                <Zap className="w-6 h-6 text-accent animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-primary">Sync in progress</h3>
                <p className="text-sm text-secondary">Please wait while we update your library</p>
              </div>
            </div>

            <div className="space-y-5">
              {activeTasks.map((task) => (
                <div key={task.task_id} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-primary">{task.task_name}</span>
                    <span className="text-accent font-bold">{task.progress ?? 0}%</span>
                  </div>
                  <div className="h-3 bg-surface-elevated rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${Math.min(100, Math.max(0, task.progress ?? 0))}%` }}
                    />
                  </div>
                  <p className="text-xs text-secondary">{task.message || 'Working...'}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 text-sm text-secondary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Do not close this page</span>
            </div>
          </div>
        </div>
      )}

      {/* Sticky mini-bar for quick view (shows below navbar when not in overlay) */}
      {hasActive && (
        <div className="sticky top-16 z-40 bg-surface/95 backdrop-blur border-b border-border px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-accent" />
            <span className="text-sm font-medium text-primary">
              {activeTasks.length} sync task(s) running...
            </span>
            <div className="flex-1 h-1.5 bg-surface-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all"
                style={{
                  width: `${Math.min(100, Math.max(0, activeTasks.reduce((a, t) => a + (t.progress ?? 0), 0) / activeTasks.length))}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Toasts */}
      <div className="fixed bottom-4 right-4 z-[60] space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm shadow-lg border ${
              toast.success
                ? 'bg-green-500/10 border-green-500/20 text-green-400'
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            }`}
          >
            {toast.success ? (
              <CheckCircle className="w-4 h-4 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 shrink-0" />
            )}
            <span className="font-medium">{toast.name}</span>
            <span className="text-secondary">{toast.message}</span>
          </div>
        ))}
      </div>
    </>
  )
}
