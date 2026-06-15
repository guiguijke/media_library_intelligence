import { useEffect, useRef, useState } from 'react'
import { useTasks } from '../hooks/useTasks'
import { useToast } from '../contexts/ToastContext'
import { CheckCircle, XCircle, Loader2, Zap, X, Minus, Maximize2 } from 'lucide-react'

export default function TaskMonitor() {
  const { data: tasks } = useTasks()
  const { addToast } = useToast()
  const prevTasksRef = useRef([])
  const [recentDone, setRecentDone] = useState([])
  const [minimized, setMinimized] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  const activeTasks = (tasks || []).filter((t) => t.status === 'running')
  const hasActive = activeTasks.length > 0 || recentDone.length > 0

  useEffect(() => {
    if (!tasks) {
      prevTasksRef.current = []
      return
    }

    const prevRunning = prevTasksRef.current.filter((t) => t.status === 'running')
    const currentRunningIds = new Set(
      (tasks || []).filter((t) => t.status === 'running').map((t) => t.task_id)
    )

    const justFinished = prevRunning.filter((t) => !currentRunningIds.has(t.task_id))

    justFinished.forEach((t) => {
      const currentTask = (tasks || []).find((ct) => ct.task_id === t.task_id)
      const success = currentTask?.status === 'success'
      addToast({
        type: success ? 'success' : 'error',
        title: t.task_name || 'Task',
        message: success ? 'Completed successfully' : currentTask?.message || 'Failed',
      })

      const doneTask = {
        ...currentTask,
        _doneAt: Date.now(),
      }
      setRecentDone((prev) => [...prev, doneTask])
      setTimeout(() => {
        setRecentDone((prev) => prev.filter((x) => x.task_id !== t.task_id))
      }, 3000)
    })

    prevTasksRef.current = tasks
  }, [tasks])

  useEffect(() => {
    if (activeTasks.length > 0) {
      setDismissed(false)
    }
  }, [activeTasks.length])

  const displayTasks = [
    ...activeTasks,
    ...recentDone.filter((d) => !activeTasks.find((a) => a.task_id === d.task_id)),
  ]

  const showOverlay = hasActive && !dismissed && !minimized

  return (
    <>
      {showOverlay && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in-up">
          <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-md shadow-2xl mx-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-accent/10 rounded-xl">
                <Zap className="w-6 h-6 text-accent animate-pulse" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-primary">Sync in progress</h3>
                <p className="text-sm text-secondary">Please wait while we update your library</p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setMinimized(true)}
                  className="p-1.5 rounded-lg text-secondary hover:text-primary hover:bg-surface-elevated transition-colors focus-ring"
                  title="Minimize"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setDismissed(true)}
                  className="p-1.5 rounded-lg text-secondary hover:text-primary hover:bg-surface-elevated transition-colors focus-ring"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-5">
              {displayTasks.map((task) => {
                const isDone = task.status === 'success' || task.status === 'failure'
                return (
                  <div key={task.task_id} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-primary">{task.task_name}</span>
                      <span className="text-accent font-bold">{task.progress ?? 0}%</span>
                    </div>
                    <div className="h-3 bg-surface-elevated rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ease-out ${
                          isDone ? 'bg-green-500' : 'bg-accent'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, task.progress ?? 0))}%` }}
                      />
                    </div>
                    <p className="text-xs text-secondary">{task.message || 'Working...'}</p>
                  </div>
                )
              })}
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 text-sm text-secondary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Do not close this page</span>
            </div>
          </div>
        </div>
      )}

      {hasActive && (
        <div className="sticky top-16 z-40 bg-surface/95 backdrop-blur-xl border-b border-border px-4 py-2 animate-fade-in-up">
          <div className="max-w-7xl mx-auto flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-accent" />
            <span className="text-sm font-medium text-primary">
              {activeTasks.length > 0
                ? `${activeTasks.length} sync task(s) running...`
                : 'Finishing up...'}
            </span>
            <div className="flex-1 h-1.5 bg-surface-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(
                      0,
                      displayTasks.reduce((a, t) => a + (t.progress ?? 0), 0) /
                        displayTasks.length
                    )
                  )}%`,
                }}
              />
            </div>
            {minimized && (
              <button
                onClick={() => setMinimized(false)}
                className="p-1 rounded-lg text-secondary hover:text-primary hover:bg-surface-elevated transition-colors focus-ring"
                title="Expand"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
    </>
  )
}
