import { Link } from 'react-router-dom'
import RotatingBanner from '../components/RotatingBanner'
import './Home.css'

const FAN_FAVORITE_SLIDES = [
  { image: '/media/products/basic-hoodie-big-yale.jpg', alt: 'Basic Hoodie Big Yale' },
  { image: '/media/products/2025-yale-vs-harvard-t-shirt.jpg', alt: '2025 Yale Vs Harvard T Shirt' },
  { image: '/media/products/boola-boola-t-shirt.jpg', alt: 'Boola Boola T Shirt' },
]

export default function Home() {
  return (
    <div className="home">
      <section className="home__hero">
        <RotatingBanner slides={FAN_FAVORITE_SLIDES} />
        <div className="home__hero-content">
          <h1>Campus Customs</h1>
          <p>Bulldog spirit, made to order.</p>
          <Link to="/products" className="home__cta">
            Shop the Collection
          </Link>
        </div>
      </section>

      <section className="home__gallery">
        <h2>Fan Favorites</h2>
        <div className="home__gallery-grid">
          <Link to="/products/basic-hoodie-big-yale" className="home__gallery-item">
            <img src="/media/products/basic-hoodie-big-yale.jpg" alt="Basic Hoodie Big Yale" loading="lazy" />
            <span>Basic Hoodie Big Yale — $68</span>
          </Link>
          <Link to="/products/2025-yale-vs-harvard-t-shirt" className="home__gallery-item">
            <img src="/media/products/2025-yale-vs-harvard-t-shirt.jpg" alt="2025 Yale Vs Harvard T Shirt" loading="lazy" />
            <span>2025 Yale Vs Harvard Tee — $32</span>
          </Link>
          <Link to="/products/boola-boola-t-shirt" className="home__gallery-item">
            <img src="/media/products/boola-boola-t-shirt.jpg" alt="Boola Boola T Shirt" loading="lazy" />
            <span>Boola Boola Tee — $32</span>
          </Link>
        </div>
      </section>

      <section className="home__section">
        <h2>What We're About</h2>
        <p>
          Campus Customs started as a table of hand-stenciled sweatshirts outside the Elm Street
          dining hall and grew into a full lineup of gear for every corner of campus life. From
          residential college crewnecks to game-day tees, everything we carry is designed to be
          worn hard and worn proud, on the Green or in the bleachers.
        </p>
      </section>

      <section className="home__section home__section--alt">
        <h2>Featured This Week</h2>
        <p>
          It's rivalry season, and the shop floor is stacked with fresh Harvard-Yale graphics,
          restocked hoodies in every residential college colorway, and a run of fencing, sailing,
          and ice hockey left-chest pieces for the team supporters in your life.
        </p>
        <Link to="/products" className="home__link">
          Browse everything →
        </Link>
      </section>
    </div>
  )
}
