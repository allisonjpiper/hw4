import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../api'
import { useCurrentProduct } from '../CurrentProductContext'
import type { ProductDetail as ProductDetailType } from '../types'
import './ProductDetail.css'

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { setCurrentProduct } = useCurrentProduct()

  useEffect(() => {
    if (!productId) return
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError('Could not load this product.'))
  }, [productId])

  // Publish which product is on screen so the chat widget can resolve
  // context-free questions like "is this in pink?" (Problem 8).
  useEffect(() => {
    if (product) {
      setCurrentProduct({ product_id: product.product_id, name: product.name })
    }
    return () => setCurrentProduct(null)
  }, [product, setCurrentProduct])

  if (error) return <p className="products__error">{error}</p>
  if (!product) return <p className="product-detail__loading">Loading...</p>

  return (
    <div className="product-detail">
      <Link to="/products" className="product-detail__back">
        ← Back to all products
      </Link>
      <div className="product-detail__layout">
        <img src={product.image_url} alt={product.name} className="product-detail__image" />
        <div className="product-detail__info">
          <h1>{product.name}</h1>
          <p className="product-detail__price">${product.price.toFixed(2)}</p>
          <p className="product-detail__description">{product.description}</p>

          <h3>Colors</h3>
          <p>{product.colors.join(', ')}</p>

          <h3>Sizes &amp; Stock</h3>
          <table className="product-detail__stock">
            <thead>
              <tr>
                <th>Size</th>
                <th>In Stock</th>
              </tr>
            </thead>
            <tbody>
              {product.inventory.map((inv) => (
                <tr key={inv.size}>
                  <td>{inv.size}</td>
                  <td>{inv.quantity > 0 ? inv.quantity : 'Out of stock'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button className="product-detail__add" disabled>
            Add to Cart (coming soon)
          </button>
        </div>
      </div>
    </div>
  )
}
