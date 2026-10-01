import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api'
import { useChatSearch } from '../ChatSearchContext'
import type { Product } from '../types'
import './Products.css'

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState<string | null>(null)
  const { results, clearResults } = useChatSearch()

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError('Could not load products. Is the backend running?'))
  }, [])

  if (error) return <p className="products__error">{error}</p>

  const showingChatResults = results !== null
  const displayed = showingChatResults ? results : products

  return (
    <div className="products">
      <h1>{showingChatResults ? 'From Your Chat Search' : 'Shop All'}</h1>
      {showingChatResults && (
        <div className="products__chat-banner">
          <span>Showing products the shop assistant found for you.</span>
          <button onClick={clearResults}>View all products</button>
        </div>
      )}
      <div className="products__grid">
        {displayed.map((p, i) => (
          <Link key={p.product_id} to={`/products/${p.product_id}`} className="product-card">
            {!showingChatResults && i < 3 && <span className="product-card__badge">Best Seller</span>}
            <img src={p.image_url} alt={p.name} />
            <div className="product-card__body">
              <h3>{p.name}</h3>
              <p className="product-card__price">${p.price.toFixed(2)}</p>
              {'description' in p && <p className="product-card__description">{(p as Product).description}</p>}
              <p className="product-card__colors">{p.colors.join(', ')}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
