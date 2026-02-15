import { app, BrowserWindow, shell } from 'electron'
import { join } from 'path'

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

app.whenReady().then(() => {
  // Windows taskbar grouping ID
  app.setAppUserModelId('com.resumebuddy')

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
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
