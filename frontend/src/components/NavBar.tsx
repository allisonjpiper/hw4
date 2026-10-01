import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import './NavBar.css'

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <NavLink to="/" className="navbar__brand">
        <span className="navbar__brand-mark">CC</span>
        Campus Customs
      </NavLink>
      <nav className="navbar__links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          Home
        </NavLink>
        <NavLink to="/products" className={({ isActive }) => (isActive ? 'active' : '')}>
          Products
        </NavLink>
        <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>
          About Us
        </NavLink>
        {user ? (
          <>
            <span className="navbar__greeting">Hi, {user.first_name ?? user.name}</span>
            <button className="navbar__cta navbar__cta--button" onClick={handleLogout}>
              Log Out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className={({ isActive }) => (isActive ? 'active' : '')}>
              Log In
            </NavLink>
            <NavLink to="/create-account" className="navbar__cta">
              Create Account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  )
}
