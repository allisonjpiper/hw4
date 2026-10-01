import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { fetchChatHistory, sendChatMessage } from '../api'
import { useAuth } from '../AuthContext'
import { useChatSearch } from '../ChatSearchContext'
import { useCurrentProduct } from '../CurrentProductContext'
import type { PageContext, ProductCard } from '../types'
import './ChatWidget.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ProductCard[]
}

const GREETING: Message = {
  role: 'assistant',
  content: 'Hi! I can help you find Campus Customs gear, check prices, and check stock. What are you looking for?',
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { setResults } = useChatSearch()
  const { currentProduct } = useCurrentProduct()
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])

  // Reload a logged-in customer's saved conversation when they arrive/log in;
  // reset to the plain greeting for a guest or after logging out (Problem 8).
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      return
    }
    fetchChatHistory(user.id)
      .then((history) => {
        if (history.length > 0) {
          setMessages(history)
        }
      })
      .catch(() => {
        /* keep the default greeting if history can't be loaded */
      })
  }, [user])

  async function handleSend() {
    const text = draft.trim()
    if (!text || sending) return
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const pageContext: PageContext = currentProduct
        ? { path: location.pathname, product_id: currentProduct.product_id, product_name: currentProduct.name }
        : { path: location.pathname }
      const reply = await sendChatMessage(text, user?.id ?? null, pageContext)
      setMessages((prev) => [...prev, { role: 'assistant', content: reply.reply, products: reply.products }])
      if (reply.products.length > 0) {
        // API contract: whenever the agent's reply includes product cards,
        // the Products page updates to show exactly those products.
        setResults(reply.products)
        navigate('/products')
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "Sorry, I couldn't reach the shop assistant. Please try again." },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-widget">
      <div
        className={`chat-widget__panel ${open ? 'chat-widget__panel--open' : ''}`}
        aria-hidden={!open}
      >
        <div className="chat-widget__header">
          <span>Campus Customs Chat</span>
          <button onClick={() => setOpen(false)} aria-label="Close chat" tabIndex={open ? 0 : -1}>
            ×
          </button>
        </div>
        <div className="chat-widget__messages">
          {messages.map((m, i) => (
            <div key={i} className={`chat-widget__message chat-widget__message--${m.role}`}>
              {m.content}
              {m.products && m.products.length > 0 && (
                <div className="chat-widget__cards">
                  {m.products.map((p) => (
                    <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-widget__card">
                      <img src={p.image_url} alt={p.name} />
                      <div>
                        <div className="chat-widget__card-name">{p.name}</div>
                        <div className="chat-widget__card-price">${p.price.toFixed(2)}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="chat-widget__message chat-widget__message--assistant">Thinking...</div>
          )}
        </div>
        <div className="chat-widget__input-row">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about products..."
            disabled={sending}
            tabIndex={open ? 0 : -1}
          />
          <button onClick={handleSend} disabled={sending} tabIndex={open ? 0 : -1}>
            Send
          </button>
        </div>
      </div>
      <button className="chat-widget__toggle" onClick={() => setOpen((o) => !o)}>
        {open ? 'Close' : 'Chat'}
      </button>
    </div>
  )
}
