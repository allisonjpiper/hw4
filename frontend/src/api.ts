import type { ChatHistoryMessage, ChatReply, PageContext, Product, ProductDetail, User } from './types'

async function handleJson<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail ?? 'Something went wrong.')
  }
  return data as T
}

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch('/api/products')
  if (!res.ok) throw new Error('Failed to load products')
  return res.json()
}

export async function fetchProduct(productId: string): Promise<ProductDetail> {
  const res = await fetch(`/api/products/${productId}`)
  if (!res.ok) throw new Error('Failed to load product')
  return res.json()
}

export async function registerAccount(input: {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}): Promise<User> {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  return handleJson<User>(res)
}

export async function login(input: { email: string; password: string }): Promise<User> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  return handleJson<User>(res)
}

export async function sendChatMessage(
  message: string,
  userId: number | null,
  pageContext: PageContext,
): Promise<ChatReply> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId, page_context: pageContext }),
  })
  return handleJson<ChatReply>(res)
}

export async function fetchChatHistory(userId: number): Promise<ChatHistoryMessage[]> {
  const res = await fetch(`/api/chat/history/${userId}`)
  if (!res.ok) throw new Error('Failed to load chat history')
  return res.json()
}
