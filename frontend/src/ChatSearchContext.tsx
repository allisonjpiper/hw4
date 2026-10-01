import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductCard } from './types'

interface ChatSearchContextValue {
  results: ProductCard[] | null
  setResults: (results: ProductCard[]) => void
  clearResults: () => void
}

const ChatSearchContext = createContext<ChatSearchContextValue | undefined>(undefined)

export function ChatSearchProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<ProductCard[] | null>(null)

  return (
    <ChatSearchContext.Provider
      value={{
        results,
        setResults: (next) => setResultsState(next),
        clearResults: () => setResultsState(null),
      }}
    >
      {children}
    </ChatSearchContext.Provider>
  )
}

export function useChatSearch() {
  const ctx = useContext(ChatSearchContext)
  if (!ctx) throw new Error('useChatSearch must be used within a ChatSearchProvider')
  return ctx
}
