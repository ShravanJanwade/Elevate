import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '../lib/api'
import { Calendar, Briefcase, FileText, ChevronRight, Activity, TrendingUp, Inbox } from 'lucide-react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'
// Premium Radar Component
function MetricsRadarChart({ overall, keyword, semantic }) {
  const data = [
    { metric: 'Overall Match', score: overall, fullMark: 100 },
    { metric: 'Keyword Matrix', score: keyword, fullMark: 100 },
    { metric: 'Semantic Depth', score: semantic, fullMark: 100 },
  ];

  return (
    <div style={{ width: '100%', height: '320px', padding: '1rem 0' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <defs>
            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0f766e" stopOpacity={0.6}/>
              <stop offset="100%" stopColor="#4f46e5" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="scoreStroke" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#4f46e5"/>
              <stop offset="100%" stopColor="#0f766e"/>
            </linearGradient>
          </defs>
          <PolarGrid stroke="var(--border-subtle)" strokeDasharray="3 3" />
          <PolarAngleAxis 
            dataKey="metric" 
            tick={{ fill: 'var(--brand-navy)', fontSize: 14, fontWeight: 700 }} 
          />
          <PolarRadiusAxis 
            domain={[0, 100]} 
            tick={false} 
            axisLine={false} 
          />
          <Tooltip 
            cursor={{ stroke: 'var(--border-subtle)', strokeWidth: 1 }}
            wrapperStyle={{ outline: 'none' }}
            contentStyle={{ 
              backgroundColor: '#fff', 
              borderRadius: '12px', 
              border: '1px solid var(--border-subtle)', 
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
              fontWeight: 600,
              color: 'var(--brand-navy)',
              padding: '12px 16px'
            }}
            itemStyle={{ color: '#0f766e', fontWeight: 800, fontSize: '1.2rem', padding: 0 }}
            labelStyle={{ color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', fontSize: '0.8rem', letterSpacing: '0.05em' }}
            formatter={(value) => [`${value}%`, 'Score']}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="url(#scoreStroke)"
            strokeWidth={3}
            fill="url(#scoreGradient)"
            fillOpacity={1}
            activeDot={{ r: 6, fill: '#0f766e', stroke: '#fff', strokeWidth: 2 }}
            isAnimationActive={true}
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

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
    if (selected === id) return;
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
    if (score >= 80) return '#0f766e' // teal
    if (score >= 50) return '#4f46e5' // indigo
    return '#ef4444' // red
  }
  
  const getScoreBg = (score) => {
    if (score >= 80) return '#ccfbf1' // teal-bg
    if (score >= 50) return '#e0e7ff' // indigo-bg
    return '#fee2e2' // red-bg
  }

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch { return dateStr }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
      style={{ padding: '3rem 2rem', maxWidth: '1400px', margin: '0 auto', width: '100%', minHeight: '100vh' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--brand-navy)', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity className="icon-grad" size={32} /> Analysis History
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem', fontSize: '1.05rem' }}>Review your past resume evaluations and growth metrics.</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/')}>
          + New Analysis
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '12px', marginBottom: '2rem', border: '1px solid #fca5a5' }}>
          ⚠ {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>
          <div className="spinner" style={{ marginBottom: '1rem' }} /> <br/> Loading architectural archives...
        </div>
      ) : sessions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '6rem 2rem', background: 'var(--bg-elevated)', borderRadius: '24px', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          <Inbox size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 1.5rem', opacity: 0.5 }} />
          <h3 style={{ fontSize: '1.5rem', color: 'var(--brand-navy)', marginBottom: '0.5rem' }}>No past analyses found.</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto' }}>Your career trajectory begins here. Head back to the dashboard to run your first evaluation.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
          
          {/* Left Grid: Session List */}
          <div style={{ flex: selected ? '0 0 35%' : '1', display: 'grid', gridTemplateColumns: selected ? '1fr' : 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1rem', transition: 'all 0.5s ease' }}>
            {sessions.map((s) => {
              const focus = selected === s.id;
              return (
                <motion.div
                  key={s.id}
                  layout
                  onClick={() => loadDetail(s.id)}
                  whileHover={{ y: -4, boxShadow: '0 12px 24px -10px rgba(0,0,0,0.1)' }}
                  style={{
                    background: focus ? '#fff' : 'var(--bg-elevated)',
                    border: focus ? '2px solid var(--accent-gold)' : '1px solid var(--border-subtle)',
                    borderRadius: '16px', padding: '1.5rem', cursor: 'pointer', position: 'relative',
                    boxShadow: focus ? '0 10px 30px rgba(10, 37, 64, 0.08)' : 'var(--shadow-sm)',
                    overflow: 'hidden'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 600 }}>
                      <Calendar size={16} /> {formatDate(s.created_at)}
                    </div>
                    <div style={{ 
                      background: getScoreBg(s.overall_score), color: getScoreColor(s.overall_score), 
                      padding: '4px 12px', borderRadius: '20px', fontWeight: '700', fontSize: '0.85rem' 
                    }}>
                      {s.overall_score}% Match
                    </div>
                  </div>
                  
                  <h4 style={{ fontSize: '1.1rem', color: 'var(--brand-navy)', marginBottom: '0.5rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    <Briefcase size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: '-2px', color: 'var(--text-muted)' }}/>
                    {s.session_label || 'Target Job Analysis'}
                  </h4>
                  
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    <FileText size={14} style={{ display: 'inline', marginRight: '6px', verticalAlign: '-2px' }}/>
                    {s.job_description_preview?.replace(/\n/g, ' ')}...
                  </p>

                  <div style={{ position: 'absolute', bottom: '1.5rem', right: '1.5rem', color: focus ? 'var(--accent-gold)' : 'var(--border-subtle)' }}>
                     <ChevronRight size={20} />
                  </div>
                </motion.div>
              )
            })}
          </div>

          {/* Right Pane: Detail View */}
          <AnimatePresence mode="wait">
            {selected && (
              <motion.div
                key={selected}
                initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 50 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ flex: '1', background: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '24px', padding: '2.5rem', boxShadow: 'var(--shadow-md)', minHeight: '600px' }}
              >
                {detailLoading ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                    <div className="spinner" style={{ marginBottom: '1rem', width: '30px', height: '30px' }} /> Fetching telemetry...
                  </div>
                ) : detail ? (
                  <>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '3rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '2rem' }}>
                       <div>
                         <h2 style={{ fontSize: '1.6rem', color: 'var(--brand-navy)', marginBottom: '0.5rem', fontWeight: 800 }}>Analysis Report</h2>
                         <div style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                           <span><Calendar size={14} style={{display:'inline', marginRight:'4px'}}/> {formatDate(detail.session.created_at)}</span>
                         </div>
                       </div>
                    </div>

                    <div style={{ marginBottom: '3rem', background: 'var(--bg-elevated)', padding: '1rem', borderRadius: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <h3 style={{ alignSelf: 'flex-start', marginLeft: '1rem', marginTop: '1rem', fontSize: '1.1rem', color: 'var(--brand-navy)', fontWeight: 800 }}>Core Dynamics</h3>
                      <MetricsRadarChart 
                        overall={detail.session.overall_score} 
                        keyword={detail.session.keyword_score} 
                        semantic={detail.session.semantic_score} 
                      />
                    </div>

                    {detail.section_scores?.length > 0 && (
                      <div style={{ marginBottom: '3rem' }}>
                        <h3 style={{ fontSize: '1.25rem', color: 'var(--brand-navy)', fontWeight: 800, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <TrendingUp size={20} /> Component Breakdown
                        </h3>
                        <div style={{ display: 'grid', gap: '1.25rem' }}>
                          {detail.section_scores.map((s, i) => (
                            <div key={i} style={{ background: 'var(--bg-elevated)', padding: '1.25rem', borderRadius: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontWeight: 600 }}>
                                <span style={{ textTransform: 'capitalize', color: 'var(--brand-navy)' }}>{s.section_name}</span>
                                <span style={{ color: getScoreColor(s.similarity_score) }}>{s.similarity_score}%</span>
                              </div>
                              <div style={{ height: '8px', background: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${Math.min(s.similarity_score, 100)}%`, background: getScoreColor(s.similarity_score), borderRadius: '4px', transition: 'width 1s ease' }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {detail.bullets?.length > 0 && (
                      <div>
                        <h3 style={{ fontSize: '1.25rem', color: 'var(--brand-navy)', fontWeight: 800, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Briefcase size={20} /> Impact Signals
                        </h3>
                        <div style={{ display: 'grid', gap: '1rem' }}>
                          {detail.bullets.map((b, i) => (
                            <div key={i} style={{ display: 'flex', gap: '1rem', padding: '1rem', borderLeft: `4px solid ${getScoreColor(b.similarity_score)}`, background: 'var(--bg-elevated)', borderRadius: '0 8px 8px 0' }}>
                              <div style={{ background: getScoreBg(b.similarity_score), color: getScoreColor(b.similarity_score), padding: '4px 12px', borderRadius: '20px', fontWeight: '800', fontSize: '0.8rem', height: 'fit-content' }}>
                                {b.similarity_score}%
                              </div>
                              <span style={{ color: 'var(--brand-navy)', lineHeight: 1.6, fontSize: '0.95rem' }}>
                                {b.rewritten_text || b.bullet_text}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : null}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
