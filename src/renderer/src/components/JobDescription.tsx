import React, { useState } from 'react'
import { analyzeJob } from '../api/client'
import type { JobAnalysis } from '../types/schema'

type AnalysisState = 'idle' | 'analyzing' | 'done' | 'error'

interface JobDescriptionProps {
  onJobAnalyzed: (job: JobAnalysis) => void
}

function JobDescription({ onJobAnalyzed }: JobDescriptionProps): React.JSX.Element {
  const [jobText, setJobText] = useState('')
  const [state, setState] = useState<AnalysisState>('idle')
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleAnalyze(): Promise<void> {
    if (!jobText.trim()) return
    setError(null)
    setAnalysis(null)
    setState('analyzing')

    const result = await analyzeJob(jobText)
    if (!result.ok) {
      setError(result.error)
      setState('error')
      return
    }

    setAnalysis(result.data)
    onJobAnalyzed(result.data)
    setState('done')
  }

  function handleClear(): void {
    setJobText('')
    setState('idle')
    setAnalysis(null)
    setError(null)
  }

  return (
    <section className="tab-pane" aria-label="Job Description">
      <h2 className="pane-title">Paste Job Description</h2>
      <p className="pane-subtitle">
        Paste the full job description below. The AI will extract requirements, ATS keywords,
        and seniority context to tailor your resume.
      </p>

      <textarea
        className="job-textarea"
        placeholder="Paste the job description here..."
        value={jobText}
        onChange={(e) => setJobText(e.target.value)}
        rows={12}
        aria-label="Job description input"
        disabled={state === 'analyzing'}
      />

      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <button
          className="btn btn--primary"
          onClick={handleAnalyze}
          disabled={!jobText.trim() || state === 'analyzing'}
        >
          {state === 'analyzing' ? 'Analyzing...' : 'Analyze Job'}
        </button>
        {(state === 'done' || state === 'error') && (
          <button className="btn btn--secondary" onClick={handleClear}>
            Clear
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {state === 'done' && analysis && (
        <div className="analysis-results">
          <h3 className="preview-title">{analysis.job_title}</h3>
          {analysis.company_name && (
            <p className="company-name">{analysis.company_name}</p>
          )}
          {analysis.seniority_level && (
            <p className="company-name" style={{ marginBottom: 0 }}>
              Level: {analysis.seniority_level}
              {analysis.years_experience_required
                ? ` · ${analysis.years_experience_required}+ years required`
                : ''}
            </p>
          )}

          {analysis.required_skills.length > 0 && (
            <div className="keyword-section">
              <h4>Required Skills</h4>
              <div className="tag-list">
                {analysis.required_skills.map((skill) => (
                  <span key={skill} className="tag tag--required">{skill}</span>
                ))}
              </div>
            </div>
          )}

          {analysis.preferred_skills.length > 0 && (
            <div className="keyword-section">
              <h4>Preferred Skills</h4>
              <div className="tag-list">
                {analysis.preferred_skills.map((skill) => (
                  <span key={skill} className="tag tag--preferred">{skill}</span>
                ))}
              </div>
            </div>
          )}

          {analysis.keywords_for_ats.length > 0 && (
            <div className="keyword-section">
              <h4>ATS Keywords</h4>
              <div className="tag-list">
                {analysis.keywords_for_ats.map((kw) => (
                  <span key={kw} className="tag tag--ats">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {analysis.key_responsibilities.length > 0 && (
            <div className="keyword-section">
              <h4>Key Responsibilities</h4>
              <ul style={{ paddingLeft: 'var(--space-5)', color: 'var(--color-fg-primary)', fontSize: 'var(--font-size-sm)', lineHeight: 'var(--line-height-relaxed)' }}>
                {analysis.key_responsibilities.slice(0, 6).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default JobDescription
