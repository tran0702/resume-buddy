import React, { useState } from 'react'
import type {
  MasterProfile,
  ContactInfo,
  WorkExperience,
  Education,
  Project
} from '../types/schema'

interface ProfileEditorProps {
  profile: MasterProfile
  onSave: (profile: MasterProfile) => void
  onCancel: () => void
}

// ---- Internal helper: editable string list (certifications, languages, volunteer) ----

interface StringListSectionProps {
  label: string
  items: string[]
  onAdd: (value: string) => void
  onRemove: (index: number) => void
}

function StringListSection({ label, items, onAdd, onRemove }: StringListSectionProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState('')

  function handleAdd(): void {
    if (!inputValue.trim()) return
    onAdd(inputValue.trim())
    setInputValue('')
  }

  return (
    <section className="editor-section">
      <h4 className="editor-section-heading">{label}</h4>
      <div className="editor-tag-input-row">
        <input
          className="editor-input"
          placeholder={`Add ${label.toLowerCase()} item...`}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAdd() } }}
        />
        <button className="btn btn--secondary btn--sm" onClick={handleAdd}>Add</button>
      </div>
      {items.length > 0 && (
        <ul className="editor-string-list">
          {items.map((item, i) => (
            <li key={i} className="editor-string-list-item">
              <span>{item}</span>
              <button
                className="btn--icon btn--icon-danger"
                onClick={() => onRemove(i)}
                title={`Remove ${label.toLowerCase()} item`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

// ---- Main ProfileEditor ----

function ProfileEditor({ profile, onSave, onCancel }: ProfileEditorProps): React.JSX.Element {
  const [draft, setDraft] = useState<MasterProfile>(() =>
    JSON.parse(JSON.stringify(profile))
  )
  const [skillInput, setSkillInput] = useState('')

  // ---- Contact helpers ----

  function setContact(field: keyof ContactInfo, value: string): void {
    setDraft((prev) => ({
      ...prev,
      contact: { ...prev.contact, [field]: value || undefined }
    }))
  }

  // ---- Work experience helpers ----

  function updateExp(index: number, field: keyof WorkExperience, value: unknown): void {
    setDraft((prev) => {
      const exps = [...prev.work_experience]
      exps[index] = { ...exps[index], [field]: value }
      return { ...prev, work_experience: exps }
    })
  }

  function addBullet(expIndex: number): void {
    setDraft((prev) => {
      const exps = [...prev.work_experience]
      exps[expIndex] = { ...exps[expIndex], bullets: [...exps[expIndex].bullets, ''] }
      return { ...prev, work_experience: exps }
    })
  }

  function updateBullet(expIndex: number, bulletIndex: number, value: string): void {
    setDraft((prev) => {
      const exps = [...prev.work_experience]
      const bullets = [...exps[expIndex].bullets]
      bullets[bulletIndex] = value
      exps[expIndex] = { ...exps[expIndex], bullets }
      return { ...prev, work_experience: exps }
    })
  }

  function removeBullet(expIndex: number, bulletIndex: number): void {
    setDraft((prev) => {
      const exps = [...prev.work_experience]
      exps[expIndex] = {
        ...exps[expIndex],
        bullets: exps[expIndex].bullets.filter((_, i) => i !== bulletIndex)
      }
      return { ...prev, work_experience: exps }
    })
  }

  function addExperience(): void {
    const blank: WorkExperience = {
      company: '',
      title: '',
      start_date: '',
      end_date: null,
      location: null,
      bullets: ['']
    }
    setDraft((prev) => ({ ...prev, work_experience: [...prev.work_experience, blank] }))
  }

  function removeExperience(index: number): void {
    setDraft((prev) => ({
      ...prev,
      work_experience: prev.work_experience.filter((_, i) => i !== index)
    }))
  }

  function moveExperience(index: number, direction: 'up' | 'down'): void {
    setDraft((prev) => {
      const exps = [...prev.work_experience]
      const target = direction === 'up' ? index - 1 : index + 1
      if (target < 0 || target >= exps.length) return prev
      ;[exps[index], exps[target]] = [exps[target], exps[index]]
      return { ...prev, work_experience: exps }
    })
  }

  // ---- Education helpers ----

  function updateEdu(index: number, field: keyof Education, value: unknown): void {
    setDraft((prev) => {
      const edus = [...prev.education]
      edus[index] = { ...edus[index], [field]: value }
      return { ...prev, education: edus }
    })
  }

  function addEducation(): void {
    const blank: Education = {
      institution: '',
      degree: '',
      field_of_study: '',
      graduation_date: '',
      gpa: null,
      honors: []
    }
    setDraft((prev) => ({ ...prev, education: [...prev.education, blank] }))
  }

  function removeEducation(index: number): void {
    setDraft((prev) => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index)
    }))
  }

  // ---- Skills ----

  function addSkill(): void {
    const trimmed = skillInput.trim()
    if (!trimmed || draft.skills.includes(trimmed)) return
    setDraft((prev) => ({ ...prev, skills: [...prev.skills, trimmed] }))
    setSkillInput('')
  }

  function removeSkill(skill: string): void {
    setDraft((prev) => ({ ...prev, skills: prev.skills.filter((s) => s !== skill) }))
  }

  // ---- Generic string list (certifications, languages, volunteer) ----

  function addListItem(field: 'certifications' | 'languages' | 'volunteer', value: string): void {
    if (!value.trim()) return
    setDraft((prev) => ({ ...prev, [field]: [...(prev[field] ?? []), value.trim()] }))
  }

  function removeListItem(field: 'certifications' | 'languages' | 'volunteer', index: number): void {
    setDraft((prev) => ({
      ...prev,
      [field]: (prev[field] ?? []).filter((_, i) => i !== index)
    }))
  }

  // ---- Projects ----

  function updateProject(index: number, field: keyof Project, value: unknown): void {
    setDraft((prev) => {
      const projs = [...(prev.projects ?? [])]
      projs[index] = { ...projs[index], [field]: value }
      return { ...prev, projects: projs }
    })
  }

  function addProject(): void {
    const blank: Project = { name: '', description: '', technologies: [], url: null }
    setDraft((prev) => ({ ...prev, projects: [...(prev.projects ?? []), blank] }))
  }

  function removeProject(index: number): void {
    setDraft((prev) => ({
      ...prev,
      projects: (prev.projects ?? []).filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="editor-overlay">
      {/* Header */}
      <div className="editor-header">
        <h3 className="editor-title">Edit Profile</h3>
        <div className="editor-header-actions">
          <button className="btn btn--secondary btn--sm" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn--primary btn--sm" onClick={() => onSave(draft)}>
            Save Changes
          </button>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="editor-body">

        {/* Contact */}
        <section className="editor-section">
          <h4 className="editor-section-heading">Contact</h4>
          <div className="editor-grid-2">
            <div className="editor-field">
              <label className="editor-label">Name</label>
              <input
                className="editor-input"
                value={draft.contact.name}
                onChange={(e) => setContact('name', e.target.value)}
              />
            </div>
            <div className="editor-field">
              <label className="editor-label">Email</label>
              <input
                className="editor-input"
                value={draft.contact.email}
                onChange={(e) => setContact('email', e.target.value)}
              />
            </div>
            <div className="editor-field">
              <label className="editor-label">Phone</label>
              <input
                className="editor-input"
                value={draft.contact.phone ?? ''}
                onChange={(e) => setContact('phone', e.target.value)}
              />
            </div>
            <div className="editor-field">
              <label className="editor-label">Location</label>
              <input
                className="editor-input"
                value={draft.contact.location ?? ''}
                onChange={(e) => setContact('location', e.target.value)}
              />
            </div>
            <div className="editor-field">
              <label className="editor-label">LinkedIn</label>
              <input
                className="editor-input"
                value={draft.contact.linkedin ?? ''}
                onChange={(e) => setContact('linkedin', e.target.value)}
              />
            </div>
            <div className="editor-field">
              <label className="editor-label">GitHub</label>
              <input
                className="editor-input"
                value={draft.contact.github ?? ''}
                onChange={(e) => setContact('github', e.target.value)}
              />
            </div>
          </div>
        </section>

        {/* Summary */}
        <section className="editor-section">
          <h4 className="editor-section-heading">Summary</h4>
          <textarea
            className="editor-textarea"
            rows={4}
            value={draft.summary ?? ''}
            onChange={(e) =>
              setDraft((prev) => ({ ...prev, summary: e.target.value || null }))
            }
          />
        </section>

        {/* Work Experience */}
        <section className="editor-section">
          <div className="editor-section-row">
            <h4 className="editor-section-heading">Work Experience</h4>
            <button className="btn btn--secondary btn--sm" onClick={addExperience}>
              + Add Position
            </button>
          </div>
          {draft.work_experience.map((exp, ei) => (
            <div key={ei} className="editor-card">
              <div className="editor-card-controls">
                <span className="editor-card-index">{ei + 1}</span>
                <button
                  className="btn--icon"
                  onClick={() => moveExperience(ei, 'up')}
                  disabled={ei === 0}
                  title="Move up"
                >
                  ↑
                </button>
                <button
                  className="btn--icon"
                  onClick={() => moveExperience(ei, 'down')}
                  disabled={ei === draft.work_experience.length - 1}
                  title="Move down"
                >
                  ↓
                </button>
                <button
                  className="btn--icon btn--icon-danger"
                  onClick={() => removeExperience(ei)}
                  title="Remove position"
                >
                  ×
                </button>
              </div>
              <div className="editor-grid-2">
                <div className="editor-field">
                  <label className="editor-label">Company</label>
                  <input
                    className="editor-input"
                    value={exp.company}
                    onChange={(e) => updateExp(ei, 'company', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Job Title</label>
                  <input
                    className="editor-input"
                    value={exp.title}
                    onChange={(e) => updateExp(ei, 'title', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Start Date (YYYY-MM)</label>
                  <input
                    className="editor-input"
                    value={exp.start_date}
                    onChange={(e) => updateExp(ei, 'start_date', e.target.value)}
                    placeholder="2022-03"
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">End Date (YYYY-MM, blank = Present)</label>
                  <input
                    className="editor-input"
                    value={exp.end_date ?? ''}
                    onChange={(e) => updateExp(ei, 'end_date', e.target.value || null)}
                    placeholder="Present"
                  />
                </div>
                <div className="editor-field editor-field--full">
                  <label className="editor-label">Location</label>
                  <input
                    className="editor-input"
                    value={exp.location ?? ''}
                    onChange={(e) => updateExp(ei, 'location', e.target.value || null)}
                  />
                </div>
              </div>
              <div className="editor-bullets">
                <span className="editor-label">Bullets</span>
                {exp.bullets.map((b, bi) => (
                  <div key={bi} className="editor-bullet-row">
                    <input
                      className="editor-input editor-input--bullet"
                      value={b}
                      onChange={(e) => updateBullet(ei, bi, e.target.value)}
                    />
                    <button
                      className="btn--icon btn--icon-danger"
                      onClick={() => removeBullet(ei, bi)}
                      title="Remove bullet"
                    >
                      ×
                    </button>
                  </div>
                ))}
                <button className="btn btn--secondary btn--sm" onClick={() => addBullet(ei)}>
                  + Add Bullet
                </button>
              </div>
            </div>
          ))}
        </section>

        {/* Education */}
        <section className="editor-section">
          <div className="editor-section-row">
            <h4 className="editor-section-heading">Education</h4>
            <button className="btn btn--secondary btn--sm" onClick={addEducation}>
              + Add Education
            </button>
          </div>
          {draft.education.map((edu, ei) => (
            <div key={ei} className="editor-card">
              <div className="editor-card-controls">
                <button
                  className="btn--icon btn--icon-danger"
                  onClick={() => removeEducation(ei)}
                  title="Remove education entry"
                >
                  ×
                </button>
              </div>
              <div className="editor-grid-2">
                <div className="editor-field editor-field--full">
                  <label className="editor-label">Institution</label>
                  <input
                    className="editor-input"
                    value={edu.institution}
                    onChange={(e) => updateEdu(ei, 'institution', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Degree</label>
                  <input
                    className="editor-input"
                    value={edu.degree}
                    onChange={(e) => updateEdu(ei, 'degree', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Field of Study</label>
                  <input
                    className="editor-input"
                    value={edu.field_of_study}
                    onChange={(e) => updateEdu(ei, 'field_of_study', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Graduation Date (YYYY-MM)</label>
                  <input
                    className="editor-input"
                    value={edu.graduation_date}
                    onChange={(e) => updateEdu(ei, 'graduation_date', e.target.value)}
                    placeholder="2020-05"
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">GPA (optional)</label>
                  <input
                    className="editor-input"
                    type="number"
                    step="0.01"
                    value={edu.gpa ?? ''}
                    onChange={(e) =>
                      updateEdu(ei, 'gpa', e.target.value ? parseFloat(e.target.value) : null)
                    }
                  />
                </div>
              </div>
            </div>
          ))}
        </section>

        {/* Skills */}
        <section className="editor-section">
          <h4 className="editor-section-heading">Skills</h4>
          <div className="editor-tag-input-row">
            <input
              className="editor-input"
              placeholder="Type a skill and press Enter"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') { e.preventDefault(); addSkill() }
              }}
            />
            <button className="btn btn--secondary btn--sm" onClick={addSkill}>
              Add
            </button>
          </div>
          {draft.skills.length > 0 && (
            <div className="tag-list editor-tag-list">
              {draft.skills.map((skill) => (
                <span key={skill} className="tag tag--preferred editor-tag">
                  {skill}
                  <button className="tag-remove" onClick={() => removeSkill(skill)} title="Remove skill">
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Certifications */}
        <StringListSection
          label="Certifications"
          items={draft.certifications ?? []}
          onAdd={(v) => addListItem('certifications', v)}
          onRemove={(i) => removeListItem('certifications', i)}
        />

        {/* Projects */}
        <section className="editor-section">
          <div className="editor-section-row">
            <h4 className="editor-section-heading">Projects</h4>
            <button className="btn btn--secondary btn--sm" onClick={addProject}>
              + Add Project
            </button>
          </div>
          {(draft.projects ?? []).map((proj, pi) => (
            <div key={pi} className="editor-card">
              <div className="editor-card-controls">
                <button
                  className="btn--icon btn--icon-danger"
                  onClick={() => removeProject(pi)}
                  title="Remove project"
                >
                  ×
                </button>
              </div>
              <div className="editor-grid-2">
                <div className="editor-field editor-field--full">
                  <label className="editor-label">Name</label>
                  <input
                    className="editor-input"
                    value={proj.name}
                    onChange={(e) => updateProject(pi, 'name', e.target.value)}
                  />
                </div>
                <div className="editor-field editor-field--full">
                  <label className="editor-label">Description</label>
                  <textarea
                    className="editor-textarea"
                    rows={2}
                    value={proj.description}
                    onChange={(e) => updateProject(pi, 'description', e.target.value)}
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">Technologies (comma-separated)</label>
                  <input
                    className="editor-input"
                    value={proj.technologies.join(', ')}
                    onChange={(e) =>
                      updateProject(
                        pi,
                        'technologies',
                        e.target.value.split(',').map((t) => t.trim()).filter(Boolean)
                      )
                    }
                  />
                </div>
                <div className="editor-field">
                  <label className="editor-label">URL (optional)</label>
                  <input
                    className="editor-input"
                    value={proj.url ?? ''}
                    onChange={(e) => updateProject(pi, 'url', e.target.value || null)}
                  />
                </div>
              </div>
            </div>
          ))}
        </section>

        {/* Languages */}
        <StringListSection
          label="Languages"
          items={draft.languages ?? []}
          onAdd={(v) => addListItem('languages', v)}
          onRemove={(i) => removeListItem('languages', i)}
        />

        {/* Volunteer */}
        <StringListSection
          label="Volunteer"
          items={draft.volunteer ?? []}
          onAdd={(v) => addListItem('volunteer', v)}
          onRemove={(i) => removeListItem('volunteer', i)}
        />

      </div>
    </div>
  )
}

export default ProfileEditor
