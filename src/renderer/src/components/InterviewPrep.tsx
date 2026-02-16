import React, { useState } from 'react'
import { generateInterviewPrep } from '../api/client'
import type { MasterProfile, JobAnalysis, InterviewPrepResult, InterviewQA } from '../types/schema'

type PrepState = 'idle' | 'generating' | 'done' | 'error'

interface InterviewPrepProps {
  profile: MasterProfile | null
  jobAnalysis: JobAnalysis | null
}

// ---- Accordion card for a single Q&A pair ----

function QACard({ qa, index }: { qa: InterviewQA; index: number }): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="qa-card">
      <button
        className={`qa-card-question${expanded ? ' qa-card-question--expanded' : ''}`}
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <span className="qa-card-index">{index + 1}</span>
        <span className="qa-card-question-text">{qa.question}</span>
        <span className="qa-card-chevron">{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div className="qa-card-answer">
          <p className="qa-card-answer-label">Suggested Answer</p>
          <p className="qa-card-answer-text">{qa.suggested_answer}</p>
        </div>
      )}
    </div>
  )
}

// ---- Main component ----

function InterviewPrep({ profile, jobAnalysis }: InterviewPrepProps): React.JSX.Element {
  const [state, setState] = useState<PrepState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<InterviewPrepResult | null>(null)

  const hasProfile = profile !== null
  const hasJob = jobAnalysis !== null
  const ready = hasProfile && hasJob
  const isGenerating = state === 'generating'

  async function handleGenerate(): Promise<void> {
    if (!ready) return
    setError(null)
    setState('generating')

    const res = await generateInterviewPrep(profile, jobAnalysis)
    if (!res.ok) {
      setError(res.error)
      setState('error')
      return
    }
    setResult(res.data)
    setState('done')
  }

  return (
    <section className="tab-pane" aria-label="Interview Prep">
      <h2 className="pane-title">Interview Prep</h2>
      <p className="pane-subtitle">
        AI-generated interview questions and suggested answers tailored to your profile and the job.
      </p>

      {/* Prerequisite status pills — same pattern as Results */}
      <div className="generation-prereqs">
        <span className={`prereq-pill prereq-pill--${hasProfile ? 'ok' : 'missing'}`}>
          {hasProfile ? '✓ Profile ready' : '✗ No profile — upload a resume first'}
        </span>
        <span className={`prereq-pill prereq-pill--${hasJob ? 'ok' : 'missing'}`}>
          {hasJob ? '✓ Job analyzed' : '✗ No job — paste a job description first'}
        </span>
      </div>

      {ready && (
        <div className="generate-buttons">
          <button
            className="btn btn--primary"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating questions...' : 'Generate Interview Prep'}
          </button>
          {state === 'done' && (
            <button
              className="btn btn--secondary"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              Regenerate
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {state === 'done' && result && (
        <div className="interview-prep-results">

          {/* Behavioural Questions */}
          <div className="qa-section">
            <h3 className="qa-section-heading">Behavioural Questions</h3>
            <p className="qa-section-hint">Use the STAR method: Situation, Task, Action, Result.</p>
            <div className="qa-list">
              {result.behavioural_questions.map((qa, i) => (
                <QACard key={i} qa={qa} index={i} />
              ))}
            </div>
          </div>

          {/* Technical Questions */}
          <div className="qa-section">
            <h3 className="qa-section-heading">Technical Questions</h3>
            <p className="qa-section-hint">Based on required skills for this role.</p>
            <div className="qa-list">
              {result.technical_questions.map((qa, i) => (
                <QACard key={i} qa={qa} index={i} />
              ))}
            </div>
          </div>

          {/* Questions to Ask */}
          <div className="qa-section">
            <h3 className="qa-section-heading">Questions to Ask the Interviewer</h3>
            <ul className="questions-to-ask-list">
              {result.questions_to_ask.map((q, i) => (
                <li key={i} className="questions-to-ask-item">{q}</li>
              ))}
            </ul>
          </div>

        </div>
      )}

      {!ready && state === 'idle' && (
        <div className="empty-state">
          <p className="empty-state-text">Prerequisites not met.</p>
          <p className="empty-state-hint">
            Complete both the Profile Upload and Job Description tabs to enable interview prep.
          </p>
        </div>
      )}
    </section>
  )
}

export default InterviewPrep
