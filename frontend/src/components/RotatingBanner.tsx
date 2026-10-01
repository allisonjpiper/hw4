import { useEffect, useState } from 'react'
import './RotatingBanner.css'

interface Slide {
  image: string
  alt: string
}

const SLIDE_INTERVAL_MS = 4000

export default function RotatingBanner({ slides }: { slides: Slide[] }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % slides.length)
    }, SLIDE_INTERVAL_MS)
    return () => clearInterval(id)
  }, [slides.length])

  return (
    <div className="rotating-banner">
      {slides.map((slide, i) => (
        <img
          key={slide.image}
          src={slide.image}
          alt={slide.alt}
          className={`rotating-banner__slide ${i === index ? 'rotating-banner__slide--active' : ''}`}
        />
      ))}
      <div className="rotating-banner__overlay" />
      <div className="rotating-banner__dots">
        {slides.map((slide, i) => (
          <button
            key={slide.image}
            className={`rotating-banner__dot ${i === index ? 'rotating-banner__dot--active' : ''}`}
            aria-label={`Show slide ${i + 1}`}
            onClick={() => setIndex(i)}
          />
        ))}
      </div>
    </div>
  )
}
