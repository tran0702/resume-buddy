# Resume Buddy — Developer Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Setup & Running Locally](#3-setup--running-locally)
4. [Architecture](#4-architecture)
5. [API Reference](#5-api-reference)
6. [What Was Built (Phases 0–2)](#6-what-was-built-phases-02)
7. [What Comes Next (Phase 3)](#7-what-comes-next-phase-3)

---

## 1. Project Overview

Resume Buddy is a local-first desktop app built with:

| Layer | Technology | Purpose |
|---|---|---|
| Desktop shell | Electron 33 | Cross-platform window + OS integration |
| Frontend | React 18 + TypeScript | UI components |
| Build tool | electron-vite 2 + Vite 5 | Dev server + production bundling |
| Backend | Python Flask 3.1 | Document parsing + AI orchestration |
| AI (primary) | Google Gemini 1.5 Flash | Structured JSON extraction |
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
│           ├── App.tsx        ← Shell: header + tab bar + health check
│           ├── types/
│           │   └── schema.ts  ← MasterProfile, JobAnalysis, GeneratedDocument
│           ├── api/
│           │   └── client.ts  ← Typed fetch wrappers for Flask endpoints
│           ├── components/
│           │   ├── TabBar.tsx
│           │   ├── ProfileUpload.tsx   ← upload + parse + extract profile
│           │   ├── JobDescription.tsx  ← paste + analyze job
│           │   └── Results.tsx         ← Phase 3 placeholder
│           └── styles/
│               ├── global.css          ← Tokyo Night CSS variables + reset
│               └── components.css      ← all component styles
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
│       └── ai/
│           ├── __init__.py
│           ├── base.py        ← AIProvider ABC + AIProviderError
│           ├── orchestrator.py ← get_ai_provider() factory
│           ├── gemini.py      ← GeminiProvider (active)
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
       ├── /extract-profile ──────────┐
       │                              ▼
       └── /analyze-job ──── AIOrchestrator.get_ai_provider()
                                      │
                             ┌────────┴────────┐
                             ▼                 ▼
                       GeminiProvider    ClaudeProvider
                      (active)           (stub)
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
    def provider_name(self) -> str: ...
```

To activate Claude: set `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY` in `.env`, then uncomment the implementation template in `backend/api/ai/claude.py`.

To add a new provider (e.g. OpenAI): create `backend/api/ai/openai.py` implementing `AIProvider`, add a branch in `backend/api/ai/orchestrator.py`, and add the key to `.env.example`.

### Shared Schema Contract

`src/renderer/src/types/schema.ts` and `backend/api/ai/schemas.py` define the same data shapes in TypeScript and Python respectively. **Any change to one must be mirrored in the other.**

Key types:

| Type | Description |
|---|---|
| `MasterProfile` | Full structured resume (contact, experience, education, skills…) |
| `JobAnalysis` | Extracted job requirements, ATS keywords, seniority level |
| `GeneratedDocument` | Output of Phase 3 document generation |

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

---

## 6. What Was Built (Phases 0–2)

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
- **React components**: ProfileUpload (upload → parse → extract, shows skill tags), JobDescription (analyze → required/preferred/ATS keyword tags), Results (placeholder)

---

## 7. What Comes Next (Phase 3)

Phase 3 is **Template & Document Generation**. The foundation is fully in place — this phase adds the output side.

### 3a. Output Format Decision
- Primary: **DOCX** (`python-docx` is already installed)
- Secondary: **PDF** — export from DOCX using `docx2pdf` (Windows/Mac) or LibreOffice headless

### 3b. New Flask Endpoint: `/generate-resume`

```
POST /generate-resume
Body: {
  "profile": MasterProfile,   ← from /extract-profile
  "job_analysis": JobAnalysis, ← from /analyze-job
  "options": {
    "include_skills": true,
    "include_volunteer": false,
    "include_hobbies": false,
    "max_pages": 2
  }
}
Returns: {
  "docx_base64": "...",         ← DOCX file as base64 string
  "filename": "Senior Software Engineer - Resume - Applied.docx",
  "page_count_estimate": 1
}
```

### 3c. New Flask Endpoint: `/generate-cover-letter`

```
POST /generate-cover-letter
Body: {
  "profile": MasterProfile,
  "job_analysis": JobAnalysis,
  "options": {
    "include_header": true,
    "include_footer": false,
    "max_pages": 1
  }
}
Returns: {
  "docx_base64": "...",
  "filename": "Senior Software Engineer - Cover Letter - Applied.docx"
}
```

### 3d. Resume Builder Implementation Plan

**New files to create:**

```
backend/api/
├── generation.py              ← new blueprint: /generate-resume, /generate-cover-letter
└── templates/
    ├── __init__.py
    ├── resume_builder.py      ← Harvard-style DOCX builder using python-docx
    └── cover_letter_builder.py
```

**`resume_builder.py` responsibilities:**
1. Accept `MasterProfile` + `JobAnalysis` dicts
2. Call AI to produce a **tailored bullet list** — rewrite experience bullets to match job keywords
3. Build the DOCX using `python-docx` with Harvard-style formatting:
   - Name as large heading, contact info in one line
   - Bold company + right-aligned dates
   - Indented bullet points
4. Page limit heuristic: estimate character count per section; warn if over limit (exact pagination not enforceable in DOCX without rendering)
5. Return the DOCX as `io.BytesIO`, which the endpoint base64-encodes

**New AI prompt needed in `gemini.py`:**
```
Given this MasterProfile and JobAnalysis, rewrite the experience bullets
to be tailored for the job. Emphasize keywords: {keywords_for_ats}.
Return JSON: { "tailored_bullets": { "company_title_key": ["bullet", ...] } }
```

### 3e. Frontend Updates (Phase 3)

**`Results.tsx`** becomes functional — replace the placeholder with:
- Download button for resume DOCX
- Download button for cover letter DOCX
- ATS match score display
- Tailoring notes (what the AI changed)

**`App.tsx`** — add state to pass `MasterProfile` and `JobAnalysis` between tabs, or use React Context to share data across all three tabs.

### 3f. New Backend Dependency

Add to `requirements.txt`:
```
docx2pdf==0.1.8   # PDF export (requires Word on Windows, LibreOffice on Linux)
```

### Suggested Implementation Order for Phase 3

1. Add `backend/api/templates/resume_builder.py` — DOCX generation, no AI yet (hardcoded bullets first)
2. Test DOCX output manually, verify Harvard style formatting
3. Add AI tailoring prompt to `gemini.py` — `tailor_resume()` method
4. Wire up `backend/api/generation.py` blueprint
5. Update `Results.tsx` to show download buttons
6. Add shared state (React Context) so profile + job analysis flow into Results tab
7. Add cover letter builder following the same pattern
8. Add PDF export as a bonus step
