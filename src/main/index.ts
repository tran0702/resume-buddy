import { app, BrowserWindow, shell, ipcMain } from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs'

// ---- Settings ---------------------------------------------------------------

interface AppSettings {
  aiProvider: 'gemini' | 'claude'
  geminiApiKey: string
  anthropicApiKey: string
  geminiModel: string
  anthropicModel: string
}

const DEFAULT_SETTINGS: AppSettings = {
  aiProvider: 'gemini',
  geminiApiKey: '',
  anthropicApiKey: '',
  geminiModel: 'gemini-2.5-flash-lite',
  anthropicModel: 'claude-opus-4-5-20250929'
}

function getSettingsPath(): string {
  return join(app.getPath('userData'), 'settings.json')
}

function loadSettings(): AppSettings {
  const settingsPath = getSettingsPath()
  if (!existsSync(settingsPath)) return { ...DEFAULT_SETTINGS }
  try {
    const raw = readFileSync(settingsPath, 'utf-8')
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

function saveSettings(settings: AppSettings): void {
  mkdirSync(app.getPath('userData'), { recursive: true })
  writeFileSync(getSettingsPath(), JSON.stringify(settings, null, 2), 'utf-8')
}

// ---- Flask process management -----------------------------------------------

let flaskProcess: ChildProcess | null = null
const FLASK_PORT = 5001

function getFlaskExePath(): string {
  // extraResources in electron-builder.yml places the onedir output here:
  return join(process.resourcesPath, 'backend', 'run_backend', 'run_backend.exe')
}

function buildFlaskEnv(settings: AppSettings): NodeJS.ProcessEnv {
  return {
    ...process.env,
    FLASK_PORT: String(FLASK_PORT),
    FLASK_DEBUG: 'false',
    AI_PROVIDER: settings.aiProvider,
    GEMINI_API_KEY: settings.geminiApiKey,
    GEMINI_MODEL: settings.geminiModel,
    ANTHROPIC_API_KEY: settings.anthropicApiKey,
    ANTHROPIC_MODEL: settings.anthropicModel,
    PYTHONUNBUFFERED: '1',  // ensures stdout is flushed immediately
  }
}

function spawnFlask(settings: AppSettings): void {
  if (!app.isPackaged) {
    // Dev mode: Flask is started by concurrently in `npm run dev`
    console.log('[Main] Dev mode — Flask managed by concurrently.')
    return
  }

  const exePath = getFlaskExePath()
  if (!existsSync(exePath)) {
    console.error(`[Main] Flask executable not found: ${exePath}`)
    return
  }

  console.log(`[Main] Spawning Flask: ${exePath}`)
  flaskProcess = spawn(exePath, [], {
    env: buildFlaskEnv(settings),
    windowsHide: true,           // suppress console window popup on Windows
    stdio: ['ignore', 'pipe', 'pipe']
  })

  flaskProcess.stdout?.on('data', (data: Buffer) => {
    process.stdout.write(`[Flask] ${data.toString()}`)
  })
  flaskProcess.stderr?.on('data', (data: Buffer) => {
    process.stderr.write(`[Flask] ${data.toString()}`)
  })

  flaskProcess.on('exit', (code, signal) => {
    console.warn(`[Main] Flask exited (code=${code}, signal=${signal})`)
    flaskProcess = null
  })

  flaskProcess.on('error', (err) => {
    console.error(`[Main] Flask spawn error: ${err.message}`)
    flaskProcess = null
  })
}

function killFlask(): void {
  if (flaskProcess && !flaskProcess.killed) {
    console.log('[Main] Terminating Flask process...')
    flaskProcess.kill()
    flaskProcess = null
  }
}

async function waitForFlask(timeoutMs = 20000, pollMs = 300): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${FLASK_PORT}/health`)
      if (res.ok) return true
    } catch {
      // not ready yet — keep polling
    }
    await new Promise<void>((r) => setTimeout(r, pollMs))
  }
  return false
}

// ---- IPC handlers -----------------------------------------------------------

function registerIpcHandlers(): void {
  ipcMain.handle('settings:load', (): AppSettings => {
    return loadSettings()
  })

  ipcMain.handle('settings:save', (_event, settings: AppSettings): { ok: boolean } => {
    saveSettings(settings)
    return { ok: true }
  })

  ipcMain.handle('settings:hasApiKey', (): boolean => {
    // In dev mode, Flask already has keys from .env — always allow through
    if (!app.isPackaged) return true
    const s = loadSettings()
    return s.aiProvider === 'gemini' ? !!s.geminiApiKey : !!s.anthropicApiKey
  })

  ipcMain.handle('flask:restart', async (): Promise<{ ok: boolean }> => {
    killFlask()
    await new Promise<void>((r) => setTimeout(r, 500))
    spawnFlask(loadSettings())
    // In dev mode, Flask is already running via concurrently — just poll
    const ready = await waitForFlask(15000)
    return { ok: ready }
  })
}

// ---- Window -----------------------------------------------------------------

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,               // show only after ready-to-show to prevent white flash
    autoHideMenuBar: true,
    backgroundColor: '#1a1b26', // Tokyo Night background — prevents white flash on load
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,          // required for @electron-toolkit/preload
      contextIsolation: true,  // security baseline — always on
      nodeIntegration: false   // security baseline — always off
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  // Open all external links in the OS default browser, not inside Electron
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // In development: electron-vite injects ELECTRON_RENDERER_URL pointing to Vite dev server
  // In production: load the built renderer HTML file
  if (process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// ---- App lifecycle ----------------------------------------------------------

app.whenReady().then(async () => {
  // Windows taskbar grouping ID
  app.setAppUserModelId('com.resumebuddy')

  registerIpcHandlers()

  const settings = loadSettings()
  spawnFlask(settings)

  if (app.isPackaged) {
    console.log('[Main] Waiting for Flask to be ready...')
    const ready = await waitForFlask(20000)
    if (ready) {
      console.log('[Main] Flask is ready.')
    } else {
      console.error('[Main] Flask did not respond within 20s — opening app anyway.')
    }
  }

  createWindow()

  // macOS: re-create window when dock icon is clicked and no windows exist
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// Quit app when all windows are closed (Windows / Linux behavior)
// On macOS this is handled by the 'activate' event above
app.on('window-all-closed', () => {
  killFlask()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  killFlask()
})
