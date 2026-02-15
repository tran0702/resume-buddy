# Resume Buddy — Developer Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Setup & Running Locally](#3-setup--running-locally)
4. [Architecture](#4-architecture)
5. [API Reference](#5-api-reference)
6. [What Was Built (Phases 0–3)](#6-what-was-built-phases-03)
7. [What Comes Next (Phase 4)](#7-what-comes-next-phase-4)

---

## 1. Project Overview

Resume Buddy is a local-first desktop app built with:

| Layer | Technology | Purpose |
|---|---|---|
| Desktop shell | Electron 33 | Cross-platform window + OS integration |
| Frontend | React 18 + TypeScript | UI components |
| Build tool | electron-vite 2 + Vite 5 | Dev server + production bundling |
| Backend | Python Flask 3.1 | Document parsing + AI orchestration + DOCX generation |
| AI (primary) | Google Gemini 1.5 Flash | Structured JSON extraction + bullet tailoring |
| AI (stub) | Anthropic Claude | Ready to activate when key is available |

All AI calls happen server-side in Flask. The renderer never sees API keys.

---

## 2. Repository Structure

```
resume-buddy/
├── .gitignore
├── .env.example               ← copy to .env and fill in keys
├── package.json               ← npm scripts, Electron + React deps
├── electron.vite.config.ts    ← build pipeline (main / preload / renderer)
├── tsconfig.json              ← root: references node + web configs
├── tsconfig.node.json         ← main process + preload compiler options
├── tsconfig.web.json          ← React renderer compiler options
├── electron-builder.yml       ← Phase 5 packaging stub
│
├── src/
│   ├── main/
│   │   └── index.ts           ← Electron main process
│   ├── preload/
│   │   └── index.ts           ← contextBridge (exposes platform only)
│   └── renderer/
│       ├── index.html         ← Vite entry + Content Security Policy
│       └── src/
│           ├── main.tsx       ← React root
│           ├── App.tsx        ← Shell: header + tab bar + health check + shared state
│           ├── types/
│           │   └── schema.ts  ← All shared types (MasterProfile, JobAnalysis,
│           │                     ResumeGenerationOptions, ResumeGenerationResult, …)
│           ├── api/
│           │   └── client.ts  ← Typed fetch wrappers for all 6 Flask endpoints
│           ├── components/
│           │   ├── TabBar.tsx
│           │   ├── ProfileUpload.tsx   ← upload + parse + extract; fires onProfileExtracted
│           │   ├── JobDescription.tsx  ← paste + analyze job; fires onJobAnalyzed
│           │   └── Results.tsx         ← options panel + generate + preview + download
│           └── styles/
│               ├── global.css          ← Tokyo Night CSS variables + reset
│               └── components.css      ← all component styles (Phases 1–3)
│
├── backend/
│   ├── __init__.py            ← makes backend a Python package
│   ├── app.py                 ← Flask entry point (load_dotenv → create_app → run)
│   ├── config.py              ← Config class reads os.environ
│   ├── requirements.txt
│   └── api/
│       ├── __init__.py        ← create_app() factory + CORS + blueprint registration
│       ├── documents.py       ← POST /parse-document
│       ├── jobs.py            ← POST /analyze-job
│       ├── profiles.py        ← POST /extract-profile
│       ├── generation.py      ← POST /generate-resume, POST /generate-cover-letter
│       ├── templates/
│       │   ├── __init__.py
│       │   ├── resume_builder.py       ← Harvard-style DOCX builder
│       │   └── cover_letter_builder.py ← Cover letter DOCX builder
│       └── ai/
│           ├── __init__.py
│           ├── base.py        ← AIProvider ABC (4 abstract methods)
│           ├── orchestrator.py ← get_ai_provider() factory
│           ├── gemini.py      ← GeminiProvider (active — all 4 methods implemented)
│           ├── claude.py      ← ClaudeProvider (stub — activate when key is ready)
│           └── schemas.py     ← Python dataclasses mirroring schema.ts
│
└── docs/
    ├── roadmap.md             ← product roadmap + phase tracking
    └── developer-guide.md     ← this file
```

---

## 3. Setup & Running Locally

### Prerequisites
- Node.js 18+ with npm
- Python 3.10+
- A Google Gemini API key (get one at [aistudio.google.com](https://aistudio.google.com))

### First-time Setup

```bash
# 1. Clone and enter the project
cd resume-buddy

# 2. Install Node dependencies
npm install

# 3. Create Python virtual environment
python -m venv .venv

# 4. Install Python dependencies
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # Mac / Linux
pip install -r backend/requirements.txt

# 5. Create your .env file
copy .env.example .env          # Windows
# cp .env.example .env          # Mac / Linux
# Then open .env and add your GEMINI_API_KEY
```

### Running in Development

```bash
npm run dev
```

This uses `concurrently` to start both:
- **Flask** on `http://localhost:5001` (via `.venv/Scripts/python -m backend.app`)
- **Electron + Vite** dev server on `http://localhost:5173`

The Electron window opens automatically. The status pill in the header shows **"Backend Connected"** (green) when Flask is reachable.

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `gemini` | Active AI provider: `gemini` or `claude` |
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Model name — can use `gemini-2.0-flash` etc. |
| `ANTHROPIC_API_KEY` | *(optional)* | Anthropic key — only needed if `AI_PROVIDER=claude` |
| `ANTHROPIC_MODEL` | `claude-opus-4-5-20250929` | Claude model name |
| `FLASK_PORT` | `5001` | Flask port |
| `FLASK_DEBUG` | `true` | Flask debug mode |

---

## 4. Architecture

### Communication Flow

```
Electron Main Process
       │
       │  loads
       ▼
React Renderer (Vite / localhost:5173 in dev)
       │
       │  fetch() HTTP — plain HTTP, no IPC
       ▼
Flask Backend (localhost:5001)
       │
       ├── /parse-document → pdfminer.six / python-docx / plain read
       │
       ├── /extract-profile ──────────────────┐
       │                                       │
       ├── /analyze-job ────────────── AIOrchestrator.get_ai_provider()
       │                                       │
       ├── /generate-resume ──────────         ├── GeminiProvider (active)
       │        │                    │         │     extract_profile()
       │        ├── tailor_bullets() │         │     analyze_job()
       │        └── resume_builder   │         │     tailor_bullets()
       │                             │         │     generate_cover_letter_text()
       └── /generate-cover-letter ───┘         │
                │                              └── ClaudeProvider (stub)
                ├── generate_cover_letter_text()
                └── cover_letter_builder
```

**Key security decisions:**
- `contextIsolation: true` + `nodeIntegration: false` — always enforced
- API keys live only in Flask — the renderer never sees them
- Flask binds to `127.0.0.1` only (not `0.0.0.0`)
- CORS restricted to localhost origins only
- Content Security Policy in `index.html` explicitly whitelists `localhost:5001`

### AI Provider Pattern

All providers implement `AIProvider` (abstract base in `backend/api/ai/base.py`):

```python
class AIProvider(ABC):
    def extract_profile(self, resume_text: str) -> dict: ...
    def analyze_job(self, job_description_text: str) -> dict: ...
    def tailor_bullets(self, profile_dict: dict, job_analysis_dict: dict) -> dict: ...
    def generate_cover_letter_text(self, profile_dict: dict, job_analysis_dict: dict) -> dict: ...

    @property
    def provider_name(self) -> str: ...
```

**`tailor_bullets()` return shape:**
```json
{
  "tailored_experience": [
    { "company": "Acme", "title": "Engineer", "tailored_bullets": ["..."] }
  ],
  "tailoring_notes": ["Emphasized Python and Docker from ATS keywords"],
  "ats_match_score": 78
}
```

**`generate_cover_letter_text()` return shape:**
```json
{
  "cover_letter_text": "Opening paragraph...\n\nBody paragraph...\n\nClosing paragraph.",
  "subject_line": "Application for Senior Software Engineer — Jane Doe"
}
```

To activate Claude: set `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY` in `.env`, then uncomment the implementation template in `backend/api/ai/claude.py`.

### Shared Schema Contract

`src/renderer/src/types/schema.ts` and `backend/api/ai/schemas.py` define the same data shapes in TypeScript and Python respectively. **Any change to one must be mirrored in the other.**

Key types:

| Type | Description |
|---|---|
| `MasterProfile` | Full structured resume (contact, experience, education, skills…) |
| `JobAnalysis` | Extracted job requirements, ATS keywords, seniority level |
| `ResumeGenerationOptions` | Section toggles + max_pages |
| `ResumeGenerationResult` | docx_base64, filename, preview_text, tailoring_notes, ats_match_score |
| `CoverLetterGenerationOptions` | include_header, include_footer toggles |
| `CoverLetterGenerationResult` | docx_base64, filename, preview_text |

### State Flow (Frontend)

Shared state lives in `App.tsx` and flows down as props:

```
App.tsx
  ├── masterProfile: MasterProfile | null    ← set by ProfileUpload
  └── jobAnalysis: JobAnalysis | null        ← set by JobDescription

  ProfileUpload   → onProfileExtracted(profile) → sets masterProfile
  JobDescription  → onJobAnalyzed(job)       → sets jobAnalysis
  Results         ← receives profile + jobAnalysis as read-only props
```

---

## 5. API Reference

All endpoints are on `http://localhost:5001`.

### `GET /health`
Returns server status.
```json
{ "status": "ok", "version": "0.1.0" }
```

### `POST /parse-document`
Accepts `multipart/form-data` with a `file` field (`.pdf`, `.docx`, `.txt`).
Returns extracted plain text — **no AI involved**.
```json
{ "text": "...", "filename": "resume.pdf" }
```
Errors: `400` no file | `415` unsupported type | `422` no text extracted | `500` parse failure

### `POST /extract-profile`
Body: `{ "text": "raw resume text" }`
Returns `MasterProfile` JSON via AI.
```json
{
  "contact": { "name": "Jane Doe", "email": "jane@example.com", ... },
  "work_experience": [...],
  "education": [...],
  "skills": ["Python", "React", ...],
  ...
}
```
Errors: `400` missing body | `422` text too short | `502` AI provider error

### `POST /analyze-job`
Body: `{ "text": "full job description" }`
Returns `JobAnalysis` JSON via AI.
```json
{
  "job_title": "Senior Software Engineer",
  "company_name": "Acme Corp",
  "required_skills": [...],
  "preferred_skills": [...],
  "keywords_for_ats": [...],
  "seniority_level": "senior",
  ...
}
```
Errors: `400` missing body | `422` text too short | `502` AI provider error

### `POST /generate-resume`
Body:
```json
{
  "profile": { ...MasterProfile... },
  "job_analysis": { ...JobAnalysis... },
  "options": {
    "include_skills": true,
    "include_projects": false,
    "include_certifications": true,
    "include_volunteer": false,
    "max_pages": 2
  }
}
```
Flow: `tailor_bullets()` → `resume_builder.build()` → base64 encode

Response:
```json
{
  "docx_base64": "...",
  "filename": "Senior Software Engineer - Resume - Applied.docx",
  "preview_text": "Jane Doe\njane@example.com | ...\n\nEXPERIENCE\n...",
  "tailoring_notes": ["Emphasized Python and Docker from ATS keywords"],
  "ats_match_score": 78
}
```
Errors: `400` missing fields | `502` AI provider error

### `POST /generate-cover-letter`
Body:
```json
{
  "profile": { ...MasterProfile... },
  "job_analysis": { ...JobAnalysis... },
  "options": {
    "include_header": true,
    "include_footer": false
  }
}
```
Flow: `generate_cover_letter_text()` → `cover_letter_builder.build()` → base64 encode

Response:
```json
{
  "docx_base64": "...",
  "filename": "Senior Software Engineer - Cover Letter - Applied.docx",
  "preview_text": "Jane Doe\njane@example.com\n...\nDear Hiring Manager,\n\n..."
}
```
Errors: `400` missing fields | `502` AI provider error

---

## 6. What Was Built (Phases 0–3)

### Phase 0 — Security & Init
- `.gitignore` covering Node, Python, Electron, OS artifacts
- `.env.example` with all keys documented
- Virtual environment (`.venv/`) with all Python deps installed

### Phase 1 — Foundation
- **Electron main process** (`src/main/index.ts`): security-hardened window creation, OS-specific behaviour, `backgroundColor` prevents white flash
- **Preload script** (`src/preload/index.ts`): exposes only `platform` via `contextBridge`
- **React shell** (`App.tsx`): 3-tab layout, backend health check on mount
- **Tokyo Night design system**: full CSS variable palette in `global.css`, zero icon libraries
- **Dev workflow**: `npm run dev` starts Flask + Electron together via `concurrently`

### Phase 2 — Core Engine
- **Schema contract**: TypeScript interfaces + Python dataclasses, in sync
- **Document parsing**: PDF via `pdfminer.six`, DOCX via `python-docx`, TXT via plain read
- **AI orchestrator**: provider-agnostic factory, switchable via `AI_PROVIDER` env var
- **Gemini provider**: uses new `google-genai` SDK (not deprecated `google-generativeai`); JSON mode (`response_mime_type='application/json'`) for reliable structured output
- **Claude stub**: imports cleanly, raises clear error if called, includes commented implementation template
- **Flask endpoints**: `/parse-document`, `/extract-profile`, `/analyze-job` — all with input validation and structured error responses
- **React components**: ProfileUpload (upload → parse → extract, shows skill tags), JobDescription (analyze → required/preferred/ATS keyword tags)

### Phase 3 — Document Generation
- **AI methods added**: `tailor_bullets()` (rewrites experience bullets for the target job) and `generate_cover_letter_text()` (writes full cover letter body) — implemented in Gemini, stubbed in Claude
- **Harvard-style resume builder** (`backend/api/templates/resume_builder.py`): name 18pt bold centred, section headers ALL CAPS bold with bottom border rule, company+date row with right-aligned tab stop, italic title line, hanging-indent bullets, section toggles, page-limit heuristic with warnings in `tailoring_notes`
- **Cover letter builder** (`backend/api/templates/cover_letter_builder.py`): optional header (name/contact/date/company), salutation, AI-generated body paragraphs split on `\n\n`, closing, optional page-number footer via XML field
- **Generation blueprint** (`backend/api/generation.py`): `/generate-resume` and `/generate-cover-letter` — both return base64 DOCX + filename + preview text
- **Shared state lifted** to `App.tsx`: `masterProfile` and `jobAnalysis` flow down as props; `ProfileUpload` and `JobDescription` fire callbacks when data is ready
- **Results tab** (`src/renderer/src/components/Results.tsx`): prerequisite status pills, options panel (section toggles + page limit + cover letter toggles), Generate Resume / Generate Cover Letter buttons, text preview card, ATS score badge (green/orange/red), tailoring notes list, Download .docx button (`base64 → Uint8Array → Blob → anchor click`)
- **Phase 3 CSS**: prereq pills, options panel, generate buttons, preview card, ATS score badge, tailoring notes

---

## 7. What Comes Next (Phase 4)

Phase 4 is **User Experience & Features**. The full generation pipeline works end-to-end — Phase 4 focuses on polish, profile editing, and additional workflow tools.

### 4a. Profile Management (Manual Edit)

The current flow is one-way: upload resume → AI extracts profile → read-only preview.
Phase 4 adds the ability to manually edit the extracted profile before generating documents.

**Approach — inline editable fields:**

Add an "Edit Profile" mode to `ProfileUpload.tsx` (or a dedicated `ProfileEditor.tsx` component):
- Contact section: text inputs for name, email, phone, location, LinkedIn, GitHub
- Work experience: editable company/title/dates, add/remove/reorder bullet points
- Education: editable institution/degree/field/graduation date
- Skills: tag input (add/remove individual skills)
- Certifications, projects, languages, volunteer: add/remove list items

The edited `MasterProfile` object must be passed back up to `App.tsx` via the existing `onProfileExtracted` callback (or a new `onProfileUpdated` callback).

**Key consideration**: The current `App.tsx` state only stores the most recently extracted profile. If the user edits then re-uploads, the edits are lost. Phase 4 should ensure edits are preserved — either by keeping a separate `editedProfile` state alongside the raw extracted one, or by treating the profile as fully mutable from the moment it is extracted.

**Suggested implementation order:**
1. Add edit button to profile preview card in `ProfileUpload.tsx`
2. Create `ProfileEditor.tsx` — renders all profile fields as inputs
3. On save, fire `onProfileExtracted` with the edited profile
4. Wire up in `App.tsx` — no new state needed, just re-use `setMasterProfile`

### 4b. File Naming Convention (Already in Generation)

The naming convention `[Job Title] - Resume - Applied.docx` and `[Job Title] - Cover Letter - Applied.docx` is already implemented in `backend/api/generation.py` via the `_safe_filename()` helper. No further work needed here.

### 4c. Template Selection (Visual Picker)

Currently only one resume template exists (Harvard style). Phase 4 can add a template picker.

**Approach:**
- Define a `template: 'harvard' | 'modern' | 'minimal'` field in `ResumeGenerationOptions`
- Add it to `schema.ts` and the backend `options` dict
- Create `backend/api/templates/modern_builder.py` (or similar) following the same `build(profile, tailored, options) -> tuple[io.BytesIO, str]` interface
- In `generation.py`, dispatch to the correct builder based on `options.get('template', 'harvard')`
- In `Results.tsx`, add a template selector (radio group or visual cards) to the options panel

### 4d. Application Helper UI

**Salary Context Input:**
- A simple form with fields: job title, location, years of experience, and a manual salary range entry
- No external API — user manually enters the market rate range they have researched
- Display as a reference card in the Results tab or as a separate sub-tab

**Application Q&A:**
- Text fields for common application questions: visa/work authorization status, "Why this company?", preferred start date
- Store answers in component state; optionally pass to AI to incorporate into cover letter

### 4e. Interview Prep Module

Add a fourth tab: "Interview Prep"

**Flow:**
1. User clicks "Generate Interview Prep" (requires profile + job analysis — same prerequisites as Results)
2. Calls a new endpoint `POST /generate-interview-prep`
3. AI returns a structured set of likely interview questions with suggested talking-point answers based on the profile and job

**New backend work needed:**
- Add `generate_interview_prep(profile_dict, job_analysis_dict) -> dict` to `AIProvider` ABC
- Implement in `gemini.py` with a prompt that returns:
  ```json
  {
    "behavioural_questions": [{ "question": "...", "suggested_answer": "..." }],
    "technical_questions": [{ "question": "...", "suggested_answer": "..." }],
    "questions_to_ask": ["..."]
  }
  ```
- Stub in `claude.py`
- Add `POST /generate-interview-prep` to `generation.py`

**New frontend work needed:**
- Add `InterviewPrep.tsx` component
- Add a fourth tab to `App.tsx` and `TABS` array
- Display questions in expandable accordion cards

### 4f. Implementation Order for Phase 4

1. **Profile editor** — highest user value, needed before any downstream work on templates
2. **Interview prep tab** — standalone new feature, no dependencies on profile editor
3. **Template picker** — requires creating at least one additional DOCX builder
4. **Application helper UI** — lower priority, can be done incrementally

### Phase 4 Files to Create

| File | Purpose |
|---|---|
| `src/renderer/src/components/ProfileEditor.tsx` | Inline editable profile form |
| `src/renderer/src/components/InterviewPrep.tsx` | Interview questions display |
| `backend/api/templates/modern_builder.py` | Second resume template (optional) |

### Phase 4 Files to Modify

| File | Change |
|---|---|
| `src/renderer/src/App.tsx` | Add InterviewPrep tab + state |
| `src/renderer/src/components/ProfileUpload.tsx` | Add edit mode / link to ProfileEditor |
| `src/renderer/src/components/Results.tsx` | Add template selector, salary context |
| `src/renderer/src/types/schema.ts` | Add `InterviewPrepResult`, extend `ResumeGenerationOptions` with `template` |
| `src/renderer/src/api/client.ts` | Add `generateInterviewPrep()` |
| `backend/api/ai/base.py` | Add `generate_interview_prep()` abstract method |
| `backend/api/ai/gemini.py` | Implement `generate_interview_prep()` |
| `backend/api/ai/claude.py` | Stub `generate_interview_prep()` |
| `backend/api/generation.py` | Add `POST /generate-interview-prep` route |
| `src/renderer/src/styles/components.css` | Add Phase 4 component styles |
