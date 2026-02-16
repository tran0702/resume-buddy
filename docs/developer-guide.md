# Resume Buddy — Developer Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Setup & Running Locally](#3-setup--running-locally)
4. [Architecture](#4-architecture)
5. [API Reference](#5-api-reference)
6. [What Was Built (Phases 0–5)](#6-what-was-built-phases-05)
7. [Building for Windows](#7-building-for-windows)

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
├── electron-builder.yml       ← electron-builder config (zip + dir targets for Windows)
│
├── src/
│   ├── main/
│   │   └── index.ts           ← Electron main process
│   ├── preload/
│   │   └── index.ts           ← contextBridge (exposes platform + IPC: settings, flask:restart)
│   └── renderer/
│       ├── index.html         ← Vite entry + Content Security Policy
│       └── src/
│           ├── main.tsx       ← React root
│           ├── env.d.ts       ← Window.api type declarations (AppSettings, IPC channels)
│           ├── App.tsx        ← Shell: header + tab bar + health check + shared state + setup check
│           ├── types/
│           │   └── schema.ts  ← All shared types (MasterProfile, JobAnalysis,
│           │                     ResumeGenerationOptions, ResumeGenerationResult, …)
│           ├── api/
│           │   └── client.ts  ← Typed fetch wrappers for all Flask endpoints
│           ├── components/
│           │   ├── TabBar.tsx
│           │   ├── ApiKeySetup.tsx     ← First-run modal: provider + API key entry
│           │   ├── ProfileUpload.tsx   ← upload + parse + extract; fires onProfileExtracted
│           │   ├── JobDescription.tsx  ← paste + analyze job; fires onJobAnalyzed
│           │   └── Results.tsx         ← options panel + generate + preview + download
│           └── styles/
│               ├── global.css          ← Tokyo Night CSS variables + reset
│               └── components.css      ← all component styles (Phases 1–5)
│
├── backend/
│   ├── __init__.py            ← makes backend a Python package
│   ├── app.py                 ← Flask entry point (frozen guard + load_dotenv → create_app → run)
│   ├── config.py              ← Config class reads os.environ
│   ├── requirements.txt
│   └── api/
│       ├── __init__.py        ← create_app() factory + CORS + after_request null-origin hook
│       ├── documents.py       ← POST /parse-document
│       ├── jobs.py            ← POST /analyze-job
│       ├── profiles.py        ← POST /extract-profile
│       ├── generation.py      ← POST /generate-resume, /generate-cover-letter, /generate-interview-prep
│       ├── templates/
│       │   ├── __init__.py
│       │   ├── resume_builder.py       ← Harvard-style DOCX builder
│       │   ├── modern_builder.py       ← Modern-style DOCX builder
│       │   └── cover_letter_builder.py ← Cover letter DOCX builder
│       └── ai/
│           ├── __init__.py
│           ├── base.py        ← AIProvider ABC (5 abstract methods incl. generate_interview_prep)
│           ├── orchestrator.py ← get_ai_provider() factory
│           ├── gemini.py      ← GeminiProvider (active — all 5 methods implemented)
│           ├── claude.py      ← ClaudeProvider (stub — activate when key is ready)
│           └── schemas.py     ← Python dataclasses mirroring schema.ts
│
├── backend/tests/             ← pytest suite (Phase 5a — 60 tests)
│   ├── __init__.py
│   ├── conftest.py            ← session Flask app, mock_ai_provider fixture
│   ├── fixtures/
│   │   ├── sample_resume.txt
│   │   ├── sample_resume.pdf
│   │   └── sample_resume.docx
│   ├── test_document_parsing.py   ← unit tests for _extract_* helpers
│   ├── test_document_routes.py    ← HTTP tests for /parse-document
│   └── test_generation_routes.py  ← mocked AI tests for generation endpoints
│
├── scripts/
│   ├── create_test_fixtures.py    ← one-time: generates fixtures above
│   └── run_backend.py             ← PyInstaller entry point (frozen mode)
│
├── pyproject.toml             ← pytest config (testpaths, pythonpath=["."])
├── backend.spec               ← PyInstaller spec (onedir, collect_all for pdfminer/docx/genai)
├── requirements-dev.txt       ← pytest, fpdf2 (fixture generation)
├── requirements-build.txt     ← pyinstaller
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
Electron Main Process (src/main/index.ts)
       │
       ├── dev:      Flask started by concurrently (npm run dev)
       ├── packaged: spawns run_backend.exe, polls /health until ready
       │
       │  IPC (contextBridge)
       ├── settings:load / settings:save  → userData/settings.json
       ├── settings:hasApiKey             → true in dev, checks settings in prod
       └── flask:restart                  → kill + respawn Flask with new env
       │
       │  loads
       ▼
React Renderer (Vite / localhost:5173 in dev, file:// in prod)
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
       ├── /generate-cover-letter ────┘         │     generate_interview_prep()
       │                                        │
       └── /generate-interview-prep            └── ClaudeProvider (stub)
```

**Key security decisions:**
- `contextIsolation: true` + `nodeIntegration: false` — always enforced
- API keys stored only in `userData/settings.json` (packaged) or `.env` (dev) — renderer never sees them
- Flask binds to `127.0.0.1` only (not `0.0.0.0`)
- CORS: explicit `after_request` hook handles `Origin: null` (Electron file:// sends null, not `file://`)
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

## 6. What Was Built (Phases 0–5)

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

### Phase 4 — User Experience & Features
- **Profile Editor** (`src/renderer/src/components/ProfileEditor.tsx`): full inline-editable form for all MasterProfile sections (contact, summary, work experience with bullet add/remove/reorder, education, skills tag-input, certifications/languages/volunteer string lists, projects). Deep-clone pattern with `JSON.parse(JSON.stringify(profile))` for safe draft state
- **`editedProfile` state** in `App.tsx`: fresh upload resets both `masterProfile` and `editedProfile`; editing only touches `editedProfile`; `Results` and `InterviewPrep` consume `editedProfile`
- **Interview Prep tab** (`src/renderer/src/components/InterviewPrep.tsx`): 4th tab, same prerequisite pills as Results, calls `POST /generate-interview-prep`, accordion Q&A cards (click to expand answer), three sections: Behavioural, Technical, Questions to Ask
- **`generate_interview_prep()` AI method**: added to `AIProvider` ABC, implemented in `GeminiProvider` (5 behavioural + 5 technical + 4 questions grounded in profile data), stubbed in `ClaudeProvider`
- **Modern resume template** (`backend/api/templates/modern_builder.py`): same interface as `resume_builder.py`; name 22pt bold centered, contact line with `·` separator, horizontal rule, SMALL CAPS headers via `w:smallCaps` XML with blue `7aa2f7` bottom border accent
- **Template picker** in `Results.tsx`: two radio-card options (Harvard / Modern), sent as `options.template` to backend; `generation.py` dispatches to the correct builder
- **Application Reference Card** in `Results.tsx`: collapsible panel (collapsed by default) with Salary Context (job title, location, years exp, currency, min/max + formatted range display) and Application Q&A (visa status, start date, why this company, willing to relocate); frontend-only, no backend
- **Phase 4 CSS**: editor overlay, grid/field/label/input/textarea/card patterns, btn--icon variants, tag-remove, string-list, QA accordion cards, template picker cards, app-helper panel

### Phase 5 — Testing & Windows Packaging

**5a — Validation Suite**
- **60 pytest tests** covering document parsing edge cases (TXT/PDF/DOCX), mocked AI providers (no API calls), and generation route integration tests
- Test infrastructure: `pyproject.toml` (pytest config), `backend/tests/` package, `backend/tests/fixtures/` (generated TXT + DOCX + PDF)
- Run: `npm run test:backend`
- Edge cases covered: UTF-8, latin-1 fallback, CJK chars, CRLF line endings, blank paragraphs, corrupt files, uppercase extensions, multi-dot filenames, AIProviderError → 502

**5b — Windows Packaging**
- **PyInstaller** (`backend.spec`): freezes Flask + all deps into `dist/backend/run_backend/run_backend.exe` (`--onedir` mode, `upx=False`)
  - `collect_all()` for pdfminer (CMap data files), python-docx (default.docx template), google.genai (namespace package), anthropic
  - `console=True` so Electron can capture stdout for readiness detection
- **Electron main** (`src/main/index.ts`): spawns `run_backend.exe` in packaged mode; polls `/health` (20s timeout); IPC for settings + flask:restart
- **Settings storage**: `userData/settings.json` — API keys never touch the renderer
- **First-run modal** (`ApiKeySetup.tsx`): provider dropdown + password input; saves settings + restarts Flask
- **Build output**: `release/Resume Buddy-0.1.0-win.zip` (portable) + `release/win-unpacked/` (direct launch)

---

## 7. Building for Windows

### Prerequisites
- Python venv with all deps installed (including `pyinstaller` from `requirements-build.txt`)
- Node deps installed (`npm install`)

### Full build (one command)

```bash
npm run dist:win
```

This runs:
1. `npm run build` — compiles Electron + React to `out/`
2. `npm run pyinstaller` — freezes Flask to `dist/backend/run_backend/`
3. `npx electron-builder --win --x64` — bundles everything to `release/`

### Step-by-step (useful for debugging)

```bash
# 1. Build JS
npm run build

# 2. Freeze Flask (takes ~3–5 minutes first time)
.venv/Scripts/python -m PyInstaller backend.spec --distpath dist/backend --workpath dist/build_work --noconfirm

# 3. Smoke test the frozen Flask (should print "[Flask] Frozen backend on http://127.0.0.1:5001")
dist/backend/run_backend/run_backend.exe
# Ctrl+C to stop

# 4. Package with electron-builder
npx electron-builder --win --x64
```

### Output files

| File | Description |
|---|---|
| `release/Resume Buddy-0.1.0-win.zip` | Portable ZIP — extract and run `Resume Buddy.exe` |
| `release/win-unpacked/Resume Buddy.exe` | Unpacked build for direct launch / testing |
| `release/builder-debug.yml` | electron-builder debug info |

### Known limitations (MVP)

- **SmartScreen warning**: unsigned binary shows "Windows protected your PC" — click "More info" → "Run anyway". Expected for MVP.
- **Port 5001 conflict**: if already bound, Flask fails and the app shows "Backend Offline". Post-MVP fix: dynamic port selection.
- **Installer size**: ~150–250 MB (PyInstaller bundles Python + all deps). Expected for a Python-based desktop app.
- **No macOS build**: `mac:` target removed from `electron-builder.yml` for this phase. Add back in Phase 5c.
