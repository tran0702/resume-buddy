# backend.spec
# PyInstaller spec for the Resume Buddy Flask backend.
#
# Build from project root:
#   .venv/Scripts/pyinstaller backend.spec --distpath dist/backend --workpath dist/build_work --noconfirm
#
# Output: dist/backend/run_backend/   (onedir — run_backend.exe + all DLLs)
# Electron picks this up via extraResources in electron-builder.yml.

import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect complete packages — each returns (datas, binaries, hiddenimports).
# This handles embedded data files (pdfminer CMap pickles, docx templates, etc.)
datas_pdfminer,   binaries_pdfminer,   hiddenimports_pdfminer   = collect_all('pdfminer')
datas_docx,       binaries_docx,       hiddenimports_docx       = collect_all('docx')
datas_genai,      binaries_genai,      hiddenimports_genai      = collect_all('google.genai')
datas_google_auth, binaries_google_auth, hiddenimports_google_auth = collect_all('google.auth')
datas_anthropic,  binaries_anthropic,  hiddenimports_anthropic  = collect_all('anthropic')

a = Analysis(
    ['scripts/run_backend.py'],
    pathex=['.'],               # project root — ensures 'backend' package is found
    binaries=(
        binaries_pdfminer
        + binaries_docx
        + binaries_genai
        + binaries_google_auth
        + binaries_anthropic
    ),
    datas=(
        datas_pdfminer
        + datas_docx
        + datas_genai
        + datas_google_auth
        + datas_anthropic
    ),
    hiddenimports=[
        # backend package and all submodules
        'backend',
        'backend.app',
        'backend.config',
        'backend.api',
        'backend.api.documents',
        'backend.api.jobs',
        'backend.api.profiles',
        'backend.api.generation',
        'backend.api.ai',
        'backend.api.ai.base',
        'backend.api.ai.gemini',
        'backend.api.ai.claude',
        'backend.api.ai.orchestrator',
        'backend.api.ai.schemas',
        'backend.api.templates',
        'backend.api.templates.resume_builder',
        'backend.api.templates.modern_builder',
        'backend.api.templates.cover_letter_builder',
        # Flask internals
        'flask',
        'flask_cors',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.middleware.proxy_fix',
        # pdfminer dynamic codec loading
        'pdfminer.high_level',
        'pdfminer.layout',
        'pdfminer.pdfinterp',
        'pdfminer.pdfdevice',
        'pdfminer.pdfpage',
        'pdfminer.converter',
        'pdfminer.cmapdb',
        'pdfminer.utils',
        'pdfminer.pdffont',
        # python-docx
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.shared',
        'docx.enum.text',
        # google-genai namespace package
        'google.genai',
        'google.genai.types',
        'google.auth',
        'google.auth.credentials',
        'google.auth.transport.requests',
        # anthropic (stub — must be importable even though it raises on use)
        'anthropic',
        # python-dotenv (used in non-frozen dev mode only, but must be importable)
        'dotenv',
    ] + hiddenimports_pdfminer + hiddenimports_docx + hiddenimports_genai
      + hiddenimports_google_auth + hiddenimports_anthropic,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dev-only tools — must not be bundled
        'pytest',
        'fpdf2',
        'fpdf',
        # Unused heavy packages
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='run_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can corrupt DLLs and trigger false AV positives
    console=True,       # Must be True — Electron captures stdout to detect readiness
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='run_backend',  # → dist/backend/run_backend/
)
