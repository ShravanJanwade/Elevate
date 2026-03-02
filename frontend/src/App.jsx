import { useState } from 'react'

function App() {
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAnalyze = async () => {
    setError('')
    setResults(null)

    if (!jobDescription.trim()) {
      setError('Please enter a job description.')
      return
    }
    if (!resumeText.trim() && !resumeFile) {
      setError('Please paste your resume text or upload a file.')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('job_description', jobDescription)

      if (resumeFile) {
        formData.append('resume_file', resumeFile)
      } else {
        formData.append('resume_text', resumeText)
      }

      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Something went wrong.')
        return
      }

      setResults(data)
    } catch (err) {
      setError('Could not connect to the analysis server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'high'
    if (score >= 40) return 'mid'
    return 'low'
  }

  return (
    <>
      <header className="header">
        <div className="header-inner">
          <div style={{ display: 'flex', alignItems: 'baseline' }}>
            <span className="logo">Elevate</span>
            <span className="logo-subtitle">AI Resume Analyzer</span>
          </div>
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <h1>Analyze &amp; Optimize Your Resume</h1>
          <p>
            Paste your resume and a job description below. Our AI engine uses
            semantic embeddings and NLP to score your fit and suggest improvements.
          </p>
        </section>

        {/* Input Panel */}
        <div className="input-panel">
          <div className="input-card">
            <label>
              <span className="label-icon">📄</span>
              Resume
            </label>
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
                    if (f) {
                      setResumeFile(f)
                      setResumeText('')
                    }
                  }}
                />
              </label>
              {resumeFile && <span className="file-name">{resumeFile.name}</span>}
            </div>
          </div>

          <div className="input-card">
            <label>
              <span className="label-icon">💼</span>
              Job Description
            </label>
            <textarea
              id="jd-input"
              placeholder="Paste the target job description here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>
        </div>

        {/* Analyze Button */}
        <div className="analyze-row">
          <button
            id="analyze-btn"
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Analyzing...
              </>
            ) : (
              <>🚀 Analyze Resume</>
            )}
          </button>
        </div>

        {/* Error */}
        {error && <div className="error-banner" id="error-msg">{error}</div>}

        {/* Results */}
        {results && (
          <div className="results-section" id="results">
            {/* Score Overview */}
            <div className="score-overview">
              <div className="score-card overall">
                <div className="score-value">{results.overall_score}%</div>
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

            {/* Keywords + Bullet Scores */}
            <div className="detail-grid">
              <div className="detail-card">
                <h3>🔑 Keyword Analysis</h3>
                {results.keyword_analysis.matched.length > 0 && (
                  <>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                      Found in your resume:
                    </p>
                    <div className="keyword-list" style={{ marginBottom: '1rem' }}>
                      {results.keyword_analysis.matched.map((kw, i) => (
                        <span className="keyword-tag matched" key={`m-${i}`}>✓ {kw}</span>
                      ))}
                    </div>
                  </>
                )}
                {results.keyword_analysis.missing.length > 0 && (
                  <>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                      Missing from your resume:
                    </p>
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
                  {results.semantic_analysis.bullet_scores.slice(0, 10).map((b, i) => (
                    <div className="bullet-item" key={i}>
                      <span className={`bullet-score ${getScoreColor(b.similarity)}`}>
                        {b.similarity}%
                      </span>
                      <span className="bullet-text">{b.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Suggestions */}
            {results.suggestions && results.suggestions.length > 0 && (
              <div className="suggestions-section">
                <h2>✨ AI Rewrite Suggestions</h2>
                {results.suggestions.map((s, i) => (
                  <div className="suggestion-card" key={i} id={`suggestion-${i}`}>
                    <div className="suggestion-label original-label">Original</div>
                    <div className="suggestion-text">{s.original}</div>
                    <div className="suggestion-label improved-label">Suggested Rewrite</div>
                    <div className="suggestion-text improved">{s.improved}</div>
                    <span className="suggestion-score-badge">
                      Similarity: {s.original_score}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        Elevate — AI Resume Analyzer &amp; Optimizer &bull; Foundations of AI Course Project
      </footer>
    </>
  )
}

export default App
