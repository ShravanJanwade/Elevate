import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    apiFetch('/api/history')
      .then((r) => r.json())
      .then((data) => {
        if (data.error) setError(data.error)
        else setSessions(data.sessions || [])
      })
      .catch(() => setError('Failed to load history.'))
      .finally(() => setLoading(false))
  }, [])

  const loadDetail = async (id) => {
    setSelected(id)
    setDetail(null)
    setDetailLoading(true)
    try {
      const r = await apiFetch(`/api/history/${id}`)
      const data = await r.json()
      if (data.error) setError(data.error)
      else setDetail(data)
    } catch {
      setError('Failed to load session detail.')
    } finally {
      setDetailLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'high'
    if (score >= 40) return 'mid'
    return 'low'
  }

  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }}>Analysis History</h2>
        <button className="analyze-btn" style={{ padding: '0.5rem 1.2rem', fontSize: '0.9rem' }} onClick={() => navigate('/')}>
          + New Analysis
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <p>Loading…</p>
      ) : sessions.length === 0 ? (
        <p>No past analyses found. Run your first analysis!</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 2fr' : '1fr', gap: '1.5rem' }}>
          <div>
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`suggestion-card ${selected === s.id ? 'selected-session' : ''}`}
                style={{ cursor: 'pointer', marginBottom: '0.75rem' }}
                onClick={() => loadDetail(s.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {new Date(s.created_at).toLocaleString()}
                  </span>
                  <span className={`bullet-score ${getScoreColor(s.overall_score)}`}>
                    {s.overall_score}%
                  </span>
                </div>
                {s.session_label && <div style={{ fontWeight: 600, marginTop: '0.25rem' }}>{s.session_label}</div>}
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {s.job_description_preview}{s.job_description_preview?.length >= 100 ? '…' : ''}
                </div>
              </div>
            ))}
          </div>

          {selected && (
            <div>
              {detailLoading ? (
                <p>Loading session…</p>
              ) : detail ? (
                <>
                  <div className="score-overview" style={{ marginBottom: '1rem' }}>
                    <div className="score-card overall">
                      <div className="score-value">{detail.session.overall_score}%</div>
                      <div className="score-label">Overall</div>
                    </div>
                    <div className="score-card keyword">
                      <div className="score-value">{detail.session.keyword_score}%</div>
                      <div className="score-label">Keyword</div>
                    </div>
                    <div className="score-card semantic">
                      <div className="score-value">{detail.session.semantic_score}%</div>
                      <div className="score-label">Semantic</div>
                    </div>
                  </div>

                  {detail.section_scores?.length > 0 && (
                    <div className="section-scores-panel" style={{ marginBottom: '1rem' }}>
                      <h3>Section Scores</h3>
                      {detail.section_scores.map((s, i) => (
                        <div key={i} style={{ marginBottom: '0.5rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>{s.section_name}</span>
                            <span className={`bullet-score ${getScoreColor(s.similarity_score)}`}>{s.similarity_score}%</span>
                          </div>
                          <div className="section-score-bar-track">
                            <div className={`section-score-bar-fill ${getScoreColor(s.similarity_score)}`} style={{ width: `${Math.min(s.similarity_score, 100)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {detail.bullets?.length > 0 && (
                    <div className="detail-card">
                      <h3>Bullet Scores</h3>
                      <div className="bullet-list">
                        {detail.bullets.map((b, i) => (
                          <div key={i} className="bullet-item">
                            <span className={`bullet-score ${getScoreColor(b.similarity_score)}`}>{b.similarity_score}%</span>
                            <span className="bullet-text">{b.rewritten_text || b.bullet_text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : null}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
