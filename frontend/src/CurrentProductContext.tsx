import { createContext, useContext, useState, type ReactNode } from 'react'

interface CurrentProductValue {
  product_id: string
  name: string
}

interface CurrentProductContextValue {
  currentProduct: CurrentProductValue | null
  setCurrentProduct: (product: CurrentProductValue | null) => void
}

const CurrentProductContext = createContext<CurrentProductContextValue | undefined>(undefined)

export function CurrentProductProvider({ children }: { children: ReactNode }) {
  const [currentProduct, setCurrentProduct] = useState<CurrentProductValue | null>(null)
  return (
    <CurrentProductContext.Provider value={{ currentProduct, setCurrentProduct }}>
      {children}
    </CurrentProductContext.Provider>
  )
}

export function useCurrentProduct() {
  const ctx = useContext(CurrentProductContext)
  if (!ctx) throw new Error('useCurrentProduct must be used within a CurrentProductProvider')
  return ctx
}
