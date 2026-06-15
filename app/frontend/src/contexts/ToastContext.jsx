import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'

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
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

function ToastContainer({ toasts, onRemove }) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[70] space-y-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  )
}

function Toast({ toast, onRemove }) {
  let icon = <Info className="w-4 h-4 shrink-0" />
  let colors = 'bg-surface-elevated border-border text-primary'
  if (toast.type === 'success') {
    icon = <CheckCircle className="w-4 h-4 shrink-0 text-green-400" />
    colors = 'bg-green-500/10 border-green-500/20 text-green-400'
  } else if (toast.type === 'error') {
    icon = <XCircle className="w-4 h-4 shrink-0 text-red-400" />
    colors = 'bg-red-500/10 border-red-500/20 text-red-400'
  } else if (toast.type === 'warning') {
    icon = <AlertCircle className="w-4 h-4 shrink-0 text-yellow-400" />
    colors = 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
  }

  return (
    <div
      className={`flex items-start gap-3 rounded-xl px-4 py-3 text-sm shadow-xl border min-w-[16rem] max-w-sm animate-fade-in-up ${colors}`}
    >
      {icon}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-primary">{toast.title}</p>
        {toast.message && <p className="text-secondary text-xs mt-0.5">{toast.message}</p>}
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        className="p-0.5 rounded text-secondary hover:text-primary hover:bg-black/10 transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
