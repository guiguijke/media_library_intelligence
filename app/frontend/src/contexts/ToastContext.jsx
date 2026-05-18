import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toast) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    const item = { ...toast, id }
    setToasts((prev) => [...prev, item])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, toast.duration || 4000)
    return id
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

import { CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react'

function ToastContainer({ toasts }) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[60] space-y-2">
      {toasts.map((toast) => {
        let icon = <Info className="w-4 h-4 shrink-0" />
        let colors = 'bg-surface-elevated border-border text-primary'
        if (toast.type === 'success') {
          icon = <CheckCircle className="w-4 h-4 shrink-0" />
          colors = 'bg-green-500/10 border-green-500/20 text-green-400'
        } else if (toast.type === 'error') {
          icon = <XCircle className="w-4 h-4 shrink-0" />
          colors = 'bg-red-500/10 border-red-500/20 text-red-400'
        } else if (toast.type === 'warning') {
          icon = <AlertCircle className="w-4 h-4 shrink-0" />
          colors = 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
        }

        return (
          <div
            key={toast.id}
            className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm shadow-lg border ${colors}`}
          >
            {icon}
            <span className="font-medium">{toast.title}</span>
            {toast.message && <span className="text-secondary">{toast.message}</span>}
          </div>
        )
      })}
    </div>
  )
}
