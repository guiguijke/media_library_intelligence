import React, { createContext, useContext, useState, useCallback } from 'react'

const SelectionContext = createContext(null)

export function SelectionProvider({ children }) {
  const [selected, setSelected] = useState(new Set())

  const toggle = useCallback((id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const isSelected = useCallback((id) => selected.has(id), [selected])

  const clear = useCallback(() => setSelected(new Set()), [])

  const add = useCallback((id) => {
    setSelected((prev) => new Set(prev).add(id))
  }, [])

  const remove = useCallback((id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  return (
    <SelectionContext.Provider value={{ selected, toggle, isSelected, clear, add, remove }}>
      {children}
    </SelectionContext.Provider>
  )
}

export function useSelection() {
  const ctx = useContext(SelectionContext)
  if (!ctx) throw new Error('useSelection must be used within SelectionProvider')
  return ctx
}
