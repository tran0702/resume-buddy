import React, { useState } from 'react'
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
    max_pages: 2
  })
  const [coverOptions, setCoverOptions] = useState<CoverLetterGenerationOptions>({
    include_header: true,
    include_footer: false
  })

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
