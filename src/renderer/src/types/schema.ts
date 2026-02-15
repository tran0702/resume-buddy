// ============================================================
// Resume Buddy — Shared Schema Definitions
// These TypeScript interfaces mirror the Python dataclasses in:
//   backend/api/ai/schemas.py
// Any change here must be reflected there and vice versa.
// ============================================================

// ------ Master Profile ------

export interface ContactInfo {
  name: string
  email: string
  phone?: string | null
  location?: string | null
  linkedin?: string | null
  github?: string | null
  portfolio?: string | null
}

export interface WorkExperience {
  company: string
  title: string
  start_date: string        // "YYYY-MM" format
  end_date: string | null   // null = present
  location?: string | null
  bullets: string[]
}

export interface Education {
  institution: string
  degree: string
  field_of_study: string
  graduation_date: string
  gpa?: number | null
  honors?: string[]
}

export interface Project {
  name: string
  description: string
  technologies: string[]
  url?: string | null
}

export interface MasterProfile {
  contact: ContactInfo
  summary?: string | null
  work_experience: WorkExperience[]
  education: Education[]
  skills: string[]
  certifications?: string[]
  projects?: Project[]
  languages?: string[]
  volunteer?: string[]
}

// ------ Job Analysis ------

export interface JobRequirement {
  skill: string
  importance: 'required' | 'preferred' | 'nice-to-have'
}

export interface JobAnalysis {
  job_title: string
  company_name?: string | null
  required_skills: string[]
  preferred_skills: string[]
  key_responsibilities: string[]
  years_experience_required?: number | null
  education_required?: string | null
  industry?: string | null
  seniority_level?: 'entry' | 'mid' | 'senior' | 'lead' | 'executive' | null
  keywords_for_ats: string[]
  company_values?: string[]
  raw_requirements?: JobRequirement[]
}

// ------ Generated Document ------

export type DocumentType = 'resume' | 'cover_letter' | 'interview_prep'

export interface GeneratedDocument {
  document_type: DocumentType
  job_title: string
  company_name?: string | null
  generated_at: string        // ISO 8601 timestamp
  content: string             // plaintext or markdown preview
  tailoring_notes?: string[]
  ats_match_score?: number    // 0–100
}

// ------ Phase 3: Generation ------

export interface ResumeGenerationOptions {
  include_skills: boolean
  include_projects: boolean
  include_certifications: boolean
  include_volunteer: boolean
  max_pages: 1 | 2
}

export interface CoverLetterGenerationOptions {
  include_header: boolean
  include_footer: boolean
}

export interface ResumeGenerationResult {
  docx_base64: string
  filename: string
  preview_text: string
  tailoring_notes: string[]
  ats_match_score: number
}

export interface CoverLetterGenerationResult {
  docx_base64: string
  filename: string
  preview_text: string
}

// ------ API Response Wrappers ------

export interface ApiSuccess<T> {
  ok: true
  data: T
}

export interface ApiError {
  ok: false
  error: string
  detail?: string
}

export type ApiResult<T> = ApiSuccess<T> | ApiError
