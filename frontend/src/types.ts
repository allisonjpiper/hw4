export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  price: number
  image_url: string
}

export interface InventoryEntry {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  search_tags: string[]
  inventory: InventoryEntry[]
}

export interface User {
  id: number
  first_name: string | null
  last_name: string | null
  name: string
  email: string
}

export interface ProductCard {
  product_id: string
  name: string
  price: number
  image_url: string
  colors: string[]
  garment_type: string
}

export interface ChatReply {
  reply: string
  products: ProductCard[]
}

export interface PageContext {
  path: string
  product_id?: string
  product_name?: string
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: ProductCard[]
}
