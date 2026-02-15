import { contextBridge } from 'electron'

// Expose minimal, safe APIs to the renderer process via contextBridge.
// The renderer communicates with Flask via plain HTTP fetch — no IPC needed.
// This preload only exposes platform information for OS-specific UI tweaks.

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('api', {
      platform: process.platform
    })
  } catch (error) {
    console.error('[Preload] contextBridge error:', error)
  }
} else {
  // Fallback for non-isolated context (should not occur in production)
  // @ts-ignore
  window.api = { platform: process.platform }
}
