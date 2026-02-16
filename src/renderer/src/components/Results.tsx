import React, { useState, useEffect } from 'react'
import { generateResume, generateCoverLetter } from '../api/client'
import type {
  MasterProfile, JobAnalysis,
  ResumeGenerationOptions, CoverLetterGenerationOptions,
  ResumeGenerationResult, CoverLetterGenerationResult
} from '../types/schema'

type GenerationState =
  | 'idle'
  | 'generating-resume'
  | 'generating-cover'
  | 'resume-ready'
  | 'cover-ready'
  | 'error'

interface ResultsProps {
  profile: MasterProfile | null
  jobAnalysis: JobAnalysis | null
}

interface AppHelperState {
  job_title: string
  location: string
  years_experience: string
  salary_min: string
  salary_max: string
  currency: 'USD' | 'GBP' | 'EUR' | 'AUD' | 'CAD'
  visa_status: string
  why_this_company: string
  preferred_start_date: string
  willing_to_relocate: boolean
}

function downloadDocx(base64: string, filename: string): void {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))
  const blob = new Blob([bytes], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  })
  const url = URL.createObjectURL(blob)
  const a = Object.assign(document.createElement('a'), { href: url, download: filename })
  a.click()
  URL.revokeObjectURL(url)
}

function AtsScoreBadge({ score }: { score: number }): React.JSX.Element {
  const tier = score >= 70 ? 'high' : score >= 40 ? 'mid' : 'low'
  return (
    <span className={`ats-badge ats-badge--${tier}`}>
      ATS Match: {score}%
    </span>
  )
}

function Results({ profile, jobAnalysis }: ResultsProps): React.JSX.Element {
  const [state, setState] = useState<GenerationState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [resumeResult, setResumeResult] = useState<ResumeGenerationResult | null>(null)
  const [coverResult, setCoverResult] = useState<CoverLetterGenerationResult | null>(null)

  const [resumeOptions, setResumeOptions] = useState<ResumeGenerationOptions>({
    include_skills: true,
    include_projects: false,
    include_certifications: true,
    include_volunteer: false,
    max_pages: 2,
    template: 'harvard'
  })
  const [coverOptions, setCoverOptions] = useState<CoverLetterGenerationOptions>({
    include_header: true,
    include_footer: false
  })

  // Application Helper state — frontend only, not sent to backend
  const [showAppHelper, setShowAppHelper] = useState(false)
  const [appHelper, setAppHelper] = useState<AppHelperState>({
    job_title: '',
    location: '',
    years_experience: '',
    salary_min: '',
    salary_max: '',
    currency: 'USD',
    visa_status: '',
    why_this_company: '',
    preferred_start_date: '',
    willing_to_relocate: false
  })

  // Pre-fill job_title from jobAnalysis whenever it changes
  useEffect(() => {
    if (jobAnalysis?.job_title) {
      setAppHelper((prev) => ({ ...prev, job_title: jobAnalysis.job_title }))
    }
  }, [jobAnalysis])

  function setAppField<K extends keyof AppHelperState>(field: K, value: AppHelperState[K]): void {
    setAppHelper((prev) => ({ ...prev, [field]: value }))
  }

  const hasProfile = profile !== null
  const hasJob = jobAnalysis !== null
  const ready = hasProfile && hasJob
  const isGenerating = state === 'generating-resume' || state === 'generating-cover'

  async function handleGenerateResume(): Promise<void> {
    if (!ready) return
    setError(null)
    setState('generating-resume')

    const result = await generateResume(profile, jobAnalysis, resumeOptions)
    if (!result.ok) {
      setError(result.error)
      setState('error')
      return
    }
    setResumeResult(result.data)
    setState('resume-ready')
  }

  async function handleGenerateCoverLetter(): Promise<void> {
    if (!ready) return
    setError(null)
    setState('generating-cover')

    const result = await generateCoverLetter(profile, jobAnalysis, coverOptions)
    if (!result.ok) {
      setError(result.error)
      setState('error')
      return
    }
    setCoverResult(result.data)
    setState('cover-ready')
  }

  return (
    <section className="tab-pane" aria-label="Results">
      <h2 className="pane-title">Generate Documents</h2>
      <p className="pane-subtitle">
        Tailor your resume and generate a cover letter for the analyzed job.
      </p>

      {/* Prerequisite status pills */}
      <div className="generation-prereqs">
        <span className={`prereq-pill prereq-pill--${hasProfile ? 'ok' : 'missing'}`}>
          {hasProfile ? '✓ Profile ready' : '✗ No profile — upload a resume first'}
        </span>
        <span className={`prereq-pill prereq-pill--${hasJob ? 'ok' : 'missing'}`}>
          {hasJob ? '✓ Job analyzed' : '✗ No job — paste a job description first'}
        </span>
      </div>

      {ready && (
        <>
          {/* Options panel */}
          <div className="options-panel">
            <div className="options-group">
              <h3 className="options-heading">Resume Sections</h3>
              <div className="options-checkboxes">
                {(
                  [
                    ['include_skills', 'Skills'],
                    ['include_projects', 'Projects'],
                    ['include_certifications', 'Certifications'],
                    ['include_volunteer', 'Volunteer']
                  ] as [keyof ResumeGenerationOptions, string][]
                ).map(([key, label]) => (
                  <label key={key} className="option-label">
                    <input
                      type="checkbox"
                      checked={resumeOptions[key] as boolean}
                      onChange={(e) =>
                        setResumeOptions((prev) => ({ ...prev, [key]: e.target.checked }))
                      }
                      disabled={isGenerating}
                    />
                    {label}
                  </label>
                ))}
              </div>

              <div className="options-row">
                <span className="options-row-label">Page limit:</span>
                {([1, 2] as (1 | 2)[]).map((n) => (
                  <label key={n} className="option-label">
                    <input
                      type="radio"
                      name="max_pages"
                      value={n}
                      checked={resumeOptions.max_pages === n}
                      onChange={() =>
                        setResumeOptions((prev) => ({ ...prev, max_pages: n }))
                      }
                      disabled={isGenerating}
                    />
                    {n} page{n > 1 ? 's' : ''}
                  </label>
                ))}
              </div>
            </div>

            <div className="options-group">
              <h3 className="options-heading">Resume Template</h3>
              <div className="template-picker">
                {(
                  [
                    {
                      id: 'harvard' as const,
                      name: 'Harvard Style',
                      description: 'Traditional ALL-CAPS headers, right-aligned dates'
                    },
                    {
                      id: 'modern' as const,
                      name: 'Modern',
                      description: 'Clean SMALL CAPS headers with blue accent underline'
                    }
                  ]
                ).map((tpl) => (
                  <label
                    key={tpl.id}
                    className={`template-card${resumeOptions.template === tpl.id ? ' template-card--selected' : ''}`}
                  >
                    <input
                      type="radio"
                      name="template"
                      value={tpl.id}
                      checked={resumeOptions.template === tpl.id}
                      onChange={() => setResumeOptions((prev) => ({ ...prev, template: tpl.id }))}
                      disabled={isGenerating}
                      style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
                    />
                    <span className="template-card-name">{tpl.name}</span>
                    <span className="template-card-desc">{tpl.description}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="options-group">
              <h3 className="options-heading">Cover Letter Options</h3>
              <div className="options-checkboxes">
                <label className="option-label">
                  <input
                    type="checkbox"
                    checked={coverOptions.include_header}
                    onChange={(e) =>
                      setCoverOptions((prev) => ({ ...prev, include_header: e.target.checked }))
                    }
                    disabled={isGenerating}
                  />
                  Include header (name, contact, date)
                </label>
                <label className="option-label">
                  <input
                    type="checkbox"
                    checked={coverOptions.include_footer}
                    onChange={(e) =>
                      setCoverOptions((prev) => ({ ...prev, include_footer: e.target.checked }))
                    }
                    disabled={isGenerating}
                  />
                  Include page number footer
                </label>
              </div>
            </div>
          </div>

          {/* Generate buttons */}
          <div className="generate-buttons">
            <button
              className="btn btn--primary"
              onClick={handleGenerateResume}
              disabled={isGenerating}
            >
              {state === 'generating-resume' ? 'Generating resume...' : 'Generate Resume'}
            </button>
            <button
              className="btn btn--secondary"
              onClick={handleGenerateCoverLetter}
              disabled={isGenerating}
            >
              {state === 'generating-cover' ? 'Generating cover letter...' : 'Generate Cover Letter'}
            </button>
          </div>

          {/* Application Reference Card */}
          <div className="app-helper-panel">
            <button
              className="app-helper-toggle"
              onClick={() => setShowAppHelper((prev) => !prev)}
              aria-expanded={showAppHelper}
            >
              <span className="app-helper-toggle-label">Application Reference Card</span>
              <span className="app-helper-toggle-chevron">{showAppHelper ? '▲' : '▼'}</span>
            </button>

            {showAppHelper && (
              <div className="app-helper-body">
                <p className="app-helper-hint">
                  Fill in details for quick reference while completing job applications.
                  This data stays in the app only.
                </p>

                {/* Salary Context */}
                <div className="app-helper-group">
                  <h4 className="app-helper-group-heading">Salary Context</h4>
                  <div className="app-helper-grid">
                    <div className="editor-field">
                      <label className="editor-label">Job Title</label>
                      <input
                        className="editor-input"
                        value={appHelper.job_title}
                        onChange={(e) => setAppField('job_title', e.target.value)}
                      />
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Location</label>
                      <input
                        className="editor-input"
                        value={appHelper.location}
                        onChange={(e) => setAppField('location', e.target.value)}
                        placeholder="e.g. London, UK"
                      />
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Years Experience</label>
                      <input
                        className="editor-input"
                        type="number"
                        min="0"
                        value={appHelper.years_experience}
                        onChange={(e) => setAppField('years_experience', e.target.value)}
                      />
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Currency</label>
                      <select
                        className="editor-input editor-select"
                        value={appHelper.currency}
                        onChange={(e) =>
                          setAppField('currency', e.target.value as AppHelperState['currency'])
                        }
                      >
                        {(['USD', 'GBP', 'EUR', 'AUD', 'CAD'] as const).map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Salary Min</label>
                      <input
                        className="editor-input"
                        type="number"
                        min="0"
                        value={appHelper.salary_min}
                        onChange={(e) => setAppField('salary_min', e.target.value)}
                        placeholder="e.g. 60000"
                      />
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Salary Max</label>
                      <input
                        className="editor-input"
                        type="number"
                        min="0"
                        value={appHelper.salary_max}
                        onChange={(e) => setAppField('salary_max', e.target.value)}
                        placeholder="e.g. 80000"
                      />
                    </div>
                  </div>
                  {(appHelper.salary_min || appHelper.salary_max) && (
                    <p className="app-helper-salary-display">
                      Target range: {appHelper.currency} {appHelper.salary_min || '?'} –{' '}
                      {appHelper.salary_max || '?'}
                    </p>
                  )}
                </div>

                {/* Application Q&A */}
                <div className="app-helper-group">
                  <h4 className="app-helper-group-heading">Application Q&A</h4>
                  <div className="app-helper-grid">
                    <div className="editor-field">
                      <label className="editor-label">Visa / Work Authorization</label>
                      <select
                        className="editor-input editor-select"
                        value={appHelper.visa_status}
                        onChange={(e) => setAppField('visa_status', e.target.value)}
                      >
                        <option value="">Select...</option>
                        <option value="Citizen">Citizen</option>
                        <option value="Permanent Resident">Permanent Resident</option>
                        <option value="Work Visa">Work Visa (no sponsorship needed)</option>
                        <option value="Requires Sponsorship">Requires Sponsorship</option>
                        <option value="Student Visa">Student Visa / OPT</option>
                      </select>
                    </div>
                    <div className="editor-field">
                      <label className="editor-label">Preferred Start Date</label>
                      <input
                        className="editor-input"
                        value={appHelper.preferred_start_date}
                        onChange={(e) => setAppField('preferred_start_date', e.target.value)}
                        placeholder="e.g. 2 weeks notice / Immediately"
                      />
                    </div>
                    <div className="editor-field editor-field--full">
                      <label className="editor-label">Why This Company</label>
                      <textarea
                        className="editor-textarea"
                        rows={3}
                        value={appHelper.why_this_company}
                        onChange={(e) => setAppField('why_this_company', e.target.value)}
                        placeholder="What genuinely excites you about this company or role?"
                      />
                    </div>
                    <div className="editor-field">
                      <label className="option-label" style={{ marginTop: 'var(--space-1)' }}>
                        <input
                          type="checkbox"
                          checked={appHelper.willing_to_relocate}
                          onChange={(e) => setAppField('willing_to_relocate', e.target.checked)}
                        />
                        Willing to relocate
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {/* Resume result */}
      {state === 'resume-ready' && resumeResult && (
        <div className="preview-card">
          <div className="preview-card-header">
            <span className="preview-card-title">{resumeResult.filename}</span>
            <AtsScoreBadge score={resumeResult.ats_match_score} />
            <button
              className="btn btn--primary btn--sm"
              onClick={() => downloadDocx(resumeResult.docx_base64, resumeResult.filename)}
            >
              Download .docx
            </button>
          </div>

          {resumeResult.tailoring_notes.length > 0 && (
            <ul className="tailoring-notes-list">
              {resumeResult.tailoring_notes.map((note, i) => (
                <li key={i}>{note}</li>
              ))}
            </ul>
          )}

          <pre className="preview-text">{resumeResult.preview_text}</pre>
        </div>
      )}

      {/* Cover letter result */}
      {state === 'cover-ready' && coverResult && (
        <div className="preview-card">
          <div className="preview-card-header">
            <span className="preview-card-title">{coverResult.filename}</span>
            <button
              className="btn btn--primary btn--sm"
              onClick={() => downloadDocx(coverResult.docx_base64, coverResult.filename)}
            >
              Download .docx
            </button>
          </div>

          <pre className="preview-text">{coverResult.preview_text}</pre>
        </div>
      )}

      {!ready && state === 'idle' && (
        <div className="empty-state">
          <p className="empty-state-text">Prerequisites not met.</p>
          <p className="empty-state-hint">
            Complete both the Profile Upload and Job Description tabs to enable generation.
          </p>
        </div>
      )}
    </section>
  )
}

export default Results
