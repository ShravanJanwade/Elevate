import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, FileText, CheckCircle, ChevronDown, Check, X, Copy, Zap, Briefcase, Award, Download, DownloadCloud, Edit3, Eye, FileDigit, ListChecks, Shapes, RefreshCcw, Code, Brain, TrendingUp, Layout, Shield, Target, Activity, Gauge, Building2, AlertTriangle } from 'lucide-react'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import HistoryPage from './pages/HistoryPage'
import { apiFetch } from './lib/api'

// Set up PDF worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

/* ======================================================================
   Animated Score Ring (SVG)
   ====================================================================== */
function ScoreRing({ score, colorClass }) {
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const [offset, setOffset] = useState(circumference)

  useEffect(() => {
    const timer = setTimeout(() => {
      const pct = Math.min(score, 100) / 100
      setOffset(circumference - pct * circumference)
    }, 400)
    return () => clearTimeout(timer)
  }, [score, circumference])

  return (
    <div className="ring-wrapper">
      <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
        <circle cx="50" cy="50" r={radius} className="ring-bg" />
        <circle
          cx="50" cy="50" r={radius}
          className={`ring-fill ${colorClass}`}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-value">{score}%</div>
    </div>
  )
}

/* ======================================================================
   Loading Overlay with Humor and Framer Animation
   ====================================================================== */
function LoadingOverlay() {
  const phrases = [
    "Injecting corporate synergy...",
    "Bribing the ATS algorithm...",
    "Unpacking career baggage...",
    "Replacing 'did stuff' with 'spearheaded initiatives'...",
    "Pivoting to blockchain...",
    "Extracting your hidden potential...",
    "Aggregating buzzwords...",
    "Calculating coffee requirements..."
  ]
  const [text, setText] = useState(phrases[0])

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      index = (index + 1) % phrases.length
      setText(phrases[index])
    }, 2800)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div 
      className="loading-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(10, 25, 47, 0.75)',
        backdropFilter: 'blur(20px)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        color: '#fff'
      }}
    >
      
      {/* MAGNIFICENT ANIMATED SCANNER */}
      <div style={{ position: 'relative', width: '120px', height: '150px', marginBottom: '3rem' }}>
        {/* Document Base */}
        <motion.div 
          style={{ width: '100%', height: '100%', background: '#fff', borderRadius: '12px', padding: '15px', position: 'absolute', top: 0, left: 0, boxShadow: '0 0 30px rgba(255,255,255,0.1)' }}
          animate={{ scale: [1, 1.02, 1], rotate: [0, 2, -2, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'70%', marginBottom:'12px'}}/>
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'100%', marginBottom:'8px'}}/>
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'90%', marginBottom:'8px'}}/>
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'85%', marginBottom:'16px'}}/>
          
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'60%', marginBottom:'8px'}}/>
          <div style={{height:'6px', background:'#e2e8f0', borderRadius:'3px', width:'95%', marginBottom:'8px'}}/>
        </motion.div>

        {/* AI Laser Beam */}
        <motion.div
           style={{
             position: 'absolute', left: '-15%', right: '-15%', height: '4px',
             background: 'var(--accent-gold)', borderRadius: '2px',
             boxShadow: '0 0 20px var(--accent-gold), 0 0 40px var(--accent-gold)'
           }}
           animate={{ top: ['-5%', '105%', '-5%'] }}
           transition={{ duration: 2.2, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Floating Icons */}
        <motion.div 
          style={{ position: 'absolute', top: '-15px', right: '-15px', color: 'var(--accent-gold)', background: '#fff', borderRadius: '50%', padding: '5px', boxShadow: '0 5px 15px rgba(0,0,0,0.3)' }}
          animate={{ rotate: 360, scale: [1, 1.2, 1] }}
          transition={{ rotate: { duration: 4, repeat: Infinity, ease: "linear" }, scale: { duration: 2, repeat: Infinity } }}
        >
          <RefreshCcw size={24}/>
        </motion.div>

        <motion.div 
          style={{ position: 'absolute', bottom: '-10px', left: '-20px', color: '#10b981', background: '#fff', borderRadius: '50%', padding: '5px', boxShadow: '0 5px 15px rgba(0,0,0,0.3)' }}
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <CheckCircle size={22}/>
        </motion.div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div 
          key={text}
          className="humor-text"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -15 }}
          transition={{ duration: 0.5 }}
          style={{
            fontFamily: 'Outfit', fontSize: '2.2rem', fontWeight: 800, letterSpacing: '-0.02em',
            background: 'var(--grad-accent)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            textAlign: 'center', padding: '0 1rem'
          }}
        >
          {text}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  )
}

/* ======================================================================
   Navbar
   ====================================================================== */
function Navbar() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="navbar">
      <div className="navbar-inner">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <div className="navbar-logo-mark">
            <Zap size={15} strokeWidth={2.5} color="#fff" />
          </div>
          <span className="navbar-logo-text">Elevate</span>
          <span className="navbar-logo-badge">Pro</span>
        </Link>

        {/* Right side */}
        {user && (
          <div className="navbar-right">
            <Link to="/history" className="navbar-link">
              History
            </Link>
            <div className="navbar-divider" />
            <div className="navbar-user">
              <div className="navbar-avatar">
                {user.email?.[0]?.toUpperCase()}
              </div>
              <span className="navbar-email">{user.email}</span>
            </div>
            <button
              className="navbar-signout"
              onClick={() => { signOut(); navigate('/login') }}
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

/* ======================================================================
   Main Analyzer Page
   ====================================================================== */
function AnalyzerPage() {
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [fileUrl, setFileUrl] = useState(null)
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [useLLM, setUseLLM] = useState(true)
  
  const [results, setResults] = useState(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  
  const [modifiedBullets, setModifiedBullets] = useState({})
  const [bulletRewrites, setBulletRewrites] = useState({}) 
  const [templateData, setTemplateData] = useState({})
  
  const [viewMode, setViewMode] = useState('original') // 'original' | 'modified' | 'latex'
  const [activeTab, setActiveTab] = useState('overview') 

  const [numPages, setNumPages] = useState(null)
  const [previewHtml, setPreviewHtml] = useState('')   // docx → HTML
  const [previewText, setPreviewText] = useState('')   // txt → plain text

  const fileInputRef = useRef(null)
  const reportRef = useRef(null)
  const modifiedResumeRef = useRef(null)

  const handleFile = async (f) => {
    if (!f) return
    const name = f.name.toLowerCase()
    const isPdf  = f.type === 'application/pdf'
    const isDocx = name.endsWith('.docx')
    const isTxt  = name.endsWith('.txt')
    if (!isPdf && !isDocx && !isTxt) return

    setResumeFile(f)
    setResumeText('')
    setFileUrl(null)
    setPreviewHtml('')
    setPreviewText('')

    if (isPdf) {
      setFileUrl(URL.createObjectURL(f))
    } else if (isDocx || isTxt) {
      // Convert to PDF on the backend for a clean rendered preview
      try {
        const form = new FormData()
        form.append('file', f)
        const resp = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/preview-pdf`, {
          method: 'POST',
          body: form,
        })
        if (resp.ok) {
          const blob = await resp.blob()
          setFileUrl(URL.createObjectURL(blob))
          return
        }
      } catch {
        // fall through to client-side fallback
      }
      // Client-side fallback: docx → HTML via mammoth, txt → plain text
      if (isDocx) {
        try {
          const mammoth = await import('mammoth')
          const arrayBuffer = await f.arrayBuffer()
          const result = await mammoth.convertToHtml({ arrayBuffer })
          setPreviewHtml(result.value)
        } catch {
          setPreviewText('Could not render Word preview.')
        }
      } else {
        const text = await f.text()
        setPreviewText(text)
      }
    }
  }

  const handleDragOver = useCallback((e) => { e.preventDefault(); setDragOver(true) }, [])
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setDragOver(false) }, [])
  const handleDrop = useCallback((e) => {
    e.preventDefault(); setDragOver(false)
    const files = e.dataTransfer.files
    if (files.length > 0) handleFile(files[0])
  }, [])

  const handleAnalyze = async () => {
    setError('');
    if (!jobDescription.trim()) { setError('Please enter a target job description.'); return }
    if (!resumeText.trim() && !resumeFile) { setError('Please provide your resume document.'); return }

    setLoading(true)
    try {
      let res
      if (resumeFile) {
        const formData = new FormData()
        formData.append('job_description', jobDescription)
        formData.append('resume_file', resumeFile)
        const { data: { session } } = await (await import('./lib/supabaseClient')).supabase.auth.getSession()
        res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/analyze`, {
          method: 'POST', body: formData,
          headers: { Authorization: `Bearer ${session?.access_token}` },
        })
      } else {
        res = await apiFetch('/api/analyze', {
          method: 'POST',
          body: JSON.stringify({ job_description: jobDescription, resume_text: resumeText }),
        })
      }

      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Something went wrong.'); setLoading(false); return }
      
      setResults(data)
      setDrawerOpen(true)
      setModifiedBullets({})
      setBulletRewrites({})
      setViewMode('original')
      setActiveTab('all')
    } catch {
      setError('Could not connect to the analysis server. Please ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const acceptRewrite = (index, text) => {
    setModifiedBullets((prev) => ({ ...prev, [index]: text }))
  }

  const handleRewriteBullet = async (index, bulletText) => {
    setBulletRewrites((prev) => ({ ...prev, [index]: { loading: true } }))
    try {
      const res = await apiFetch('/api/rewrite', {
        method: 'POST',
        body: JSON.stringify({ bullet: bulletText, job_description: jobDescription, use_llm: useLLM }),
      })
      const data = await res.json()
      setBulletRewrites((prev) => ({
        ...prev, [index]: { rewritten: data.rewritten, loading: false }
      }))
    } catch {
      setBulletRewrites((prev) => ({ ...prev, [index]: { loading: false, error: 'Rewrite failed' } }))
    }
  }

  const handleTemplateChange = (field, val) => setTemplateData(prev => ({...prev, [field]: val}));

  const downloadDraft = async () => {
    if (!modifiedResumeRef.current) return
    try {
      const canvas = await html2canvas(modifiedResumeRef.current, { scale: 3, useCORS: true, logging: false })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'pt', 'a4')
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
      pdf.save('Jakes_Resume_Render.pdf')
    } catch (err) {
      console.error("PDF Export failed", err)
    }
  }

  const downloadReport = async () => {
    if (!reportRef.current) return
    
    const prevTab = activeTab;
    setActiveTab('all');
    
    // Wait for the tab to render fully, then unlock height
    setTimeout(async () => {
      const el = reportRef.current;
      const prevOverflow = el.style.overflow;
      const prevHeight = el.style.height;
      
      el.style.overflow = 'visible';
      el.style.height = 'auto'; // allow it to stretch down
      
      try {
        const canvas = await html2canvas(el, { scale: 2, useCORS: true, logging: false, windowHeight: el.scrollHeight });
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'pt', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
        
        const pageHeight = pdf.internal.pageSize.getHeight();
        let heightLeft = pdfHeight;
        let position = 0;
        
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
        heightLeft -= pageHeight;
        
        while (heightLeft >= 0) {
          position = heightLeft - pdfHeight;
          pdf.addPage();
          pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
          heightLeft -= pageHeight;
        }
        
        pdf.save('Elevate_Analysis_Report.pdf');
      } catch (err) {
        console.error("Report generation failed", err);
      } finally {
        el.style.overflow = prevOverflow;
        el.style.height = prevHeight;
        setActiveTab(prevTab);
      }
    }, 400); // giving React time to mount the All tab
  }

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
  }

  const layoutVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
    exit: { opacity: 0, x: -50, transition: { duration: 0.4 } }
  }

  const drawerVariants = {
    hidden: { x: '100%', opacity: 0 },
    visible: { x: 0, opacity: 1, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
  }

  const leftPaneVariants = {
    centered: { width: '100%', borderRight: 'none', background: 'var(--bg-app)', transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
    split: { width: '45%', borderRight: '1px solid var(--border-subtle)', background: 'var(--bg-app)', transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
  }

  const hasResults = results !== null

  const displayScore = results?.overall_score || 0
  const semanticScore = results?.semantic_analysis?.overall_score || 0
  const skillMatch = results?.keyword_analysis?.match_percentage || 0
  
  const domains = results?.keyword_analysis?.domain_coverage || {}
  const missingSkills = results?.keyword_analysis?.missing || []
  const safeMissingSkills = Array.isArray(missingSkills) ? missingSkills : []

  const originalBullets = results?.semantic_analysis?.bullet_scores || []
  const suggestions = results?.suggestions || []
  const entities = results?.entities || {}

  // v3 data
  const impactAnalysis = results?.impact_analysis || {}
  const trajectoryAnalysis = results?.trajectory_analysis || {}
  const layoutAnalysis = results?.layout_analysis || {}
  const pedigreeAnalysis = results?.pedigree_analysis || {}
  const judgeEval = results?.judge_evaluation || {}
  const allFlags = results?.all_flags || []
  const dims = results?.dimensions || {}

  const getScoreColor = (score) => {
    if(score >= 80) return '#10b981'
    if(score >= 50) return '#f59e0b'
    return '#ef4444'
  }

  const getDecisionColor = (d) => {
    if(d === 'SHORTLIST') return '#10b981'
    if(d === 'REJECT') return '#ef4444'
    return '#f59e0b'
  }

  const getFlagIcon = (type) => {
    if(type === 'green') return <CheckCircle size={14} color="#10b981"/>
    if(type === 'red') return <AlertTriangle size={14} color="#ef4444"/>
    return <Activity size={14} color="#f59e0b"/>
  }

  /* Logic to safely extract segments of bullets exactly like the previous step */
  const getSegregatedBullets = () => {
    const totalBullets = originalBullets.length;
    const expCount = Math.max(1, Math.ceil(totalBullets * 0.6));
    const projCount = Math.max(1, Math.ceil(totalBullets * 0.2));

    const expBullets = originalBullets.slice(0, expCount);
    const projBullets = originalBullets.slice(expCount, expCount + projCount);
    const achieveBullets = originalBullets.slice(expCount + projCount);
    
    return { expBullets, projBullets, achieveBullets, expCount, projCount };
  }

  // Handle precisely segregating dynamic abstract sections into Resume visually matching Jake's 
  const renderJakesVisual = () => {
    const { expBullets, projBullets, achieveBullets, expCount, projCount } = getSegregatedBullets();

    return (
      <>
        {/* Education Section */}
        <div className="r-section">
          <div className="r-heading">Education</div>
          <div className="r-item-head">
            <span style={{fontWeight: 'bold'}}>
              <input className="editable-jake" placeholder="University Name" style={{fontWeight: 'bold'}} value={templateData.uni !== undefined ? templateData.uni : (results?.education_analysis?.resume_degree || '')} onChange={(e) => handleTemplateChange('uni', e.target.value)} />
            </span>
            <span style={{fontStyle: 'italic'}}>
              <input className="editable-jake" placeholder="Location" style={{textAlign: 'right', fontStyle: 'italic'}} value={templateData.locE !== undefined ? templateData.locE : (entities.location || '')} onChange={(e) => handleTemplateChange('locE', e.target.value)} />
            </span>
          </div>
          <div className="r-item-sub">
            <span>{results?.education_analysis?.resume_degree || 'Bachelor of Science'} {results?.education_analysis?.resume_field ? `in ${results?.education_analysis?.resume_field}` : ''}</span>
            <span>
              <input className="editable-jake" placeholder="Graduation Date" style={{textAlign: 'right'}} value={templateData.grad !== undefined ? templateData.grad : ''} onChange={(e) => handleTemplateChange('grad', e.target.value)} />
            </span>
          </div>
        </div>

        {/* Experience Section */}
        {expBullets.length > 0 && (
          <div className="r-section">
            <div className="r-heading">Experience</div>
            <div className="r-item-head">
              <span style={{fontWeight: 'bold'}}>
                <input className="editable-jake" placeholder="Job Title" style={{fontWeight: 'bold'}} value={templateData.role !== undefined ? templateData.role : (entities.role || '')} onChange={(e) => handleTemplateChange('role', e.target.value)} />
              </span>
              <span style={{fontStyle: 'italic'}}>
                <input className="editable-jake" placeholder="Start Date -- End Date" style={{textAlign: 'right', fontStyle: 'italic'}} value={templateData.dates !== undefined ? templateData.dates : (entities.years || '')} onChange={(e) => handleTemplateChange('dates', e.target.value)} />
              </span>
            </div>
            <div className="r-item-sub">
              <span>
                <input className="editable-jake" placeholder="Company Name" value={templateData.company !== undefined ? templateData.company : (entities.company || '')} onChange={(e) => handleTemplateChange('company', e.target.value)} />
              </span>
              <span>
                 <input className="editable-jake" placeholder="Location" style={{textAlign: 'right'}} value={templateData.locW !== undefined ? templateData.locW : (entities.location || '')} onChange={(e) => handleTemplateChange('locW', e.target.value)} />
              </span>
            </div>
            <ul className="r-bullets">
              {expBullets.map((b, relativeIndex) => {
                const globalIndex = relativeIndex;
                return (
                  <li className={`r-bullet-txt ${modifiedBullets[globalIndex] ? 'modified' : ''}`} key={`exp-${globalIndex}`}>
                    {modifiedBullets[globalIndex] || b.text}
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {/* Projects Section */}
        {projBullets.length > 0 && (
          <div className="r-section">
            <div className="r-heading">Projects</div>
            <div className="r-item-head">
              <span style={{fontWeight: 'bold'}}>Architecture Scaling System</span>
              <span style={{fontStyle: 'italic'}}>Jan 20XX -- Mar 20XX</span>
            </div>
            <ul className="r-bullets" style={{marginTop: '0.2rem'}}>
              {projBullets.map((b, relativeIndex) => {
                 const globalIndex = expCount + relativeIndex;
                 return (
                   <li className={`r-bullet-txt ${modifiedBullets[globalIndex] ? 'modified' : ''}`} key={`proj-${globalIndex}`}>
                     {modifiedBullets[globalIndex] || b.text}
                   </li>
                 )
              })}
            </ul>
          </div>
        )}

        {achieveBullets.length > 0 && (
          <div className="r-section">
            <div className="r-heading">Leadership \& Achievements</div>
            <ul className="r-bullets" style={{marginTop: '0.2rem'}}>
              {achieveBullets.map((b, relativeIndex) => {
                 const globalIndex = expCount + projCount + relativeIndex;
                 return (
                   <li className={`r-bullet-txt ${modifiedBullets[globalIndex] ? 'modified' : ''}`} key={`ach-${globalIndex}`}>
                     {modifiedBullets[globalIndex] || b.text}
                   </li>
                 )
              })}
            </ul>
          </div>
        )}
      </>
    )
  }

  // Generate the actual raw LaTeX code block mapping Jake's Resume
  const generateJakesLatex = () => {
    const { expBullets, projBullets, achieveBullets, expCount, projCount } = getSegregatedBullets();
    
    // LaTeX Escaping helper
    const esc = (str) => {
      if(!str) return ""
      return str.replace(/&/g, '\\&').replace(/%/g, '\\%').replace(/\$/g, '\\$').replace(/#/g, '\\#').replace(/_/g, '\\_');
    }

    let out = `%-------------------------
% Resume in Latex
% Author : Jake Gutierrez (Generated by Elevate Pro)
% Based off of: https://github.com/sb2nov/resume
%------------------------

\\documentclass[letterpaper,11pt]{article}

\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}

\\pagestyle{fancy}
\\fancyhf{} % clear all header and footer fields
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

% Adjust margins
\\addtolength{\\oddsidemargin}{-0.5in}
\\addtolength{\\evensidemargin}{-0.5in}
\\addtolength{\\textwidth}{1in}
\\addtolength{\\topmargin}{-.5in}
\\addtolength{\\textheight}{1.0in}

\\urlstyle{same}

\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

% Sections formatting
\\titleformat{\\section}{
  \\vspace{-4pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]

% Custom commands
\\newcommand{\\resumeItem}[1]{
  \\item\\small{
    {#1 \\vspace{-2pt}}
  }
}

\\newcommand{\\resumeSubheading}[4]{
  \\vspace{-2pt}\\item
    \\begin{tabular*}{0.97\\textwidth}[t]{l@{\\extracolsep{\\fill}}r}
      \\textbf{#1} & #2 \\\\
      \\textit{\\small#3} & \\textit{\\small #4} \\\\
    \\end{tabular*}\\vspace{-7pt}
}

\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0.15in, label={}]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}
\\newcommand{\\resumeItemListStart}{\\begin{itemize}}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\begin{document}

%----------HEADING----------
\\begin{center}
    \\textbf{\\Huge \\scshape ${esc(entities.name) || 'Jake Gutierrez'}} \\\\ \\vspace{1pt}
    \\small ${entities.phone ? esc(entities.phone) + ' $|$' : ''} 
    ${entities.email ? `\\href{mailto:${esc(entities.email)}}{\\underline{${esc(entities.email)}}} $|$` : ''} 
    ${entities.linkedin ? `\\href{https://${esc(entities.linkedin.replace('https://',''))}}{\\underline{LinkedIn}} $|$` : ''}
    ${entities.github_link ? `\\href{${esc(entities.github_link)}}{\\underline{GitHub}} $|$` : ''}
    ${entities.leetcode_link ? `\\href{${esc(entities.leetcode_link)}}{\\underline{LeetCode}} $|$` : ''}
\\end{center}

%-----------EDUCATION-----------
\\section{Education}
  \\resumeSubHeadingListStart
    \\resumeSubheading
      {${esc(templateData.uni !== undefined ? templateData.uni : (results?.education_analysis?.resume_degree || 'University Name'))}}{${esc(templateData.locE !== undefined ? templateData.locE : (entities.location || 'Location'))}}
      {${esc(results?.education_analysis?.resume_degree) || 'Bachelor of Science'} ${esc(results?.education_analysis?.resume_field) ? `in ${esc(results?.education_analysis?.resume_field)}` : ''}}{${esc(templateData.grad || 'Graduation Date')}}
  \\resumeSubHeadingListEnd
`;

    if (expBullets.length > 0) {
      out += `\n%-----------EXPERIENCE-----------\n\\section{Experience}\n  \\resumeSubHeadingListStart\n    \\resumeSubheading\n      {${esc(templateData.role !== undefined ? templateData.role : (entities.role || 'Job Title'))}}{${esc(templateData.locW !== undefined ? templateData.locW : (entities.location || 'Location'))}}\n      {${esc(templateData.company !== undefined ? templateData.company : (entities.company || 'Company Name'))}}{${esc(templateData.dates !== undefined ? templateData.dates : (entities.years || 'Start Date -- End Date'))}}\n      \\resumeItemListStart\n`;
      expBullets.forEach((b, i) => {
        out += `        \\resumeItem{${esc(modifiedBullets[i] || b.text)}}\n`;
      });
      out += `      \\resumeItemListEnd\n  \\resumeSubHeadingListEnd\n`;
    }

    if (projBullets.length > 0) {
      out += `\n%-----------PROJECTS-----------\n\\section{Projects}\n  \\resumeSubHeadingListStart\n    \\resumeSubheading\n      {Architecture Scaling System}{}\n      {Technologies: Various}{Jan 20XX -- Mar 20XX}\n      \\resumeItemListStart\n`;
      projBullets.forEach((b, i) => {
        out += `        \\resumeItem{${esc(modifiedBullets[expCount + i] || b.text)}}\n`;
      });
      out += `      \\resumeItemListEnd\n  \\resumeSubHeadingListEnd\n`;
    }

    out += `\n%-----------PROGRAMMING SKILLS-----------\n\\section{Technical Skills}\n \\begin{itemize}[leftmargin=0.15in, label={}]\n    \\small{\\item{\n     \\textbf{Technologies}{: ${esc(results?.keyword_analysis?.matched?.join(', '))}}\n    }}\n \\end{itemize}\n`;

    // Dynamic Extra Sections
    ['certifications', 'awards', 'publications', 'volunteer'].forEach(secKey => {
      if (results?.parsed_data?.[secKey]) {
        const title = secKey.charAt(0).toUpperCase() + secKey.slice(1);
        out += `\n%-----------${secKey.toUpperCase()}-----------\n\\section{${title}}\n  \\small{${esc(results.parsed_data[secKey])}}\n`;
      }
    });

    out += `\n\\end{document}`;

    return out;
  }

  return (
    <main className="app-main">
      <AnimatePresence>
        {loading && <LoadingOverlay key="loading" />}
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {/* ==================== LEFT PANE ==================== */}
        <motion.div 
          className="pane-left"
          variants={leftPaneVariants}
          initial="centered"
          animate={(hasResults && drawerOpen) ? "split" : "centered"}
        >
          {!hasResults ? (
            <motion.div 
              className="layout-centered"
              variants={layoutVariants}
              initial="initial" animate="animate" exit="exit"
            >
              <div className="hero">
                <h1>Elevate Your Career</h1>
                <p>Upload your resume document and the target Job Description. Our multi-model engine provides instant parsing, deep gap analysis, and interactive rewriting.</p>
              </div>

              <div className="input-stack">
                <div className="input-group">
                  <label className="input-label"><FileText size={18}/> Resume Document</label>
                  {!resumeFile ? (
                    <div 
                      className={`file-dropzone ${dragOver ? 'drag-active' : ''}`}
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
                    >
                      <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx" style={{display:'none'}} onChange={(e) => handleFile(e.target.files[0])} />
                      <div className="file-icon-wrapper"><UploadCloud size={28} /></div>
                      <div className="file-info">
                        <span className="file-primary-text">Browse files</span> or drag and drop<br/>
                        PDF, Word (.docx) or plain text (.txt) supported
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="file-dropzone" style={{padding: '1.5rem', borderColor: 'var(--color-success)', background: '#fff', boxShadow: '0 4px 15px rgba(16, 185, 129, 0.1)'}}>
                        <div className="file-icon-wrapper" style={{color: 'var(--color-success)', background: 'var(--bg-success)'}}><CheckCircle size={24}/></div>
                        <div className="file-info" style={{color: 'var(--color-success)', fontWeight: 600}}>{resumeFile.name} Uploaded Successfully</div>
                        <button className="btn-secondary" style={{marginTop: '0.75rem', fontSize: '0.8rem'}} onClick={() => { setResumeFile(null); setFileUrl(null) }}>Clear File</button>
                      </div>
                    </>
                  )}

                  {!resumeFile && (
                    <textarea 
                      className="input-box" 
                      style={{minHeight: '80px', marginTop: '1rem'}}
                      placeholder="...or paste your resume plaintext here."
                      value={resumeText} 
                      onChange={(e) => setResumeText(e.target.value)}
                    />
                  )}
                </div>

                <div className="input-group">
                  <label className="input-label"><Briefcase size={18}/> Job Description</label>
                  <textarea 
                    className="input-box" 
                    placeholder="Paste the target job description requirements here..."
                    value={jobDescription} 
                    onChange={(e) => setJobDescription(e.target.value)}
                  />
                </div>

                {error && <div style={{color: 'var(--color-error)', background: 'var(--bg-error)', padding: '1rem', borderRadius: '12px', fontSize: '0.95rem', border: '1px solid rgba(239, 68, 68, 0.3)'}}>{error}</div>}

                {/* Fixed Center Alignment Request */}
                <div className="action-bar" style={{justifyContent: 'center', marginTop: '1rem', display: 'flex', width: '100%'}}>
                  <button className="btn-primary" onClick={handleAnalyze} disabled={loading} style={{margin: '0 auto'}}>
                    <CheckCircle size={18}/> Generate AI Analysis
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            // Flex 100% Height Mode for Previews
            <motion.div className="preview-container" initial={{opacity: 0}} animate={{opacity: 1}}>
              
              <div className="preview-tab-bar">
                <div className="preview-tabs">
                  <button onClick={()=>setViewMode('original')} className={`preview-tab${viewMode==='original' ? ' active' : ''}`}>
                    <Eye size={14}/> Original
                  </button>
                  <button onClick={()=>setViewMode('modified')} className={`preview-tab${viewMode==='modified' ? ' active' : ''}`}>
                    <Edit3 size={14}/> Resume Render
                  </button>
                  <button onClick={()=>setViewMode('latex')} className={`preview-tab${viewMode==='latex' ? ' active' : ''}`}>
                    <Code size={14}/> LaTeX
                  </button>
                </div>
                <button onClick={() => { setResults(null); setDrawerOpen(false); setResumeFile(null); setFileUrl(null); setPreviewHtml(''); setPreviewText(''); }} className="preview-new-btn">
                  <RefreshCcw size={13}/> New Analysis
                </button>
              </div>

              <div className="preview-viewport">
                {/* All three views always mounted — opacity crossfade, no unmounting */}

                {/* ORIGINAL */}
                <div style={{
                  position:'absolute', inset:0, overflowY:'auto',
                  opacity: viewMode==='original' ? 1 : 0,
                  pointerEvents: viewMode==='original' ? 'auto' : 'none',
                  transition: 'opacity 0.3s ease',
                }}>
                  {fileUrl ? (
                    /* PDF */
                    <Document file={fileUrl} onLoadSuccess={onDocumentLoadSuccess}
                      loading={<div style={{padding:'2rem',textAlign:'center',color:'#94a3b8',fontSize:'0.9rem'}}>Rendering PDF…</div>}>
                      {Array.from(new Array(numPages||0),(_,i)=>(
                        <Page key={`page_${i+1}`} pageNumber={i+1} renderTextLayer={false} renderAnnotationLayer={false} width={typeof window!=='undefined'?Math.floor(window.innerWidth*0.42):580}/>
                      ))}
                    </Document>
                  ) : previewHtml ? (
                    /* DOCX → HTML */
                    <div style={{background:'#f0f0f0',minHeight:'100%',padding:'2rem',display:'flex',justifyContent:'center'}}>
                      <div style={{
                        background:'#fff', maxWidth:'760px', width:'100%',
                        padding:'3rem 3.5rem', boxShadow:'0 4px 24px rgba(0,0,0,0.1)',
                        borderRadius:'4px', fontSize:'11pt', lineHeight:1.6,
                        fontFamily:'Times New Roman, serif', color:'#000',
                      }}
                        dangerouslySetInnerHTML={{__html: previewHtml}}
                      />
                    </div>
                  ) : previewText ? (
                    /* TXT */
                    <div style={{background:'#f0f0f0',minHeight:'100%',padding:'2rem',display:'flex',justifyContent:'center'}}>
                      <div style={{
                        background:'#fff', maxWidth:'760px', width:'100%',
                        padding:'3rem 3.5rem', boxShadow:'0 4px 24px rgba(0,0,0,0.1)',
                        borderRadius:'4px', fontSize:'0.9rem', lineHeight:1.8,
                        fontFamily:'monospace', color:'#1e293b',
                        whiteSpace:'pre-wrap', wordBreak:'break-word',
                      }}>
                        {previewText}
                      </div>
                    </div>
                  ) : (
                    <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100%',color:'#94a3b8',fontSize:'0.9rem',flexDirection:'column',gap:'0.75rem'}}>
                      <FileText size={40} strokeWidth={1} color="#cbd5e1"/>
                      <span>Upload a resume to preview it here</span>
                    </div>
                  )}
                </div>

                {/* RESUME RENDER */}
                <div style={{
                  position:'absolute', inset:0, overflowY:'auto',
                  opacity: viewMode==='modified' ? 1 : 0,
                  pointerEvents: viewMode==='modified' ? 'auto' : 'none',
                  transition: 'opacity 0.3s ease',
                }}>
                  <div className="a4-wrapper">
                    <div className="jakes-resume" ref={modifiedResumeRef}>
                      <div className="r-name">{entities.name||'Jake Gutierrez'}</div>
                      <div className="r-contact">
                        {entities.email&&<span>{entities.email} </span>}
                        {entities.phone&&<span>• {entities.phone} </span>}
                        {entities.linkedin&&<span>• <a href={`https://${entities.linkedin.replace('https://','')}`}>LinkedIn</a> </span>}
                        {entities.github_link&&<span>• <a href={entities.github_link}>GitHub</a> </span>}
                        {entities.leetcode_link&&<span>• <a href={entities.leetcode_link}>LeetCode</a> </span>}
                      </div>
                      {renderJakesVisual()}
                      <div className="r-section">
                        <div className="r-heading">Technical Skills</div>
                        <div style={{marginTop:'0.4rem',fontSize:'11pt'}}>
                          <span style={{fontWeight:'bold'}}>Languages/Tech:</span> {results?.keyword_analysis?.matched?.join(', ')}
                        </div>
                      </div>
                      {['certifications','awards','publications','volunteer'].map(secKey=>{
                        if(!results?.parsed_data?.[secKey]) return null;
                        return(
                          <div className="r-section" key={secKey}>
                            <div className="r-heading">{secKey.charAt(0).toUpperCase()+secKey.slice(1)}</div>
                            <div style={{fontSize:'11pt',margin:'4px 0 0 1rem',whiteSpace:'pre-wrap'}}>{results.parsed_data[secKey]}</div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>

                {/* LATEX */}
                <div style={{
                  position:'absolute', inset:0, overflowY:'auto',
                  opacity: viewMode==='latex' ? 1 : 0,
                  pointerEvents: viewMode==='latex' ? 'auto' : 'none',
                  transition: 'opacity 0.3s ease',
                }}>
                  <div className="latex-code-container" style={{minHeight:'100%'}}>{generateJakesLatex()}</div>
                </div>
              </div>

              {viewMode === 'modified' && (
                <button className="preview-export-btn" onClick={downloadDraft}>
                  <DownloadCloud size={16}/> Export to PDF
                </button>
              )}
              {viewMode === 'latex' && (
                <button className="preview-export-btn" onClick={() => navigator.clipboard.writeText(generateJakesLatex())}>
                  <Copy size={16}/> Copy LaTeX · Paste into Overleaf
                </button>
              )}
            </motion.div>
          )}
        </motion.div>

        {/* ==================== RIGHT PANE (RESULTS) ==================== */}
        {hasResults && drawerOpen && (
          <motion.div
            className="pane-right"
            variants={drawerVariants}
            initial="hidden" animate="visible" exit="hidden"
            style={{ width: '55%' }}
          >
            {/* PREMIUM MASTHEAD */}
            <div className="report-masthead">
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start'}}>
                <div>
                  <div className="report-masthead-title">Candidate Intelligence Report</div>
                  <div className="report-masthead-sub">Powered by Elevate v3 · Multi-Model Neural Pipeline</div>
                </div>
                <button className="report-masthead-btn danger" onClick={() => setDrawerOpen(false)}>
                  <X size={14}/> Close
                </button>
              </div>
              <div className="report-masthead-actions">
                <button className="report-masthead-btn" onClick={downloadReport}><Download size={13}/> Export PDF</button>
                {['all','overview','v3','skills','points','editor'].map(tab => (
                  <button key={tab} className={`report-masthead-btn${activeTab===tab?' active':''}`}
                    style={activeTab===tab?{background:'rgba(212,175,55,0.25)',borderColor:'rgba(212,175,55,0.5)',color:'#d4af37'}:{}}
                    onClick={()=>setActiveTab(tab)}>
                    {tab==='all'?'All':tab==='overview'?'Overview':tab==='v3'?'Intelligence':tab==='skills'?'Skills':tab==='points'?'Bullets':'Suggestions'}
                  </button>
                ))}
              </div>
            </div>

            {/* SCROLLABLE CONTENT */}
            <div className="tab-content-area" ref={reportRef} style={{paddingTop:'1.75rem'}}>

              {/* OVERVIEW */}
              {(activeTab==='all'||activeTab==='overview') && (<>

                {/* VERDICT CARD */}
                {judgeEval.decision && (
                  <div className={`verdict-card verdict-${judgeEval.decision?.toLowerCase()}`}>
                    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:'1rem'}}>
                      <div>
                        <div className="verdict-decision-badge">
                          {judgeEval.decision==='SHORTLIST'?<CheckCircle size={13}/>:judgeEval.decision==='REJECT'?<X size={13}/>:<Activity size={13}/>}
                          {judgeEval.decision}
                        </div>
                        <div className="verdict-score-giant">{displayScore}<span style={{fontSize:'2rem',opacity:0.5}}>%</span></div>
                        <div className="verdict-score-label">Overall Match Score</div>
                        <div className="verdict-meta">
                          {judgeEval.method==='neural'?'Flan-T5 Neural Judge':'Template Judge'} &nbsp;·&nbsp;
                          Confidence: {((judgeEval.confidence||0)*100).toFixed(0)}%
                        </div>
                      </div>
                      {/* Mini dimension bars */}
                      <div style={{display:'flex',flexDirection:'column',gap:'0.6rem',minWidth:'160px'}}>
                        {[
                          {label:'Skill Match',val:skillMatch,color:'#059669'},
                          {label:'Semantic',val:semanticScore,color:'#2563eb'},
                          {label:'Impact',val:dims.impact||0,color:'#7c3aed'},
                          {label:'Layout',val:dims.layout||0,color:'#d97706'},
                        ].map(b=>(
                          <div key={b.label}>
                            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.68rem',color:'#94a3b8',marginBottom:'3px',fontWeight:700,letterSpacing:'0.05em',textTransform:'uppercase'}}>
                              <span>{b.label}</span><span style={{color:b.color}}>{Math.round(b.val)}%</span>
                            </div>
                            <div style={{height:'4px',background:'#e2e8f0',borderRadius:'99px',overflow:'hidden'}}>
                              <div style={{height:'100%',width:`${Math.min(b.val,100)}%`,background:b.color,borderRadius:'99px',transition:'width 1s ease'}}/>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    {judgeEval.reasoning && (
                      <div className="verdict-reasoning">{judgeEval.reasoning}</div>
                    )}
                  </div>
                )}

                {/* 3 SCORE CARDS */}
                <div className="premium-scores-row">
                  {[
                    {label:'Total Alignment',score:displayScore,sub:`${results.strength||'Strong'}`,colorClass:'accent',barClass:'accent'},
                    {label:'Skill Coverage',score:skillMatch,sub:`${results.keyword_analysis?.matched?.length||0} keywords matched`,colorClass:'blue',barClass:'blue'},
                    {label:'Semantic Depth',score:semanticScore,sub:'Context verified',colorClass:'green',barClass:'green'},
                  ].map(c=>(
                    <div key={c.label} className={`premium-score-card card-${c.colorClass}`}>
                      <div className="pscore-label">{c.label}</div>
                      <div className="pscore-number" style={{color:getScoreColor(c.score)}}>{c.score}<span style={{fontSize:'1.2rem',opacity:0.4}}>%</span></div>
                      <div className="pscore-bar-track" style={{marginBottom:'0.75rem'}}>
                        <div className={`pscore-bar-fill ${c.barClass}`} style={{width:`${Math.min(c.score,100)}%`}}/>
                      </div>
                      <div className="pscore-badge" style={{
                        background: c.score>=80?'#d1fae5':c.score>=50?'#fef3c7':'#fee2e2',
                        color: c.score>=80?'#065f46':c.score>=50?'#92400e':'#991b1b'
                      }}>{c.sub}</div>
                    </div>
                  ))}
                </div>

                {/* DIMENSION CARDS */}
                <div className="dim-cards-row">
                  {[
                    {label:'Impact',score:dims.impact,icon:<Target size={18}/>,bg:'linear-gradient(135deg,#f5f3ff,#ede9fe)',color:'#7c3aed',border:'#c4b5fd'},
                    {label:'Trajectory',score:dims.trajectory,icon:<TrendingUp size={18}/>,bg:'linear-gradient(135deg,#ecfeff,#cffafe)',color:'#0891b2',border:'#a5f3fc'},
                    {label:'Layout',score:dims.layout,icon:<Layout size={18}/>,bg:'linear-gradient(135deg,#fffbeb,#fef3c7)',color:'#d97706',border:'#fde68a'},
                    {label:'Experience',score:dims.experience,icon:<Briefcase size={18}/>,bg:'linear-gradient(135deg,#f0fdf4,#dcfce7)',color:'#059669',border:'#bbf7d0'},
                  ].map(d=>(
                    <div key={d.label} className="dim-card-premium" style={{background:d.bg,border:`1px solid ${d.border}`}}>
                      <div className="dim-icon" style={{color:d.color}}>{d.icon}</div>
                      <div className="dim-score" style={{color:d.color}}>{Math.round(d.score||0)}</div>
                      <div className="dim-label" style={{color:d.color}}>{d.label}</div>
                    </div>
                  ))}
                </div>

                {/* INTERPRETATION */}
                {results.interpretation && (
                  <div className="interpretation-block">
                    <p className="interpretation-text">{results.interpretation}</p>
                  </div>
                )}
              </>)}

              {/* SKILLS */}
              {(activeTab==='all'||activeTab==='skills') && (<>

                {safeMissingSkills.length>0 && (
                  <div className="premium-panel">
                    <div className="premium-panel-header">
                      <div className="premium-panel-icon" style={{background:'#fee2e2'}}><AlertTriangle size={18} color="#ef4444"/></div>
                      <div className="premium-panel-title">Critical Skill Gaps</div>
                      <span style={{fontSize:'0.75rem',background:'#fee2e2',color:'#b91c1c',padding:'0.2rem 0.6rem',borderRadius:'99px',fontWeight:700}}>{safeMissingSkills.length} missing</span>
                    </div>
                    <div className="premium-panel-body">
                      <div className="missing-chips">
                        {safeMissingSkills.map((kw,i)=>(
                          <span key={i} className="missing-chip"><X size={11}/>{kw}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#eff6ff'}}><Shapes size={18} color="#3b82f6"/></div>
                    <div className="premium-panel-title">Domain Coverage Map</div>
                  </div>
                  <div className="premium-panel-body" style={{display:'flex',flexDirection:'column',gap:'1.5rem'}}>
                    {Object.keys(domains).map(domKey=>{
                      const dom=domains[domKey];
                      if(!dom.in_jd||dom.in_jd.length===0) return null;
                      const matched=dom.in_jd.filter(s=>dom.in_resume?.includes(s)).length;
                      const pct=Math.round((matched/dom.in_jd.length)*100);
                      return (
                        <div key={domKey} className="skill-category-row">
                          <div className="skill-category-header">
                            <span className="skill-category-name">{domKey.replace(/_/g,' ')}</span>
                            <span className="skill-category-pct">{matched}/{dom.in_jd.length} · {pct}%</span>
                          </div>
                          <div className="skill-bar-track">
                            <div className="skill-bar-fill" style={{width:`${pct}%`,background:pct>=75?'#10b981':pct>=40?'#f59e0b':'#ef4444'}}/>
                          </div>
                          <div className="skill-tags-row">
                            {dom.in_jd.map((s,i)=>{
                              const found=dom.in_resume?.includes(s);
                              return found
                                ?<span key={i} className="matched-chip"><Check size={11}/>{s}</span>
                                :<span key={i} className="missing-chip"><X size={11}/>{s}</span>
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </>)}

              {/* BULLET ANALYSIS */}
              {(activeTab==='all'||activeTab==='points') && (
                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#f0f9ff'}}><ListChecks size={18} color="#0ea5e9"/></div>
                    <div className="premium-panel-title">Line-by-Line Analysis</div>
                    <span style={{fontSize:'0.75rem',color:'var(--text-muted)',marginLeft:'auto'}}>{originalBullets.length} bullets</span>
                  </div>
                  <div className="premium-panel-body" style={{padding:'1rem'}}>
                    {originalBullets.length>0 ? originalBullets.map((bullet,i)=>{
                      const rw=bulletRewrites[i];
                      const isApplied=modifiedBullets[i]===(rw?.rewritten||bullet.text);
                      const sc=bullet.similarity||0;
                      return (
                        <div className="premium-bullet" key={i}>
                          <div className="premium-bullet-top">
                            <div className="bullet-score-bar" style={{background:getScoreColor(sc)}}/>
                            <div className="bullet-score-section">
                              <div className="bullet-score-num" style={{color:getScoreColor(sc)}}>{sc.toFixed(0)}</div>
                              <div className="bullet-score-pct">/ 100</div>
                            </div>
                            <div className="bullet-text-section">
                              <p>{bullet.text}</p>
                            </div>
                          </div>
                          <div className="bullet-footer">
                            <span className="bullet-strength-label" style={{color:getScoreColor(sc)}}>{bullet.strength||'Moderate'}</span>
                            {!rw?.rewritten && (
                              <button className="bullet-optimize-btn" disabled={rw?.loading} onClick={()=>handleRewriteBullet(i,bullet.text)}>
                                {rw?.loading?<><RefreshCcw size={12} style={{animation:'spin 0.8s linear infinite'}}/> Optimizing...</>:<><Zap size={12}/> Optimize</>}
                              </button>
                            )}
                          </div>
                          {rw?.rewritten && (
                            <div className="rewrite-result-box">
                              <div className="rewrite-result-label">AI-Optimized Version</div>
                              <div className="rewrite-result-text">{rw.rewritten}</div>
                              <button className={`btn-apply ${isApplied?'applied':'pending'}`} onClick={()=>!isApplied&&acceptRewrite(i,rw.rewritten)}>
                                {isApplied?<><Check size={12}/> Applied to Draft</>:<><Edit3 size={12}/> Apply to Draft</>}
                              </button>
                            </div>
                          )}
                        </div>
                      )
                    }):<p style={{color:'var(--text-muted)',textAlign:'center',padding:'2rem'}}>No bullet points detected.</p>}
                  </div>
                </div>
              )}

              {/* V3 INTELLIGENCE */}
              {(activeTab==='all'||activeTab==='v3') && (<>

                {/* Impact */}
                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#f5f3ff'}}><Target size={18} color="#7c3aed"/></div>
                    <div className="premium-panel-title">Impact Density</div>
                    <div className="premium-panel-score" style={{color:getScoreColor(impactAnalysis.score||0)}}>{Math.round(impactAnalysis.score||0)}%</div>
                  </div>
                  <div className="premium-panel-body">
                    <div className="stat-trio">
                      <div className="stat-box" style={{background:'#f0fdf4'}}>
                        <div className="stat-box-num" style={{color:'#059669'}}>{impactAnalysis.impact_count||0}</div>
                        <div className="stat-box-lbl" style={{color:'#059669'}}>Impact</div>
                      </div>
                      <div className="stat-box" style={{background:'#fffbeb'}}>
                        <div className="stat-box-num" style={{color:'#d97706'}}>{impactAnalysis.mixed_count||0}</div>
                        <div className="stat-box-lbl" style={{color:'#d97706'}}>Mixed</div>
                      </div>
                      <div className="stat-box" style={{background:'#fef2f2'}}>
                        <div className="stat-box-num" style={{color:'#dc2626'}}>{impactAnalysis.duty_count||0}</div>
                        <div className="stat-box-lbl" style={{color:'#dc2626'}}>Duty Only</div>
                      </div>
                    </div>
                    <div style={{fontSize:'0.85rem',color:'var(--text-secondary)',lineHeight:1.6,marginTop:'0.5rem'}}>
                      {(impactAnalysis.impact_ratio||0)>=0.5?'Strong quantified impact across bullet points. Resume demonstrates measurable outcomes.'
                       :(impactAnalysis.impact_ratio||0)>=0.2?'Some quantified impact present. Adding more metrics would significantly strengthen this resume.'
                       :'Resume lacks quantified achievements. Critical to add metrics — percentages, dollar amounts, scale.'}
                    </div>
                  </div>
                </div>

                {/* Trajectory */}
                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#ecfeff'}}><TrendingUp size={18} color="#0891b2"/></div>
                    <div className="premium-panel-title">Career Trajectory</div>
                    <div className="premium-panel-score" style={{color:getScoreColor(trajectoryAnalysis.score||0)}}>{Math.round(trajectoryAnalysis.score||0)}</div>
                  </div>
                  <div className="premium-panel-body">
                    <div className="quad-stats" style={{marginBottom:'1.25rem'}}>
                      <div className="quad-stat"><div className="quad-stat-num">{trajectoryAnalysis.total_years||0}</div><div className="quad-stat-lbl">Years Exp</div></div>
                      <div className="quad-stat"><div className="quad-stat-num">{trajectoryAnalysis.entry_count||0}</div><div className="quad-stat-lbl">Positions</div></div>
                      <div className="quad-stat"><div className="quad-stat-num" style={{color:'#10b981'}}>{trajectoryAnalysis.progressions||0}</div><div className="quad-stat-lbl">Promotions</div></div>
                      <div className="quad-stat"><div className="quad-stat-num" style={{color:trajectoryAnalysis.avg_tenure_months>=18?'#10b981':'#f59e0b'}}>{Math.round(trajectoryAnalysis.avg_tenure_months||0)}mo</div><div className="quad-stat-lbl">Avg Tenure</div></div>
                    </div>
                    {(trajectoryAnalysis.flags||[]).map((f,i)=>(
                      <div key={i} className="flag-row" style={{color:f.type==='green'?'#059669':f.type==='red'?'#dc2626':'#d97706'}}>
                        {getFlagIcon(f.type)}{f.detail}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Layout / Document Quality */}
                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#fffbeb'}}><Layout size={18} color="#d97706"/></div>
                    <div className="premium-panel-title">Document Quality</div>
                    <div className="premium-panel-score" style={{color:getScoreColor(layoutAnalysis.score||0)}}>{Math.round(layoutAnalysis.score||0)}</div>
                  </div>
                  <div className="premium-panel-body">
                    {layoutAnalysis.dimensions && (
                      <div className="quad-stats" style={{marginBottom:'1rem'}}>
                        {Object.entries(layoutAnalysis.dimensions).map(([key,val])=>(
                          <div key={key} className="quad-stat">
                            <div style={{background:`${getScoreColor(val)}18`,borderRadius:'10px',padding:'0.5rem 0.25rem',marginBottom:'0.3rem'}}>
                              <div className="quad-stat-num" style={{color:getScoreColor(val)}}>{Math.round(val)}</div>
                            </div>
                            <div className="quad-stat-lbl" style={{textTransform:'capitalize'}}>{key}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {(layoutAnalysis.flags||[]).map((f,i)=>(
                      <div key={i} className="flag-row" style={{color:f.type==='green'?'#059669':f.type==='red'?'#dc2626':'#d97706'}}>
                        {getFlagIcon(f.type)}{f.detail}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Pedigree */}
                {pedigreeAnalysis.score>0 && (
                  <div className="premium-panel">
                    <div className="premium-panel-header">
                      <div className="premium-panel-icon" style={{background:'#eef2ff'}}><Building2 size={18} color="#6366f1"/></div>
                      <div className="premium-panel-title">Company Pedigree</div>
                      <div className="premium-panel-score" style={{color:getScoreColor(pedigreeAnalysis.score||0)}}>{Math.round(pedigreeAnalysis.score||0)}</div>
                    </div>
                    <div className="premium-panel-body">
                      <p style={{fontSize:'0.9rem',color:'var(--text-secondary)',marginBottom:'1rem',lineHeight:1.6}}>{pedigreeAnalysis.summary}</p>
                      {(pedigreeAnalysis.signals||[]).map((s,i)=>(
                        <div key={i} className="flag-row" style={{color:s.type==='green'?'#059669':'#d97706'}}>
                          {getFlagIcon(s.type)}{s.detail}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>)}

              {/* SUGGESTIONS */}
              {(activeTab==='all'||activeTab==='editor') && (
                <div className="premium-panel">
                  <div className="premium-panel-header">
                    <div className="premium-panel-icon" style={{background:'#fffbeb'}}><Edit3 size={18} color="#d97706"/></div>
                    <div className="premium-panel-title">Actionable Rewrites</div>
                    <span style={{fontSize:'0.75rem',background:'#fef3c7',color:'#92400e',padding:'0.2rem 0.6rem',borderRadius:'99px',fontWeight:700}}>{suggestions.length} suggestions</span>
                  </div>
                  <div className="premium-panel-body" style={{padding:'0.75rem'}}>
                    {suggestions.map((s,i)=>{
                      const _found=originalBullets.findIndex(b=>b.text===s.original);
                      const origIndex=_found>=0?_found:i;
                      const isApplied=modifiedBullets[origIndex]===s.improved;
                      return (
                        <div key={i} className="suggestion-card">
                          <div className="suggestion-original">
                            <div className="suggestion-original-label">Original · {s.original_score}% match</div>
                            <div className="suggestion-original-text">{s.original}</div>
                          </div>
                          <div className="suggestion-improved">
                            <div className="suggestion-improved-label">AI Executive Rewrite</div>
                            <div className="suggestion-improved-text">{s.improved}</div>
                          </div>
                          <div className="suggestion-actions">
                            <button className={`btn-apply ${isApplied?'applied':'pending'}`} onClick={()=>!isApplied&&acceptRewrite(origIndex,s.improved)}>
                              {isApplied?<><Check size={13}/> Applied to Draft</>:<><Edit3 size={13}/> Inject into Draft</>}
                            </button>
                            <button className="report-masthead-btn" style={{background:'transparent',border:'1px solid var(--border-subtle)',color:'var(--text-secondary)'}} onClick={()=>navigator.clipboard.writeText(s.improved)}>
                              <Copy size={13}/> Copy
                            </button>
                          </div>
                        </div>
                      )
                    })}
                    {suggestions.length===0 && <p style={{color:'var(--text-muted)',textAlign:'center',padding:'2rem'}}>No suggestions generated.</p>}
                  </div>
                </div>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {hasResults && !drawerOpen && (
        <button className="fab-reopen" onClick={() => setDrawerOpen(true)}>
          <FileDigit size={20}/> Reopen Dashboard
        </button>
      )}
    </main>
  )
}

/* ======================================================================
   App Root
   ====================================================================== */
export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/" element={<ProtectedRoute><AnalyzerPage /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
      </Routes>
    </>
  )
}
