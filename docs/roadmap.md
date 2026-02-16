
# Resume Refiner - Product Roadmap & Strategy

## 1. Goal Description
Build a local desktop application that customizes resumes and cover letters based on a master profile and job description, utilizing AI (Gemini/Claude) to optimize for keywords and generate interview preparation materials.

## 2. Technical Strategy & Architecture
- **Frontend**: React (Typescript) wrapped in Electron.
    - *Why*: Ensures a cross-platform desktop experience (Windows/Mac/Linux) while allowing for easy transition to a web application in the future.
- **Backend (Local)**: Python (Flask).
    - *Why*: Python offers superior libraries for natural language processing (`pdfminer.six`) and document generation (`python-docx`). Run locally to keep user data private initially.
- **AI Integration**: Modular API interface.
    - *Why*: Supports switching between providers (Google Gemini, Anthropic Claude) to avoid vendor lock-in and optimize for cost/performance.

## 3. Implementation Phases

### Phase 0: Initialization & Security (Completed)
- [x] Git Repository Setup & .gitignore
- [x] Security: Secure API key storage (.env)
- [x] `.env.example` committed to repo (documents required keys for collaborators)

### Phase 1: Foundation & Setup (Completed)
- [x] Project Repository: Electron + React boilerplate.
- [x] Backend Integration: Local Python Flask server.
- [x] Basic UI Skeleton: Profile Upload, Job Description Input, Results View.
- [x] Design System: "Tokyo Night" Theme (Minimalist, No Icons).
- [x] Dev workflow: `concurrently` script to run Flask + Electron together (`npm run dev`).
- [x] IPC strategy: Electron renderer communicates with Flask via HTTP (localhost); document decision.

### Phase 2: Core Processing Engine (Completed)
- [x] **Schema Definition**: `MasterProfile`, `JobAnalysis`, `GeneratedDocument` types.
    -   TypeScript interfaces (frontend) + Python dataclasses (backend).
    -   Defines the contract between all layers before any integration work.
- [x] Document Ingestion: PDF/DOCX/TXT parsing.
- [x] AI Orchestrator: Unified API handler for Gemini/Claude.
- [x] Job Analysis: `analyze-job` endpoint to extract requirements (defined input/output schema).

### Phase 3: Template & Document Generation (Completed)
- [x] **Output Format**: DOCX as primary output; PDF export as secondary.
- [x] **Resume Builder**:
    -   "Master Profile" data structure (prerequisite — must be completed first).
    -   Harvard Style Template engine.
    -   Section Toggles (Skills, Volunteer, Hobbies).
    -   Page Limit Enforcer (Max 2 pages; approximated via character/line count heuristic — exact DOCX pagination not guaranteed).
- [x] **Cover Letter Generator**:
    -   Length Control (Max 2 pages).
    -   Header/Footer toggles.

### Phase 4: User Experience & Features (Completed)
- [x] **File Naming Conventions**:
    -   Resume: `[Job Title] - Resume - Applied`
    -   Cover Letter: `[Job Title] - Cover Letter - Applied`
- [x] **Profile Management**: Manual edit of parsed profile data.
- [x] **Template Selection**: Visual picker for layouts (Harvard + Modern).
- [x] **Application Helper UI**:
    -   Salary Context Input: manual entry of market rate range with currency selector (no external API).
    -   Application Q&A (Visa status, "Why us?", start date, willing to relocate).
- [x] **Interview Prep Module**: On-demand Q&A generation (behavioural + technical + questions to ask).

### Phase 5: Testing & Packaging (Completed — Windows)
- [x] **5a — Validation suite**: 60-test pytest suite covering document parsing edge cases (TXT/PDF/DOCX), mocked AI providers (no API calls), generation route integration tests. Run with `npm run test:backend`.
- [x] **5b — Windows packaging**:
    -   Flask backend frozen via PyInstaller `--onedir` → `dist/backend/run_backend/run_backend.exe`
    -   Electron main spawns the frozen Flask in packaged mode; polls `/health` until ready.
    -   First-run API key setup modal (`ApiKeySetup.tsx`); keys stored in `userData/settings.json` via IPC.
    -   `electron-builder` produces `release/Resume Buddy-0.1.0-win.zip` (portable) + `win-unpacked/` directory.
    -   Full build: `npm run dist:win` (build + pyinstaller + electron-builder).
- [ ] macOS packaging (`.dmg`) — deferred to Phase 5c.
- [ ] Code signing (Apple Developer ID for macOS; SmartScreen bypass for Windows) — post-MVP.
- [ ] Auto-update strategy: `electron-updater` — deferred to post-MVP.

## 4. Future Expansion (Web/Mobile)
-   **Web Port**: Host React frontend on Vercel/Netlify; deploy Python backend to AWS Lambda/GCP Cloud Run.
-   **Mobile**: Use React Native for frontend; reuse cloud backend API.
