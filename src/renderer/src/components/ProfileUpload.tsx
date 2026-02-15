import React, { useState, useRef } from 'react'
import { parseDocument, extractProfile } from '../api/client'
import type { MasterProfile } from '../types/schema'

type UploadState = 'idle' | 'parsing' | 'extracting' | 'done' | 'error'

function ProfileUpload(): React.JSX.Element {
  const [state, setState] = useState<UploadState>('idle')
  const [profile, setProfile] = useState<MasterProfile | null>(null)
  const [rawText, setRawText] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = e.target.files?.[0]
    if (!file) return

    setError(null)
    setProfile(null)
    setRawText(null)
    setState('parsing')

    // Step 1: Parse the document file to plain text
    const parseResult = await parseDocument(file)
    if (!parseResult.ok) {
      setError(parseResult.error)
      setState('error')
      return
    }

    const { text } = parseResult.data
    setRawText(text)
    setState('extracting')

    // Step 2: Extract structured MasterProfile from the parsed text
    const profileResult = await extractProfile(text)
    if (!profileResult.ok) {
      setError(profileResult.error)
      setState('error')
      return
    }

    setProfile(profileResult.data)
    setState('done')

    // Reset the file input so the same file can be re-uploaded
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const isLoading = state === 'parsing' || state === 'extracting'

  return (
    <section className="tab-pane" aria-label="Profile Upload">
      <h2 className="pane-title">Upload Your Resume</h2>
      <p className="pane-subtitle">
        Upload a PDF, DOCX, or TXT file. Your file is parsed locally — only anonymized text is
        sent to the AI provider for profile extraction.
      </p>

      <div className="upload-zone">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          className="file-input-hidden"
          aria-label="Upload resume file"
          disabled={isLoading}
        />
        <button
          className="btn btn--primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          {state === 'idle' && 'Choose File'}
          {state === 'parsing' && 'Parsing document...'}
          {state === 'extracting' && 'Extracting profile...'}
          {state === 'done' && 'Upload Another'}
          {state === 'error' && 'Try Again'}
        </button>
        <p className="upload-hint">Supported formats: .pdf  .docx  .txt</p>
      </div>

      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {state === 'done' && profile && (
        <div className="profile-preview">
          <h3 className="preview-title">{profile.contact.name}</h3>
          {profile.contact.email && (
            <p className="preview-email">{profile.contact.email}</p>
          )}
          <div className="preview-stats">
            <span>{profile.work_experience.length} position{profile.work_experience.length !== 1 ? 's' : ''}</span>
            <span>{profile.education.length} degree{profile.education.length !== 1 ? 's' : ''}</span>
            <span>{profile.skills.length} skill{profile.skills.length !== 1 ? 's' : ''}</span>
          </div>

          {profile.skills.length > 0 && (
            <div className="keyword-section">
              <h4>Skills</h4>
              <div className="tag-list">
                {profile.skills.slice(0, 20).map((skill) => (
                  <span key={skill} className="tag tag--preferred">{skill}</span>
                ))}
                {profile.skills.length > 20 && (
                  <span className="tag tag--preferred">+{profile.skills.length - 20} more</span>
                )}
              </div>
            </div>
          )}

          {rawText && (
            <details className="raw-text-details">
              <summary>View extracted text</summary>
              <pre className="raw-text">{rawText.slice(0, 800)}{rawText.length > 800 ? '...' : ''}</pre>
            </details>
          )}
        </div>
      )}
    </section>
  )
}

export default ProfileUpload
