import { useState } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import HistoryPage from './pages/HistoryPage'
import { apiFetch } from './lib/api'

function Navbar() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <header className="header">
      <div className="header-inner">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <span className="logo">Elevate</span>
          </Link>
          <span className="logo-subtitle">AI Resume Analyzer</span>
        </div>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Link to="/history" style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textDecoration: 'none' }}>
              History
            </Link>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{user.email}</span>
            <button
              onClick={handleSignOut}
              style={{
                background: 'none',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '0.25rem 0.75rem',
                cursor: 'pointer',
                fontSize: '0.82rem',
                color: 'var(--text-muted)',
              }}
            >
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

function AnalyzerPage() {
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [useLLM, setUseLLM] = useState(false)
  const [sectionData, setSectionData] = useState(null)

  const [bulletRewrites, setBulletRewrites] = useState({})
  const [bulletOverrides, setBulletOverrides] = useState({})

  const handleAnalyze = async () => {
    setError('')
    setResults(null)
    setSectionData(null)
    setBulletRewrites({})
    setBulletOverrides({})

    if (!jobDescription.trim()) { setError('Please enter a job description.'); return }
    if (!resumeText.trim() && !resumeFile) { setError('Please paste your resume text or upload a file.'); return }

    setLoading(true)
    try {
      let res
      if (resumeFile) {
        const formData = new FormData()
        formData.append('job_description', jobDescription)
        formData.append('resume_file', resumeFile)
        const { data: { session } } = await (await import('./lib/supabaseClient')).supabase.auth.getSession()
        res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/analyze`, {
          method: 'POST',
          body: formData,
          headers: { Authorization: `Bearer ${session?.access_token}` },
        })
      } else {
        res = await apiFetch('/api/analyze', {
          method: 'POST',
          body: JSON.stringify({ job_description: jobDescription, resume_text: resumeText }),
        })
      }

      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Something went wrong.'); return }

      setResults(data)

      if (data.session_id) {
        const secRes = await apiFetch('/api/analyze/sections', {
          method: 'POST',
          body: JSON.stringify({
            job_description: jobDescription,
            resume_text: resumeFile ? '' : resumeText,
            session_id: data.session_id,
          }),
        })
        const secData = await secRes.json()
        if (!secData.error) setSectionData(secData.sections)
      }
    } catch (err) {
      setError('Could not connect to the analysis server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleRewrite = async (index, bullet) => {
    setBulletRewrites((prev) => ({ ...prev, [index]: { ...prev[index], loading: true } }))
    try {
      const res = await apiFetch('/api/rewrite', {
        method: 'POST',
        body: JSON.stringify({
          bullet,
          job_description: jobDescription,
          use_llm: useLLM,
          bullet_id: results?.semantic_analysis?.bullet_scores?.[index]?.bullet_id || '',
        }),
      })
      const data = await res.json()
      setBulletRewrites((prev) => ({
        ...prev,
        [index]: { rewritten: data.rewritten, method: data.method, loading: false },
      }))
    } catch {
      setBulletRewrites((prev) => ({ ...prev, [index]: { ...prev[index], loading: false, error: 'Rewrite failed.' } }))
    }
  }

  const handleAccept = async (index, rewritten) => {
    const bulletText = rewritten
    let newScore = bulletOverrides[index]?.score ?? null
    try {
      const res = await apiFetch('/api/rescore/bullet', {
        method: 'POST',
        body: JSON.stringify({
          bullet: bulletText,
          job_description: jobDescription,
          bullet_id: results?.semantic_analysis?.bullet_scores?.[index]?.bullet_id || '',
        }),
      })
      const data = await res.json()
      newScore = data.new_score ?? newScore
    } catch { }

    setBulletOverrides((prev) => ({ ...prev, [index]: { text: rewritten, score: newScore } }))
    setBulletRewrites((prev) => { const n = { ...prev }; delete n[index]; return n })
  }

  const handleDiscard = (index) => {
    setBulletRewrites((prev) => { const n = { ...prev }; delete n[index]; return n })
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'high'
    if (score >= 40) return 'mid'
    return 'low'
  }

  const computeDisplayScore = () => {
    if (!results) return null
    const bullets = results.semantic_analysis?.bullet_scores || []
    if (bullets.length === 0) return results.overall_score
    const overallSem = bullets.reduce((sum, b, i) => {
      const score = bulletOverrides[i]?.score ?? b.similarity
      return sum + score
    }, 0) / bullets.length
    return Math.round((results.keyword_analysis.match_percentage * 0.4 + overallSem * 0.6) * 10) / 10
  }

  const displayScore = computeDisplayScore()

  return (
    <main className="container">
      <section className="hero">
        <h1>Analyze &amp; Optimize Your Resume</h1>
        <p>
          Paste your resume and a job description below. Our AI engine uses
          semantic embeddings and NLP to score your fit and suggest improvements.
        </p>
      </section>

      <div className="input-panel">
        <div className="input-card">
          <label><span className="label-icon">📄</span>Resume</label>
          <textarea
            id="resume-input"
            placeholder="Paste your resume text here..."
            value={resumeText}
            onChange={(e) => { setResumeText(e.target.value); setResumeFile(null) }}
          />
          <div className="file-upload-row">
            <label className="file-upload-btn" id="upload-btn">
              📎 Upload PDF
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={(e) => {
                  const f = e.target.files[0]
                  if (f) { setResumeFile(f); setResumeText('') }
                }}
              />
            </label>
            {resumeFile && <span className="file-name">{resumeFile.name}</span>}
          </div>
        </div>

        <div className="input-card">
          <label><span className="label-icon">💼</span>Job Description</label>
          <textarea
            id="jd-input"
            placeholder="Paste the target job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          />
        </div>
      </div>

      <div className="analyze-row" style={{ flexDirection: 'column', gap: '0.75rem' }}>
        <button id="analyze-btn" className="analyze-btn" onClick={handleAnalyze} disabled={loading}>
          {loading ? <><span className="spinner" />Analyzing…</> : <>🚀 Analyze Resume</>}
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', justifyContent: 'center' }}>
          <label className="toggle-switch">
            <input type="checkbox" checked={useLLM} onChange={(e) => setUseLLM(e.target.checked)} />
            <span className="toggle-slider" />
          </label>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Use AI Rewrite (Flan-T5)</span>
        </div>
      </div>

      {error && <div className="error-banner" id="error-msg">{error}</div>}

      {results && (
        <div className="results-section" id="results">
          <div className="score-overview">
            <div className="score-card overall">
              <div className="score-value">{displayScore}%</div>
              <div className="score-label">Overall Match</div>
            </div>
            <div className="score-card keyword">
              <div className="score-value">{results.keyword_analysis.match_percentage}%</div>
              <div className="score-label">Keyword Match</div>
            </div>
            <div className="score-card semantic">
              <div className="score-value">{results.semantic_analysis.overall_score}%</div>
              <div className="score-label">Semantic Similarity</div>
            </div>
          </div>

          <div className="detail-grid">
            <div className="detail-card">
              <h3>🔑 Keyword Analysis</h3>
              {results.keyword_analysis.matched.length > 0 && (
                <>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Found in your resume:</p>
                  <div className="keyword-list" style={{ marginBottom: '1rem' }}>
                    {results.keyword_analysis.matched.map((kw, i) => (
                      <span className="keyword-tag matched" key={`m-${i}`}>✓ {kw}</span>
                    ))}
                  </div>
                </>
              )}
              {results.keyword_analysis.missing.length > 0 && (
                <>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Missing from your resume:</p>
                  <div className="keyword-list">
                    {results.keyword_analysis.missing.map((kw, i) => (
                      <span className="keyword-tag missing" key={`x-${i}`}>✗ {kw}</span>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="detail-card">
              <h3>📊 Bullet-Point Scores</h3>
              <div className="bullet-list">
                {results.semantic_analysis.bullet_scores.slice(0, 10).map((b, i) => {
                  const override = bulletOverrides[i]
                  const displayText = override?.text ?? b.text
                  const displaySim = override?.score ?? b.similarity
                  const rw = bulletRewrites[i]
                  return (
                    <div key={i} style={{ marginBottom: '0.75rem' }}>
                      <div className="bullet-item">
                        <span className={`bullet-score ${getScoreColor(displaySim)}`}>{displaySim}%</span>
                        <span className="bullet-text">{displayText}</span>
                        <button
                          className="rewrite-btn"
                          onClick={() => handleRewrite(i, displayText)}
                          disabled={rw?.loading}
                          title="Rewrite this bullet"
                        >
                          {rw?.loading ? (useLLM ? <><span className="spinner" style={{ width: '10px', height: '10px' }} /></> : '…') : '✍️'}
                        </button>
                      </div>
                      {rw?.loading && useLLM && (
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                          AI is rewriting your bullet… this may take ~30s
                        </p>
                      )}
                      {rw?.rewritten && (
                        <div className="rewrite-suggestion">
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                            Suggested ({rw.method}):
                          </div>
                          <div className="suggestion-text improved" style={{ marginBottom: '0.5rem' }}>{rw.rewritten}</div>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button className="accept-btn" onClick={() => handleAccept(i, rw.rewritten)}>Accept</button>
                            <button className="discard-btn" onClick={() => handleDiscard(i)}>Discard</button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {sectionData && sectionData.length > 0 && (
            <div className="section-scores-panel">
              <h2>🗂 Section Scores</h2>
              <div className="section-scores-grid">
                {sectionData.map((s, i) => (
                  <div className="section-score-card" key={i}>
                    <div className="section-score-header">
                      <span className="section-name">{s.name.charAt(0).toUpperCase() + s.name.slice(1)}</span>
                      <span className={`section-score-value ${getScoreColor(s.score)}`}>{s.score}%</span>
                    </div>
                    <div className="section-score-bar-track">
                      <div className={`section-score-bar-fill ${getScoreColor(s.score)}`} style={{ width: `${Math.min(s.score, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.suggestions && results.suggestions.length > 0 && (
            <div className="suggestions-section">
              <h2>✨ AI Rewrite Suggestions</h2>
              {results.suggestions.map((s, i) => (
                <div className="suggestion-card" key={i} id={`suggestion-${i}`}>
                  <div className="suggestion-label original-label">Original</div>
                  <div className="suggestion-text">{s.original}</div>
                  <div className="suggestion-label improved-label">Suggested Rewrite</div>
                  <div className="suggestion-text improved">{s.improved}</div>
                  <span className="suggestion-score-badge">Similarity: {s.original_score}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  )
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AnalyzerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
      </Routes>
      <footer className="footer">
        Elevate — AI Resume Analyzer &amp; Optimizer
      </footer>
    </>
  )
}
