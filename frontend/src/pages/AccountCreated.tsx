import { Link, useLocation } from 'react-router-dom'
import './AuthForm.css'

export default function AccountCreated() {
  const location = useLocation()
  const email = (location.state as { email?: string } | null)?.email

  return (
    <div className="auth-form">
      <h1>Account Created</h1>
      <p className="auth-form__success">
        Your Campus Customs account{email ? ` for ${email}` : ''} has been created.
      </p>
      <p>Please log in to continue.</p>
      <Link to="/login" state={{ email }} className="auth-form__link-button">
        Go to Log In
      </Link>
    </div>
  )
}
