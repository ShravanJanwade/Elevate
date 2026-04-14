import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { CheckCircle } from 'lucide-react'

export default function SignupPage() {
  const { signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) { setError('Passwords do not match.'); return }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return }
    setLoading(true)
    const { error } = await signUp(email, password)
    setLoading(false)
    if (error) { setError(error.message) } else { setDone(true) }
  }

  if (done) {
    return (
      <div className="auth-page">
        <div className="auth-center">
          <div className="auth-card" style={{ textAlign: 'center' }}>
            <div className="auth-confirm-icon">
              <CheckCircle size={32} color="#10b981" strokeWidth={1.5} />
            </div>
            <h1 className="auth-title">Check your email</h1>
            <p className="auth-desc" style={{ marginTop: '0.5rem' }}>
              We sent a confirmation link to{' '}
              <strong style={{ color: 'var(--text-heading)' }}>{email}</strong>.
              Click it to activate your account.
            </p>
            <p className="auth-footer" style={{ marginTop: '2rem' }}>
              Already confirmed?{' '}
              <Link to="/login" className="auth-link">Sign in</Link>
            </p>
          </div>
          <p className="auth-legal">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-center">

        {/* Card */}
        <div className="auth-card">
          <div className="auth-card-top">
            <h1 className="auth-title">Create account</h1>
            <p className="auth-desc">Start screening resumes with AI in minutes.</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <div className="auth-field">
              <label className="auth-label" htmlFor="email">Email</label>
              <input
                id="email"
                className="auth-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label className="auth-label" htmlFor="password">Password</label>
              <input
                id="password"
                className="auth-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Min. 6 characters"
                autoComplete="new-password"
                minLength={6}
              />
            </div>

            <div className="auth-field">
              <label className="auth-label" htmlFor="confirm">Confirm password</label>
              <input
                id="confirm"
                className="auth-input"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-btn" type="submit" disabled={loading}>
              {loading
                ? <><span className="auth-spinner" /> Creating account…</>
                : 'Create account'
              }
            </button>
          </form>

          <p className="auth-footer">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign in</Link>
          </p>
        </div>

        <p className="auth-legal">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const { signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    const { error } = await signUp(email, password)
    setLoading(false)
    if (error) {
      setError(error.message)
    } else {
      setDone(true)
    }
  }

  if (done) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1 className="logo">Elevate</h1>
          <h2>Check your email</h2>
          <p>We sent a confirmation link to <strong>{email}</strong>. Click it to activate your account, then <Link to="/login">sign in</Link>.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="logo">Elevate</h1>
        <h2>Create Account</h2>
        <form onSubmit={handleSubmit}>
          <div className="auth-field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>
          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>
          <div className="auth-field">
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>
          {error && <div className="error-banner">{error}</div>}
          <button className="analyze-btn" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Sign Up'}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign In</Link>
        </p>
      </div>
    </div>
  )
}
