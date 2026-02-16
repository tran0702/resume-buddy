import { contextBridge, ipcRenderer } from 'electron'

// Expose minimal, safe APIs to the renderer process via contextBridge.
// HTTP communication with Flask uses plain fetch() — no IPC needed for that.
// IPC is used only for settings persistence and Flask lifecycle management.

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('api', {
      platform: process.platform,

      // Settings — read/write from userData/settings.json via main process
      loadSettings: () => ipcRenderer.invoke('settings:load'),
      saveSettings: (settings: unknown) => ipcRenderer.invoke('settings:save', settings),
      hasApiKey: () => ipcRenderer.invoke('settings:hasApiKey'),

      // Flask lifecycle — restart with new env vars after settings change
      restartFlask: () => ipcRenderer.invoke('flask:restart'),
    })
  } catch (error) {
    console.error('[Preload] contextBridge error:', error)
  }
} else {
  // Fallback for non-isolated context (should not occur in production)
  // @ts-ignore
  window.api = { platform: process.platform }
}
