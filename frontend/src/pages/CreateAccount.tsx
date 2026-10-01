import { useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerAccount } from '../api'
import './AuthForm.css'

function passwordStrengthErrors(password: string): string[] {
  const errors: string[] = []
  if (password.length < 8) errors.push('at least 8 characters')
  if (!/[a-z]/.test(password)) errors.push('a lowercase letter')
  if (!/[A-Z]/.test(password)) errors.push('an uppercase letter')
  if (!/\d/.test(password)) errors.push('a number')
  if (!/[^A-Za-z0-9]/.test(password)) errors.push('a symbol')
  return errors
}

export default function CreateAccount() {
  const navigate = useNavigate()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const strengthErrors = useMemo(() => passwordStrengthErrors(password), [password])
  const passwordsMatch = password.length > 0 && password === confirmPassword

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (strengthErrors.length > 0) {
      setError(`Password needs: ${strengthErrors.join(', ')}.`)
      return
    }
    if (!passwordsMatch) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      await registerAccount({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        confirm_password: confirmPassword,
      })
      navigate('/account-created', { state: { email } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create account.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-form">
      <h1>Create Account</h1>
      {error && <p className="auth-form__error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <label>
          First Name
          <input
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Ada"
            required
          />
        </label>
        <label>
          Last Name
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Lovelace"
            required
          />
        </label>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@yale.edu"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </label>
        <p className="auth-form__hint">
          Must include an uppercase and lowercase letter, a number, and a symbol.
        </p>
        <label>
          Confirm Password
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating account...' : 'Create Account'}
        </button>
      </form>
    </div>
  )
}
