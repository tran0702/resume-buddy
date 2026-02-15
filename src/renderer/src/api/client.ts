import type { MasterProfile, JobAnalysis, ApiResult } from '../types/schema'

const BASE_URL = 'http://localhost:5001'

// ---------- Generic fetch helpers ----------

async function post<T>(path: string, body: Record<string, unknown>): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    const json = await response.json()
    if (!response.ok) {
      return { ok: false, error: json.error ?? 'Unknown server error', detail: json.detail }
    }
    return { ok: true, data: json as T }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error — is Flask running?'
    return { ok: false, error: message }
  }
}

async function postFile<T>(path: string, file: File): Promise<ApiResult<T>> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    // No Content-Type header — browser sets multipart/form-data with boundary automatically
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      body: formData
    })
    const json = await response.json()
    if (!response.ok) {
      return { ok: false, error: json.error ?? 'File upload error', detail: json.detail }
    }
    return { ok: true, data: json as T }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Upload failed — is Flask running?'
    return { ok: false, error: message }
  }
}

// ---------- Exported API functions ----------

/** Upload a resume file (PDF/DOCX/TXT) and parse it to raw text */
export async function parseDocument(
  file: File
): Promise<ApiResult<{ text: string; filename: string }>> {
  return postFile('/parse-document', file)
}

/** Extract a structured MasterProfile from raw resume text */
export async function extractProfile(text: string): Promise<ApiResult<MasterProfile>> {
  return post<MasterProfile>('/extract-profile', { text })
}

/** Analyze a job description and return a structured JobAnalysis */
export async function analyzeJob(text: string): Promise<ApiResult<JobAnalysis>> {
  return post<JobAnalysis>('/analyze-job', { text })
}

/** Health check — verify Flask backend is reachable */
export async function healthCheck(): Promise<ApiResult<{ status: string; version: string }>> {
  try {
    const response = await fetch(`${BASE_URL}/health`)
    const json = await response.json()
    return { ok: true, data: json }
  } catch {
    return { ok: false, error: 'Flask backend is not reachable' }
  }
}
